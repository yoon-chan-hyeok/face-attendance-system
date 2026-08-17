# app/services/face_service.py
import logging
import numpy as np
import os
import threading
import cv2
from deepface import DeepFace
from typing import List, Dict, Any, Optional, Tuple
from app.utils.converters import convert_numpy_types

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class FaceAnalysisService:
    def __init__(self):
        # path -> (mtime, vector_list)
        self._vector_cache: Dict[str, Tuple[float, list]] = {}
        self._cache_lock = threading.Lock()

    def clear_vector_cache(self):
        with self._cache_lock:
            self._vector_cache.clear()
        logger.info("Vector cache cleared")

    def _load_vector_cached(self, path: str) -> Optional[list]:
        try:
            if not os.path.exists(path):
                return None

            mtime = os.path.getmtime(path)

            with self._cache_lock:
                cached = self._vector_cache.get(path)
                if cached and cached[0] == mtime:
                    return cached[1]

            vector = np.load(path).tolist()
            with self._cache_lock:
                self._vector_cache[path] = (mtime, vector)
            return vector
        except Exception:
            return None

    def load_vector(self, path: str) -> Optional[list]:
        return self._load_vector_cached(path)

    def build_candidates(self, users: List[Any], log_prefix: str = "[Face]") -> List[Tuple[Any, list]]:
        candidates: List[Tuple[Any, list]] = []
        for user in users:
            path = getattr(user, "profile_image", None)
            if not path:
                continue

            vector = self._load_vector_cached(path)
            if vector is None:
                logger.warning(f"{log_prefix} Vector load failed or missing: {getattr(user, 'name', 'unknown')} ({path})")
                continue
            candidates.append((user, vector))
        return candidates

    def vector_distance(self, vector1: list, vector2: list) -> Optional[float]:
        try:
            np_vec1 = np.array(vector1, dtype=np.float32)
            np_vec2 = np.array(vector2, dtype=np.float32)
            norm1 = np.linalg.norm(np_vec1)
            norm2 = np.linalg.norm(np_vec2)
            if norm1 == 0 or norm2 == 0:
                return None
            cosine_similarity = np.dot(np_vec1, np_vec2) / (norm1 * norm2)
            return float(1 - cosine_similarity)
        except Exception:
            return None

    def rank_candidates(self, target_vector: list, candidates: List[Tuple[Any, list]]) -> List[Dict[str, Any]]:
        ranked: List[Dict[str, Any]] = []
        for user, candidate_vector in candidates:
            distance = self.vector_distance(target_vector, candidate_vector)
            if distance is None:
                continue
            ranked.append({"user": user, "distance": distance})
        ranked.sort(key=lambda x: x["distance"])
        return ranked

    def compute_sharpness(self, img_path: str) -> float:
        image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            return 0.0
        return float(cv2.Laplacian(image, cv2.CV_64F).var())
    
    def check_liveness(self, img_path: str, threshold: float = 0.5) -> Dict[str, Any]:
        """
        Liveness check: Smile emotion analysis
        Passes if DeepFace 'happy' probability >= threshold. Default threshold: 0.5
        
        Args:
            img_path: Image file path
            threshold: Happy probability threshold (0.0 ~ 1.0, default 0.5)
        
        Returns:
            {
                "passed": bool,
                "happy_score": float,
                "threshold": float,
                "emotions": dict  # Full emotion distribution
            }
        """
        try:
            # Analyze emotion only (fast)
            result = DeepFace.analyze(
                img_path=img_path,
                actions=['emotion'],
                enforce_detection=True
            )
            
            # Result is a list (multiple faces possible)
            if not result:
                return {
                    "passed": False,
                    "happy_score": 0.0,
                    "threshold": threshold,
                    "error": "No face detected"
                }
            
            # Use first face's emotion result
            emotion_data = result[0] if isinstance(result, list) else result
            
            # Debug: Check actual return structure
            logger.info(f"[Liveness] DeepFace return type: {type(emotion_data)}")
            if isinstance(emotion_data, dict):
                logger.info(f"[Liveness] DeepFace return keys: {list(emotion_data.keys())}")
            
            # Extract emotion data based on actual DeepFace.analyze() return structure
            emotions = {}
            if isinstance(emotion_data, dict):
                # Case 1: {'emotion': {'happy': 0.5, ...}}
                if 'emotion' in emotion_data:
                    emotions = emotion_data['emotion']
                    logger.info(f"[Liveness] Emotion data extracted from 'emotion' key")
                # Case 2: Direct emotion dict {'happy': 0.5, 'sad': 0.3, ...}
                elif any(key in emotion_data for key in ['happy', 'sad', 'angry', 'surprise', 'fear', 'disgust', 'neutral']):
                    emotions = emotion_data
                    logger.info(f"[Liveness] Emotion data extracted directly from keys")
                else:
                    logger.warning(f"[Liveness] Unexpected structure: {emotion_data}")
            
            # Extract happy probability
            happy_score = emotions.get('happy', 0.0)
            
            # Debug log
            logger.info(f"[Liveness] Full emotion analysis result: {emotions}")
            logger.info(f"[Liveness] happy score: {happy_score:.3f}, threshold: {threshold}, passed: {happy_score >= threshold}")
            
            passed = happy_score >= threshold
            
            return {
                "passed": bool(passed),
                "happy_score": float(happy_score),
                "threshold": threshold,
                "emotions": convert_numpy_types(emotions)
            }
            
        except ValueError as e:
            logger.warning(f"Liveness check failed: No face detected. ({img_path}) - {e}")
            return {
                "passed": False,
                "happy_score": 0.0,
                "threshold": threshold,
                "error": "Face not detected"
            }
        except Exception as e:
            logger.error(f"Error during liveness check: {e}")
            import traceback
            logger.error(f"[Liveness] Detailed error:\n{traceback.format_exc()}")
            return {
                "passed": False,
                "happy_score": 0.0,
                "threshold": threshold,
                "error": str(e)
            }
    
    def analyze_face(self, img_path: str, actions: List[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Analyze face attributes from image (age, gender, race, emotion)
        """
        if actions is None:
            actions = ['age', 'gender', 'race', 'emotion']
        
        logger.info(f"Face analysis started: {img_path}, actions={actions}")
        
        try:
            result = DeepFace.analyze(
                img_path=img_path,
                actions=actions,
                enforce_detection=True
            )
            logger.info(f"Face analysis successful: {len(result)} faces detected")
            return convert_numpy_types(result)
            
        except ValueError:
            logger.warning(f"Face analysis failed: No face detected. ({img_path})")
            print(f"Face analysis failed: No face detected.")
            return None
        except Exception as e:
            logger.error(f"Error during face analysis: {e}")
            print(f"Face analysis failed: {e}")
            return None

    def create_embedding(self, img_path: str, model_name: str = "ArcFace") -> Optional[List[Dict[str, Any]]]:
        """
        Create face embedding (vector) from image
        DeepFace.represent
        """
        logger.info(f"Embedding creation started: {img_path}, model={model_name}")
        
        # 모델 설정 (ArcFace)
        try:
            result = DeepFace.represent(
                img_path=img_path,
                model_name=model_name,
                detector_backend="retinaface",
                enforce_detection=True
            )
            
            face_count = len(result)
            logger.info(f"Embedding created successfully: {face_count} faces detected")
            
            return convert_numpy_types(result)
            
        except ValueError as e:
            logger.warning(f"Embedding creation failed (no face detected): {e} ({img_path})")
            print(f"Embedding creation failed (no face detected): {e}")
            return None
            
        except Exception as e:
            logger.error(f"Error during embedding creation: {e}")
            print(f"Embedding creation failed (other error): {e}")
            return None

    def verify_vector(self, vector1: list, vector2: list, threshold: float = 0.68) -> Dict[str, Any]:
        """
        Verify similarity between two face vectors (Cosine Similarity)
        """
        try:
            np_vec1 = np.array(vector1)
            np_vec2 = np.array(vector2)
            
            norm1 = np.linalg.norm(np_vec1)
            norm2 = np.linalg.norm(np_vec2)
            dot_product = np.dot(np_vec1, np_vec2)
            
            if norm1 == 0 or norm2 == 0:
                return {"verified": False, "distance": 1.0, "error": "Zero vector"}
                
            cosine_similarity = dot_product / (norm1 * norm2)
            cosine_distance = 1 - cosine_similarity
            
            verified = cosine_distance < threshold
            
            logger.info(f"Vector verification: distance={cosine_distance:.4f}, threshold={threshold}, result={verified}")
            
            return {
                "verified": bool(verified),
                "distance": float(cosine_distance),
                "threshold": threshold,
                "model": "ArcFace"
            }
            
        except Exception as e:
            logger.error(f"Vector verification failed: {e}")
            return {"verified": False, "distance": -1.0, "error": str(e)}

    # 사용자 인식
    def find_closest_match(
        self,
        target_vector: list,
        candidates: List[Tuple[Any, list]],
        threshold: float = 0.68,
        margin_threshold: float = 0.03
    ) -> Optional[Dict[str, Any]]:
        result = self.find_closest_match_with_reason(
            target_vector=target_vector,
            candidates=candidates,
            threshold=threshold,
            margin_threshold=margin_threshold
        )
        if result.get("matched"):
            return result
        return None

    def find_closest_match_with_reason(
        self,
        target_vector: list,
        candidates: List[Tuple[Any, list]],
        threshold: float = 0.68,
        margin_threshold: float = 0.03
    ) -> Dict[str, Any]:
        """
        1:N matching - Find the most similar vector
        
        Args:
            target_vector: Face vector to find
            candidates: List of comparison targets [(user_obj, vector_list), ...]
            threshold: Threshold value
            
        Returns:
            Most similar user info or None
        """
        best_match = None
        min_distance = float('inf')
        second_min_distance = float('inf')
        
        np_target = np.array(target_vector)
        norm_target = np.linalg.norm(np_target)
        
        if norm_target == 0:
            return {
                "matched": False,
                "failure_reason": "invalid_target",
                "message": "Invalid target vector.",
                "threshold": float(threshold),
                "margin_threshold": float(margin_threshold),
            }

        for user, candidate_vector in candidates:
            try:
                np_candidate = np.array(candidate_vector)
                norm_candidate = np.linalg.norm(np_candidate)
                
                if norm_candidate == 0:
                    continue
                    
                dot_product = np.dot(np_target, np_candidate)
                cosine_similarity = dot_product / (norm_target * norm_candidate)
                distance = 1 - cosine_similarity
                
                if distance < min_distance:
                    second_min_distance = min_distance
                    min_distance = distance
                    best_match = user
                elif distance < second_min_distance:
                    second_min_distance = distance
            except Exception:
                continue

        if not best_match:
            logger.info("User identification failed: no valid candidates")
            return {
                "matched": False,
                "failure_reason": "no_candidates",
                "message": "No valid candidates.",
                "threshold": float(threshold),
                "margin_threshold": float(margin_threshold),
            }

        # Margin gate:
        # If second-best is too close to best, classification is ambiguous.
        # For single-candidate scenarios, skip margin gating.
        if np.isfinite(second_min_distance):
            margin = second_min_distance - min_distance
            margin_passed = margin >= margin_threshold
        else:
            margin = float('inf')
            margin_passed = True

        threshold_passed = min_distance < threshold

        if threshold_passed and margin_passed:
            logger.info(f"User identification successful: {best_match.name}, distance={min_distance:.4f}")
            return {
                "matched": True,
                "user": best_match,
                "distance": float(min_distance),
                "second_distance": float(second_min_distance) if np.isfinite(second_min_distance) else None,
                "margin": float(margin),
                "threshold": float(threshold),
                "margin_threshold": float(margin_threshold),
            }
        else:
            logger.info(
                "User identification failed: "
                f"min distance={min_distance:.4f}, "
                f"second distance={second_min_distance if np.isfinite(second_min_distance) else 'N/A'}, "
                f"margin={margin if np.isfinite(margin) else 'N/A'}, "
                f"threshold={threshold}, margin_threshold={margin_threshold}"
            )
            if not threshold_passed:
                failure_reason = "threshold"
                message = "No matching user: threshold not met."
            else:
                failure_reason = "margin_gate"
                message = "No matching user: margin gate rejected ambiguous match."

            return {
                "matched": False,
                "failure_reason": failure_reason,
                "message": message,
                "distance": float(min_distance),
                "second_distance": float(second_min_distance) if np.isfinite(second_min_distance) else None,
                "margin": float(margin) if np.isfinite(margin) else None,
                "threshold": float(threshold),
                "margin_threshold": float(margin_threshold),
            }

    def find_closest_match_user_level_with_reason(
        self,
        target_vector: list,
        candidates: List[Tuple[Any, list]],
        threshold: float = 0.68,
        margin_threshold: float = 0.03
    ) -> Dict[str, Any]:
        """
        User-level matching:
        - Aggregate multiple sample embeddings per user by min distance
        - Compute top1/top2 and margin gate on distinct users
        """
        if not candidates:
            return {
                "matched": False,
                "failure_reason": "no_candidates",
                "message": "No valid candidates.",
                "threshold": float(threshold),
                "margin_threshold": float(margin_threshold),
            }

        per_user_best: Dict[Any, Dict[str, Any]] = {}
        for user, candidate_vector in candidates:
            distance = self.vector_distance(target_vector, candidate_vector)
            if distance is None:
                continue

            key = getattr(user, "id", id(user))
            existing = per_user_best.get(key)
            if existing is None or distance < existing["distance"]:
                per_user_best[key] = {"user": user, "distance": float(distance)}

        if not per_user_best:
            return {
                "matched": False,
                "failure_reason": "no_candidates",
                "message": "No valid candidates.",
                "threshold": float(threshold),
                "margin_threshold": float(margin_threshold),
            }

        ranked_users = sorted(per_user_best.values(), key=lambda x: x["distance"])
        top1 = ranked_users[0]
        best_user = top1["user"]
        min_distance = float(top1["distance"])
        best_user_id = getattr(best_user, "id", None)

        if len(ranked_users) > 1:
            second_user = ranked_users[1]["user"]
            second_user_id = getattr(second_user, "id", None)
            second_min_distance = float(ranked_users[1]["distance"])
            margin = second_min_distance - min_distance
            margin_passed = margin >= margin_threshold
        else:
            second_user = None
            second_user_id = None
            second_min_distance = None
            margin = float("inf")
            margin_passed = True

        threshold_passed = min_distance < threshold

        if threshold_passed and margin_passed:
            logger.info(
                "User-level identification successful: "
                f"top1_id={best_user_id}, top1_name={getattr(best_user, 'name', 'unknown')}, "
                f"top2_id={second_user_id}, top2_name={getattr(second_user, 'name', 'N/A') if second_user else 'N/A'}, "
                f"distance={min_distance:.4f}, "
                f"second_distance={second_min_distance if second_min_distance is not None else 'N/A'}, "
                f"margin={margin if np.isfinite(margin) else 'N/A'}, "
                f"threshold={threshold}, margin_threshold={margin_threshold}"
            )
            return {
                "matched": True,
                "user": best_user,
                "user_id": best_user_id,
                "second_user_id": second_user_id,
                "distance": min_distance,
                "second_distance": second_min_distance,
                "margin": float(margin) if np.isfinite(margin) else None,
                "threshold": float(threshold),
                "margin_threshold": float(margin_threshold),
            }

        if not threshold_passed:
            failure_reason = "threshold"
            message = "No matching user: threshold not met."
        else:
            failure_reason = "margin_gate"
            message = "No matching user: margin gate rejected ambiguous match."

        logger.info(
            "User-level identification failed: "
            f"reason={failure_reason}, "
            f"top1_id={best_user_id}, top1_name={getattr(best_user, 'name', 'unknown')}, "
            f"top2_id={second_user_id}, top2_name={getattr(second_user, 'name', 'N/A') if second_user else 'N/A'}, "
            f"distance={min_distance:.4f}, "
            f"second_distance={second_min_distance if second_min_distance is not None else 'N/A'}, "
            f"margin={margin if np.isfinite(margin) else 'N/A'}, "
            f"threshold={threshold}, margin_threshold={margin_threshold}"
        )

        return {
            "matched": False,
            "failure_reason": failure_reason,
            "message": message,
            "user_id": best_user_id,
            "second_user_id": second_user_id,
            "distance": min_distance,
            "second_distance": second_min_distance,
            "margin": float(margin) if np.isfinite(margin) else None,
            "threshold": float(threshold),
            "margin_threshold": float(margin_threshold),
        }
