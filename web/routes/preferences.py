"""
Preferences routes for Arcane Auditor.

Handles rule evolution preferences and export preferences.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.preferences_manager import (
    get_new_rule_default_enabled,
    set_new_rule_default_enabled,
    get_excel_single_tab,
    set_excel_single_tab,
)

router = APIRouter()


class RuleEvolutionPreferencesPayload(BaseModel):
    """Payload for updating rule evolution preferences."""
    new_rule_default_enabled: bool


class ExportPreferencesPayload(BaseModel):
    """Payload for updating export preferences."""
    excel_single_tab: bool


@router.get("/api/rule-evolution-preferences")
async def get_rule_evolution_preferences_api():
    """Return the current rule evolution preferences."""
    try:
        enabled = get_new_rule_default_enabled()
        return {
            "new_rule_default_enabled": enabled
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/rule-evolution-preferences")
async def set_rule_evolution_preferences_api(payload: RuleEvolutionPreferencesPayload):
    """Persist rule evolution preference changes."""
    try:
        success = set_new_rule_default_enabled(bool(payload.new_rule_default_enabled))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save preferences")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/export-preferences")
async def get_export_preferences_api():
    """Return the current export preferences."""
    try:
        enabled = get_excel_single_tab()
        return {
            "excel_single_tab": enabled
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.post("/api/export-preferences")
async def set_export_preferences_api(payload: ExportPreferencesPayload):
    """Persist export preference changes."""
    try:
        success = set_excel_single_tab(bool(payload.excel_single_tab))
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save preferences")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


