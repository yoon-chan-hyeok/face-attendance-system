# Learning & Engineering Roadmap

## 1. 모델 평가

- 조명, 각도, 거리, 안경·마스크 조건별 평가 세트 설계
- threshold 변화에 따른 FAR, FRR, ROC 분석
- centroid-only와 centroid + sample rerank의 정확도·지연 비교
- liveness 우회 시나리오와 한계 문서화

**완료 증거:** 익명 평가 리포트, 고정된 calibration 절차, 실패 사례 갤러리

## 2. 백엔드·DB

- Alembic migration, transaction, 동시 check-in/out race condition 학습
- API schema validation과 권한 분리
- embedding 암호화·보관 기간·삭제 정책 구현

**완료 증거:** 통합 테스트, ERD, 동시성 테스트, 보안 체크리스트

## 3. 배포·관측

- Docker Compose로 web/API/DB 분리
- 요청 지연, 인식 실패율, DB 오류율 metrics
- 구조화 로그와 correlation ID
- CI에서 frontend build, Python test, lint 자동 실행

**완료 증거:** clean environment 재현 영상과 CI 통과 기록

