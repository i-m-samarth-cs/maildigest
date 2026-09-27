"""
Email API routes.
GET  /emails/digest        — emails for a specific date (default: today)
GET  /emails/{id}          — single email with full content
GET  /emails/{id}/html     — sanitized HTML body
GET  /emails/digest/stats  — category counts for today
"""
from datetime import date
from typing import Optional

import bleach
from fastapi import APIRouter, Depends, Query, HTTPException

from api.deps import get_current_user
from services.db import get_supabase, get_emails_for_date, get_email_by_id

router = APIRouter(prefix="/emails", tags=["emails"])

# Allowed HTML tags for sanitized email rendering
ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p", "br", "div", "span", "table", "thead", "tbody", "tr", "td", "th",
    "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li",
    "strong", "em", "b", "i", "u", "a", "img", "blockquote", "pre", "code",
    "hr", "section", "article", "header", "footer", "main",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "width", "height"],
    "td": ["colspan", "rowspan", "align", "valign"],
    "th": ["colspan", "rowspan", "align", "valign"],
    "*": ["style", "class"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(html: str) -> str:
    """Strip dangerous tags/attributes from email HTML before rendering."""
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


@router.get("/digest")
async def get_digest(
    date_str: Optional[str] = Query(None, alias="date"),
    timezone: str = Query("Asia/Kolkata"),
    category: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user=Depends(get_current_user),
):
    """
    Returns all emails for a given date, with optional filters.
    AI analysis is included when available but absence never hides an email.
    """
    target_date = date_str or date.today().isoformat()
    db = get_supabase()
    emails = await get_emails_for_date(db, user["sub"], target_date, _tz_offset(timezone))

    # Optional filters — applied in Python to keep DB query simple
    if category:
        emails = [
            e for e in emails
            if _get_analysis(e).get("category") == category
        ]

    if account_id:
        emails = [e for e in emails if e.get("account_id") == account_id]

    if search:
        q = search.lower()
        emails = [
            e for e in emails
            if q in (e.get("subject") or "").lower()
            or q in (e.get("sender_email") or "").lower()
            or q in (e.get("sender_name") or "").lower()
            or q in (e.get("snippet") or "").lower()
        ]

    total = len(emails)
    start = (page - 1) * page_size
    paginated = emails[start: start + page_size]

    # Build category counts from full list
    stats = _compute_stats(emails)

    return {
        "date": target_date,
        "total": total,
        "page": page,
        "page_size": page_size,
        "stats": stats,
        "emails": [_safe_email(e) for e in paginated],
    }


@router.get("/digest/stats")
async def get_digest_stats(
    date_str: Optional[str] = Query(None, alias="date"),
    timezone: str = Query("Asia/Kolkata"),
    user=Depends(get_current_user),
):
    target_date = date_str or date.today().isoformat()
    db = get_supabase()
    emails = await get_emails_for_date(db, user["sub"], target_date, _tz_offset(timezone))
    return {"date": target_date, "total": len(emails), "stats": _compute_stats(emails)}


@router.get("/{email_id}")
async def get_email(email_id: str, user=Depends(get_current_user)):
    db = get_supabase()
    email = await get_email_by_id(db, email_id)
    if not email:
        raise HTTPException(404, "Email not found.")

    # Verify ownership via account → user join
    account = email.get("email_accounts") or {}
    if account.get("user_id") != user["sub"]:
        raise HTTPException(403, "Access denied.")

    return _safe_email(email, include_body=True)


@router.get("/{email_id}/html")
async def get_email_html(email_id: str, user=Depends(get_current_user)):
    """Returns sanitized HTML safe to render in an iframe/sandbox."""
    db = get_supabase()
    email = await get_email_by_id(db, email_id)
    if not email:
        raise HTTPException(404, "Email not found.")

    account = email.get("email_accounts") or {}
    if account.get("user_id") != user["sub"]:
        raise HTTPException(403, "Access denied.")

    raw_html = email.get("body_html") or ""
    safe_html = sanitize_html(raw_html) if raw_html else ""

    return {"email_id": email_id, "html": safe_html}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_email(e: dict, include_body: bool = False) -> dict:
    """Strip encrypted/sensitive fields and optionally include body."""
    result = {
        "id": e.get("id"),
        "account_id": e.get("account_id"),
        "provider_message_id": e.get("provider_message_id"),
        "provider_thread_id": e.get("provider_thread_id"),
        "sender_name": e.get("sender_name"),
        "sender_email": e.get("sender_email"),
        "recipients": e.get("recipients"),
        "cc": e.get("cc"),
        "subject": e.get("subject"),
        "received_at": e.get("received_at"),
        "snippet": e.get("snippet"),
        "provider_url": e.get("provider_url"),
        "has_attachments": e.get("has_attachments"),
        "is_read": e.get("is_read"),
        "is_starred": e.get("is_starred"),
        "ai_analysis": _get_analysis(e) or None,
        "account": {
            "provider": (e.get("email_accounts") or {}).get("provider"),
            "email_address": (e.get("email_accounts") or {}).get("email_address"),
            "display_name": (e.get("email_accounts") or {}).get("display_name"),
        },
    }
    if include_body:
        result["body_text"] = e.get("body_text")
        # HTML is served separately via /html endpoint for security
    return result


def _get_analysis(e: dict) -> dict:
    """Normalize ai_analysis — Supabase may return a dict or a list."""
    a = e.get("ai_analysis")
    if not a:
        return {}
    if isinstance(a, list):
        return a[0] if a else {}
    return a  # already a dict


def _compute_stats(emails: list) -> dict:
    counts: dict = {}
    for e in emails:
        cat = _get_analysis(e).get("category", "other") or "other"
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def _tz_offset(timezone: str) -> str:
    """Very basic timezone to offset mapping. Extend as needed."""
    offsets = {
        "Asia/Kolkata": "+05:30",
        "UTC": "+00:00",
        "America/New_York": "-05:00",
        "America/Los_Angeles": "-08:00",
        "Europe/London": "+00:00",
    }
    return offsets.get(timezone, "+05:30")
