```
"""
AWS Cognito Authentication Router
Handles signup, login, token verification, and user management via Cognito
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
import logging
import secrets

from app.core.config import settings
from app.services.dynamodb_service import dynamodb_service

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory session store (for JWT tokens)
# In production, use Redis or DynamoDB
sessions = {}


# Request/Response Models
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class ConfirmSignUpRequest(BaseModel):
    email: EmailStr
    confirmation_code: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ConfirmForgotPasswordRequest(BaseModel):
    email: EmailStr
    confirmation_code: str
    new_password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current logged-in user from JWT token"""
    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
    else:
        # Try to get from cookie
        token = request.cookies.get("access_token")
    
    if not token:
        return None
    
    # Verify token with Cognito
    decoded = cognito_service.verify_token(token)
    if not decoded:
        return None
    
    # Get user from database
    user_sub = decoded.get('sub')
    email = decoded.get('email')
    
    if not email:
        return None
    
    user = db.query(User).filter(User.email == email).first()
    
    # Create user if doesn't exist (first login)
    if not user:
        user = User(
            id=user_sub,
            email=email,
            name=decoded.get('name'),
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.last_login = datetime.utcnow()
        if decoded.get('name') and not user.name:
            user.name = decoded.get('name')
        db.commit()
    
    return user


@router.post("/signup")
async def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    if not settings.use_cognito:
        raise HTTPException(status_code=500, detail="Cognito is not enabled")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Sign up in Cognito
    result = cognito_service.sign_up(request.email, request.password, request.name)
    
    if not result.get('success'):
        error_msg = result.get('error_message', 'Signup failed')
        raise HTTPException(status_code=400, detail=error_msg)
    
    return {
        "message": "User registered successfully. Please check your email for confirmation code.",
        "user_sub": result.get('user_sub'),
        "code_delivery_details": result.get('code_delivery_details')
    }


@router.post("/confirm-signup")
async def confirm_signup(request: ConfirmSignUpRequest, db: Session = Depends(get_db)):
    """Confirm user signup with verification code"""
    if not settings.use_cognito:
        raise HTTPException(status_code=500, detail="Cognito is not enabled")
    
    result = cognito_service.confirm_sign_up(request.email, request.confirmation_code)
    
    if not result.get('success'):
        error_msg = result.get('error_message', 'Confirmation failed')
        raise HTTPException(status_code=400, detail=error_msg)
    
    return {"message": "User confirmed successfully. You can now login."}


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return tokens"""
    if not settings.use_cognito:
        raise HTTPException(status_code=500, detail="Cognito is not enabled")
    
    # Authenticate with Cognito
    result = cognito_service.initiate_auth(request.email, request.password)
    
    if not result.get('success'):
        error_code = result.get('error_code', '')
        error_msg = result.get('error_message', 'Login failed')
        
        # Handle specific Cognito errors
        if error_code == 'UserNotConfirmedException':
            raise HTTPException(status_code=400, detail="Please confirm your email before logging in")
        elif error_code == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Invalid email or password")
        else:
            raise HTTPException(status_code=401, detail=error_msg)
    
    # Get user info
    access_token = result.get('access_token')
    user_info = cognito_service.get_user_info(access_token)
    
    if not user_info:
        raise HTTPException(status_code=500, detail="Failed to get user information")
    
    # Get or create user in database
    user = db.query(User).filter(User.email == user_info['email']).first()
    if not user:
        user = User(
            id=user_info['sub'],
            email=user_info['email'],
            name=user_info.get('name'),
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        db.add(user)
    else:
        user.last_login = datetime.utcnow()
        if user_info.get('name') and not user.name:
            user.name = user_info['name']
    
    db.commit()
    
    # Create session
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "access_token": access_token,
        "refresh_token": result.get('refresh_token'),
        "id_token": result.get('id_token'),
        "email": user_info['email'],
        "user_id": user_info['sub']
    }
    
    # Return tokens
    response = JSONResponse({
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": result.get('refresh_token'),
        "id_token": result.get('id_token'),
        "expires_in": result.get('expires_in'),
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    })
    
    # Set HTTP-only cookie with access token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=result.get('expires_in', 3600),
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    
    return response


@router.post("/refresh-token")
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token"""
    if not settings.use_cognito:
        raise HTTPException(status_code=500, detail="Cognito is not enabled")
    
    result = cognito_service.refresh_token(request.refresh_token)
    
    if not result.get('success'):
        error_msg = result.get('error_message', 'Token refresh failed')
        raise HTTPException(status_code=401, detail=error_msg)
    
    response = JSONResponse({
        "access_token": result.get('access_token'),
        "id_token": result.get('id_token'),
        "expires_in": result.get('expires_in')
    })
    
    # Update cookie
    response.set_cookie(
        key="access_token",
        value=result.get('access_token'),
        httponly=True,
        max_age=result.get('expires_in', 3600),
        samesite="lax",
        secure=False
    )
    
    return response


@router.get("/logout")
async def logout(request: Request):
    """Logout user"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    response.delete_cookie("session_id")
    return response


@router.get("/user")
async def get_user_info(request: Request, db: Session = Depends(get_db)):
    """Get current user info"""
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


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Initiate forgot password flow"""
    if not settings.use_cognito:
        raise HTTPException(status_code=500, detail="Cognito is not enabled")
    
    result = cognito_service.forgot_password(request.email)
    
    if not result.get('success'):
        error_msg = result.get('error_message', 'Failed to initiate password reset')
        raise HTTPException(status_code=400, detail=error_msg)
    
    return {
        "message": "Password reset code sent to your email",
        "code_delivery_details": result.get('code_delivery_details')
    }


@router.post("/confirm-forgot-password")
async def confirm_forgot_password(request: ConfirmForgotPasswordRequest):
    """Confirm password reset"""
    if not settings.use_cognito:
        raise HTTPException(status_code=500, detail="Cognito is not enabled")
    
    result = cognito_service.confirm_forgot_password(
        request.email,
        request.confirmation_code,
        request.new_password
    )
    
    if not result.get('success'):
        error_msg = result.get('error_message', 'Password reset failed')
        raise HTTPException(status_code=400, detail=error_msg)
    
    return {"message": "Password reset successfully. You can now login with your new password."}


@router.get("/hosted-ui-login")
async def hosted_ui_login(redirect_uri: Optional[str] = None):
    """Redirect to Cognito Hosted UI for OAuth login"""
    if not settings.use_cognito:
        raise HTTPException(status_code=500, detail="Cognito is not enabled")
    
    if not redirect_uri:
        redirect_uri = settings.cognito_callback_url
    
    state = secrets.token_urlsafe(32)
    auth_url = cognito_service.get_hosted_ui_url(redirect_uri, state)
    
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/callback")
async def auth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle Cognito OAuth callback"""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    
    # Exchange code for tokens (simplified - in production, do this server-side)
    # For now, redirect to frontend with code
    # Frontend should exchange code for tokens
    
    return RedirectResponse(url=f"/?code={code}&state={state}", status_code=302)


# Initialize database on module import
init_db()

