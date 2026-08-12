![Face Attendance System project hero](assets/project-hero.svg)

<div align="center">

**RetinaFace·ArcFace 인식 파이프라인을 multi-frame enrollment, ambiguity rejection, FastAPI·MariaDB·React 출결 workflow로 연결한 full-stack engineering case study**

![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![Vision](https://img.shields.io/badge/Vision-RetinaFace%20%2B%20ArcFace-4F46E5)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-0EA5E9?logo=react&logoColor=white)
![Status](https://img.shields.io/badge/Public-Engineering%20Case%20Study-D97706)

[핵심 설계](#세-가지-핵심-판단) · [시스템 구조](#시스템-구조) · [개인정보 경계](#개인정보와-공개-범위) · [확장 계획](docs/LEARNING_ROADMAP.md)

</div>

---

## 이 프로젝트는

얼굴 인식 모델의 top-1 결과를 출석 처리에 바로 사용하면 흐린 등록 사진, 비슷한 후보와 중복 검출 때문에 잘못된 기록이 남을 수 있습니다. 이 프로젝트는 RetinaFace와 ArcFace를 실제 출결 흐름에 연결하면서 등록 품질, 모호한 식별과 기록 일관성을 함께 다룬 full-stack case study입니다.

등록 단계에서는 여러 frame을 수집하고 품질 기준을 통과한 sample로 representation을 구성합니다. 식별 단계에서는 similarity threshold뿐 아니라 top-2 margin도 확인해 애매한 후보를 거절합니다. 승인된 결과는 FastAPI, MariaDB와 React 관리 화면을 거쳐 IN/OUT 기록으로 저장됩니다.

### 시작한 이유

모델 demo와 운영 시스템 사이에는 판정 기준, 데이터 모델, 예외 처리와 개인정보 경계가 있습니다. 얼굴을 찾고 이름을 반환하는 기능만으로는 출결 업무를 안정적으로 처리할 수 없습니다. 인식 결과를 보수적인 decision rule과 application workflow로 연결하는 과정을 정리하기 위해 만들었습니다.

### 이 프로젝트에서 적용한 접근

얼굴 인식 모델의 top-1 결과를 바로 출석 기록으로 남기는 대신, 실제 사용자 흐름을 먼저 연결해 어디에서 잘못된 기록이 생기는지 살펴봤습니다. 등록 사진 품질, 비슷한 두 후보, 중복 검출과 IN/OUT 상태를 각각 나눠 본 뒤 multi-frame enrollment와 threshold plus margin 규칙을 적용했습니다.

모델 출력이 API, DB와 관리 화면을 거쳐 업무 기록이 되는 전체 흐름을 기준으로 설계했습니다. 생체정보를 다루는 만큼 공개 가능한 구조와 비공개 데이터를 분리했고, 현재 threshold를 운영 기준으로 과장하지 않았습니다. FAR과 FRR 보정, 동시성, 권한, 관측과 배포 항목은 추가 검증이 필요한 작업으로 문서화했습니다.

## 상세 설명

| 구분 | 내용 |
|---|---|
| **Vision** | RetinaFace detection과 ArcFace embedding으로 얼굴 영역과 identity representation을 생성 |
| **Enrollment** | multi-frame quality filtering 후 centroid candidate와 원본 sample을 함께 보존 |
| **Decision rule** | top-1 threshold와 top-2 margin을 동시에 적용해 ambiguous match를 reject |
| **Application** | FastAPI, SQLAlchemy, MariaDB, React/Vite로 등록·식별·IN/OUT 기록·관리 화면을 연결 |
| **Public scope** | 생체정보와 운영 설정을 제외한 architecture, decision rule, trade-off 중심 case study |

`0.68` threshold와 `0.03` margin은 구현 예시값입니다. 실제 환경에는 별도 데이터로 FAR/FRR calibration이 필요합니다.

## 제품으로 연결할 때 생기는 문제

얼굴 인식 demo와 출결 시스템 사이에는 여러 engineering gap이 있습니다.

- 등록 사진이 흐리거나 한 각도에 치우치면 representation이 불안정합니다.
- top-1 점수만 높다고 동일인이라고 단정할 수 없습니다.
- 같은 사람이 한 frame에서 중복 검출될 수 있습니다.
- 인식 결과를 IN/OUT 상태·사용자·로그 모델과 연결해야 합니다.
- 얼굴 image와 embedding은 생체정보이므로 공개·보관 경계가 필요합니다.

## 시스템 구조

```mermaid
flowchart LR
    C["Camera frames"] --> D["RetinaFace<br/>detection"]
    D --> Q["Quality +<br/>sharpness gate"]
    Q --> E["ArcFace<br/>embeddings"]
    E --> M["Centroid candidate<br/>+ sample verification"]
    M --> G{"Threshold 0.68<br/>Margin 0.03"}
    G -->|accept| A["Attendance service"]
    G -->|uncertain| R["Reject / retry"]
    A --> DB["MariaDB<br/>users · vectors · logs"]
    DB --> UI["React<br/>admin dashboard"]
```

## 세 가지 핵심 판단

### 1 · 등록 품질을 추론보다 먼저 관리

1초 동안 여러 frame을 모으고 선명도 기준을 통과한 얼굴만 사용했습니다. 우연히 잘 나온 한 장보다 다양한 sample을 보관하고 centroid를 후보 탐색에 사용하도록 구성했습니다.

### 2 · 최고 점수만으로 승인하지 않음

top-1 similarity가 threshold를 넘더라도 top-2와 차이가 작으면 identity가 모호합니다. 절대 기준 `0.68`과 후보 간 margin `0.03`을 함께 적용해 ambiguous match를 거절했습니다.

### 3 · 모델 출력을 업무 상태로 변환

식별 성공을 끝으로 두지 않고 최근 기록을 기준으로 IN/OUT을 전환하고, 사용자·embedding·attendance log를 관계형 모델로 분리했습니다.

## 구현 기능

- multi-frame enrollment와 quality filtering
- single / multi-face identification
- 동일 사용자의 중복 검출 정리
- smile·blink 기반 보조 liveness
- 실시간 camera attendance와 IN/OUT 전환
- 사용자·embedding·attendance log 관리
- 관리자용 사용자·로그 화면
- 환경변수 기반 DB·frontend API configuration

## 주요 설계 결정

| 결정 | 이유 | 남은 검증 |
|---|---|---|
| centroid 후보 + sample 재비교 | 탐색 속도와 개인 내 다양성 동시 반영 | 사용자 규모별 latency |
| threshold + margin gate | 유사한 두 후보 사이의 모호성 거절 | FAR/FRR calibration |
| multi-frame enrollment | blur·각도 편향 완화 | 조건별 등록 품질 실험 |
| liveness를 보조 신호로 한정 | 단순 blink/smile의 보안 한계 인정 | 전문 anti-spoofing 평가 |
| image·embedding 공개 제외 | 생체정보 노출 방지 | 보관·삭제 정책 |

## 개인정보와 공개 범위

이 저장소는 **engineering case study**를 공개합니다. 원본 작업 환경에는 실제 얼굴 image, embedding, DB 설정과 운영 configuration이 포함되어 있어 application source snapshot과 개인정보성 artifact는 공개하지 않았습니다.

공개 범위:

- 시스템 architecture와 주요 data flow
- identification decision rule과 설계 근거
- 구현 stack, 기능 범위, engineering trade-off
- 개인정보·보안·운영 한계와 학습 로드맵

실제 운영에는 명시적 동의, 접근 통제, 암호화, 보관 기간, 삭제 절차와 FAR/FRR·spoof robustness 검증이 추가로 필요합니다.

## 기여 범위

사용자 흐름, 등록·식별 전략, decision rule, API·DB·frontend 통합과 반복 검증을 맡았습니다. threshold의 해석 범위와 생체정보를 포함한 비공개 경계를 별도로 검토했습니다.

[모델 평가·보안·운영 확장 로드맵](docs/LEARNING_ROADMAP.md)


