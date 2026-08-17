# Attendance API guide

모든 경로의 prefix는 `/api/v1/attendance`입니다. 요청과 응답의 전체 스키마는 서버 실행 후 `/docs`에서 확인할 수 있습니다.

## 출결 기록 경로

| Method | Path | 입력 및 처리 |
|---|---|---|
| `POST` | `/check-in-out` | 이미지 1장, 선택적 smile 라이브니스 |
| `POST` | `/check-in-out-v2` | 3개 이상 프레임, 선택적 blink 라이브니스, 마지막 프레임 임베딩 |
| `POST` | `/check-in-out-v3` | 3개 이상·최대 5개 프레임, 유효 임베딩 평균 |
| `POST` | `/check-in-out-v4` | 3개 이상·최대 5개 프레임 중 sharpness가 가장 높은 한 장만 임베딩 |
| `POST` | `/check-in-out-multi-image` | 사진 한 장의 여러 얼굴을 식별하고 사용자별 한 번만 기록 |

프론트엔드 기본 출결 화면은 V4를 호출합니다.

식별 성공 후 다음 규칙으로 출결을 기록합니다.

```text
마지막 기록 없음 -> IN
마지막 기록 IN   -> OUT
마지막 기록 OUT  -> IN
```

## 조회 경로

| Method | Path | 설명 |
|---|---|---|
| `GET` | `/history/{employee_id}?limit=10` | 특정 사용자의 최근 출결 이력 |
| `GET` | `/history?limit=50` | 전체 최근 출결 이력 |
| `GET` | `/status/{employee_id}` | 마지막 기록을 기준으로 현재 상태 조회 |

## 판정 실패

다음 경우에는 출결 로그를 생성하지 않습니다.

- 얼굴 또는 등록 후보를 찾지 못한 경우
- 최저 cosine distance가 `0.68` 이상인 경우
- 서로 다른 사용자 Top-1/Top-2 거리 차이가 `0.03` 미만인 경우
- 라이브니스가 활성화되어 있고 smile/blink 검사를 통과하지 못한 경우

이 값은 현재 코드의 기준값이며, 운영 데이터 기반 FAR/FRR 보정 결과는 아닙니다.

## 주의

- 출결 기록 시각은 서버의 `datetime.now()`를 사용합니다.
- 동시 요청에 대한 트랜잭션·중복 기록 검증은 완료되지 않았습니다.
- 프로덕션 배포 전 인증·권한, CORS, DB 접근 제한과 생체정보 보관 정책이 필요합니다.
