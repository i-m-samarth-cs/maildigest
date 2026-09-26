"""
FastAPI dependency: extract and verify the Supabase JWT from the Authorization header.
"""
import os
import jwt
from fastapi import HTTPException, Header
from typing import Optional


SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header.")

    token = authorization.split(" ", 1)[1]
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
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
