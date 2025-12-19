"""
AWS Cognito OIDC Authentication Router using authlib
Implements OAuth 2.0 / OpenID Connect flow with Cognito Hosted UI
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from typing import Optional
import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
import json
import base64
import struct
import logging

from app.core.config import settings
from app.core.security import create_access_token
from app.core.auth import get_current_user_obj as get_current_user
from app.services.dynamodb_service import dynamodb_service
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize OAuth with authlib (similar to Flask example)
# Note: OAuth client needs to be initialized without Config for proper session handling
oauth = OAuth()

# Register Cognito as OIDC provider (similar to Flask example)
# Build registration kwargs
register_kwargs = {
    "name": "cognito",
    "authority": settings.cognito_authority,
    "client_id": settings.cognito_client_id,
    "server_metadata_url": settings.cognito_server_metadata_url,
    "client_kwargs": {"scope": settings.cognito_scopes},  # These must match Cognito App Client allowed scopes
}

# Only add client_secret if provided (web apps typically don't need it)
if settings.cognito_client_secret:
    register_kwargs["client_secret"] = settings.cognito_client_secret

oauth.register(**register_kwargs)


from ..core.auth import get_current_user_obj as get_current_user


@router.get("/login")
async def login(request: Request):
    """Redirect to Cognito Hosted UI for authentication"""
    if not settings.use_cognito:
        raise HTTPException(status_code=500, detail="Cognito is not enabled")

    if not settings.cognito_user_pool_id or not settings.cognito_client_id:
        raise HTTPException(
            status_code=500,
            detail="Cognito is not configured. Please set COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID in your .env file.",
        )

    redirect_uri = settings.cognito_callback_url

    # Validate redirect URI against whitelist
    if redirect_uri not in settings.allowed_redirect_uris:
        logger.error(f"Invalid Cognito redirect URI: {redirect_uri}. Not in whitelist: {settings.allowed_redirect_uris}")
        raise HTTPException(
            status_code=500, detail="Cognito OAuth redirect URI not properly configured. Contact administrator."
        )

    # CRITICAL: Redirect 127.0.0.1 to localhost to ensure cookies match the callback URL
    # Cognito requires localhost for HTTP callbacks, so we must ensure the session is on localhost
    if request.url.hostname == "127.0.0.1":
        localhost_url = str(request.url).replace("127.0.0.1", "localhost")
        logger.info(f"[Cognito OIDC] Redirecting 127.0.0.1 to localhost: {localhost_url}")
        return RedirectResponse(url=localhost_url)

    # CRITICAL: Cognito only allows HTTP for localhost, not 127.0.0.1
    # AWS Cognito error: "HTTPS is required over HTTP except for http://localhost"
    # So we MUST use localhost in the callback URL, even if user accesses via 127.0.0.1
    # This ensures:
    # 1. Cognito accepts the callback URL (localhost is allowed for HTTP)
    # 2. Browser cookies work (both localhost and 127.0.0.1 cookies work for localhost)
    request_host = request.url.hostname

    # Normalize callback URL to use localhost (required by Cognito)
    original_redirect_uri = redirect_uri
    if "127.0.0.1" in redirect_uri:
        redirect_uri = redirect_uri.replace("127.0.0.1", "localhost")
        logger.info(f"[Cognito OIDC] Changed callback URL from 127.0.0.1 to localhost (Cognito requirement)")

    # Ensure callback URL uses localhost (required by Cognito for HTTP)
    if "localhost" not in redirect_uri:
        logger.error(f"[Cognito OIDC] ❌ Callback URL doesn't use localhost: {redirect_uri}")
        logger.error(
            f"[Cognito OIDC] Cognito requires localhost for HTTP callbacks. Please update COGNITO_CALLBACK_URL in .env"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"Invalid callback URL: {redirect_uri}\n\n"
                "Cognito requires callback URLs to use 'localhost' for HTTP (not '127.0.0.1').\n"
                f"Please update COGNITO_CALLBACK_URL in .env to use 'localhost'.\n"
                f"Expected format: http://localhost:8000/auth/callback"
            ),
        )

    # CRITICAL: Log the exact redirect_uri being sent to Cognito
    # This must EXACTLY match what's configured in Cognito App Client
    logger.info(f"[Cognito OIDC] ===== REDIRECT URI DEBUG =====")
    logger.info(f"[Cognito OIDC] Original redirect_uri from config: {original_redirect_uri}")
    logger.info(f"[Cognito OIDC] Final redirect_uri being sent to Cognito: {redirect_uri}")
    logger.info(f"[Cognito OIDC] Request hostname: {request_host}")
    logger.info(f"[Cognito OIDC] Request URL: {request.url}")
    logger.info(f"[Cognito OIDC] ==============================")
    logger.info(f"[Cognito OIDC] ⚠️  Make sure this EXACT URL is in Cognito App Client → Allowed callback URLs:")
    logger.info(f"[Cognito OIDC] ⚠️  {redirect_uri}")
    logger.info(f"[Cognito OIDC] ==============================")

    # Ensure session is initialized and accessible
    if not hasattr(request, "session"):
        raise HTTPException(status_code=500, detail="Session middleware not configured")

    # CRITICAL: Initialize session BEFORE authlib redirect
    # This ensures the session cookie is set before redirecting to Cognito
    # Starlette only sets cookies when session is modified
    # We MUST modify the session to trigger cookie setting
    if "_session_init" not in request.session:
        request.session["_session_init"] = True
        logger.info("[Cognito OIDC] Session initialized before redirect")
        logger.info(f"[Cognito OIDC] Session keys after init: {list(request.session.keys())}")

    # Force session to be marked as modified
    # This ensures Starlette SessionMiddleware will set the cookie
    # Access the session dict to trigger modification detection
    _ = request.session.get("_session_init")  # Access to ensure session is loaded

    # Use authlib to redirect to Cognito with explicit scope
    # The scope must match what's configured in Cognito App Client
    # authlib will automatically generate and store state in session
    try:
        logger.info(f"[Cognito OIDC] Initiating authorize_redirect with redirect_uri: {redirect_uri}")

        # Create redirect - authlib will add state to session
        # IMPORTANT: authlib stores state with key: _state_cognito_{state_value}
        response = await oauth.cognito.authorize_redirect(
            request,
            redirect_uri,
            scope=settings.cognito_scopes,  # Use configured scopes - must match Cognito App Client settings
        )

        logger.info(f"[Cognito OIDC] authorize_redirect returned response type: {type(response)}")

        # Log session state IMMEDIATELY after authlib adds state
        # This shows what authlib stored
        session_keys = list(request.session.keys())
        state_keys = [k for k in session_keys if k.startswith("_state_cognito_")]
        logger.info(f"[Cognito OIDC] Session keys after authlib redirect: {session_keys}")

        # CRITICAL: Ensure session is saved before redirect
        # Starlette SessionMiddleware only saves session when it's modified
        # authlib modifies the session, but we need to ensure it's persisted
        # Modify session again to trigger save
        request.session["_oauth_redirect_done"] = True

        # Log the redirect URL and verify state is stored
        redirect_url = None
        if hasattr(response, "headers") and "location" in response.headers:
            redirect_url = response.headers["location"]
            logger.info(f"[Cognito OIDC] Redirecting to: {redirect_url[:100]}...")
            # Extract state from redirect URL for debugging
            if "state=" in redirect_url:
                try:
                    url_state = redirect_url.split("state=")[1].split("&")[0]
                    logger.info(f"[Cognito OIDC] State in redirect URL: {url_state}")
                    # Verify this state is in session
                    expected_key = f"_state_cognito_{url_state}"
                    if expected_key in request.session:
                        logger.info(f"[Cognito OIDC] ✅ State key '{expected_key}' found in session!")
                        state_data = request.session.get(expected_key)
                        logger.info(f"[Cognito OIDC] State data: {state_data}")
                    else:
                        logger.error(f"[Cognito OIDC] ❌ State key '{expected_key}' NOT found in session!")
                        logger.error(f"[Cognito OIDC] Available keys: {list(request.session.keys())}")
                        # This is a critical error - state must be in session before redirect
                        # We will still proceed but log heavily
                except Exception as e:
                    logger.error(f"[Cognito OIDC] Error parsing state from URL: {e}")

        # CRITICAL: Force session to be saved by accessing it
        # Starlette SessionMiddleware saves session when response is finalized
        # But we need to ensure the session dict is properly modified
        # Create a new response to ensure session middleware processes it
        from starlette.responses import RedirectResponse as StarletteRedirectResponse

        # Get the redirect URL from authlib's response
        if redirect_url:
            # Create a new redirect response that will trigger session save
            final_response = StarletteRedirectResponse(url=redirect_url, status_code=302)

            # Copy session to ensure it's included
            # The SessionMiddleware will handle setting the cookie
            logger.info(f"[Cognito OIDC] Final session keys before redirect: {list(request.session.keys())}")

            return final_response

        return response
    except Exception as e:
        logger.error(f"[Cognito OIDC] Error creating redirect: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create OAuth redirect: {str(e)}")


@router.get("/callback")
async def authorize(request: Request):
    """Handle Cognito OAuth callback and retrieve user data"""
    # Log all query parameters for debugging
    logger.info(f"[Cognito OIDC] Callback received with params: {dict(request.query_params)}")

    try:
        # Check for OAuth errors first (e.g., invalid_scope)
        error = request.query_params.get("error")
        error_description = request.query_params.get("error_description")

        if error:
            logger.error(f"[Cognito OIDC] OAuth error: {error} - {error_description}")
            error_msg = error_description or error

            # Provide helpful message for invalid_scope error
            if error == "invalid_request" and "scope" in (error_description or "").lower():
                error_msg = (
                    f"Invalid scope error: {error_description}. "
                    f"Requested scopes: '{settings.cognito_scopes}'. "
                    "Please enable these scopes in your Cognito App Client settings:\n"
                    "1. Go to AWS Console → Cognito → User Pools\n"
                    "2. Select your User Pool\n"
                    "3. Go to 'App integration' tab\n"
                    "4. Click on your App Client\n"
                    "5. Scroll to 'Hosted UI' section\n"
                    "6. Under 'Allowed OAuth scopes', enable: openid, email, profile\n"
                    "7. Click 'Save changes'\n"
                    "8. Restart your application"
                )

            raise HTTPException(status_code=400, detail=error_msg)

        logger.info("[Cognito OIDC] Callback received")

        # CRITICAL: Log cookie information FIRST to diagnose why session isn't found
        callback_state = request.query_params.get("state")
        cookies_received = dict(request.cookies)
        cookie_header = request.headers.get("cookie", "Not present")

        logger.info(f"[Cognito OIDC] ===== COOKIE DEBUG =====")
        logger.info(f"[Cognito OIDC] State from callback URL: {callback_state}")
        logger.info(f"[Cognito OIDC] Cookies received: {cookies_received}")
        logger.info(f"[Cognito OIDC] Cookie header: {cookie_header[:200]}")
        logger.info(f"[Cognito OIDC] Request hostname: {request.url.hostname}")
        logger.info(f"[Cognito OIDC] Request scheme: {request.url.scheme}")
        logger.info(f"[Cognito OIDC] Request URL: {request.url}")

        # Check if session cookie is present
        if "session" not in cookies_received:
            logger.error("[Cognito OIDC] ❌ Session cookie NOT received from browser!")
            logger.error("[Cognito OIDC] This means the browser didn't send the cookie back.")
            logger.error("[Cognito OIDC] Possible causes:")
            logger.error("[Cognito OIDC] 1. Cookie was never set (check Set-Cookie header in login response)")
            logger.error("[Cognito OIDC] 2. Cookie domain/path mismatch")
            logger.error("[Cognito OIDC] 3. Browser blocking cookies")
            logger.error("[Cognito OIDC] 4. Cookie expired or cleared")
        else:
            logger.info("[Cognito OIDC] ✅ Session cookie received from browser!")

        logger.info(f"[Cognito OIDC] Session keys: {list(request.session.keys())}")
        logger.info(f"[Cognito OIDC] Full session dict: {dict(request.session)}")
        logger.info(f"[Cognito OIDC] ========================")

        # Check if state exists in session (authlib stores it with provider name prefix)
        state_keys = [k for k in request.session.keys() if "state" in k.lower()]
        logger.info(f"[Cognito OIDC] State-related keys in session: {state_keys}")

        # Check ALL keys for potential state storage
        all_keys = list(request.session.keys())
        logger.info(f"[Cognito OIDC] ALL session keys: {all_keys}")

        # Check for authlib's state key format: _state_cognito_{state_value}
        expected_state_key = f"_state_cognito_{callback_state}" if callback_state else None
        if expected_state_key:
            logger.info(f"[Cognito OIDC] Looking for state key: {expected_state_key}")
            if expected_state_key in request.session:
                state_data = request.session.get(expected_state_key)
                logger.info(f"[Cognito OIDC] Found state data: {state_data}")
            else:
                logger.error(f"[Cognito OIDC] State key NOT found in session!")
                # Check for any _state_cognito_ keys
                all_state_keys = [k for k in all_keys if k.startswith("_state_cognito_")]
                logger.error(f"[Cognito OIDC] Available state keys: {all_state_keys}")

        for key in all_keys:
            value = request.session.get(key)
            logger.info(f"[Cognito OIDC] Session[{key}] = {str(value)[:100] if value else 'None'}")

        # Ensure session is properly initialized
        if not hasattr(request, "session"):
            logger.error("[Cognito OIDC] Session not available")
            raise HTTPException(
                status_code=500, detail="Session not available. Please ensure SessionMiddleware is configured."
            )

        # Authorize access token with the request
        # authlib will verify the state parameter automatically
        # If state verification fails, it might be due to session cookie issues
        try:
            token = await oauth.cognito.authorize_access_token(request)
        except Exception as state_error:
            error_str = str(state_error)
            logger.error(f"[Cognito OIDC] State verification failed: {error_str}")
            logger.error(f"[Cognito OIDC] Callback state: {callback_state}")
            logger.error(f"[Cognito OIDC] Session keys: {list(request.session.keys())}")
            logger.error(f"[Cognito OIDC] Full session: {dict(request.session)}")

            # Check if it's specifically a state mismatch error
            if "mismatching_state" in error_str.lower() or "state" in error_str.lower():
                # Try to manually verify state if stored differently
                # authlib might store state with a different key format
                all_session_keys = list(request.session.keys())
                logger.info(f"[Cognito OIDC] All session keys for debugging: {all_session_keys}")

                # Check common authlib state key patterns
                possible_state_keys = [
                    "_state_cognito",
                    "cognito_state",
                    "_oauth_state_cognito",
                    f"_state_{settings.cognito_client_id}",
                ]

                found_state = None
                for key in possible_state_keys:
                    if key in request.session:
                        found_state = request.session.get(key)
                        logger.info(f"[Cognito OIDC] Found state in key '{key}': {found_state}")
                        break

                if not found_state:
                    logger.error("[Cognito OIDC] No state found in session - session cookie likely not maintained")
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Session state not found. This means your browser isn't maintaining cookies between redirects.\n\n"
                            "Solutions:\n"
                            "1. Ensure cookies are enabled in your browser\n"
                            "2. Don't use incognito/private mode\n"
                            "3. Check browser DevTools → Application → Cookies → localhost:8000\n"
                            "4. Clear all cookies and try again\n"
                            "5. Ensure APP_SECRET_KEY is set in .env file"
                        ),
                    )

            # Re-raise the original error with context
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Authentication failed: 400: {error_str}\n\n"
                    "Common fixes:\n"
                    "1. Clear browser cookies for localhost:8000\n"
                    "2. Ensure APP_SECRET_KEY is set and consistent in .env\n"
                    "3. Don't use incognito/private browsing mode\n"
                    "4. Check browser DevTools → Application → Cookies\n"
                    "5. Restart your application server\n"
                    f"6. Callback state received: {callback_state}\n"
                    f"7. Session keys: {list(request.session.keys())}"
                ),
            )

        logger.info("[Cognito OIDC] Access token obtained successfully")
        logger.debug(f"[Cognito OIDC] Token keys: {list(token.keys())}")

        # Get user info from token (authlib should fetch it automatically)
        user_info = token.get("userinfo")

        if not user_info:
            # If userinfo not automatically fetched, fetch it manually from userinfo endpoint
            logger.info("[Cognito OIDC] Userinfo not in token, fetching from endpoint")
            try:
                # Use the access token to fetch userinfo
                access_token = token.get("access_token")
                if access_token:
                    resp = await oauth.cognito.get("userinfo", token={"access_token": access_token})
                    user_info = resp.json()
                    logger.info(f"[Cognito OIDC] Userinfo fetched: {list(user_info.keys())}")
                else:
                    logger.error("[Cognito OIDC] No access token in response")
                    raise HTTPException(status_code=400, detail="No access token received from Cognito")
            except Exception as e:
                logger.error(f"[Cognito OIDC] Failed to get userinfo: {e}", exc_info=True)
                raise HTTPException(status_code=400, detail=f"Failed to get user info from Cognito: {str(e)}")

        if not user_info:
            raise HTTPException(status_code=400, detail="No user information available")

        # Store user data in session
        request.session["user"] = {
            "sub": user_info.get("sub"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture", ""),
        }

        # Update DynamoDB
        try:
            from ..services.dynamodb_service import dynamodb_service

            email = user_info.get("email")
            if email:
                dynamodb_service.update_user_login(email)
                logger.info(f"[Cognito OIDC] Updated DynamoDB for user {email}")
        except Exception as e:
            logger.error(f"[Cognito OIDC] Failed to update DynamoDB: {e}")

        logger.info(f"[Cognito OIDC] Login successful for {user_info.get('email')}")

        # Redirect to home page
        return RedirectResponse(url="/", status_code=302)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"[Cognito OIDC] Unexpected error in callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=(
                f"Unexpected error during authentication: {str(e)}\n\n"
                "Please check server logs for details.\n"
                f"Error type: {type(e).__name__}"
            ),
        )


@router.get("/logout")
async def logout(request: Request):
    """Logout user and clear session"""
    # Clear session
    request.session.pop("user", None)

    # Optionally redirect to Cognito logout URL
    if settings.cognito_domain:
        # Handle both formats: full domain or just prefix
        if ".auth." in settings.cognito_domain or ".amazoncognito.com" in settings.cognito_domain:
            # Already a full domain, use as-is
            domain = settings.cognito_domain
        else:
            # Just a prefix, construct full domain
            domain = f"{settings.cognito_domain}.auth.{settings.cognito_region}.amazoncognito.com"

        logout_url = f"https://{domain}/logout?client_id={settings.cognito_client_id}&logout_uri={settings.cognito_logout_url}"
        return RedirectResponse(url=logout_url, status_code=302)

    # Simple redirect to home
    return RedirectResponse(url="/", status_code=302)


@router.get("/user")
async def get_user_info(request: Request):
    """Get current user info (API endpoint for frontend)"""
    user = get_current_user(request)
    if not user:
        return {"logged_in": False}

    return {"logged_in": True, "user": {"id": user.id, "email": user.email, "name": user.name, "picture": user.picture}}


@router.get("/debug/session")
async def debug_session(request: Request):
    """Debug endpoint to check session cookie and state"""
    from fastapi.responses import JSONResponse

    # Try to set a test value in session to see if cookie gets set
    request.session["_debug_test"] = "test_value"

    session_data = {
        "has_session": hasattr(request, "session"),
        "session_keys": list(request.session.keys()) if hasattr(request, "session") else [],
        "session_data": dict(request.session) if hasattr(request, "session") else {},
        "cookies_received": dict(request.cookies),
        "cookie_header": request.headers.get("cookie", "Not present"),
        "user_agent": request.headers.get("user-agent", "Not present"),
        "request_url": str(request.url),
        "request_hostname": request.url.hostname,
        "request_scheme": request.url.scheme,
        "session_modified": getattr(request.session, "_modified", "unknown") if hasattr(request, "session") else "N/A",
    }

    # Create response
    response = JSONResponse(content=session_data)

    # Check what cookies will be set in response headers
    # Starlette SessionMiddleware sets cookies after response is created
    # We need to check the response after it's been processed
    # For now, add info about what should happen
    session_data["note"] = (
        "Session cookie should be set by SessionMiddleware. Check browser DevTools → Network → Response Headers → Set-Cookie"
    )
    session_data["session_cookie_name"] = "session"

    # The Set-Cookie header will be added by SessionMiddleware
    # We can't read it here because middleware processes after this
    # But we can verify the session was modified
    if hasattr(request, "session"):
        # Force session to be saved
        request.session["_debug_accessed"] = True

    return response
