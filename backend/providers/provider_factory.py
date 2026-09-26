from typing import Dict, Any
from providers.base import EmailProvider
from providers.gmail_provider import GmailProvider
from providers.outlook_provider import OutlookProvider

PROVIDER_MAP = {
    "gmail": GmailProvider,
    "outlook": OutlookProvider,
}


def get_provider(provider: str, account_id: str, credentials: Dict[str, Any]) -> EmailProvider:
    cls = PROVIDER_MAP.get(provider.lower())
    if not cls:
        raise ValueError(f"Unsupported provider: {provider}. Supported: {list(PROVIDER_MAP.keys())}")
    return cls(account_id, credentials)
