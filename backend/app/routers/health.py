"""
헬스체크 라우터
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    """
    서버 상태 확인
    """
    return {
        "status": "healthy",
        "service": "DeepFace API"
    }

