# app/routers/attendance.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple

from app.db.session import get_db
from app.models.user import User
from app.models.user_embedding import UserEmbedding
from app.services.attendance_service import attendance_service
from app.core.dependencies import face_service
from app.services.liveness_service import liveness_config_service
from app.services.blink_service import blink_service
from app.schemas.attendance import AttendanceResponse, AttendanceHistoryResponse
from app.utils.file_utils import FileUtils
import numpy as np
import cv2

router = APIRouter(tags=["attendance"])


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


def _build_match_failure_detail(match_result: Dict | None) -> str:
    if not match_result:
        return "No matching user found."

    reason = match_result.get("failure_reason")
    distance = match_result.get("distance")
    threshold = match_result.get("threshold")
    margin = match_result.get("margin")
    margin_threshold = match_result.get("margin_threshold")

    if reason == "margin_gate":
        return (
            "No matching user found: margin gate rejected this match "
            f"(margin={margin}, required>={margin_threshold})."
        )
    if reason == "threshold":
        return (
            "No matching user found: threshold not met "
            f"(distance={distance}, threshold={threshold})."
        )
    return "No matching user found."


@router.post("/check-in-out", response_model=AttendanceResponse)
async def check_in_out(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Face recognition based automatic check-in/out
    
    - Identifies user from uploaded face image
    - If liveness mode is enabled, performs smile verification first
    - Automatically records OUT if last record was IN, and vice versa
    - Records as IN if this is the first record
    
    Example scenario:
    1. Check-in (IN)
    2. Leave (OUT)
    3. Return (IN)
    4. Check-out (OUT)
    """
    temp_path = None
    
    print(f"=== [Attendance] Check-in/out request started ===")
    
    try:
        # 1. Save image
        temp_path = FileUtils.save_upload_file(file)
        
        # 2. Liveness check (if enabled)
        if liveness_config_service.is_enabled():
            print(f"[Attendance] Liveness check started...")
            liveness_result = face_service.check_liveness(temp_path)
            
            if not liveness_result.get("passed", False):
                happy_score = liveness_result.get("happy_score", 0.0)
                threshold = liveness_result.get("threshold", 0.5)
                raise HTTPException(
                    status_code=400,
                    detail=f"Liveness check failed: Please smile!"
                )
            print(f"[Attendance] Liveness check passed")
        
        # 3. Create face embedding
        embedding_result = face_service.create_embedding(temp_path)
        
        if not embedding_result:
            raise HTTPException(
                status_code=400, 
                detail="No face detected in image."
            )
        
        target_vector = embedding_result[0]['embedding']
        print(f"[Attendance] Face vector created")
        
        # 4. User identification (1:N matching) - same logic as /identify
        users = db.query(User).all()
        
        if not users:
            raise HTTPException(
                status_code=404, 
                detail="No registered users found."
            )
        
        match_result = _hybrid_match_user(db, target_vector, users, top_k=5)
        
        if not match_result or not match_result.get("matched"):
            raise HTTPException(
                status_code=404, 
                detail=_build_match_failure_detail(match_result)
            )
        
        matched_user = match_result['user']
        distance = match_result['distance']
        print(f"[Attendance] User identified: {matched_user.name} (distance: {distance:.4f})")
        
        # 5. Record attendance (auto IN/OUT)
        attendance_log = attendance_service.record_attendance(
            db=db,
            employee_id=matched_user.employee_id,
            employee_name=matched_user.name
        )
        
        action_text = "Check-in" if attendance_log.action_type.value == "IN" else "Check-out"
        print(f"[Attendance] {action_text} recorded: {matched_user.name} ({attendance_log.action_at})")
        
        return AttendanceResponse(
            success=True,
            message=f"{action_text} completed",
            action_type=attendance_log.action_type.value,
            employee_id=attendance_log.employee_id,
            employee_name=attendance_log.employee_name,
            action_at=attendance_log.action_at
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Attendance] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Attendance processing failed: {str(e)}")
    finally:
        if temp_path:
            FileUtils.delete_file(temp_path)


@router.post("/check-in-out-v2", response_model=AttendanceResponse)
async def check_in_out_v2(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    [V2] Face recognition based automatic check-in/out (eye blink liveness)    
    """
    temp_paths = []
    
    print(f"=== [Attendance V2] Check-in/out request started ({len(files)} frames) ===")
    
    if len(files) < 3:
        raise HTTPException(
            status_code=400,
            detail="Minimum 3 frames required. (Recommended: 10~15)"
        )
    
    try:
        # 1. Save all images
        for file in files:
            temp_path = FileUtils.save_upload_file(file)
            temp_paths.append(temp_path)
        
        print(f"[Attendance V2] {len(temp_paths)} frames saved")
        
        # 2. Liveness check (if enabled) - MediaPipe eye blink
        if liveness_config_service.is_enabled():
            print(f"[Attendance V2] Liveness check started (eye blink)...")
            blink_result = blink_service.detect_blink(temp_paths)
            
            if not blink_result.get("blink_detected", False):
                blink_count = blink_result.get("blink_count", 0)
                detail = blink_result.get("detail", "No eye blink detected")
                raise HTTPException(
                    status_code=400,
                    detail=f"Please blink your eyes! (Detected blinks: {blink_count})"
                )
            
            blink_count = blink_result.get("blink_count", 0)
            print(f"[Attendance V2] Liveness check passed (blink count: {blink_count})")
        
        # 3. Create face embedding (using last frame) - existing DeepFace logic
        last_frame = temp_paths[-1]
        embedding_result = face_service.create_embedding(last_frame)
        
        if not embedding_result:
            raise HTTPException(
                status_code=400, 
                detail="No face detected in image."
            )
        
        target_vector = embedding_result[0]['embedding']
        print(f"[Attendance V2] Face vector created")
        
        # 4. User identification (1:N matching)
        users = db.query(User).all()
        
        if not users:
            raise HTTPException(
                status_code=404, 
                detail="No registered users found."
            )
        
        match_result = _hybrid_match_user(db, target_vector, users, top_k=5)
        
        if not match_result or not match_result.get("matched"):
            raise HTTPException(
                status_code=404, 
                detail=_build_match_failure_detail(match_result)
            )
        
        matched_user = match_result['user']
        distance = match_result['distance']
        print(f"[Attendance V2] User identified: {matched_user.name} (distance: {distance:.4f})")
        
        # 5. Record attendance (auto IN/OUT)
        attendance_log = attendance_service.record_attendance(
            db=db,
            employee_id=matched_user.employee_id,
            employee_name=matched_user.name
        )
        
        action_text = "Check-in" if attendance_log.action_type.value == "IN" else "Check-out"
        print(f"[Attendance V2] {action_text} recorded: {matched_user.name} ({attendance_log.action_at})")
        
        return AttendanceResponse(
            success=True,
            message=f"{action_text}",
            action_type=attendance_log.action_type.value,
            employee_id=attendance_log.employee_id,
            employee_name=attendance_log.employee_name,
            action_at=attendance_log.action_at
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Attendance V2] Error: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Attendance processing failed: {str(e)}")
    finally:
        # Delete all temp files
        for path in temp_paths:
            FileUtils.delete_file(path)


@router.post("/check-in-out-v3", response_model=AttendanceResponse)
async def check_in_out_v3(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    [V3] Face recognition based automatic check-in/out
    - Uses multiple frames
    - Runs blink liveness (when enabled)
    - Computes average embedding from all valid frames, then matches once
    """
    temp_paths = []

    print(f"=== [Attendance V3] Check-in/out request started ({len(files)} frames) ===")

    if len(files) < 3:
        raise HTTPException(
            status_code=400,
            detail="Minimum 3 frames required. (Recommended: 5)"
        )

    try:
        max_frames = 5
        selected_files = files[:max_frames]

        # 1. Save all images
        for file in selected_files:
            temp_path = FileUtils.save_upload_file(file)
            temp_paths.append(temp_path)

        print(f"[Attendance V3] {len(temp_paths)} frames saved (max {max_frames})")

        # 2. Liveness check (if enabled) - MediaPipe eye blink
        if liveness_config_service.is_enabled():
            print(f"[Attendance V3] Liveness check started (eye blink)...")
            blink_result = blink_service.detect_blink(temp_paths)

            if not blink_result.get("blink_detected", False):
                blink_count = blink_result.get("blink_count", 0)
                raise HTTPException(
                    status_code=400,
                    detail=f"Please blink your eyes! (Detected blinks: {blink_count})"
                )

            blink_count = blink_result.get("blink_count", 0)
            print(f"[Attendance V3] Liveness check passed (blink count: {blink_count})")

        # 3. Create embeddings for all frames and average valid vectors
        vectors = []
        for path in temp_paths:
            embedding_result = face_service.create_embedding(path)
            if not embedding_result:
                continue
            vectors.append(np.array(embedding_result[0]['embedding'], dtype=np.float32))

        if not vectors:
            raise HTTPException(
                status_code=400,
                detail="No face detected in captured frames."
            )

        avg_vector = np.mean(np.stack(vectors, axis=0), axis=0)
        avg_norm = np.linalg.norm(avg_vector)
        if avg_norm == 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid face vector computed from frames."
            )

        target_vector = (avg_vector / avg_norm).tolist()
        print(f"[Attendance V3] Averaged embedding created from {len(vectors)} valid frames")

        # 4. User identification (1:N matching)
        users = db.query(User).all()

        if not users:
            raise HTTPException(
                status_code=404,
                detail="No registered users found."
            )

        match_result = _hybrid_match_user(db, target_vector, users, top_k=5)

        if not match_result or not match_result.get("matched"):
            raise HTTPException(
                status_code=404,
                detail=_build_match_failure_detail(match_result)
            )

        matched_user = match_result['user']
        distance = match_result['distance']
        print(f"[Attendance V3] User identified: {matched_user.name} (distance: {distance:.4f})")

        # 5. Record attendance (auto IN/OUT)
        attendance_log = attendance_service.record_attendance(
            db=db,
            employee_id=matched_user.employee_id,
            employee_name=matched_user.name
        )

        action_text = "Check-in" if attendance_log.action_type.value == "IN" else "Check-out"
        print(f"[Attendance V3] {action_text} recorded: {matched_user.name} ({attendance_log.action_at})")

        return AttendanceResponse(
            success=True,
            message=f"{action_text}",
            action_type=attendance_log.action_type.value,
            employee_id=attendance_log.employee_id,
            employee_name=attendance_log.employee_name,
            action_at=attendance_log.action_at
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Attendance V3] Error: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Attendance processing failed: {str(e)}")
    finally:
        for path in temp_paths:
            FileUtils.delete_file(path)


@router.post("/check-in-out-v4", response_model=AttendanceResponse)
async def check_in_out_v4(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    [V4] Face recognition based automatic check-in/out
    - Uses up to 5 frames for capture/liveness
    - Selects best frame by sharpness
    - Creates one embedding from best frame
    """
    temp_paths = []

    print(f"=== [Attendance V4] Check-in/out request started ({len(files)} frames) ===")

    if len(files) < 3:
        raise HTTPException(
            status_code=400,
            detail="Minimum 3 frames required. (Recommended: 5)"
        )

    try:
        max_frames = 5
        selected_files = files[:max_frames]

        # 1. Save selected images
        for file in selected_files:
            temp_path = FileUtils.save_upload_file(file)
            temp_paths.append(temp_path)

        print(f"[Attendance V4] {len(temp_paths)} frames saved (max {max_frames})")

        # 2. Liveness check (if enabled) - MediaPipe eye blink
        if liveness_config_service.is_enabled():
            print(f"[Attendance V4] Liveness check started (eye blink)...")
            blink_result = blink_service.detect_blink(temp_paths)

            if not blink_result.get("blink_detected", False):
                blink_count = blink_result.get("blink_count", 0)
                raise HTTPException(
                    status_code=400,
                    detail=f"Please blink your eyes! (Detected blinks: {blink_count})"
                )

            blink_count = blink_result.get("blink_count", 0)
            print(f"[Attendance V4] Liveness check passed (blink count: {blink_count})")

        # 3. Pick best frame (sharpest) and embed once
        best_path = None
        best_sharpness = -1.0
        for path in temp_paths:
            image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue
            sharpness = cv2.Laplacian(image, cv2.CV_64F).var()
            if sharpness > best_sharpness:
                best_sharpness = sharpness
                best_path = path

        if not best_path:
            raise HTTPException(
                status_code=400,
                detail="No valid frame found for face embedding."
            )

        embedding_result = face_service.create_embedding(best_path)
        if not embedding_result:
            raise HTTPException(
                status_code=400,
                detail="No face detected in selected frame."
            )

        target_vector = embedding_result[0]['embedding']
        print(f"[Attendance V4] Embedding created from best frame (sharpness: {best_sharpness:.2f})")

        # 4. User identification (1:N matching)
        users = db.query(User).all()

        if not users:
            raise HTTPException(
                status_code=404,
                detail="No registered users found."
            )

        match_result = _hybrid_match_user(db, target_vector, users, top_k=5)

        if not match_result or not match_result.get("matched"):
            raise HTTPException(
                status_code=404,
                detail=_build_match_failure_detail(match_result)
            )

        matched_user = match_result['user']
        distance = match_result['distance']
        print(f"[Attendance V4] User identified: {matched_user.name} (distance: {distance:.4f})")

        # 5. Record attendance (auto IN/OUT)
        attendance_log = attendance_service.record_attendance(
            db=db,
            employee_id=matched_user.employee_id,
            employee_name=matched_user.name
        )

        action_text = "Check-in" if attendance_log.action_type.value == "IN" else "Check-out"
        print(f"[Attendance V4] {action_text} recorded: {matched_user.name} ({attendance_log.action_at})")

        return AttendanceResponse(
            success=True,
            message=f"{action_text}",
            action_type=attendance_log.action_type.value,
            employee_id=attendance_log.employee_id,
            employee_name=attendance_log.employee_name,
            action_at=attendance_log.action_at
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Attendance V4] Error: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Attendance processing failed: {str(e)}")
    finally:
        for path in temp_paths:
            FileUtils.delete_file(path)


@router.post("/check-in-out-multi-image")
async def check_in_out_multi_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Multi-face attendance from one uploaded image.
    - Detects multiple faces in the photo
    - Matches each face to registered users
    - Records attendance once per unique matched user (best face per user)
    """
    temp_path = None

    print("=== [Attendance Multi] Check-in/out request started (single image) ===")

    try:
        temp_path = FileUtils.save_upload_file(file)

        embedding_results = face_service.create_embedding(temp_path)
        if not embedding_results:
            raise HTTPException(
                status_code=400,
                detail="No face detected in image."
            )

        users = db.query(User).all()
        if not users:
            raise HTTPException(
                status_code=404,
                detail="No registered users found."
            )

        # First pass: match every detected face
        face_matches: List[Dict] = []
        for idx, face_item in enumerate(embedding_results):
            target_vector = face_item.get("embedding")
            facial_area = face_item.get("facial_area")

            if not target_vector:
                face_matches.append(
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
            if not match_result or not match_result.get("matched"):
                face_matches.append(
                    {
                        "face_index": idx,
                        "identified": False,
                        "message": _build_match_failure_detail(match_result),
                        "failure_reason": match_result.get("failure_reason", "unknown")
                        if match_result
                        else "unknown",
                        "distance": match_result.get("distance") if match_result else None,
                        "second_distance": match_result.get("second_distance") if match_result else None,
                        "margin": match_result.get("margin") if match_result else None,
                        "facial_area": facial_area,
                    }
                )
                continue

            matched_user = match_result["user"]
            face_matches.append(
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
                    "_matched_user_obj": matched_user,
                }
            )

        # Pick one best face per user (smallest distance) to avoid duplicate IN/OUT toggles.
        best_face_by_user: Dict[int, Dict] = {}
        for item in face_matches:
            if not item.get("identified") or not item.get("user"):
                continue
            user_id = item["user"]["id"]
            distance = item.get("distance")
            if distance is None:
                continue

            existing = best_face_by_user.get(user_id)
            if existing is None or distance < existing.get("distance", float("inf")):
                best_face_by_user[user_id] = item

        best_face_indices = {item["face_index"] for item in best_face_by_user.values()}

        # Second pass: record attendance for selected best matches only.
        recorded_count = 0
        duplicate_skipped_count = 0
        final_results: List[Dict] = []

        for item in face_matches:
            clean_item = {k: v for k, v in item.items() if not k.startswith("_")}

            if not clean_item.get("identified") or not clean_item.get("user"):
                final_results.append(clean_item)
                continue

            face_index = clean_item["face_index"]
            if face_index not in best_face_indices:
                duplicate_skipped_count += 1
                clean_item["attendance_recorded"] = False
                clean_item["duplicate_skipped"] = True
                clean_item["message"] = (
                    f"Duplicate face for {clean_item['user']['name']} in same image. Attendance skipped."
                )
                final_results.append(clean_item)
                continue

            matched_user = item.get("_matched_user_obj")
            if not matched_user:
                clean_item["attendance_recorded"] = False
                clean_item["message"] = "Matched user object missing. Attendance skipped."
                final_results.append(clean_item)
                continue

            try:
                attendance_log = attendance_service.record_attendance(
                    db=db,
                    employee_id=matched_user.employee_id,
                    employee_name=matched_user.name
                )
                recorded_count += 1
                clean_item["attendance_recorded"] = True
                clean_item["duplicate_skipped"] = False
                clean_item["action_type"] = attendance_log.action_type.value
                clean_item["action_at"] = attendance_log.action_at.isoformat()
                clean_item["message"] = (
                    f"{matched_user.name}: "
                    f"{'Check-in' if attendance_log.action_type.value == 'IN' else 'Check-out'} completed"
                )
            except Exception as e:
                clean_item["attendance_recorded"] = False
                clean_item["duplicate_skipped"] = False
                clean_item["message"] = f"Attendance recording failed: {str(e)}"

            final_results.append(clean_item)

        identified_count = sum(1 for r in final_results if r.get("identified"))
        unknown_count = len(final_results) - identified_count

        return {
            "success": True,
            "message": "Multi-face check-in/out processed.",
            "face_count": len(embedding_results),
            "identified_count": identified_count,
            "unknown_count": unknown_count,
            "attendance_recorded_count": recorded_count,
            "duplicate_skipped_count": duplicate_skipped_count,
            "results": final_results,
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Attendance Multi] Error: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Attendance processing failed: {str(e)}")
    finally:
        if temp_path:
            FileUtils.delete_file(temp_path)


@router.get("/history/{employee_id}", response_model=List[AttendanceHistoryResponse])
async def get_employee_history(
    employee_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get attendance history for a specific employee
    
    - employee_id: Employee ID to query
    - limit: Maximum number of records (default 10, max 100)
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.employee_id == employee_id).first()
        if not user:
            raise HTTPException(
                status_code=404, 
                detail="User with this employee ID not found."
            )
        
        # Get attendance history
        history = attendance_service.get_employee_history(db, employee_id, limit)
        
        return [
            AttendanceHistoryResponse(
                id=log.id,
                employee_id=log.employee_id,
                employee_name=log.employee_name,
                action_type=log.action_type.value,
                action_at=log.action_at,
                created_at=log.created_at or log.action_at
            )
            for log in history
        ]
    
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[History] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[AttendanceHistoryResponse])
async def get_all_history(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get attendance history for all employees
    
    - limit: Maximum number of records (default 50, max 200)
    """
    try:
        history = attendance_service.get_all_history(db, limit)
        
        return [
            AttendanceHistoryResponse(
                id=log.id,
                employee_id=log.employee_id,
                employee_name=log.employee_name,
                action_type=log.action_type.value,
                action_at=log.action_at,
                created_at=log.created_at or log.action_at
            )
            for log in history
        ]
    
    except Exception as e:
        print(f"[History All] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{employee_id}")
async def get_employee_status(
    employee_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current status of a specific employee
    
    - If last record is IN: "Working"
    - If last record is OUT: "Checked out"
    - If no records: "Not checked in"
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.employee_id == employee_id).first()
        if not user:
            raise HTTPException(
                status_code=404, 
                detail="User with this employee ID not found."
            )
        
        # Get last attendance record
        last_action = attendance_service.get_last_action(db, employee_id)
        
        if not last_action:
            return {
                "success": True,
                "employee_id": employee_id,
                "employee_name": user.name,
                "status": "Not checked in",
                "last_action": None,
                "last_action_at": None
            }
        
        status = "Working" if last_action.action_type.value == "IN" else "Checked out"
        
        return {
            "success": True,
            "employee_id": employee_id,
            "employee_name": user.name,
            "status": status,
            "last_action": last_action.action_type.value,
            "last_action_at": last_action.action_at
        }
    
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Status] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

