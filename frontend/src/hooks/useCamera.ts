// src/hooks/useCamera.ts
import {useRef} from 'react';

export interface CapturedFrame {
  blob: Blob;
  timestamp: number;
}

/**
 * 카메라 훅
 * @returns 카메라 관련 함수
 */
export const useCamera = () => {
    const videoRef = useRef<HTMLVideoElement>(null);

    /**
     * 카메라 시작
     */
    const startCamera = async () => {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false,
        });
        if (videoRef.current) videoRef.current.srcObject = stream;
    };    

    /**
     * 카메라에서 이미지 캡처
     * @returns 캡처된 이미지의 Base64 문자열
     */
    const captureImage = (): string | null => {
        if (!videoRef.current) return null;
    
        const video = videoRef.current;
        const canvas = document.createElement('canvas');
        
        // 비디오의 실제 크기로 캔버스 설정
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        const ctx = canvas.getContext('2d');
        if (!ctx) return null;
    
        // 비디오 프레임을 캔버스에 그리기
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Base64 이미지로 변환하여 반환
        return canvas.toDataURL('image/jpeg', 0.9); // 0.9는 품질 (0~1)
    };

    /**
     * 여러 프레임 캡처 (라이브니스용)
     * @param duration - 캡처 기간 (ms)
     * @param interval - 캡처 간격 (ms)
     * @param onProgress - 진행률 콜백 (0~100)
     * @returns 캡처된 프레임 배열
     */
    const captureFrames = (
        duration: number = 2000,
        interval: number = 100,
        onProgress?: (progress: number) => void
    ): Promise<CapturedFrame[]> => {
        return new Promise((resolve, reject) => {
            if (!videoRef.current) {
                reject(new Error('Video not ready'));
                return;
            }

            const video = videoRef.current;
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            if (!ctx) {
                reject(new Error('Canvas context not available'));
                return;
            }

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            const frames: CapturedFrame[] = [];
            let frameCount = 0;
            const totalFrames = Math.floor(duration / interval);

            const captureInterval = setInterval(() => {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                canvas.toBlob((blob) => {
                    if (blob) {
                        frames.push({
                            blob,
                            timestamp: Date.now()
                        });
                        
                        frameCount++;
                        if (onProgress) {
                            const progress = Math.min(100, (frameCount / totalFrames) * 100);
                            onProgress(progress);
                        }
                    }
                }, 'image/jpeg', 0.8);
            }, interval);

            setTimeout(() => {
                clearInterval(captureInterval);
                if (frames.length < 3) {
                    reject(new Error('Failed to capture enough frames'));
                } else {
                    resolve(frames);
                }
            }, duration);
        });
    };

    return { videoRef, startCamera, captureImage, captureFrames };
};

