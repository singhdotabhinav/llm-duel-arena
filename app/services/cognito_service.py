"""
AWS Cognito Authentication Service
Handles user signup, login, token verification, and user management
"""

import os
import json
import boto3
import jwt
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from botocore.exceptions import ClientError
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)

# Initialize Cognito client
# Use AWS profile if specified, otherwise use default credentials
if settings.aws_profile:
    session = boto3.Session(profile_name=settings.aws_profile)
    cognito_client = session.client("cognito-idp", region_name=settings.cognito_region)
else:
    # Use default credentials (from ~/.aws/credentials or environment variables)
    cognito_client = boto3.client("cognito-idp", region_name=settings.cognito_region)


class CognitoService:
    """Service for AWS Cognito authentication operations"""

    def __init__(self):
        self.user_pool_id = settings.cognito_user_pool_id
        self.client_id = settings.cognito_client_id
        self.region = settings.cognito_region
        self.domain = settings.cognito_domain

    def get_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS (JSON Web Key Set) from Cognito"""
        jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
        try:
            response = requests.get(jwks_url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token from Cognito"""
        try:
            # Get JWKS
            jwks = self.get_jwks()

            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            # Find the matching key
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    from jwt.algorithms import RSAAlgorithm

                    key = RSAAlgorithm.from_jwk(json.dumps(jwk))
                    break

            if not key:
                logger.error("No matching key found in JWKS")
                return None

            # Verify and decode token
            issuer = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
            decoded = jwt.decode(token, key, algorithms=["RS256"], audience=self.client_id, issuer=issuer)

            return decoded

        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None

    def sign_up(self, email: str, password: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user in Cognito"""
        try:
            sign_up_params = {
                "ClientId": self.client_id,
                "Username": email,
                "Password": password,
                "UserAttributes": [{"Name": "email", "Value": email}],
            }

            if name:
                sign_up_params["UserAttributes"].append({"Name": "name", "Value": name})

            response = cognito_client.sign_up(**sign_up_params)

            return {
                "success": True,
                "user_sub": response.get("UserSub"),
                "code_delivery_details": response.get("CodeDeliveryDetails"),
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Cognito sign up error: {error_code} - {error_message}")
            return {"success": False, "error_code": error_code, "error_message": error_message}
        except Exception as e:
            logger.error(f"Unexpected error during sign up: {e}")
            return {"success": False, "error_message": str(e)}

    def confirm_sign_up(self, email: str, confirmation_code: str) -> Dict[str, Any]:
        """Confirm user signup with verification code"""
        try:
            response = cognito_client.confirm_sign_up(
                ClientId=self.client_id, Username=email, ConfirmationCode=confirmation_code
            )

            return {"success": True, "message": "User confirmed successfully"}

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Cognito confirm sign up error: {error_code} - {error_message}")
            return {"success": False, "error_code": error_code, "error_message": error_message}

    def initiate_auth(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and get tokens"""
        try:
            response = cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow="ADMIN_NO_SRP_AUTH",
                AuthParameters={"USERNAME": email, "PASSWORD": password},
            )

            authentication_result = response.get("AuthenticationResult", {})

            return {
                "success": True,
                "access_token": authentication_result.get("AccessToken"),
                "id_token": authentication_result.get("IdToken"),
                "refresh_token": authentication_result.get("RefreshToken"),
                "expires_in": authentication_result.get("ExpiresIn"),
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Cognito auth error: {error_code} - {error_message}")
            return {"success": False, "error_code": error_code, "error_message": error_message}

    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information using access token"""
        try:
            response = cognito_client.get_user(AccessToken=access_token)

            user_attributes = {attr["Name"]: attr["Value"] for attr in response.get("UserAttributes", [])}

            return {
                "username": response.get("Username"),
                "email": user_attributes.get("email"),
                "name": user_attributes.get("name"),
                "sub": user_attributes.get("sub"),
                "email_verified": user_attributes.get("email_verified", "false") == "true",
            }

        except ClientError as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            response = cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={"REFRESH_TOKEN": refresh_token},
            )

            authentication_result = response.get("AuthenticationResult", {})

            return {
                "success": True,
                "access_token": authentication_result.get("AccessToken"),
                "id_token": authentication_result.get("IdToken"),
                "expires_in": authentication_result.get("ExpiresIn"),
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Token refresh error: {error_code} - {error_message}")
            return {"success": False, "error_code": error_code, "error_message": error_message}

    def forgot_password(self, email: str) -> Dict[str, Any]:
        """Initiate forgot password flow"""
        try:
            response = cognito_client.forgot_password(ClientId=self.client_id, Username=email)

            return {"success": True, "code_delivery_details": response.get("CodeDeliveryDetails")}

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Forgot password error: {error_code} - {error_message}")
            return {"success": False, "error_code": error_code, "error_message": error_message}

    def confirm_forgot_password(self, email: str, confirmation_code: str, new_password: str) -> Dict[str, Any]:
        """Confirm password reset"""
        try:
            response = cognito_client.confirm_forgot_password(
                ClientId=self.client_id, Username=email, ConfirmationCode=confirmation_code, Password=new_password
            )

            return {"success": True, "message": "Password reset successfully"}

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Confirm forgot password error: {error_code} - {error_message}")
            return {"success": False, "error_code": error_code, "error_message": error_message}

    def get_hosted_ui_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Generate Cognito Hosted UI URL for OAuth flow"""
        if not self.domain:
            raise ValueError("Cognito domain not configured")

        base_url = f"https://{self.domain}.auth.{self.region}.amazoncognito.com"
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
        }

        if state:
            params["state"] = state

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}/oauth2/authorize?{query_string}"


# Global instance
cognito_service = CognitoService()
