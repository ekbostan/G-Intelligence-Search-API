from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import os

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self';"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

def authenticate(request: Request):
    valid_api_keys = os.getenv('VALID_API_KEYS', '').split(',')
    api_key = request.headers.get('X-API-KEY')
    if api_key not in valid_api_keys:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API Key")
