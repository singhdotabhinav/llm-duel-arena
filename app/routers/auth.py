from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from datetime import datetime
import secrets
import logging

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.services.dynamodb_service import dynamodb_service

router = APIRouter()

logger = logging.getLogger(__name__)

# Initialize OAuth
config = Config(
    environ={
        "GOOGLE_CLIENT_ID": settings.google_client_id,
        "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
    }
)

oauth = OAuth(config)

oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
    # Add these to help with session/state handling
    authorize_params={"access_type": "offline", "prompt": "consent"},
)


# In-memory session store (for simplicity, use Redis in production)
sessions = {}


def get_current_user(request: Request):
    """Get current logged-in user from session"""
    # Check for Starlette Session (Cognito)
    if "user" in request.session:
        user_data = request.session["user"]
        email = user_data.get("email")
        if email:
            # Return a simple object or dict that mimics the User model
            # For now, just returning the session data is often enough,
            # but let's try to get from DynamoDB if needed.
            # user = dynamodb_service.get_user(email)
            # return user

            # Actually, the session data usually has what we need (id, email, name)
            # Let's return a simple object
            class UserObj:
                def __init__(self, data):
                    self.id = data.get("sub") or data.get("id") or data.get("email")
                    self.email = data.get("email")
                    self.name = data.get("name")
                    self.picture = data.get("picture")

            return UserObj(user_data)

    # Fallback to custom session_id (Google OAuth legacy)
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None

    # The session store already holds the user data for legacy Google OAuth
    # We can construct a UserObj from it directly.
    session_data = sessions[session_id]
    if not session_data:
        return None

    class UserObj:
        def __init__(self, data):
            self.id = data.get("user_id") or data.get("email")  # Assuming user_id is stored
            self.email = data.get("email")
            self.name = data.get("name")
            self.picture = data.get("picture")

    return UserObj(session_data)


@router.get("/login")
async def login(request: Request):
    """Redirect to Google OAuth login"""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file.",
        )

    redirect_uri = settings.google_redirect_uri

    # Validate redirect URI against whitelist
    if redirect_uri not in settings.allowed_redirect_uris:
        logger.error(f"Invalid redirect URI: {redirect_uri}. Not in whitelist: {settings.allowed_redirect_uris}")
        raise HTTPException(status_code=500, detail="OAuth redirect URI not properly configured. Contact administrator.")

    logger.info("[OAuth] /auth/login invoked. Session before authorize: %s", dict(request.session))
    response = await oauth.google.authorize_redirect(request, redirect_uri)
    logger.info("[OAuth] authorize_redirect returned. Session after authorize: %s", dict(request.session))
    logger.info("[OAuth] Response headers include set-cookie: %s", response.headers.get("set-cookie"))
    return response


@router.get("/callback")
async def auth_callback(request: Request):
    """Handle Google OAuth callback"""
    try:
        logger.info("[OAuth] /auth/callback invoked. Incoming session: %s", dict(request.session))
        # Authorize access token with the request that includes session data
        token = await oauth.google.authorize_access_token(request)
        logger.info("[OAuth] Access token obtained successfully")
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        # Get or create user in DynamoDB
        email = user_info["email"]
        user = dynamodb_service.get_user(email)

        if not user:
            # Create new user
            user_data = {
                "email": email,
                "id": user_info["sub"],  # Google user ID
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "created_at": datetime.utcnow().isoformat(),
                "last_login": datetime.utcnow().isoformat(),
            }
            dynamodb_service.create_user(user_data)
            user = user_data
        else:
            # Update last login
            dynamodb_service.update_user_login(email)
            # Update name/picture if provided
            if user_info.get("name") and not user.get("name"):
                dynamodb_service.update_user(email, {"name": user_info["name"]})
            if user_info.get("picture") and not user.get("picture"):
                dynamodb_service.update_user(email, {"picture": user_info["picture"]})
            user = dynamodb_service.get_user(email) or user

        # Create session
        session_id = secrets.token_urlsafe(32)
        user_email = user.get("email") if isinstance(user, dict) else user.email
        user_name = user.get("name") if isinstance(user, dict) else user.name
        user_picture = user.get("picture") if isinstance(user, dict) else user.picture
        user_id = user.get("id") if isinstance(user, dict) else (user.get("sub") if isinstance(user, dict) else user.id)
        sessions[session_id] = {"email": user_email, "name": user_name, "picture": user_picture, "user_id": user_id}

        # Redirect to home with session cookie
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_id", value=session_id, httponly=True, max_age=30 * 24 * 60 * 60, samesite="lax"  # 30 days
        )
        logger.info("[OAuth] Login successful for %s. session_id cookie set.", user_email)
        return response

    except Exception as e:
        logger.exception("[OAuth] Authentication failed: %s", e)
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.get("/logout")
async def logout(request: Request):
    """Logout user"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]

    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session_id")
    return response


@router.get("/user")
async def get_user_info(request: Request):
    """Get current user info (API endpoint for frontend)"""
    user = get_current_user(request)
    if not user:
        return {"logged_in": False}

    return {"logged_in": True, "user": {"id": user.id, "email": user.email, "name": user.name, "picture": user.picture}}
