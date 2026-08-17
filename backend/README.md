# Face Attendance API

FastAPI, DeepFace와 SQLAlchemy로 구현한 얼굴 인식 출결 백엔드입니다. 전체 프로젝트 설명과 실행 방법은 [저장소 README](../README.md)를 참고하세요.

## 핵심 구성

- `app/services/face_service.py`: RetinaFace 검출, ArcFace 임베딩, cosine-distance 검색, threshold와 margin 판정
- `app/routers/face.py`: 단일/다중 프레임 등록, 단일/다중 얼굴 식별, 사용자 조회·삭제
- `app/routers/attendance.py`: V1~V4 출결 경로, 다중 얼굴 출결, 이력과 상태 조회
- `app/services/attendance_service.py`: 최근 기록 기반 IN/OUT 토글
- `app/services/blink_service.py`: MediaPipe Tasks 기반 blink 검출
- `app/models/`: `users`, `user_embeddings`, `attendance_log` SQLAlchemy 모델

## API prefix

| Prefix | 기능 |
|---|---|
| `/api/v1/face` | 등록, 식별, 사용자 관리 |
| `/api/v1/attendance` | 출결 기록과 이력 |
| `/api/v1/liveness` | 라이브니스 상태와 토글 |
| `/api/v1/logs` | 인메모리 런타임 로그 |
| `/docs` | OpenAPI/Swagger 문서 |

## 로컬 설정

```powershell
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

DB 스키마는 `db_reset_v2.sql`에 있습니다. 이 스크립트는 기존 `attendance_db`를 삭제하므로 전용 개발 DB에서만 사용해야 합니다.

실제 얼굴 이미지, 임베딩, 환경변수, 라이브니스 설정 이력과 모델 바이너리는 Git에서 제외됩니다.
