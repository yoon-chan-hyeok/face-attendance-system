"""
전역 의존성 및 싱글톤 인스턴스
"""
from app.services.face_service import FaceAnalysisService

# 싱글톤 인스턴스
face_service = FaceAnalysisService()

