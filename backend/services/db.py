"""
Database service using Supabase Python client.
All DB interactions go through this module.
"""
import os
from typing import Optional, List, Dict, Any
from supabase import create_client, Client


def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]  # service role key — backend only
    return create_client(url, key)


# ── Emails ────────────────────────────────────────────────────────────────────

async def upsert_email(client: Client, account_id: str, email_data: Dict[str, Any]) -> Dict:
    """
    Insert or update email. Uses (account_id, provider_message_id) unique constraint.
    Original email data is NEVER overwritten by AI fields.
    """
    payload = {
        "account_id": account_id,
        **{k: v for k, v in email_data.items() if k != "attachments"},
    }
    result = (
        client.table("emails")
        .upsert(payload, on_conflict="account_id,provider_message_id")
        .execute()
    )
    return result.data[0] if result.data else {}


async def upsert_attachments(client: Client, email_id: str, attachments: List[Dict]) -> None:
    if not attachments:
        return
    rows = [{"email_id": email_id, **a} for a in attachments]
    client.table("email_attachments").upsert(rows, on_conflict="email_id,provider_attachment_id").execute()


async def get_emails_for_date(
    client: Client,
    user_id: str,
    date_str: str,  # YYYY-MM-DD
    timezone_offset: str = "+05:30",
) -> List[Dict]:
    """
    Fetch all emails for a user for a given calendar day.
    Joins email_accounts to filter by user.
    """
    result = (
        client.table("emails")
        .select("*, email_accounts!inner(user_id, provider, email_address, display_name), ai_analysis(*)")
        .eq("email_accounts.user_id", user_id)
        .gte("received_at", f"{date_str}T00:00:00{timezone_offset}")
        .lte("received_at", f"{date_str}T23:59:59{timezone_offset}")
        .order("received_at", desc=True)
        .execute()
    )
    return result.data or []


async def get_email_by_id(client: Client, email_id: str) -> Optional[Dict]:
    result = (
        client.table("emails")
        .select("*, email_accounts(*), ai_analysis(*), email_attachments(*)")
        .eq("id", email_id)
        .single()
        .execute()
    )
    return result.data


# ── Accounts ──────────────────────────────────────────────────────────────────

async def get_accounts_for_user(client: Client, user_id: str) -> List[Dict]:
    result = (
        client.table("email_accounts")
        .select("*")
        .eq("user_id", user_id)
        .eq("enabled", True)
        .execute()
    )
    return result.data or []


async def update_account_sync_status(
    client: Client, account_id: str, status: str, cursor: Optional[str] = None
) -> None:
    payload: Dict[str, Any] = {"sync_status": status, "last_sync_at": "now()"}
    if cursor is not None:
        payload["sync_cursor"] = cursor
    client.table("email_accounts").update(payload).eq("id", account_id).execute()


# ── AI Analysis ───────────────────────────────────────────────────────────────

async def upsert_ai_analysis(client: Client, email_id: str, analysis: Dict[str, Any]) -> None:
    payload = {"email_id": email_id, **analysis}
    client.table("ai_analysis").upsert(payload, on_conflict="email_id").execute()


# ── Settings ──────────────────────────────────────────────────────────────────

async def get_user_settings(client: Client, user_id: str) -> Optional[Dict]:
    result = (
        client.table("user_settings")
        .select("*")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    return result.data


async def upsert_user_settings(client: Client, user_id: str, settings: Dict) -> Dict:
    payload = {"user_id": user_id, **settings}
    result = client.table("user_settings").upsert(payload, on_conflict="user_id").execute()
    return result.data[0] if result.data else {}
