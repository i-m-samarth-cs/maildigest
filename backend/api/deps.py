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

    # Peek at the token header to see what algorithm it uses
    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "")
        logger.info(f"JWT alg from token header: {alg}")
    except Exception as e:
        logger.warning(f"Could not read JWT header: {e}")
        raise HTTPException(status_code=401, detail="Malformed token.")

    # HS256 — email/password logins (verified with SUPABASE_JWT_SECRET)
    if alg == "HS256":
        if not SUPABASE_JWT_SECRET:
            logger.error("SUPABASE_JWT_SECRET is not set")
            raise HTTPException(status_code=401, detail="Server misconfiguration: JWT secret not set.")
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired.")
        except jwt.InvalidTokenError as e:
            logger.warning(f"HS256 JWT decode failed: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # RS256 / ES256 — social OAuth logins via Supabase JWKS
    if alg in ("RS256", "ES256"):
        try:
            jwks_client = _get_jwks_client()
            if not jwks_client:
                raise HTTPException(status_code=401, detail="Server misconfiguration: SUPABASE_URL not set.")
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                options={"verify_aud": False},
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired.")
        except Exception as e:
            logger.warning(f"RS256/ES256 JWT decode failed: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # Unknown algorithm — log it so we know exactly what to add
    logger.error(f"Unsupported JWT algorithm: {alg}. Token header: {unverified_header}")
    raise HTTPException(status_code=401, detail=f"Unsupported token algorithm: {alg}")


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
        logger.info(f"Initializing JWKS client with URL: {jwks_url}")
        _jwks_client_instance = PyJWKClient(jwks_url, cache_keys=True)
        return _jwks_client_instance
    except Exception as e:
        logger.warning(f"Could not init JWKS client: {e}")
        return None
