import base64
import email as email_lib
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base import EmailProvider


class GmailProvider(EmailProvider):
    """Gmail provider using Gmail API v1 + OAuth 2.0."""

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
    ]

    def __init__(self, account_id: str, credentials: Dict[str, Any]):
        super().__init__(account_id, credentials)
        self._service = None

    def _build_creds(self) -> Credentials:
        return Credentials(
            token=self.credentials.get("access_token"),
            refresh_token=self.credentials.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.credentials.get("client_id"),
            client_secret=self.credentials.get("client_secret"),
            scopes=self.SCOPES,
        )

    async def connect(self) -> bool:
        try:
            creds = self._build_creds()
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self.credentials["access_token"] = creds.token
            self._service = build("gmail", "v1", credentials=creds, cache_discovery=False)
            return True
        except Exception:
            return False

    async def refresh_token(self) -> Dict[str, Any]:
        creds = self._build_creds()
        creds.refresh(Request())
        self.credentials["access_token"] = creds.token
        self.credentials["token_expiry"] = creds.expiry.isoformat() if creds.expiry else None
        return self.credentials

    async def sync_messages(
        self,
        since: Optional[datetime] = None,
        cursor: Optional[str] = None,
        max_results: int = 500,
    ) -> Dict[str, Any]:
        if not self._service:
            await self.connect()

        query = ""
        if since:
            # Gmail query: after:YYYY/MM/DD
            query = f"after:{since.strftime('%Y/%m/%d')}"

        messages = []
        next_cursor = cursor
        fetched = 0

        try:
            params: Dict[str, Any] = {"userId": "me", "maxResults": min(max_results, 500)}
            if query:
                params["q"] = query
            if next_cursor:
                params["pageToken"] = next_cursor

            while fetched < max_results:
                result = self._service.users().messages().list(**params).execute()
                batch = result.get("messages", [])
                messages.extend(batch)
                fetched += len(batch)
                next_cursor = result.get("nextPageToken")
                if not next_cursor or fetched >= max_results:
                    break
                params["pageToken"] = next_cursor

        except HttpError as e:
            raise RuntimeError(f"Gmail sync error: {e}")

        return {
            "messages": messages,  # [{id, threadId}] — full content fetched per message
            "next_cursor": next_cursor,
            "total_fetched": fetched,
        }

    async def get_message(self, message_id: str) -> Dict[str, Any]:
        if not self._service:
            await self.connect()

        msg = (
            self._service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        return self._parse_message(msg)

    def _parse_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

        body_text, body_html = self._extract_body(msg.get("payload", {}))

        # Parse recipients
        def parse_addrs(val: str) -> List[str]:
            if not val:
                return []
            return [a.strip() for a in val.split(",")]

        received_ts = int(msg.get("internalDate", 0)) / 1000
        received_at = datetime.fromtimestamp(received_ts, tz=timezone.utc)

        attachments = []
        self._collect_attachments(msg.get("payload", {}), attachments)

        return {
            "provider_message_id": msg["id"],
            "provider_thread_id": msg.get("threadId"),
            "internet_message_id": headers.get("message-id"),
            "sender_name": self._parse_sender_name(headers.get("from", "")),
            "sender_email": self._parse_sender_email(headers.get("from", "")),
            "recipients": parse_addrs(headers.get("to", "")),
            "cc": parse_addrs(headers.get("cc", "")),
            "bcc": parse_addrs(headers.get("bcc", "")),
            "subject": headers.get("subject", "(no subject)"),
            "received_at": received_at.isoformat(),
            "body_text": body_text,
            "body_html": body_html,
            "snippet": msg.get("snippet", ""),
            "provider_url": self.get_provider_url(msg["id"], msg.get("threadId")),
            "has_attachments": len(attachments) > 0,
            "is_read": "UNREAD" not in msg.get("labelIds", []),
            "is_starred": "STARRED" in msg.get("labelIds", []),
            "raw_metadata": {
                "label_ids": msg.get("labelIds", []),
                "size_estimate": msg.get("sizeEstimate"),
            },
            "attachments": attachments,
        }

    def _extract_body(self, payload: Dict) -> tuple[Optional[str], Optional[str]]:
        body_text = None
        body_html = None
        mime = payload.get("mimeType", "")

        if mime == "text/plain":
            body_text = self._decode_body(payload.get("body", {}).get("data", ""))
        elif mime == "text/html":
            body_html = self._decode_body(payload.get("body", {}).get("data", ""))
        elif mime.startswith("multipart/"):
            for part in payload.get("parts", []):
                t, h = self._extract_body(part)
                if t:
                    body_text = t
                if h:
                    body_html = h

        return body_text, body_html

    def _decode_body(self, data: str) -> str:
        if not data:
            return ""
        try:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _collect_attachments(self, payload: Dict, result: list):
        filename = payload.get("filename")
        body = payload.get("body", {})
        if filename and body.get("attachmentId"):
            result.append({
                "provider_attachment_id": body["attachmentId"],
                "filename": filename,
                "mime_type": payload.get("mimeType"),
                "size_bytes": body.get("size"),
            })
        for part in payload.get("parts", []):
            self._collect_attachments(part, result)

    def _parse_sender_name(self, from_header: str) -> Optional[str]:
        if "<" in from_header:
            return from_header.split("<")[0].strip().strip('"')
        return None

    def _parse_sender_email(self, from_header: str) -> str:
        if "<" in from_header:
            return from_header.split("<")[1].rstrip(">").strip()
        return from_header.strip()

    async def get_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        if not self._service:
            await self.connect()
        thread = self._service.users().threads().get(userId="me", id=thread_id, format="full").execute()
        return [self._parse_message(m) for m in thread.get("messages", [])]

    async def get_labels(self) -> List[Dict[str, str]]:
        if not self._service:
            await self.connect()
        result = self._service.users().labels().list(userId="me").execute()
        return [{"id": l["id"], "name": l["name"]} for l in result.get("labels", [])]

    async def get_attachment_metadata(self, message_id: str, attachment_id: str) -> Dict[str, Any]:
        # We only store metadata, not content
        if not self._service:
            await self.connect()
        att = (
            self._service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        return {"size_bytes": att.get("size"), "attachment_id": attachment_id}

    def get_provider_url(self, message_id: str, thread_id: Optional[str] = None) -> str:
        if thread_id:
            return f"https://mail.google.com/mail/u/0/#inbox/{thread_id}"
        return f"https://mail.google.com/mail/u/0/#inbox/{message_id}"
