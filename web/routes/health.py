"""
Health and update check routes for Arcane Auditor.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from web.services.updater import get_cached_health
from utils.preferences_manager import get_update_prefs, set_update_prefs
from pydantic import BaseModel

router = APIRouter()


class UpdatePreferencesPayload(BaseModel):
    """Payload for updating user preferences."""
    enabled: bool


@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return get_cached_health()


@router.get("/api/update-preferences")
async def get_update_preferences_api():
    """Return the current update detection preferences."""
    try:
        prefs = get_update_prefs()
        return {
            "enabled": prefs.get("enabled", False),
            "first_run_completed": prefs.get("first_run_completed", False)
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/update-preferences")
async def set_update_preferences_api(payload: UpdatePreferencesPayload):
    """Persist update detection preference changes."""
    try:
        prefs = get_update_prefs()
        prefs["enabled"] = bool(payload.enabled)
        set_update_prefs(prefs)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


