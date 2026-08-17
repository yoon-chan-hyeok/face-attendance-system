from fastapi import APIRouter, Query

from app.core.log_store import log_store

router = APIRouter(tags=["logs"])


@router.get("/recent")
async def get_recent_logs(limit: int = Query(default=200, ge=10, le=2000)):
    return {"logs": log_store.recent(limit=limit)}


@router.post("/clear")
async def clear_logs():
    log_store.clear()
    return {"success": True}
