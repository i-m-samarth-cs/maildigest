"""
OAuth 2.0 flows for Gmail and Outlook.
Tokens are encrypted before storing in the database.
"""
import os
import httpx
from typing import Dict, Any
from urllib.parse import urlencode

from supabase import Client
from services.encryption import encrypt_token


# ── Gmail OAuth ───────────────────────────────────────────────────────────────

GMAIL_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GMAIL_SCOPES = "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email"


def gmail_auth_url(state: str) -> str:
    params = {
        "client_id": os.environ["GMAIL_CLIENT_ID"],
        "redirect_uri": os.environ["GMAIL_REDIRECT_URI"],
        "response_type": "code",
        "scope": GMAIL_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GMAIL_AUTH_URL}?{urlencode(params)}"


async def gmail_exchange_code(code: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            GMAIL_TOKEN_URL,
            data={
                "code": code,
                "client_id": os.environ["GMAIL_CLIENT_ID"],
                "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
                "redirect_uri": os.environ["GMAIL_REDIRECT_URI"],
                "grant_type": "authorization_code",
            },
        )
        r.raise_for_status()
        tokens = r.json()

    # Get user info
    async with httpx.AsyncClient() as client:
        r = await client.get(
            GMAIL_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        r.raise_for_status()
        user_info = r.json()

    return {"tokens": tokens, "user_info": user_info}


# ── Outlook OAuth ─────────────────────────────────────────────────────────────

OUTLOOK_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
OUTLOOK_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
OUTLOOK_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"
OUTLOOK_SCOPES = "Mail.Read User.Read offline_access"


def outlook_auth_url(state: str) -> str:
    params = {
        "client_id": os.environ["OUTLOOK_CLIENT_ID"],
        "redirect_uri": os.environ["OUTLOOK_REDIRECT_URI"],
        "response_type": "code",
        "scope": OUTLOOK_SCOPES,
        "response_mode": "query",
        "state": state,
    }
    return f"{OUTLOOK_AUTH_URL}?{urlencode(params)}"


async def outlook_exchange_code(code: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            OUTLOOK_TOKEN_URL,
            data={
                "code": code,
                "client_id": os.environ["OUTLOOK_CLIENT_ID"],
                "client_secret": os.environ["OUTLOOK_CLIENT_SECRET"],
                "redirect_uri": os.environ["OUTLOOK_REDIRECT_URI"],
                "grant_type": "authorization_code",
                "scope": OUTLOOK_SCOPES,
            },
        )
        r.raise_for_status()
        tokens = r.json()

    async with httpx.AsyncClient() as client:
        r = await client.get(
            OUTLOOK_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        r.raise_for_status()
        user_info = r.json()

    return {"tokens": tokens, "user_info": user_info}


# ── Store account ─────────────────────────────────────────────────────────────

async def save_oauth_account(
    db: Client,
    user_id: str,
    provider: str,
    tokens: Dict[str, Any],
    user_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Save or update an OAuth account. Tokens are encrypted at rest."""
    from datetime import datetime, timezone, timedelta

    expiry = None
    if tokens.get("expires_in"):
        expiry = (datetime.now(tz=timezone.utc) + timedelta(seconds=tokens["expires_in"])).isoformat()

    if provider == "gmail":
        email = user_info.get("email", "")
        name = user_info.get("name", "")
        provider_account_id = user_info.get("sub", "")
    else:
        email = user_info.get("mail") or user_info.get("userPrincipalName", "")
        name = user_info.get("displayName", "")
        provider_account_id = user_info.get("id", "")

    payload = {
        "user_id": user_id,
        "provider": provider,
        "email_address": email,
        "display_name": name,
        "provider_account_id": provider_account_id,
        "encrypted_access_token": encrypt_token(tokens.get("access_token", "")),
        "encrypted_refresh_token": encrypt_token(tokens.get("refresh_token", "")),
        "token_expiry": expiry,
        "sync_status": "idle",
        "enabled": True,
    }

    result = (
        db.table("email_accounts")
        .upsert(payload, on_conflict="user_id,provider,email_address")
        .execute()
    )
    return result.data[0] if result.data else {}
