# app/services/blink_service.py
"""
Eye blink detection service using MediaPipe Tasks API
- Analyzes multiple frames to detect blinks via EAR (Eye Aspect Ratio) changes
- Works independently from existing DeepFace face recognition logic
- Python 3.13+ compatible (Tasks API)
"""
import logging
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Model file path
MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "face_landmarker.task"


class BlinkDetectionService:
    """Eye blink detection service (MediaPipe Tasks API)"""
    
    # MediaPipe Face Landmarker eye landmark indices
    # Left eye (6 points)
    LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
    # Right eye (6 points)
    RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    
    # EAR threshold (below this value, eyes are considered closed)
    EAR_THRESHOLD = 0.21
    
    # Consecutive frames (eyes must be closed for this many frames to count as blink)
    CONSEC_FRAMES = 2
    
    def __init__(self):
        self._landmarker = None
        self._initialized = False
        self._init_error = None
        logger.info("[BlinkService] BlinkDetectionService created (Tasks API)")
    
    def _ensure_initialized(self) -> bool:
        """Lazy initialization of MediaPipe Face Landmarker"""
        if self._initialized:
            return True
        
        if self._init_error:
            return False
        
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            # Check model file
            if not MODEL_PATH.exists():
                self._init_error = f"Model file not found: {MODEL_PATH}"
                logger.error(f"[BlinkService] {self._init_error}")
                return False
            
            # Face Landmarker options setup
            base_options = python.BaseOptions(model_asset_path=str(MODEL_PATH))
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False
            )
            
            self._landmarker = vision.FaceLandmarker.create_from_options(options)
            self._initialized = True
            logger.info("[BlinkService] MediaPipe Face Landmarker initialized")
            return True
            
        except Exception as e:
            self._init_error = str(e)
            logger.error(f"[BlinkService] MediaPipe initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _calculate_ear(self, eye_landmarks: List[tuple]) -> float:
        """
        Calculate Eye Aspect Ratio (EAR)
        
        EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
        
        Eyes open: EAR ≈ 0.25~0.35
        Eyes closed: EAR ≈ 0.1 or less
        """
        # Vertical distance
        A = np.linalg.norm(np.array(eye_landmarks[1]) - np.array(eye_landmarks[5]))
        B = np.linalg.norm(np.array(eye_landmarks[2]) - np.array(eye_landmarks[4]))
        
        # Horizontal distance
        C = np.linalg.norm(np.array(eye_landmarks[0]) - np.array(eye_landmarks[3]))
        
        # EAR calculation
        if C == 0:
            return 0.0
        
        ear = (A + B) / (2.0 * C)
        return ear
    
    def _get_eye_landmarks(self, face_landmarks, indices: List[int], img_width: int, img_height: int) -> List[tuple]:
        """Extract eye landmark coordinates from Face Landmarker"""
        landmarks = []
        for idx in indices:
            lm = face_landmarks[idx]
            x = int(lm.x * img_width)
            y = int(lm.y * img_height)
            landmarks.append((x, y))
        return landmarks
    
    def _analyze_frame(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze single frame
        
        Returns:
            {
                "success": bool,
                "left_ear": float,
                "right_ear": float,
                "avg_ear": float,
                "eyes_closed": bool
            }
        """
        # Check initialization
        if not self._ensure_initialized():
            return {"success": False, "error": self._init_error or "MediaPipe initialization failed"}
        
        try:
            import mediapipe as mp
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {"success": False, "error": "Failed to load image"}
            
            height, width = image.shape[:2]
            
            # Convert BGR to RGB and then to MediaPipe Image
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
            
            # Run Face Landmarker
            result = self._landmarker.detect(mp_image)
            
            if not result.face_landmarks or len(result.face_landmarks) == 0:
                return {"success": False, "error": "No face detected"}
            
            # First face's landmarks
            face_landmarks = result.face_landmarks[0]
            
            # Extract left/right eye landmarks
            left_eye = self._get_eye_landmarks(
                face_landmarks, self.LEFT_EYE_INDICES, width, height
            )
            right_eye = self._get_eye_landmarks(
                face_landmarks, self.RIGHT_EYE_INDICES, width, height
            )
            
            # Calculate EAR
            left_ear = self._calculate_ear(left_eye)
            right_ear = self._calculate_ear(right_eye)
            avg_ear = (left_ear + right_ear) / 2.0
            
            eyes_closed = avg_ear < self.EAR_THRESHOLD
            
            return {
                "success": True,
                "left_ear": float(left_ear),
                "right_ear": float(right_ear),
                "avg_ear": float(avg_ear),
                "eyes_closed": eyes_closed
            }
                
        except Exception as e:
            logger.error(f"[BlinkService] Frame analysis error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    # Blink count
    def detect_blink(
        self, 
        image_paths: List[str], 
        min_blinks: int = 2
    ) -> Dict[str, Any]:
        """
        Detect eye blinks from multiple frames
        
        Args:
            image_paths: List of image file paths to analyze (sorted by time)
            min_blinks: Minimum blink count (default 1)
        
        Returns:
            {
                "blink_detected": bool,
                "blink_count": int,
                "frame_count": int,
                "ear_values": List[float],
                "detail": str
            }
        """
        if not image_paths:
            return {
                "blink_detected": False,
                "blink_count": 0,
                "frame_count": 0,
                "ear_values": [],
                "detail": "No frames provided"
            }
        
        logger.info(f"[BlinkService] Blink detection started: {len(image_paths)} frames")
        
        ear_values = []
        eyes_closed_frames = 0
        blink_count = 0
        was_closed = False
        
        for i, path in enumerate(image_paths):
            result = self._analyze_frame(path)
            
            if not result.get("success", False):
                logger.warning(f"[BlinkService] Frame {i+1} analysis failed: {result.get('error')}")
                ear_values.append(None)
                continue
            
            avg_ear = result["avg_ear"]
            ear_values.append(avg_ear)
            eyes_closed = result["eyes_closed"]
            
            logger.debug(f"[BlinkService] Frame {i+1}: EAR={avg_ear:.3f}, closed={eyes_closed}")
            
            if eyes_closed:
                eyes_closed_frames += 1
                was_closed = True
            else:
                # Eyes transitioned to open state
                if was_closed and eyes_closed_frames >= self.CONSEC_FRAMES:
                    blink_count += 1
                    logger.info(f"[BlinkService] Blink detected! (total: {blink_count})")
                was_closed = False
                eyes_closed_frames = 0
        
        # Check if eyes were closed at the end
        if was_closed and eyes_closed_frames >= self.CONSEC_FRAMES:
            blink_count += 1
            logger.info(f"[BlinkService] Blink detected (final)! (total: {blink_count})")
        
        blink_detected = blink_count >= min_blinks
        
        # Filter only valid EAR values
        valid_ears = [e for e in ear_values if e is not None]
        
        detail = f"Blink count: {blink_count} (required: {min_blinks})"
        if blink_detected:
            detail = f"✓ Liveness passed: {detail}"
        else:
            detail = f"✗ Liveness failed: {detail}"
        
        logger.info(f"[BlinkService] Result: {detail}")
        
        return {
            "blink_detected": blink_detected,
            "blink_count": blink_count,
            "frame_count": len(image_paths),
            "valid_frame_count": len(valid_ears),
            "ear_values": valid_ears,
            "ear_threshold": self.EAR_THRESHOLD,
            "min_blinks_required": min_blinks,
            "detail": detail
        }


# Singleton instance
blink_service = BlinkDetectionService()
