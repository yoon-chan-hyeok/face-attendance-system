// src/pages/HomePage.tsx
/**
 * 메인 페이지 컴포넌트
 * @returns 메인 페이지 컴포넌트
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCamera } from '../hooks/useCamera';
import { checkInOutV4, getLivenessStatus, type CheckInOutResponse } from '../api/face';
import { IdentificationResult } from '../components/homepage/IdentificationResult'; 
import { CameraView } from '../components/homepage/CameraView';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { videoRef, startCamera, captureFrames } = useCamera();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CheckInOutResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [livenessEnabled, setLivenessEnabled] = useState(false);

  const TOAST_DURATION = 3000;
  const CAPTURE_DURATION = 500; // 0.5초
  const CAPTURE_INTERVAL = 100;  // 100ms 간격 (약 5프레임)

  // Start camera and check liveness status
  useEffect(() => {
    startCamera();
    
    // 라이브니스 상태 확인
    const checkLivenessStatus = () => {
      getLivenessStatus()
        .then(status => {
          setLivenessEnabled(status.enabled);
          console.log('Liveness enabled:', status.enabled);
        })
        .catch(err => {
          console.error('Failed to get liveness status:', err);
          // 로컬스토리지에서 폴백
          const saved = localStorage.getItem('livenessEnabled');
          if (saved !== null) {
            setLivenessEnabled(saved === 'true');
          }
        });
    };

    checkLivenessStatus();

    // CustomEvent 리스너 등록 (Header에서 변경 시 자동 반영)
    const handleLivenessChange = (event: CustomEvent) => {
      setLivenessEnabled(event.detail.enabled);
      console.log('Liveness status updated:', event.detail.enabled);
    };

    window.addEventListener('livenessChanged', handleLivenessChange as EventListener);

    return () => {
      window.removeEventListener('livenessChanged', handleLivenessChange as EventListener);
    };
  }, []);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    if (result) {
      timer = setTimeout(() => {
        setResult(null);
      }, TOAST_DURATION);
    }
    return () => clearTimeout(timer); // cleanup
  }, [result]);

  // Capture handler with liveness detection
  const handleIdentify = async () => {
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      // 1. 프레임 캡처 (2초간 눈 깜빡임)
      const frames = await captureFrames(
        CAPTURE_DURATION,
        CAPTURE_INTERVAL
      );

      console.log(`✅ Captured ${frames.length} frames`);

      // 2. API 호출
      const data = await checkInOutV4(frames);
      setResult(data);
      
    } catch (err: any) {
      setError(err.message || 'An error occurred during attendance check.');
      console.error('Attendance check failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='flex flex-col items-center justify-center h-full w-full '>
      <h1 className='text-3xl font-bold mb-6 text-white'>Face Attendance</h1>
      
      
      <div className='w-full max-w-2xl overflow-hidden'>
        {/* Video area */}
        <CameraView 
          videoRef={videoRef as React.RefObject<HTMLVideoElement>} 
          loading={loading}
          livenessEnabled={livenessEnabled}
        />

        <div className='mt-4'>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <button
              onClick={handleIdentify}
              disabled={loading}
              className={`py-3 px-4 rounded-md text-white font-medium transition-colors ${
                loading
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              }`}
            >
              {loading ? 'Processing...' : 'Check In/Out'}
            </button>
            <button
              onClick={() => navigate('/multi')}
              className="py-3 px-4 rounded-md text-white font-medium bg-violet-600 hover:bg-violet-700 transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2"
            >
              Upload Image (Multi-Face)
            </button>
          </div>
          
          {/* Error message display */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
              {error}
            </div>
          )}

          {/* Identification result display */}
          {result && <IdentificationResult result={result} />}          
        </div>
      </div>
    </div>
  );
};

export default HomePage;
