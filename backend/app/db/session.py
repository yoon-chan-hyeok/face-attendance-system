from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# DB 엔진 생성
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# 세션 로컬 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()

def get_db():
    """
    FastAPI 의존성 주입을 위한 DB 세션 제너레이터
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

