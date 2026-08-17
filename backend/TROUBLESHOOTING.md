# 🔧 트러블슈팅 가이드

이 문서는 `face-api` 프로젝트 개발/운영 중 발생한 문제와 해결 방법을 정리합니다.

---

## 목차

- [1. MediaPipe 호환성 문제](#1-mediapipe-호환성-문제)
- [2. MariaDB 보안 (랜섬웨어 대응)](#2-mariadb-보안-랜섬웨어-대응)
- [3. 413 Request Entity Too Large](#3-413-request-entity-too-large)

---

## 1. MediaPipe 호환성 문제

> 📅 **발생일:** 2026-01-05

### 에러
```
AttributeError: module 'mediapipe' has no attribute 'solutions'
```

### 원인
- Python 3.13 + MediaPipe 최신 버전에서 기존 `mp.solutions` API가 변경됨
- `mediapipe==0.10.9` 다운그레이드 시도 → Python 3.13 미지원으로 실패

### 해결
MediaPipe **Tasks API**로 마이그레이션:

```python
# 기존 (작동 안 함)
import mediapipe as mp
face_mesh = mp.solutions.face_mesh.FaceMesh()

# 변경 후 (Tasks API)
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

base_options = python.BaseOptions(model_asset_path="models/face_landmarker.task")
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_faces=1
)
detector = vision.FaceLandmarker.create_from_options(options)
```

### 필수 파일
- `models/face_landmarker.task` 모델 파일 필요
- 다운로드: https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task

### 추가 조치
- **Lazy Initialization** 적용 (서버 시작 시 충돌 방지)
- `.gitignore`에 `models/` 추가 (모델 파일은 Git에서 제외)

---

## 2. MariaDB 보안 (랜섬웨어 대응)

> 📅 **발생일:** 2026-01-05

### 증상
- `recover_your_data` 테이블 발견
- 비트코인 요구 메시지

### 원인
- 계정 외부 접속 허용 (%)

### 즉시 조치

#### 1) 외부 사용자 삭제
```sql
DROP USER IF EXISTS 'root'@'%';
FLUSH PRIVILEGES;
```

### 예방 수칙
- ⚠️ DB 포트(3306)는 **절대** 외부에 열지 않는다
- ⚠️ root 계정 외부 접속 금지
- ⚠️ 강력한 비밀번호 사용 (최소 16자, 특수문자 포함)
- ⚠️ 정기적인 백업 수행
---

## 3. 413 Request Entity Too Large
> 📅 **발생일:** 2026-01-06

### 에러
```
413 Request Entity Too Large
```

### 원인
다중 프레임(이미지 여러 장) 업로드 시 Nginx 기본 제한(1MB) 초과

### 해결
Nginx 설정 수정:

```nginx
# /etc/nginx/conf.d/face-attendance.conf

location /api/ {
    client_max_body_size 20M;  # 20MB 허용
    
    proxy_pass http://127.0.0.1:5011;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 적용
```bash
sudo nginx -t          # 문법 확인
sudo systemctl reload nginx  # 재시작
```

---

## 📋 환경 정보

| 항목 | 값 |
|------|-----|
| Python | 3.13 |
| FastAPI | 최신 |
| MediaPipe | 최신 (Tasks API) |
| MariaDB | 10.x |
| Nginx | 프록시 서버 |

---

## 🔗 관련 문서

- [README.md](./README.md) - 프로젝트 개요
- [ATTENDANCE_API_GUIDE.md](./ATTENDANCE_API_GUIDE.md) - API 가이드

---

*마지막 업데이트: 2026-01-06*
