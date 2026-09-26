from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class EmailProvider(ABC):
    """
    Abstract base for all email providers.
    Each provider must implement all methods below.
    Adding a new provider = subclassing this + registering in provider_factory.py.
    """

    def __init__(self, account_id: str, credentials: Dict[str, Any]):
        self.account_id = account_id
        self.credentials = credentials

    @abstractmethod
    async def connect(self) -> bool:
        """Validate credentials and establish connection."""
        pass

    @abstractmethod
    async def refresh_token(self) -> Dict[str, Any]:
        """Refresh OAuth tokens. Returns updated token dict."""
        pass

    @abstractmethod
    async def sync_messages(
        self,
        since: Optional[datetime] = None,
        cursor: Optional[str] = None,
        max_results: int = 500,
    ) -> Dict[str, Any]:
        """
        Fetch new/updated messages since last sync.
        Returns: { messages: [...], next_cursor: str | None, total_fetched: int }
        """
        pass

    @abstractmethod
    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Fetch full message content by provider message ID."""
        pass

    @abstractmethod
    async def get_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """Fetch all messages in a thread."""
        pass

    @abstractmethod
    async def get_labels(self) -> List[Dict[str, str]]:
        """Return provider labels/folders as [{id, name}]."""
        pass

    @abstractmethod
    async def get_attachment_metadata(
        self, message_id: str, attachment_id: str
    ) -> Dict[str, Any]:
        """Return metadata for a specific attachment. Do not download content."""
        pass

    @abstractmethod
    def get_provider_url(self, message_id: str, thread_id: Optional[str] = None) -> str:
        """Return the direct URL to open this message in the provider's web UI."""
        pass
