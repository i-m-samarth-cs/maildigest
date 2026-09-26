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


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")

    token = authorization.split(" ", 1)[1]

    if not SUPABASE_JWT_SECRET:
        logger.error("SUPABASE_JWT_SECRET is not set — cannot verify tokens")
        raise HTTPException(status_code=401, detail="Server misconfiguration: JWT secret not set.")

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidAudienceError:
        # Try without audience check — some Supabase setups omit it
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT decode failed (no-aud fallback): {e}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except jwt.InvalidSignatureError:
        logger.warning("JWT signature verification failed — check SUPABASE_JWT_SECRET")
        raise HTTPException(status_code=401, detail="Invalid token signature.")
    except jwt.InvalidTokenError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
