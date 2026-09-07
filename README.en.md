# Face Attendance System Upgrade

[한국어](README.md)

I upgraded an existing face attendance system after observing a look-alike user being incorrectly accepted. The changes preserve multiple enrollment samples, narrow the candidate search, and require the best candidate to be sufficiently distinct from the runner-up.

The central decision is a margin gate: when two users are too close, the system rejects the match without writing an attendance record. The implementation is a local prototype; accuracy and latency improvements have not been quantified.

## Why change the decision rule?

The target workflow is a registered user checking in or out through a camera. The initial system stored one representative embedding per user and accepted the closest candidate when its distance passed a threshold.

Tests under different lighting and camera positions exposed incorrect acceptance of similar users. A low distance to the best candidate did not explain whether a second user was almost equally close. I chose to request another capture for ambiguous cases, considering the cost of correcting a wrong attendance record later.

## Design decisions

| Problem | Implementation | Intended effect |
|---|---|---|
| One image does not represent capture variation | Store multiple sample embeddings and their centroid | Retain observed facial variation at enrollment |
| All-sample matching grows with enrollment size | Retrieve Top-5 users by centroid, then compare their samples | Limit the final sample comparisons to candidate users |
| A threshold alone accepts ambiguous candidates | Require both distance and a user-level margin gap | Reject close competing identities |
| Repeated multi-frame embedding is expensive | Embed only the sharpest attendance frame | Reduce embedding calls per repeated check-in |
| Multiple detected faces can map to one user | Keep the best match per user within an image request | Avoid toggling the same user's IN/OUT twice in that request |

For each candidate user, the matcher uses the smallest distance across that user's samples. It then compares distinct users:

```text
d1 = best user's cosine distance
d2 = second-best user's cosine distance
margin = d2 - d1

Prototype acceptance rule: d1 < 0.68 AND margin >= 0.03
```

If only one valid candidate user remains, the implementation skips the margin condition and uses distance alone. These thresholds are prototype settings, not calibrated FAR/FRR results. [`find_closest_match_user_level_with_reason`](backend/app/services/face_service.py) implements the decision and returns specific rejection reasons.

[Detailed enrollment and matching design](docs/DESIGN.md) · [API guide](backend/ATTENDANCE_API_GUIDE.md)

## Implemented workflow

FastAPI and React connect multi-frame registration, attendance, multi-face identification, user management and server logs. RetinaFace detects faces and ArcFace generates embeddings. Enrollment retains valid samples and a centroid; V4 attendance selects the sharpest of three to five frames before matching. Successful attendance toggles IN/OUT based on the latest record.

The UI provides registration at `/register`, attendance at `/`, multi-face modes at `/multi` and `/multi-live`, and management at `/db` and `/logs`. Smile-based and MediaPipe blink liveness checks are optional. [Troubleshooting notes](backend/TROUBLESHOOTING.md) record the Tasks API migration, DB access configuration and multi-image upload issues.

## Run locally

Use a dedicated local MariaDB database. [`backend/db_reset_v2.sql`](backend/db_reset_v2.sql) drops and recreates `attendance_db`; do not run it against an existing database containing data you need.

The CI checks Python syntax and lightweight unit tests on Python 3.12. It does not exercise the full DeepFace/TensorFlow inference environment. Development notes record a Python 3.13 MediaPipe issue resolved by moving to the Tasks API.

```powershell
cd backend
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Set local DB credentials, `LIVENESS_ADMIN_PASSWORD` and `CORS_ORIGINS` in `.env`. Swagger is at `http://127.0.0.1:8000/docs`. Blink liveness requires the [separate Face Landmarker model](backend/models/README.md).

From the repository's `frontend` directory in another terminal:

```powershell
cd frontend
Copy-Item .env.example .env
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`, register a user, then run attendance. The app needs a camera, MariaDB and face models. There is no public hosted demo.

## Validation and limits

Automation checks Python syntax, attendance transitions, liveness configuration and the TypeScript/Vite build. The public code implements the matching and management paths described above.

Face-dataset Accuracy/FAR/FRR, threshold calibration, before/after latency and load testing remain unmeasured. Candidate retrieval recall also matters: the sample stage cannot recover a correct user excluded by Top-k. A larger margin can increase rejection of legitimate users and must be assessed alongside false acceptance.

The prototype lacks authentication for user/log management, HTTPS and embedding encryption/retention controls. Deduplication applies within an image request; concurrent-request duplicate handling is not verified. [Evaluation and deployment work](docs/LEARNING_ROADMAP.md) records the remaining tasks. Face images, embeddings, credentials, model weights and runtime logs are excluded from Git.
