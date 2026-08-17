"""
이미지 처리 유틸리티
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import platform

class ImageUtils:
    @staticmethod
    def draw_face_box(image_path: str, facial_area: dict, text: str) -> np.ndarray:
        """
        이미지에 얼굴 박스와 텍스트를 그림 (한글 지원)
        """
        # 1. OpenCV로 이미지 읽기
        img_cv = cv2.imread(image_path)
        if img_cv is None:
            return None
            
        x = facial_area.get('x', 0)
        y = facial_area.get('y', 0)
        w = facial_area.get('w', 0)
        h = facial_area.get('h', 0)
        
        # 2. 박스는 OpenCV로 그리기 (빠름)
        cv2.rectangle(img_cv, (x, y), (x+w, y+h), (0, 0, 255), 2)
        
        # 3. 텍스트는 PIL로 그리기 (한글 지원)
        # OpenCV 이미지를 PIL 이미지로 변환
        img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # 폰트 설정 (OS별 폰트 경로)
        system_os = platform.system()
        font_path = "arial.ttf" # 기본값
        
        if system_os == "Windows":
            font_path = "malgun.ttf" # 맑은 고딕
        elif system_os == "Darwin": # Mac
            font_path = "AppleGothic.ttf"
        elif system_os == "Linux":
            font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            
        try:
            font = ImageFont.truetype(font_path, 24)
        except:
            font = ImageFont.load_default()
            
        # 텍스트 크기 계산 (Pillow 9.2.0 이상에서는 length 사용 권장되나 bbox 사용)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_w = right - left
        text_h = bottom - top
        
        # 텍스트 배경 그리기 (빨간색)
        draw.rectangle((x, y - text_h - 10, x + text_w + 10, y), fill=(255, 0, 0))
        
        # 텍스트 쓰기 (흰색)
        draw.text((x + 5, y - text_h - 5), text, font=font, fill=(255, 255, 255))
        
        # 4. 다시 OpenCV 이미지로 변환
        img_result = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        return img_result
