"""
MailDigest FastAPI backend.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth_router
from api.emails import router as emails_router
from api.accounts import router as accounts_router
from api.settings import router as settings_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("MailDigest backend starting.")
    yield
    logging.info("MailDigest backend shutting down.")


app = FastAPI(
    title="MailDigest API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
