"""
Shared authentication utilities
Provides get_current_user function used across routers
"""

from fastapi import Request
from typing import Optional, Dict, Any


def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current logged-in user from session.
    Works with both Cognito OIDC and legacy auth systems.
    
    Returns:
        User data dict with keys: id, email, name, picture
        None if user is not logged in
    """
    user_data = request.session.get("user")
    if not user_data:
        return None

    # Return user data from session
    # For Cognito OIDC, this contains: sub, email, name, picture
    # For legacy auth, this may contain: user_id, email, name, picture
    return user_data


def get_current_user_obj(request: Request):
    """
    Get current user as an object (for compatibility with old code).
    
    Returns:
        UserObj instance or None
    """
    user_data = get_current_user(request)
    if not user_data:
        return None

    class UserObj:
        def __init__(self, data):
            self.id = data.get("sub") or data.get("id") or data.get("user_id") or data.get("email")
            self.email = data.get("email")
            self.name = data.get("name")
            self.picture = data.get("picture", "")

    return UserObj(user_data)


