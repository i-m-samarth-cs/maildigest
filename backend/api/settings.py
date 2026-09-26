from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from .deps import get_current_user
from ..services.db import get_supabase, get_user_settings, upsert_user_settings

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    digest_time: Optional[str] = None
    timezone: Optional[str] = None
    ai_enabled: Optional[bool] = None
    ollama_model: Optional[str] = None
    theme: Optional[str] = None


@router.get("")
async def get_settings(user=Depends(get_current_user)):
    db = get_supabase()
    settings = await get_user_settings(db, user["sub"])
    if not settings:
        # Return defaults
        return {
            "digest_time": "20:00",
            "timezone": "Asia/Kolkata",
            "ai_enabled": True,
            "ollama_model": "llama3.2",
            "theme": "light",
        }
    return settings


@router.patch("")
async def update_settings(body: SettingsUpdate, user=Depends(get_current_user)):
    db = get_supabase()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await upsert_user_settings(db, user["sub"], updates)
    return result
