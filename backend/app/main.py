# app/main.py
import os

# TensorFlow log level setting (run before import)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=all, 1=hide INFO, 2=hide WARNING too, 3=ERROR only
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN messages

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, face, attendance, liveness, logs
from app.core.dependencies import face_service
from app.core.log_store import setup_log_capture

app = FastAPI(
    title="DeepFace API",
    description="Face Analysis API Service",
    version="1.0.0"
)

# CORS settings
origins = [
    "http://localhost:5173",  # React/Vite Frontend
    "http://127.0.0.1:5173",
    "*" # Allow all origins for development convenience (restrict in production)
]

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
        "message": "DeepFace API",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "face_emotion": "/api/v1/face/analyze/emotion",
            "face_full": "/api/v1/face/analyze/full"
        }
    }
