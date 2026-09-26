"""
Token encryption at rest using Fernet (symmetric AES-128-CBC + HMAC).
Tokens are encrypted before storing in DB and decrypted when needed.
"""
import os
import base64
from cryptography.fernet import Fernet


def _get_key() -> bytes:
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("ENCRYPTION_KEY environment variable not set.")
    # Accept both raw key and base64-encoded key
    try:
        return base64.urlsafe_b64decode(key)
    except Exception:
        return key.encode()


def get_fernet() -> Fernet:
    return Fernet(base64.urlsafe_b64encode(_get_key()[:32]))


def encrypt_token(plain: str) -> str:
    if not plain:
        return ""
    f = get_fernet()
    return f.encrypt(plain.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    if not encrypted:
        return ""
    f = get_fernet()
    return f.decrypt(encrypted.encode()).decode()


def generate_key() -> str:
    """Generate a new 32-byte Fernet-compatible key. Run once during setup."""
    return base64.urlsafe_b64encode(Fernet.generate_key()[:32]).decode()
