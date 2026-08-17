from app.services.face_service import FaceAnalysisService

# 이미지 경로
img_path = "data/images/sample.jpg"

print("=" * 50)
print("얼굴 분석 시작")
print("=" * 50)

# 서비스를 통해 얼굴 분석 실행
service = FaceAnalysisService()
result = service.analyze_emotion(img_path)

if result:
    try:
        print("\n결과:")
        print(result)
    except Exception as e:
        print(f"결과 출력 실패: {e}")
else:
    print("얼굴을 찾을 수 없습니다.")