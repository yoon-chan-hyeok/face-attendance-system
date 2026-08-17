import io
import logging
import time
from typing import Dict, List, Tuple

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.attendance_log import AttendanceLog

from app.utils.file_utils import FileUtils
from app.utils.image_utils import ImageUtils
from app.db.session import get_db
from app.models.user import User
from app.models.user_embedding import UserEmbedding
from app.core.dependencies import face_service

router = APIRouter(tags=["face"])
logger = logging.getLogger(__name__)


def _build_hybrid_candidates(db: Session, users: List[User]) -> Tuple[List[Tuple[User, list]], Dict[int, List[list]]]:
    user_ids = [u.id for u in users]
    sample_vectors_by_user: Dict[int, List[list]] = {}

    if user_ids:
        rows = (
            db.query(UserEmbedding)
            .filter(UserEmbedding.user_id.in_(user_ids), UserEmbedding.is_active == True)
            .all()
        )
        for row in rows:
            vector = face_service.load_vector(row.embedding_path)
            if vector is not None:
                sample_vectors_by_user.setdefault(row.user_id, []).append(vector)

    centroid_candidates: List[Tuple[User, list]] = []
    for user in users:
        centroid_vector = None
        if user.profile_image:
            centroid_vector = face_service.load_vector(user.profile_image)

        if centroid_vector is None and sample_vectors_by_user.get(user.id):
            vectors = np.array(sample_vectors_by_user[user.id], dtype=np.float32)
            avg = np.mean(vectors, axis=0)
            norm = np.linalg.norm(avg)
            if norm > 0:
                centroid_vector = (avg / norm).tolist()

        if centroid_vector is not None:
            centroid_candidates.append((user, centroid_vector))

    return centroid_candidates, sample_vectors_by_user


def _hybrid_match_user(db: Session, target_vector: list, users: List[User], top_k: int = 5):
    centroid_candidates, sample_vectors_by_user = _build_hybrid_candidates(db, users)
    if not centroid_candidates:
        return None

    ranked = face_service.rank_candidates(target_vector, centroid_candidates)
    if not ranked:
        return None

    rerank_candidates: List[Tuple[User, list]] = []
    for entry in ranked[:top_k]:
        user = entry["user"]
        samples = sample_vectors_by_user.get(user.id, [])

        if not samples and user.profile_image:
            centroid_vector = face_service.load_vector(user.profile_image)
            if centroid_vector is not None:
                samples = [centroid_vector]

        for vec in samples:
            rerank_candidates.append((user, vec))

    if not rerank_candidates:
        return None

    return face_service.find_closest_match_user_level_with_reason(target_vector, rerank_candidates)


@router.post("/register")
async def register_user(
    file: UploadFile = File(...),
    employee_id: str = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Legacy single-image registration.
    """
    temp_path = None
    npy_path = None

    try:
        temp_path = FileUtils.save_upload_file(file)
        embedding_result = face_service.create_embedding(temp_path)
        if not embedding_result:
            raise HTTPException(status_code=400, detail="No face detected in image.")

        face_vector = embedding_result[0]["embedding"]
        npy_path = FileUtils.save_vector_to_npy(face_vector, name)

        existing_user = db.query(User).filter(User.name == name).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Already registered.")

        new_user = User(employee_id=employee_id, name=name, profile_image=npy_path)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "success": True,
            "message": "User registered successfully.",
            "user": {
                "id": new_user.id,
                "employee_id": new_user.employee_id,
                "name": new_user.name,
                "profile_image": new_user.profile_image,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        if npy_path:
            FileUtils.delete_file(npy_path)
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    finally:
        if temp_path:
            FileUtils.delete_file(temp_path)


@router.post("/register-v2")
async def register_user_v2(
    files: List[UploadFile] = File(...),
    employee_id: str = Form(...),
    name: str = Form(...),
    captured_frame_count: int | None = Form(default=None),
    capture_elapsed_ms: int | None = Form(default=None),
    db: Session = Depends(get_db),
):
    """
    Multi-shot registration with quality filtering.
    - Capture 5~10 frames
    - Filter low quality frames
    - Save per-user sample embeddings + centroid embedding
    """
    temp_paths: List[str] = []
    saved_paths: List[str] = []

    committed = False
    started_at = time.perf_counter()
    try:
        if len(files) < 3:
            raise HTTPException(status_code=400, detail="Minimum 3 frames required for registration.")

        existing_emp = db.query(User).filter(User.employee_id == employee_id).first()
        if existing_emp:
            raise HTTPException(status_code=400, detail="Employee ID already registered.")

        existing_name = db.query(User).filter(User.name == name).first()
        if existing_name:
            raise HTTPException(status_code=400, detail="Name already registered.")

        total_input = min(len(files), 10)
        logger.info(
            f"[Register V2] request received: name={name}, employee_id={employee_id}, "
            f"frames_in_request={len(files)}, frames_used={total_input}, "
            f"captured_frame_count={captured_frame_count}, capture_elapsed_ms={capture_elapsed_ms}"
        )

        for file in files[:10]:
            temp_paths.append(FileUtils.save_upload_file(file))

        # Quality threshold intentionally moderate to avoid overly strict rejection.
        min_quality = 35.0
        accepted_count = 0
        rejected_no_face = 0
        rejected_low_quality = 0
        candidates = []
        for index, path in enumerate(temp_paths):
            quality = face_service.compute_sharpness(path)
            logger.info(f"[Register V2] frame {index+1}/{len(temp_paths)} sharpness={quality:.2f}")

            embedding_result = face_service.create_embedding(path)
            if not embedding_result:
                rejected_no_face += 1
                logger.info(f"[Register V2] frame {index+1}: rejected (no face detected)")
                continue

            if quality < min_quality:
                rejected_low_quality += 1
                logger.info(
                    f"[Register V2] frame {index+1}: rejected (low quality {quality:.2f} < {min_quality:.2f})"
                )
                continue

            accepted_count += 1
            logger.info(f"[Register V2] frame {index+1}: accepted")
            candidates.append(
                {
                    "vector": embedding_result[0]["embedding"],
                    "quality": quality,
                }
            )

        logger.info(
            f"[Register V2] summary: accepted={accepted_count}, "
            f"rejected_no_face={rejected_no_face}, rejected_low_quality={rejected_low_quality}"
        )

        failed_count = rejected_no_face + rejected_low_quality

        # Partial success is allowed: at least one valid frame.
        if len(candidates) < 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No valid face frames detected. "
                    f"(saved_npy=0, failed_frames={failed_count}, "
                    f"rejected_no_face={rejected_no_face}, rejected_low_quality={rejected_low_quality})"
                ),
            )

        candidates.sort(key=lambda x: x["quality"], reverse=True)
        selected = candidates[:10]

        user = User(employee_id=employee_id, name=name, profile_image=None)
        db.add(user)
        db.flush()

        user_dir = f"data/encodings/{employee_id}"
        sample_vectors = []
        for i, item in enumerate(selected):
            vector = item["vector"]
            sample_vectors.append(np.array(vector, dtype=np.float32))
            sample_path = FileUtils.save_vector_to_npy(vector, f"{name}_sample_{i+1}", destination_dir=user_dir)
            saved_paths.append(sample_path)
            db.add(
                UserEmbedding(
                    user_id=user.id,
                    embedding_path=sample_path,
                    quality_score=float(item["quality"]),
                    is_active=True,
                )
            )
            logger.info(f"[Register V2] saved sample embedding {i+1}/{len(selected)}: {sample_path}")

        centroid = np.mean(np.stack(sample_vectors, axis=0), axis=0)
        centroid_norm = np.linalg.norm(centroid)
        if centroid_norm == 0:
            raise HTTPException(status_code=500, detail="Failed to compute centroid embedding.")
        centroid_vector = (centroid / centroid_norm).tolist()

        centroid_path = FileUtils.save_vector_to_npy(centroid_vector, f"{name}_centroid", destination_dir=user_dir)
        saved_paths.append(centroid_path)
        user.profile_image = centroid_path
        logger.info(f"[Register V2] saved centroid embedding: {centroid_path}")

        db.commit()
        committed = True
        db.refresh(user)
        face_service.clear_vector_cache()
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(
            f"[Register V2] completed successfully: user_id={user.id}, "
            f"sample_count={len(selected)}, server_elapsed_ms={elapsed_ms}"
        )
        logger.info(
            f"[Register V2] result stats: saved_npy={len(selected)+1}, "
            f"failed_frames={failed_count}, rejected_no_face={rejected_no_face}, "
            f"rejected_low_quality={rejected_low_quality}"
        )

        return {
            "success": True,
            "message": (
                "User registered successfully (multi-shot). "
                f"saved_npy={len(selected)+1}, failed_frames={failed_count}, "
                f"rejected_no_face={rejected_no_face}, rejected_low_quality={rejected_low_quality}"
            ),
            "stats": {
                "saved_npy": len(selected) + 1,  # samples + centroid
                "saved_sample_npy": len(selected),
                "failed_frames": failed_count,
                "rejected_no_face": rejected_no_face,
                "rejected_low_quality": rejected_low_quality,
            },
            "user": {
                "id": user.id,
                "employee_id": user.employee_id,
                "name": user.name,
                "profile_image": user.profile_image,
                "sample_count": len(selected),
            },
        }
    except HTTPException:
        db.rollback()
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info(f"[Register V2] failed with HTTPException, server_elapsed_ms={elapsed_ms}")
        raise
    except Exception as e:
        db.rollback()
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.exception(f"[Register V2] failed with exception, server_elapsed_ms={elapsed_ms}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    finally:
        for p in temp_paths:
            FileUtils.delete_file(p)
        if not committed:
            for p in saved_paths:
                FileUtils.delete_file(p)


@router.post("/identify")
async def identify_user(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    temp_path = None
    try:
        temp_path = FileUtils.save_upload_file(file)
        embedding_result = face_service.create_embedding(temp_path)
        if not embedding_result:
            raise HTTPException(status_code=400, detail="No face detected in image.")

        target_vector = embedding_result[0]["embedding"]
        facial_area = embedding_result[0]["facial_area"]

        users = db.query(User).all()
        if not users:
            raise HTTPException(status_code=404, detail="No registered users.")

        match_result = _hybrid_match_user(db, target_vector, users, top_k=5)
        if match_result and match_result.get("matched"):
            matched_user = match_result["user"]
            return {
                "success": True,
                "identified": True,
                "message": f"User identified: {matched_user.name}",
                "user": {
                    "name": matched_user.name,
                    "employee_id": matched_user.employee_id,
                    "profile_image": matched_user.profile_image,
                },
                "distance": match_result["distance"],
                "match_reason": "matched",
                "facial_area": facial_area,
            }

        return {
            "success": True,
            "identified": False,
            "message": match_result.get("message", "No matching user found.") if match_result else "No matching user found.",
            "distance": None,
            "failure_reason": match_result.get("failure_reason") if match_result else "unknown",
            "facial_area": facial_area,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path:
            FileUtils.delete_file(temp_path)


@router.post("/identify/multi")
async def identify_users_from_group_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Multi-face identification from one uploaded photo.
    Returns one result entry per detected face.
    """
    temp_path = None
    try:
        temp_path = FileUtils.save_upload_file(file)
        embedding_results = face_service.create_embedding(temp_path)
        if not embedding_results:
            raise HTTPException(status_code=400, detail="No face detected in image.")

        users = db.query(User).all()
        if not users:
            raise HTTPException(status_code=404, detail="No registered users.")

        face_results = []
        for idx, face_item in enumerate(embedding_results):
            target_vector = face_item.get("embedding")
            facial_area = face_item.get("facial_area")

            if not target_vector:
                face_results.append(
                    {
                        "face_index": idx,
                        "identified": False,
                        "message": "No embedding for detected face.",
                        "failure_reason": "no_embedding",
                        "facial_area": facial_area,
                    }
                )
                continue

            match_result = _hybrid_match_user(db, target_vector, users, top_k=5)
            if match_result and match_result.get("matched"):
                matched_user = match_result["user"]
                face_results.append(
                    {
                        "face_index": idx,
                        "identified": True,
                        "message": f"User identified: {matched_user.name}",
                        "user": {
                            "id": matched_user.id,
                            "name": matched_user.name,
                            "employee_id": matched_user.employee_id,
                            "profile_image": matched_user.profile_image,
                        },
                        "distance": match_result.get("distance"),
                        "second_distance": match_result.get("second_distance"),
                        "margin": match_result.get("margin"),
                        "facial_area": facial_area,
                    }
                )
            else:
                face_results.append(
                    {
                        "face_index": idx,
                        "identified": False,
                        "message": match_result.get("message", "No matching user found.")
                        if match_result
                        else "No matching user found.",
                        "failure_reason": match_result.get("failure_reason", "unknown")
                        if match_result
                        else "unknown",
                        "distance": match_result.get("distance") if match_result else None,
                        "second_distance": match_result.get("second_distance") if match_result else None,
                        "margin": match_result.get("margin") if match_result else None,
                        "facial_area": facial_area,
                    }
                )

        return {
            "success": True,
            "face_count": len(face_results),
            "results": face_results,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path:
            FileUtils.delete_file(temp_path)


@router.post("/identify/visualize")
async def identify_visualize(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    temp_path = None
    try:
        temp_path = FileUtils.save_upload_file(file)
        embedding_result = face_service.create_embedding(temp_path)

        text_to_draw = "Unknown"
        facial_area = {}

        if embedding_result:
            target_vector = embedding_result[0]["embedding"]
            facial_area = embedding_result[0]["facial_area"]
            users = db.query(User).all()
            match_result = _hybrid_match_user(db, target_vector, users, top_k=5)

            if match_result and match_result.get("matched"):
                matched_user = match_result["user"]
                distance = match_result["distance"]
                text_to_draw = f"{matched_user.name} ({distance:.2f})"

        if facial_area:
            result_img = ImageUtils.draw_face_box(temp_path, facial_area, text_to_draw)
        else:
            result_img = cv2.imread(temp_path)

        _, im_jpg = cv2.imencode(".jpg", result_img)
        return StreamingResponse(io.BytesIO(im_jpg.tobytes()), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path:
            FileUtils.delete_file(temp_path)


@router.get("/users")
async def list_registered_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.desc()).all()
    if not users:
        return {"users": []}

    user_ids = [u.id for u in users]
    embeddings = (
        db.query(UserEmbedding)
        .filter(UserEmbedding.user_id.in_(user_ids))
        .all()
    )
    count_map: Dict[int, int] = {}
    for emb in embeddings:
        count_map[emb.user_id] = count_map.get(emb.user_id, 0) + 1

    return {
        "users": [
            {
                "id": u.id,
                "employee_id": u.employee_id,
                "name": u.name,
                "centroid_path": u.profile_image,
                "embedding_count": count_map.get(u.id, 0),
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }


@router.delete("/users/{user_id}")
async def delete_registered_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    embedding_rows = db.query(UserEmbedding).filter(UserEmbedding.user_id == user_id).all()
    paths_to_delete = [row.embedding_path for row in embedding_rows if row.embedding_path]
    if user.profile_image:
        paths_to_delete.append(user.profile_image)

    try:
        db.query(AttendanceLog).filter(AttendanceLog.employee_id == user.employee_id).delete()
        db.query(UserEmbedding).filter(UserEmbedding.user_id == user_id).delete()
        db.delete(user)
        db.commit()

        for path in set(paths_to_delete):
            FileUtils.delete_file(path)

        face_service.clear_vector_cache()
        return {"success": True, "deleted_user_id": user_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

