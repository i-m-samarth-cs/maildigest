"""
FastAPI dependency: extract and verify the Supabase JWT from the Authorization header.
Supabase newer projects use ES256 (asymmetric), verified via JWKS endpoint.
Older projects use HS256 (symmetric), verified with SUPABASE_JWT_SECRET.
"""
import os
import logging
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Header
from typing import Optional

logger = logging.getLogger(__name__)

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")

# Cache the JWKS client at module level
_jwks_client: Optional[PyJWKClient] = None

def _get_jwks_client() -> Optional[PyJWKClient]:
    global _jwks_client
    if _jwks_client is not None:
        return _jwks_client
    if not SUPABASE_URL:
        logger.error("SUPABASE_URL is not set — cannot fetch JWKS")
        return None
    jwks_url = f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    logger.info(f"Initializing JWKS client: {jwks_url}")
    _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")

    token = authorization.split(" ", 1)[1]

    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "unknown")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Malformed token.")

    # ES256 — newer Supabase projects (asymmetric, verified via JWKS)
    if alg in ("ES256", "RS256"):
        try:
            client = _get_jwks_client()
            if not client:
                raise HTTPException(status_code=401, detail="Server misconfiguration: SUPABASE_URL not set.")
            signing_key = client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                options={"verify_aud": False},
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired.")
        except Exception as e:
            logger.warning(f"ES256/RS256 JWT decode failed: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # HS256 — older Supabase projects (symmetric, verified with secret)
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

    logger.error(f"Unsupported JWT algorithm: {alg}")
    raise HTTPException(status_code=401, detail=f"Unsupported token algorithm: {alg}")
