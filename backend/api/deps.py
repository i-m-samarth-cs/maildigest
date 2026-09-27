"""
FastAPI dependency: extract and verify the Supabase JWT from the Authorization header.
"""
import os
import logging
import jwt
from fastapi import HTTPException, Header
from typing import Optional

logger = logging.getLogger(__name__)

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")

    token = authorization.split(" ", 1)[1]

    if not SUPABASE_JWT_SECRET:
        logger.error("SUPABASE_JWT_SECRET is not set — cannot verify tokens")
        raise HTTPException(status_code=401, detail="Server misconfiguration: JWT secret not set.")

    # Try HS256 first (email/password logins)
    for verify_aud in (True, False):
        try:
            options = {"verify_aud": verify_aud}
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated" if verify_aud else None,
                options=options if not verify_aud else {},
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired.")
        except jwt.InvalidAudienceError:
            continue
        except jwt.InvalidSignatureError:
            break  # Wrong secret — don't retry
        except jwt.DecodeError:
            break  # Not HS256 at all — try RS256 below
        except jwt.InvalidTokenError:
            break

    # Try RS256 (Google/social OAuth logins via Supabase)
    # For RS256 we need Supabase's JWKS — fetch from the well-known endpoint
    try:
        jwks_client = _get_jwks_client()
        if jwks_client:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="authenticated",
                options={"verify_aud": False},
            )
            return payload
    except Exception as e:
        logger.warning(f"RS256 JWT decode failed: {e}")

    raise HTTPException(status_code=401, detail="Invalid or expired token.")


_jwks_client_instance = None

def _get_jwks_client():
    global _jwks_client_instance
    if _jwks_client_instance is not None:
        return _jwks_client_instance
    if not SUPABASE_URL:
        return None
    try:
        from jwt import PyJWKClient
        jwks_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client_instance = PyJWKClient(jwks_url, cache_keys=True)
        return _jwks_client_instance
    except Exception as e:
        logger.warning(f"Could not init JWKS client: {e}")
        return None
