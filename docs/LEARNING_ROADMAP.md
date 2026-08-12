# 미구현 평가·보안·배포 계획

아래 항목은 현재 공개 case study에서 완료하지 않은 후속 검증입니다.

## 모델 평가

- 조명, 각도, 거리, 안경과 마스크 조건별 평가 세트
- threshold 변화에 따른 FAR, FRR와 ROC 분석
- centroid-only와 sample rerank의 정확도·지연 비교
- liveness 우회 시나리오 평가

## 애플리케이션과 운영

- migration, transaction과 동시 check-in/out test
- API schema validation, 인증과 권한 분리
- embedding 암호화, 보관 기간과 삭제 정책
- Docker Compose, metrics, structured log와 CI

완료 기준은 익명 평가 리포트, calibration 절차, 통합·동시성 테스트와 보안 체크리스트입니다.
