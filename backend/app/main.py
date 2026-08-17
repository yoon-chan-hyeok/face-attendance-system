# app/main.py
import os

# TensorFlow log level setting (run before import)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=all, 1=hide INFO, 2=hide WARNING too, 3=ERROR only
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN messages

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, face, attendance, liveness, logs
from app.core.dependencies import face_service
from app.core.config import settings
from app.core.log_store import setup_log_capture

app = FastAPI(
    title="Face Attendance API",
    description="Multi-frame face enrollment, ambiguity-aware identification, and attendance logging",
    version="1.0.0"
)

# CORS settings
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_log_capture()

@app.on_event("startup")
async def startup_event():
    """Server startup initialization"""
    print("=" * 50)
    print("DeepFace API server started")
    print("FaceAnalysisService instance ready")
    print("Model will be loaded on first request (~3-5 seconds)")
    print("=" * 50)

# Register each router independently
app.include_router(health.router, prefix="/api/v1")
app.include_router(health.router)
app.include_router(face.router, prefix="/api/v1/face")
app.include_router(attendance.router, prefix="/api/v1/attendance")
app.include_router(liveness.router, prefix="/api/v1/liveness")
app.include_router(logs.router, prefix="/api/v1/logs")

@app.get("/")
def root():    
    return {
        "status": 200,
        "message": "Face Attendance API",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "register": "/api/v1/face/register-v2",
            "identify": "/api/v1/face/identify",
            "attendance": "/api/v1/attendance/check-in-out-v4",
            "liveness": "/api/v1/liveness/status"
        }
    }
