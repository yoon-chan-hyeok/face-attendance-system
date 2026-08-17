# app/routers/liveness.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.liveness_service import liveness_config_service

router = APIRouter(tags=["liveness"])

class ToggleRequest(BaseModel):
    password: str
    enabled: bool

@router.post("/toggle")
async def toggle_liveness(request: ToggleRequest):
    """
    Toggle liveness mode (admin only)
    
    - password: Admin password
    - enabled: true to enable, false to disable
    - Password must match LIVENESS_ADMIN_PASSWORD from the environment
    """
    success = liveness_config_service.toggle_liveness(
        admin_password=request.password,
        enabled=request.enabled
    )
    
    if not success:
        raise HTTPException(
            status_code=403,
            detail="Admin password is incorrect."
        )
    
    return {
        "success": True,
        "enabled": request.enabled,
        "message": f"Liveness mode has been {'enabled' if request.enabled else 'disabled'}."
    }

@router.get("/status")
async def get_liveness_status():
    """
    Get liveness mode status
    """
    return liveness_config_service.get_status()

@router.get("/history")
async def get_toggle_history(limit: int = Query(default=20, ge=1, le=100)):
    """
    Get liveness toggle history
    
    - limit: Maximum number of records (default 20, max 100)
    """
    return {
        "history": liveness_config_service.get_toggle_history(limit)
    }
