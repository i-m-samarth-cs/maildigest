"""
FastAPI dependency: extract and verify the Supabase JWT from the Authorization header.
"""
import os
import logging
import jwt
from fastapi import HTTPException, Header
from typing import Optional

logger = logging.getLogger(__name__)

# Use the JWT secret exactly as provided — plain string, no encoding/decoding
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")

    token = authorization.split(" ", 1)[1]

    if not SUPABASE_JWT_SECRET:
        logger.error("SUPABASE_JWT_SECRET is not set")
        raise HTTPException(status_code=401, detail="Server misconfiguration: JWT secret not set.")

    # Log the algorithm for diagnostics
    try:
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "unknown")
        logger.info(f"JWT alg: {alg}")
    except Exception as e:
        logger.warning(f"Could not read JWT header: {e}")
        raise HTTPException(status_code=401, detail="Malformed token.")

    # Supabase always issues HS256 tokens (for all providers including Google)
    # The secret is used as a plain UTF-8 string
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
    except jwt.InvalidSignatureError:
        logger.error("JWT signature invalid — SUPABASE_JWT_SECRET may be wrong")
        raise HTTPException(status_code=401, detail="Invalid token signature.")
    except jwt.DecodeError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail=f"Token decode error: {e}")
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT invalid: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
