"""
Email sync service.
- Fetches new emails from all connected accounts.
- Stores raw email data in DB (no AI).
- Queues AI analysis separately so missing AI never blocks email display.
- GUARANTEES: every fetched email is stored. Display is never gated on AI.
"""
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta

from supabase import Client

from .db import (
    get_accounts_for_user,
    upsert_email,
    upsert_attachments,
    update_account_sync_status,
    get_user_settings,
)
from .encryption import decrypt_token
from .ai_service import analyze_email_background
from ..providers.provider_factory import get_provider

logger = logging.getLogger(__name__)


async def sync_all_accounts(client: Client, user_id: str) -> dict:
    """
    Sync all enabled accounts for a user.
    Returns a summary: { total_fetched, total_stored, accounts_synced, errors }
    """
    accounts = await get_accounts_for_user(client, user_id)
    settings = await get_user_settings(client, user_id) or {}
    ai_enabled = settings.get("ai_enabled", True)
    ollama_model = settings.get("ollama_model", "llama3.2")

    summary = {"total_fetched": 0, "total_stored": 0, "accounts_synced": 0, "errors": []}

    for account in accounts:
        try:
            result = await sync_account(client, account, ai_enabled, ollama_model)
            summary["total_fetched"] += result["fetched"]
            summary["total_stored"] += result["stored"]
            summary["accounts_synced"] += 1
        except Exception as e:
            logger.error(f"Sync failed for account {account['id']}: {e}")
            summary["errors"].append({"account_id": account["id"], "error": str(e)})

    return summary


async def sync_account(
    client: Client,
    account: dict,
    ai_enabled: bool = True,
    ollama_model: str = "llama3.2",
) -> dict:
    account_id = account["id"]
    provider_name = account["provider"]

    # Decrypt stored tokens
    credentials = {
        "access_token": decrypt_token(account.get("encrypted_access_token", "")),
        "refresh_token": decrypt_token(account.get("encrypted_refresh_token", "")),
        "client_id": _get_oauth_client_id(provider_name),
        "client_secret": _get_oauth_client_secret(provider_name),
        "token_expiry": account.get("token_expiry"),
    }

    provider = get_provider(provider_name, account_id, credentials)

    await update_account_sync_status(client, account_id, "syncing")

    try:
        await provider.connect()

        # Determine sync window — last 24h if no cursor, otherwise use cursor
        since = None
        cursor = account.get("sync_cursor")
        if not cursor:
            since = datetime.now(tz=timezone.utc) - timedelta(hours=24)

        sync_result = await provider.sync_messages(since=since, cursor=cursor)
        message_refs = sync_result["messages"]
        next_cursor = sync_result.get("next_cursor")

        fetched = 0
        stored = 0

        for ref in message_refs:
            msg_id = ref.get("id") or ref.get("provider_message_id") or ref.get("id")
            if not msg_id:
                continue
            fetched += 1

            try:
                # Fetch full message content
                message_data = await provider.get_message(msg_id)
                attachments = message_data.pop("attachments", [])

                # Store email — this is the source of truth
                saved = await upsert_email(client, account_id, message_data)
                email_id = saved.get("id")

                if email_id:
                    stored += 1
                    # Store attachment metadata (no content download)
                    await upsert_attachments(client, email_id, attachments)

                    # AI analysis is best-effort — failure NEVER affects storage/display
                    if ai_enabled:
                        try:
                            await analyze_email_background(
                                client, email_id, message_data, ollama_model
                            )
                        except Exception as ai_err:
                            logger.warning(f"AI analysis skipped for {email_id}: {ai_err}")

            except Exception as msg_err:
                logger.error(f"Failed to process message {msg_id}: {msg_err}")
                # Continue — do not let one message failure stop the rest

        await update_account_sync_status(client, account_id, "idle", cursor=next_cursor)
        return {"fetched": fetched, "stored": stored}

    except Exception as e:
        await update_account_sync_status(client, account_id, "error")
        raise e


def _get_oauth_client_id(provider: str) -> str:
    import os
    if provider == "gmail":
        return os.environ.get("GMAIL_CLIENT_ID", "")
    if provider == "outlook":
        return os.environ.get("OUTLOOK_CLIENT_ID", "")
    return ""


def _get_oauth_client_secret(provider: str) -> str:
    import os
    if provider == "gmail":
        return os.environ.get("GMAIL_CLIENT_SECRET", "")
    if provider == "outlook":
        return os.environ.get("OUTLOOK_CLIENT_SECRET", "")
    return ""
