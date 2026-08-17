import { useState } from 'react';
import { useCamera } from './useCamera';

export const useCameraCapture = () => {
  const { videoRef, startCamera, captureImage } = useCamera();
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);

  // Capture handler
  const handleCapture = () => {
    setIsCapturing(true);
    
    const image = captureImage();
    if (image) {
      setCapturedImage(image);
      console.log('✅ Image captured successfully');
    } else {
      console.error('❌ Image capture failed');
    }
    
    setIsCapturing(false);
  };

  // 캡처된 이미지 초기화
  const clearCapturedImage = () => {
    setCapturedImage(null);
  };

  return {
    videoRef,
    startCamera,
    capturedImage,
    handleCapture,
    clearCapturedImage,
    isCapturing,
  };
};
