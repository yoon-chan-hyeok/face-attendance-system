"""
데이터 타입 변환 유틸리티
"""
import numpy as np
from typing import Any


def convert_numpy_types(obj: Any) -> Any:
    """
    numpy 타입을 Python 기본 타입으로 재귀적으로 변환
    
    Args:
        obj: 변환할 객체
        
    Returns:
        Python 기본 타입으로 변환된 객체
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

