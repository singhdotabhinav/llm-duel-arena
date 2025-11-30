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
from app.services.dynamodb_service import dynamo_db_servicer, init_db

router = APIRouter()

logger = logging.getLogger(__name__)

# Initialize OAuth
config = Config(environ={
    "GOOGLE_CLIENT_ID": settings.google_client_id,
    "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
})

oauth = OAuth(config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    },
    # Add these to help with session/state handling
    authorize_params={
        'access_type': 'offline',
        'prompt': 'consent'
    }
)


# In-memory session store (for simplicity, use Redis in production)
sessions = {}


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current logged-in user from session"""
    # Check for Starlette Session (Cognito)
    if 'user' in request.session:
        user_data = request.session['user']
        email = user_data.get('email')
        if email:
            user = db.query(User).filter(User.email == email).first()
            if user:
                return user

    # Fallback to custom session_id (Google OAuth legacy)
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None
    
    user_email = sessions[session_id].get("email")
    if not user_email:
        return None
    
    user = db.query(User).filter(User.email == user_email).first()
    return user


@router.get("/login")
async def login(request: Request):
    """Redirect to Google OAuth login"""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file."
        )
    
    redirect_uri = settings.google_redirect_uri
    logger.info("[OAuth] /auth/login invoked. Session before authorize: %s", dict(request.session))
    response = await oauth.google.authorize_redirect(request, redirect_uri)
    logger.info("[OAuth] authorize_redirect returned. Session after authorize: %s", dict(request.session))
    logger.info("[OAuth] Response headers include set-cookie: %s", response.headers.get('set-cookie'))
    return response


@router.get("/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        logger.info("[OAuth] /auth/callback invoked. Incoming session: %s", dict(request.session))
        # Authorize access token with the request that includes session data
        token = await oauth.google.authorize_access_token(request)
        logger.info("[OAuth] Access token obtained successfully")
        user_info = token.get('userinfo')
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
        
        # Get or create user
        user = db.query(User).filter(User.email == user_info['email']).first()
        
        if not user:
            user = User(
                id=user_info['sub'],  # Google user ID
                email=user_info['email'],
                name=user_info.get('name'),
                picture=user_info.get('picture'),
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            db.add(user)
        else:
            user.last_login = datetime.utcnow()
            if user_info.get('name'):
                user.name = user_info['name']
            if user_info.get('picture'):
                user.picture = user_info['picture']
        
        db.commit()
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        sessions[session_id] = {
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "user_id": user.id
        }
        
        # Redirect to home with session cookie
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=30 * 24 * 60 * 60,  # 30 days
            samesite="lax"
        )
        logger.info("[OAuth] Login successful for %s. session_id cookie set.", user.email)
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
async def get_user_info(request: Request, db: Session = Depends(get_db)):
    """Get current user info (API endpoint for frontend)"""
    user = get_current_user(request, db)
    if not user:
        return {"logged_in": False}
    
    return {
        "logged_in": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture
        }
    }


# Initialize database on module import
init_db()

