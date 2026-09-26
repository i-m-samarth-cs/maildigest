from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

import httpx

from .base import EmailProvider


class OutlookProvider(EmailProvider):
    """
    Microsoft Graph API provider for Outlook / Microsoft 365.
    Uses OAuth 2.0 — no passwords.
    """

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    SCOPES = "Mail.Read User.Read offline_access"

    def __init__(self, account_id: str, credentials: Dict[str, Any]):
        super().__init__(account_id, credentials)
        self._client: Optional[httpx.AsyncClient] = None

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    async def connect(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.GRAPH_BASE}/me",
                    headers=self._auth_headers(),
                    timeout=10,
                )
                return r.status_code == 200
        except Exception:
            return False

    async def refresh_token(self) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.credentials["client_id"],
                    "client_secret": self.credentials["client_secret"],
                    "refresh_token": self.credentials["refresh_token"],
                    "grant_type": "refresh_token",
                    "scope": self.SCOPES,
                },
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
            self.credentials["access_token"] = data["access_token"]
            if "refresh_token" in data:
                self.credentials["refresh_token"] = data["refresh_token"]
            return self.credentials

    async def sync_messages(
        self,
        since: Optional[datetime] = None,
        cursor: Optional[str] = None,
        max_results: int = 500,
    ) -> Dict[str, Any]:
        messages = []
        fetched = 0

        if cursor:
            url = cursor  # Graph API $skiptoken is embedded in @odata.nextLink
        else:
            filter_str = ""
            if since:
                iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")
                filter_str = f"&$filter=receivedDateTime ge {iso}"
            url = (
                f"{self.GRAPH_BASE}/me/messages"
                f"?$select=id,conversationId,internetMessageId,from,toRecipients,ccRecipients,"
                f"bccRecipients,subject,receivedDateTime,bodyPreview,hasAttachments,isRead,flag"
                f"&$orderby=receivedDateTime desc"
                f"&$top=50"
                f"{filter_str}"
            )

        async with httpx.AsyncClient() as client:
            while fetched < max_results:
                r = await client.get(url, headers=self._auth_headers(), timeout=30)
                r.raise_for_status()
                data = r.json()
                batch = data.get("value", [])
                messages.extend(batch)
                fetched += len(batch)
                url = data.get("@odata.nextLink")
                if not url or fetched >= max_results:
                    break

        return {
            "messages": messages,
            "next_cursor": url,  # nextLink includes skiptoken
            "total_fetched": fetched,
        }

    async def get_message(self, message_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.GRAPH_BASE}/me/messages/{message_id}"
                "?$select=id,conversationId,internetMessageId,from,toRecipients,ccRecipients,"
                "bccRecipients,subject,receivedDateTime,body,bodyPreview,hasAttachments,isRead,flag,"
                "attachments",
                headers=self._auth_headers(),
                timeout=20,
            )
            r.raise_for_status()
            return self._parse_message(r.json())

    def _parse_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        def extract_emails(recipients: List[Dict]) -> List[str]:
            return [r["emailAddress"]["address"] for r in recipients if "emailAddress" in r]

        from_addr = msg.get("from", {}).get("emailAddress", {})
        received_at = datetime.fromisoformat(
            msg.get("receivedDateTime", "").replace("Z", "+00:00")
        )

        body = msg.get("body", {})
        body_html = body.get("content") if body.get("contentType") == "html" else None
        body_text = body.get("content") if body.get("contentType") == "text" else None

        attachments = []
        for att in msg.get("attachments", []):
            if att.get("@odata.type") == "#microsoft.graph.fileAttachment":
                attachments.append({
                    "provider_attachment_id": att.get("id"),
                    "filename": att.get("name"),
                    "mime_type": att.get("contentType"),
                    "size_bytes": att.get("size"),
                })

        return {
            "provider_message_id": msg["id"],
            "provider_thread_id": msg.get("conversationId"),
            "internet_message_id": msg.get("internetMessageId"),
            "sender_name": from_addr.get("name"),
            "sender_email": from_addr.get("address", ""),
            "recipients": extract_emails(msg.get("toRecipients", [])),
            "cc": extract_emails(msg.get("ccRecipients", [])),
            "bcc": extract_emails(msg.get("bccRecipients", [])),
            "subject": msg.get("subject", "(no subject)"),
            "received_at": received_at.isoformat(),
            "body_text": body_text,
            "body_html": body_html,
            "snippet": msg.get("bodyPreview", ""),
            "provider_url": self.get_provider_url(msg["id"]),
            "has_attachments": msg.get("hasAttachments", False),
            "is_read": msg.get("isRead", False),
            "is_starred": msg.get("flag", {}).get("flagStatus") == "flagged",
            "raw_metadata": {
                "importance": msg.get("importance"),
                "categories": msg.get("categories", []),
            },
            "attachments": attachments,
        }

    async def get_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.GRAPH_BASE}/me/messages"
                f"?$filter=conversationId eq '{thread_id}'"
                "&$orderby=receivedDateTime asc",
                headers=self._auth_headers(),
                timeout=20,
            )
            r.raise_for_status()
            return [self._parse_message(m) for m in r.json().get("value", [])]

    async def get_labels(self) -> List[Dict[str, str]]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.GRAPH_BASE}/me/mailFolders",
                headers=self._auth_headers(),
                timeout=10,
            )
            r.raise_for_status()
            return [{"id": f["id"], "name": f["displayName"]} for f in r.json().get("value", [])]

    async def get_attachment_metadata(self, message_id: str, attachment_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.GRAPH_BASE}/me/messages/{message_id}/attachments/{attachment_id}"
                "?$select=id,name,contentType,size",
                headers=self._auth_headers(),
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            return {
                "provider_attachment_id": data.get("id"),
                "filename": data.get("name"),
                "mime_type": data.get("contentType"),
                "size_bytes": data.get("size"),
            }

    def get_provider_url(self, message_id: str, thread_id: Optional[str] = None) -> str:
        return f"https://outlook.live.com/mail/0/inbox/id/{message_id}"
