"""
.npy 파일 읽기 테스트
"""
import numpy as np
import os

# 읽어올 파일 경로 (방금 생성된 파일명으로 수정 필요)
# 예시: "data/encodings/string_25c638e1-07ee-43c0-a55a-2e9b5c0244c6.npy"
npy_file_path = "data/encodings/string_25c638e1-07ee-43c0-a55a-2e9b5c0244c6.npy"

def read_npy_file(file_path):
    if not os.path.exists(file_path):
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return

    try:
        # .npy 파일 로드
        vector = np.load(file_path)
        
        print("=" * 50)
        print(f"파일: {file_path}")
        print("=" * 50)
        print(f"데이터 타입: {type(vector)}")
        print(f"데이터 모양(Shape): {vector.shape}")
        print(f"데이터 차원: {vector.ndim}")
        print("-" * 50)
        print("데이터 내용 (일부):")
        print(vector)
        print("=" * 50)
        
        # 전체 데이터를 보고 싶으면 아래 주석 해제
        # np.set_printoptions(threshold=np.inf)
        # print(vector)

    except Exception as e:
        print(f"파일 읽기 실패: {e}")

if __name__ == "__main__":
    read_npy_file(npy_file_path)

