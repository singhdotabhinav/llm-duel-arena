"""
Security middleware for LLM Duel Arena
Provides security headers, CORS, rate limiting, and error handling
"""

import logging
from typing import Callable, List
from fastapi import Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# Rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="memory://",  # Use memory storage (cheapest, works for single Lambda)
    headers_enabled=True,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)

        # Content Security Policy - restrict resource loading
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow inline scripts for templates
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Prevent referrer leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Enforce HTTPS in production (HSTS)
        # Only set if using HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Permissions Policy - disable unnecessary browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=(), usb=()"

        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handler to prevent information disclosure
    """

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Log the full error server-side
            logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")

            # Return generic error to client (don't expose stack traces)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "An internal error occurred. Please try again later.",
                    "error_id": f"{request.url.path}_{id(exc)}",  # Include error ID for debugging
                },
            )


def setup_cors(app, cors_origins: List[str]):
    """
    Configure CORS middleware

    Args:
        app: FastAPI application instance
        cors_origins: List of allowed origins
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )
    logger.info(f"CORS configured with origins: {cors_origins}")


def setup_rate_limiting(app):
    """
    Configure rate limiting for the application

    Args:
        app: FastAPI application instance
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting configured")


def add_security_headers(app):
    """
    Add security headers middleware

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware added")


def error_handler_middleware(app):
    """
    Add error handling middleware

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(ErrorHandlerMiddleware)
    logger.info("Error handler middleware added")
