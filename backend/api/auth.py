"""
Auth routes — OAuth initiation and callbacks for Gmail and Outlook.
State parameter is a signed JWT to prevent CSRF.
"""
import os
import secrets
import logging
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse

from services.oauth_service import (
    gmail_auth_url, gmail_exchange_code,
    outlook_auth_url, outlook_exchange_code,
    save_oauth_account,
)
from services.db import get_supabase
from api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-production")


def _make_state(provider: str, user_id: str) -> str:
    payload = {
        "provider": provider,
        "user_id": user_id,
        "nonce": secrets.token_hex(8),
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _decode_state(state: str) -> dict:
    try:
        return jwt.decode(state, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(400, "OAuth state expired. Please try again.")
    except jwt.InvalidTokenError:
        raise HTTPException(400, "Invalid OAuth state.")


# ── Gmail ─────────────────────────────────────────────────────────────────────

@router.get("/gmail/start")
async def gmail_start(user=Depends(get_current_user)):
    state = _make_state("gmail", user.get("sub") or user.get("id", ""))
    return {"url": gmail_auth_url(state)}


@router.get("/gmail/callback")
async def gmail_callback(code: str = Query(...), state: str = Query(...)):
    state_data = _decode_state(state)
    user_id = state_data["user_id"]

    data = await gmail_exchange_code(code)
    db = get_supabase()
    account = await save_oauth_account(db, user_id, "gmail", data["tokens"], data["user_info"])

    return RedirectResponse(f"{FRONTEND_URL}/settings/accounts?connected=gmail&account={account.get('email_address', '')}")


# ── Outlook ───────────────────────────────────────────────────────────────────

@router.get("/outlook/start")
async def outlook_start(user=Depends(get_current_user)):
    state = _make_state("outlook", user.get("sub") or user.get("id", ""))
    return {"url": outlook_auth_url(state)}


@router.get("/outlook/callback")
async def outlook_callback(code: str = Query(...), state: str = Query(...)):
    state_data = _decode_state(state)
    user_id = state_data["user_id"]

    data = await outlook_exchange_code(code)
    db = get_supabase()
    account = await save_oauth_account(db, user_id, "outlook", data["tokens"], data["user_info"])

    return RedirectResponse(f"{FRONTEND_URL}/settings/accounts?connected=outlook&account={account.get('email_address', '')}")
