import json
import logging
import os
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from exceptions.exceptions import BadRequestError, InternalError, ViewError
from routes import threat_designer_route, attack_tree_route
from utils.utils import custom_serializer, mask_sensitive_attributes

PORTAL_REDIRECT_URL = os.getenv("PORTAL_REDIRECT_URL", "http://localhost:3000")
TRUSTED_ORIGINS_RAW = os.getenv("TRUSTED_ORIGINS", "http://localhost:3000")
trusted_origins = [o.strip() for o in TRUSTED_ORIGINS_RAW.split(",")]

logger = logging.getLogger(__name__)

app = FastAPI(title="Threat Designer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=trusted_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(threat_designer_route.router)
app.include_router(attack_tree_route.router)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=63072000;"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    sensitive_headers = {"authorization", "cookie"}
    safe_headers = {k: v for k, v in request.headers.items() if k.lower() not in sensitive_headers}
    logger.debug("Incoming request: %s %s headers=%s", request.method, request.url.path, safe_headers)
    return await call_next(request)


@app.exception_handler(InternalError)
async def handle_internal_errors(request: Request, ex: InternalError):
    logger.error("Internal Server Error: %s", str(ex))
    return JSONResponse(status_code=500, content={"code": type(ex).__name__, "message": str(ex)})


@app.exception_handler(ViewError)
async def handle_view_errors(request: Request, ex: ViewError):
    logger.warning("Application Error: %s", str(ex))
    return JSONResponse(status_code=ex.STATUS, content=ex.to_dict())


@app.exception_handler(BadRequestError)
async def handle_bad_request_errors(request: Request, ex: BadRequestError):
    logger.warning("Bad Request Error: %s", str(ex))
    error_message = getattr(ex, "message", str(ex))
    return JSONResponse(status_code=400, content={"code": type(ex).__name__, "message": error_message})


@app.exception_handler(Exception)
async def handle_service_errors(request: Request, ex: Exception):
    logger.error("Unhandled exception: %s", str(ex), exc_info=True)
    return JSONResponse(status_code=500, content={"code": type(ex).__name__, "message": str(ex)})


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("index:app", host="0.0.0.0", port=port, reload=False)
