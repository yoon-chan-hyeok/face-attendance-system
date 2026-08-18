![얼굴 출결 시스템 고도화](assets/project-hero.svg)

<div align="center">

# 기존 얼굴 출결 시스템 고도화

**한 장의 등록 사진과 절대 임계값에 의존하던 얼굴 판정 방식을 보완했습니다.**

![Source](https://img.shields.io/badge/Application%20Source-Public-16803A)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-646CFF)
![CI](https://github.com/yoon-chan-hyeok/face-attendance-system/actions/workflows/ci.yml/badge.svg)
![Validation](https://img.shields.io/badge/Calibration-Pending-D97706)

[문제](#왜-시스템을-고도화했나) · [변경](#무엇을-바꿨나) · [판정](#얼굴을-판정하는-과정) · [실행](#로컬에서-실행하기) · [한계](#현재-확인한-범위)

</div>

## 왜 시스템을 고도화했나

이 프로젝트는 얼굴 등록과 인식 기능이 이미 있던 출결 시스템에서 시작했습니다. 초기 버전은 사용자마다 사진 한 장을 저장하고, 입력 얼굴과 가장 가까운 후보가 거리 임계값을 통과하면 출결을 승인했습니다.

조명과 촬영 위치를 바꿔 테스트하던 중 닮은 사람이 잘못 승인되는 사례가 나왔습니다. 1순위 후보의 점수만 보면 2순위 후보와 거의 차이가 없는 모호한 상황을 구분하기 어려웠습니다. 등록과 출결에 여러 프레임을 모두 사용하면 비교할 정보는 늘지만 대기 시간도 길어졌습니다.

그래서 기존 애플리케이션을 유지하면서 등록 정보는 늘리고, 반복해서 사용하는 출결 단계의 계산량은 줄이는 방향으로 고도화했습니다.

## 30초 요약

- 한 장만 저장하던 등록 방식을 3~10개 프레임의 개별 임베딩과 사용자 중심점 저장으로 바꿨습니다.
- 중심점으로 후보를 좁힌 뒤 개별 임베딩을 다시 비교합니다.
- 가장 가까운 후보의 거리와 1순위·2순위 후보의 차이를 함께 보고 승인합니다.
- 출결할 때는 3~5개 프레임 중 가장 선명한 한 장만 추론해 계산량을 조절했습니다.
- FastAPI 백엔드와 React 프론트엔드 전체 코드를 공개했고 얼굴 데이터와 운영 인증 정보는 제외했습니다.

## 무엇을 바꿨나

| 영역 | 현재 구현 |
|---|---|
| 얼굴 표현 | RetinaFace로 얼굴을 찾고 ArcFace로 512차원 임베딩 생성 |
| 사용자 등록 | 3~10개 프레임을 받아 선명도 35 미만을 제외하고 개별 임베딩과 정규화 중심점 저장 |
| 후보 검색 | 중심점 거리로 상위 5명을 고른 뒤 각 후보의 개별 임베딩을 다시 비교 |
| 승인 조건 | cosine distance `< 0.68`이고 서로 다른 사용자 1순위와 2순위의 차이가 `0.03` 이상일 때 승인 |
| 출결 처리 | 3~5개 프레임 가운데 가장 선명한 한 장으로 임베딩 생성 |
| 여러 얼굴 | 얼굴별로 식별한 뒤 같은 사용자가 한 이미지에서 두 번 기록되지 않도록 정리 |
| 출결 전환 | 최근 기록이 없거나 OUT이면 IN, 최근 기록이 IN이면 OUT |
| 라이브니스 | 미소 기반 방식과 MediaPipe Face Landmarker의 두 번 깜박임 방식 |
| 관리 화면 | 등록, 출결, 여러 얼굴 식별, 사용자 조회·삭제와 서버 로그 확인 |

선명도 `35`, 거리 임계값 `0.68`, 후보 차이 `0.03`은 현재 코드에 들어 있는 기준입니다. 운영 환경에서 FAR과 FRR을 측정해 정한 최종값은 아닙니다.

## 얼굴을 판정하는 과정

```mermaid
flowchart LR
    C["카메라 프레임"] --> D["RetinaFace 얼굴 검출"]
    D --> Q["선명도 확인"]
    Q --> E["ArcFace 임베딩"]
    E --> M["중심점 기준 상위 5명"]
    M --> S["개별 임베딩 재비교"]
    S --> G{"거리 < 0.68<br/>후보 차이 >= 0.03"}
    G -->|승인| A["출결 처리"]
    G -->|거절| R["미등록 또는 재시도"]
    A --> U["사용자 단위 중복 제거"]
    U --> DB["MariaDB 출결 기록"]
```

등록 단계에서는 촬영 조건이 다른 얼굴을 여러 장 저장합니다. 출결 단계에서는 가장 선명한 프레임 하나만 임베딩해 반복 처리의 계산량을 줄였습니다. 여러 얼굴이 들어온 사진은 얼굴별로 판정한 뒤 사용자 ID가 같은 결과 가운데 거리가 가장 가까운 하나만 기록합니다.

### 코드에서 확인할 위치

- [`FaceAnalysisService.create_embedding`](backend/app/services/face_service.py): RetinaFace 검출과 ArcFace 임베딩 생성
- [`find_closest_match_user_level_with_reason`](backend/app/services/face_service.py): 거리 임계값과 후보 차이를 함께 보는 판정
- [`register_user_v2`](backend/app/routers/face.py): 다중 프레임 등록과 중심점 생성
- [`check_in_out_v4`](backend/app/routers/attendance.py): 가장 선명한 프레임을 이용한 출결
- [`check_in_out_multi_image`](backend/app/routers/attendance.py): 여러 얼굴 판정과 사용자 중복 제거

## 로컬에서 실행하기

### 1. MariaDB 준비

전용 로컬 DB에서 [`backend/db_reset_v2.sql`](backend/db_reset_v2.sql)을 실행합니다. 이 스크립트는 `attendance_db`를 삭제하고 다시 만들기 때문에 기존 DB에는 실행하면 안 됩니다.

### 2. 백엔드

Python 3.10~3.12 환경을 권장합니다. 프로젝트 작업 당시 Python 3.13에서는 MediaPipe 호환 문제가 있었습니다.

```powershell
cd backend
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

`.env`의 DB 계정과 `LIVENESS_ADMIN_PASSWORD`를 로컬 값으로 바꿔야 합니다. 비밀번호가 없으면 라이브니스 설정을 변경할 수 없습니다. 프론트엔드 주소는 `CORS_ORIGINS`에서 지정합니다. API 문서는 `http://127.0.0.1:8000/docs`에서 볼 수 있습니다.

깜박임 라이브니스를 사용하려면 MediaPipe Face Landmarker 모델을 `backend/models/face_landmarker.task`에 따로 배치해야 합니다. 모델 파일은 저장소에 포함하지 않았습니다.

### 3. 프론트엔드

```powershell
cd frontend
Copy-Item .env.example .env
npm ci
npm run dev
```

기본 화면은 `http://127.0.0.1:5173`에서 열립니다.

## 저장소 구성

```text
backend/   FastAPI, DeepFace, SQLAlchemy, MariaDB 스키마
frontend/  React 19, Vite, TypeScript 화면
docs/      평가, 보안과 배포 전에 확인할 항목
assets/    공개 문서용 이미지
```

## 현재 확인한 범위

자동화 검사에서는 Python 코드 구문, 출결 IN/OUT 전환 단위 테스트와 TypeScript/Vite 프로덕션 빌드를 확인합니다. 얼굴 데이터셋을 이용한 정확도, FAR, FRR, ROC와 지연시간 비교는 아직 하지 않았습니다. 따라서 현재 구현을 성능 향상 수치로 설명하지 않습니다.

공개본은 로컬 연구용 프로토타입입니다. 사용자와 로그 관리 API의 인증, HTTPS, 임베딩 암호화와 보관 정책은 포함하지 않았습니다. 외부 네트워크에 그대로 배포하면 안 됩니다. 후속 평가와 운영 항목은 [평가·보안·배포 계획](docs/LEARNING_ROADMAP.md)에 정리했습니다.

실제 사용자 얼굴 이미지와 임베딩, `.env`, DB 접속 정보, 관리자 비밀번호, 모델 가중치, 로그와 빌드 결과물은 Git에 포함하지 않았습니다.
