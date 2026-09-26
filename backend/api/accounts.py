"""
Account management routes.
GET    /accounts           — list connected accounts
POST   /accounts/{id}/sync — trigger manual sync
DELETE /accounts/{id}      — disconnect account
PATCH  /accounts/{id}      — toggle enabled
"""
from fastapi import APIRouter, Depends, HTTPException

from .deps import get_current_user
from ..services.db import get_supabase, get_accounts_for_user
from ..services.sync_service import sync_account
from ..services.encryption import decrypt_token

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(user=Depends(get_current_user)):
    db = get_supabase()
    accounts = await get_accounts_for_user(db, user["sub"])
    return [_safe_account(a) for a in accounts]


@router.post("/{account_id}/sync")
async def manual_sync(account_id: str, user=Depends(get_current_user)):
    db = get_supabase()
    account = _get_verified_account(db, account_id, user["sub"])

    result = await sync_account(db, account)
    return {
        "account_id": account_id,
        "fetched": result["fetched"],
        "stored": result["stored"],
        "status": "complete",
    }


@router.delete("/{account_id}")
async def disconnect_account(account_id: str, user=Depends(get_current_user)):
    db = get_supabase()
    _get_verified_account(db, account_id, user["sub"])
    db.table("email_accounts").update({"enabled": False}).eq("id", account_id).execute()
    return {"status": "disconnected"}


@router.patch("/{account_id}")
async def update_account(account_id: str, payload: dict, user=Depends(get_current_user)):
    db = get_supabase()
    _get_verified_account(db, account_id, user["sub"])
    allowed = {k: v for k, v in payload.items() if k in {"enabled", "display_name"}}
    if not allowed:
        raise HTTPException(400, "No valid fields to update.")
    db.table("email_accounts").update(allowed).eq("id", account_id).execute()
    return {"status": "updated"}


def _get_verified_account(db, account_id: str, user_id: str) -> dict:
    result = db.table("email_accounts").select("*").eq("id", account_id).single().execute()
    account = result.data
    if not account:
        raise HTTPException(404, "Account not found.")
    if account["user_id"] != user_id:
        raise HTTPException(403, "Access denied.")
    return account


def _safe_account(a: dict) -> dict:
    return {
        "id": a["id"],
        "provider": a["provider"],
        "email_address": a["email_address"],
        "display_name": a.get("display_name"),
        "last_sync_at": a.get("last_sync_at"),
        "sync_status": a.get("sync_status"),
        "enabled": a.get("enabled"),
        "created_at": a.get("created_at"),
    }
