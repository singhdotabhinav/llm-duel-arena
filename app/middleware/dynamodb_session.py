"""
DynamoDB Session Middleware for FastAPI/Starlette
Replaces cookie-based session storage with DynamoDB-backed sessions
"""

import logging
import time
from typing import Any, Dict, Optional

from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.config import settings
from ..services.session_store import get_session_store_instance

logger = logging.getLogger(__name__)

# Cookie name for session ID
SESSION_COOKIE_NAME = "session_id"
SESSION_MAX_AGE = 3600  # 1 hour default


class DynamoDBSessionDict:
    """
    Dict-like wrapper for DynamoDB session data
    Provides interface compatible with Starlette's session dict
    """

    def __init__(self, session_id: str, session_store, initial_data: Optional[Dict[str, Any]] = None):
        self.session_id = session_id
        self.session_store = session_store
        self._data = initial_data or {}
        self._modified = False
        self._deleted = False

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._modified = True

    def __delitem__(self, key: str) -> None:
        if key in self._data:
            del self._data[key]
            self._modified = True

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def pop(self, key: str, default: Any = None) -> Any:
        if key in self._data:
            value = self._data.pop(key)
            self._modified = True
            return value
        return default

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def clear(self) -> None:
        self._data.clear()
        self._modified = True
        self._deleted = True

    def update(self, other: Dict[str, Any]) -> None:
        self._data.update(other)
        self._modified = True

    def save(self) -> bool:
        """Save session data to DynamoDB"""
        if self._deleted:
            # Session was cleared, delete from DynamoDB
            return self.session_store.delete_session(self.session_id)
        elif self._modified:
            # Update session data in DynamoDB
            success = self.session_store.update_session(self.session_id, self._data)
            if success:
                # Extend TTL on update
                self.session_store.extend_session(self.session_id, SESSION_MAX_AGE)
            return success
        return True  # No changes, nothing to save

    def create_new(self) -> str:
        """Create a new session and return session_id"""
        new_session_id = self.session_store.create_session(self._data, SESSION_MAX_AGE)
        return new_session_id


class DynamoDBSessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware that provides DynamoDB-backed session storage
    Compatible with Starlette's session interface
    """

    def __init__(self, app, session_cookie: str = SESSION_COOKIE_NAME, max_age: int = SESSION_MAX_AGE):
        super().__init__(app)
        self.session_cookie = session_cookie
        self.max_age = max_age
        self.session_store = get_session_store_instance()
        logger.info(f"DynamoDB Session Middleware initialized (cookie: {session_cookie}, max_age: {max_age}s)")

    async def dispatch(self, request: Request, call_next):
        # Get session_id from cookie
        session_id = request.cookies.get(self.session_cookie)

        # Load session data from DynamoDB (or create new session)
        session_data = None
        if session_id:
            session_data = self.session_store.get_session(session_id)
            if session_data is None:
                # Session expired or not found, create new one
                logger.debug(f"Session {session_id[:8]}... not found or expired, creating new session")
                session_id = None

        # Create session dict-like object
        if session_id:
            session = DynamoDBSessionDict(session_id, self.session_store, session_data)
        else:
            # New session - will create ID when first modified
            session = DynamoDBSessionDict("", self.session_store, {})
            session_id = None

        # Attach session to request (compatible with Starlette's session interface)
        request.state.session = session
        request.session = session  # Also set for compatibility

        # Process request
        response = await call_next(request)

        # Save session if modified
        if hasattr(request.state, "session"):
            session = request.state.session
            if isinstance(session, DynamoDBSessionDict):
                # Check if session was modified or needs creation
                if session._modified or session._deleted:
                    if session._deleted:
                        # Session was cleared
                        if session.session_id:
                            session.save()  # Delete from DynamoDB
                        # Remove cookie
                        response = self._delete_session_cookie(response)
                    elif session.session_id:
                        # Update existing session
                        session.save()
                        # Extend cookie expiration
                        response = self._set_session_cookie(response, session.session_id)
                    else:
                        # New session, create in DynamoDB
                        new_session_id = session.create_new()
                        response = self._set_session_cookie(response, new_session_id)
                elif not session.session_id and len(session._data) > 0:
                    # Session has data but no ID yet, create it
                    new_session_id = session.create_new()
                    response = self._set_session_cookie(response, new_session_id)
                elif session.session_id:
                    # Session exists but wasn't modified, extend TTL anyway (sliding expiration)
                    # Only extend if session has data (active session)
                    if len(session._data) > 0:
                        self.session_store.extend_session(session.session_id, self.max_age)
                        response = self._set_session_cookie(response, session.session_id)

        return response

    def _set_session_cookie(self, response: Response, session_id: str) -> Response:
        """Set session cookie in response"""
        # Ensure headers are mutable
        if not isinstance(response.headers, MutableHeaders):
            headers = MutableHeaders(response.headers)
        else:
            headers = response.headers

        # Build cookie string
        cookie_parts = [
            f"{self.session_cookie}={session_id}",
            "Path=/",
            f"Max-Age={self.max_age}",
            "SameSite=Lax",
        ]

        if not settings.is_local:
            # HTTPS only in production
            cookie_parts.append("Secure")

        cookie_value = "; ".join(cookie_parts)

        # Set cookie header (replace existing if present)
        if "Set-Cookie" in headers:
            # Remove existing Set-Cookie for this cookie name
            existing_cookies = headers.get_list("Set-Cookie")
            filtered = [c for c in existing_cookies if not c.startswith(f"{self.session_cookie}=")]
            headers.pop("Set-Cookie", None)
            for cookie in filtered:
                headers.append("Set-Cookie", cookie)

        headers.append("Set-Cookie", cookie_value)
        response.headers = headers
        return response

    def _delete_session_cookie(self, response: Response) -> Response:
        """Delete session cookie"""
        if not isinstance(response.headers, MutableHeaders):
            headers = MutableHeaders(response.headers)
        else:
            headers = response.headers

        # Build delete cookie string
        cookie_parts = [
            f"{self.session_cookie}=",
            "Path=/",
            "Max-Age=0",
            "SameSite=Lax",
        ]

        if not settings.is_local:
            cookie_parts.append("Secure")

        cookie_value = "; ".join(cookie_parts)

        # Set cookie header to delete
        if "Set-Cookie" in headers:
            existing_cookies = headers.get_list("Set-Cookie")
            filtered = [c for c in existing_cookies if not c.startswith(f"{self.session_cookie}=")]
            headers.pop("Set-Cookie", None)
            for cookie in filtered:
                headers.append("Set-Cookie", cookie)

        headers.append("Set-Cookie", cookie_value)
        response.headers = headers
        return response
