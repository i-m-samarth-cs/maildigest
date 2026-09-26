from typing import Dict, Any
from .base import EmailProvider
from .gmail_provider import GmailProvider
from .outlook_provider import OutlookProvider

PROVIDER_MAP = {
    "gmail": GmailProvider,
    "outlook": OutlookProvider,
}


def get_provider(provider: str, account_id: str, credentials: Dict[str, Any]) -> EmailProvider:
    cls = PROVIDER_MAP.get(provider.lower())
    if not cls:
        raise ValueError(f"Unsupported provider: {provider}. Supported: {list(PROVIDER_MAP.keys())}")
    return cls(account_id, credentials)
