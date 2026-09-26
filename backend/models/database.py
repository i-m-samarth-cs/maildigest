from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EmailAccount(BaseModel):
    id: str
    user_id: str
    provider: str  # "gmail" | "outlook"
    email_address: str
    display_name: Optional[str] = None
    provider_account_id: Optional[str] = None
    token_expiry: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    sync_status: str = "idle"  # idle | syncing | error
    enabled: bool = True
    created_at: datetime
    updated_at: datetime


class Email(BaseModel):
    id: str
    account_id: str
    provider_message_id: str
    provider_thread_id: Optional[str] = None
    internet_message_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: str
    recipients: Optional[List[str]] = []
    cc: Optional[List[str]] = []
    bcc: Optional[List[str]] = []
    subject: Optional[str] = None
    received_at: datetime
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    snippet: Optional[str] = None
    provider_url: Optional[str] = None
    has_attachments: bool = False
    is_read: bool = False
    is_starred: bool = False
    raw_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class EmailAttachment(BaseModel):
    id: str
    email_id: str
    provider_attachment_id: str
    filename: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at: datetime


class AIAnalysis(BaseModel):
    id: str
    email_id: str
    category: Optional[str] = None        # jobs | competitions | tech | reddit | newsletters | other
    subcategory: Optional[str] = None
    summary: Optional[str] = None
    priority: Optional[str] = None        # high | medium | low
    action_required: bool = False
    action_reason: Optional[str] = None
    deadline: Optional[datetime] = None
    event_date: Optional[datetime] = None
    organization: Optional[str] = None
    job_title: Optional[str] = None
    competition_name: Optional[str] = None
    keywords: Optional[List[str]] = []
    confidence: Optional[float] = None
    model: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DailyDigest(BaseModel):
    id: str
    user_id: str
    digest_date: str   # YYYY-MM-DD
    timezone: str
    total_emails: int
    complete: bool
    created_at: datetime
    updated_at: datetime


class UserSettings(BaseModel):
    id: str
    user_id: str
    digest_time: str = "20:00"
    timezone: str = "Asia/Kolkata"
    ai_enabled: bool = True
    ollama_model: str = "llama3.2"
    theme: str = "light"
    created_at: datetime
    updated_at: datetime
