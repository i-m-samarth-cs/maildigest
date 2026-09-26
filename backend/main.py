"""
MailDigest FastAPI backend.
"""
import os
import re
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from api.auth import router as auth_router
from api.emails import router as emails_router
from api.accounts import router as accounts_router
from api.settings import router as settings_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Exact origins (comma-separated)
_raw_origins = os.environ.get("ALLOWED_ORIGINS", FRONTEND_URL)
ALLOWED_ORIGINS: List[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# Wildcard origin patterns (comma-separated regexes), e.g. ".*\.vercel\.app$"
_raw_patterns = os.environ.get("ALLOWED_ORIGIN_PATTERNS", r".*\.vercel\.app$")
ALLOWED_ORIGIN_PATTERNS: List[re.Pattern] = [
    re.compile(p.strip()) for p in _raw_patterns.split(",") if p.strip()
]


def is_origin_allowed(origin: str) -> bool:
    if origin in ALLOWED_ORIGINS:
        return True
    return any(p.search(origin) for p in ALLOWED_ORIGIN_PATTERNS)


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware that supports regex pattern matching for allowed origins."""

    async def dispatch(self, request: Request, call_next) -> Response:
        origin = request.headers.get("origin", "")

        # Handle preflight OPTIONS request
        if request.method == "OPTIONS" and origin:
            if is_origin_allowed(origin):
                return Response(
                    status_code=204,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "*",
                        "Access-Control-Max-Age": "600",
                        "Vary": "Origin",
                    },
                )
            return Response(status_code=400, content="CORS origin not allowed")

        response = await call_next(request)

        if origin and is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Vary"] = "Origin"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("MailDigest backend starting.")
    logging.info(f"Allowed CORS origins: {ALLOWED_ORIGINS}")
    logging.info(f"Allowed CORS patterns: {[p.pattern for p in ALLOWED_ORIGIN_PATTERNS]}")
    yield
    logging.info("MailDigest backend shutting down.")


app = FastAPI(
    title="MailDigest API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(DynamicCORSMiddleware)

app.include_router(auth_router)
app.include_router(emails_router)
app.include_router(accounts_router)
app.include_router(settings_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "maildigest"}


@app.get("/sync")
async def trigger_sync(user_id: str):
    """
    Manual sync trigger (dev convenience). 
    In production this would be called by a scheduler or cron job.
    """
    from services.sync_service import sync_all_accounts
    from services.db import get_supabase
    db = get_supabase()
    result = await sync_all_accounts(db, user_id)
    return result
