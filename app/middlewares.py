# middlewares.py
import os
from fastapi import Request, HTTPException
import logging


async def limit_request_size(request: Request, call_next):
    max_request_size = 1048576  # 1 MB
    content_length = int(request.headers.get("content-length", 0))

    if content_length > max_request_size:
        raise HTTPException(status_code=413, detail="Request Entity Too Large")

    response = await call_next(request)
    return response

async def log_requests(request: Request, call_next):
    logger = logging.getLogger("uvicorn.access")
    logger.info(f"Request: {request.method} {request.url} Headers: {request.headers}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response
