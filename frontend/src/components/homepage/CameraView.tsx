// src/components/homepage/CameraView.tsx
import React from 'react';

interface Props {
  videoRef: React.RefObject<HTMLVideoElement>;
  loading: boolean;
  livenessEnabled?: boolean;
}

export const CameraView: React.FC<Props> = ({ videoRef, loading, livenessEnabled = false }) => {
  /**
   * 카메라 뷰 반환
   * @returns 카메라 뷰
   */
  return (
    <div className='relative aspect-video bg-black rounded-lg overflow-hidden'>
      <video 
        ref={videoRef} 
        autoPlay 
        playsInline 
        className='w-full h-full object-cover'
      />
      
      {/* 얼굴 인식 가이드 오버레이 */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        {/* 배경 어둡게 */}
        <div className="absolute inset-0 bg-black/30" />
        
        {/* 가이드 컨테이너 */}
        <div className="relative z-10 flex flex-col items-center">
          {/* 상단 안내 텍스트 */}
          <div className="mb-4 flex flex-col items-center gap-2">
            <div className="px-4 py-2 bg-black/60 rounded-full backdrop-blur-sm">
              <p className="text-white text-sm font-medium">
                Position your face in the frame
              </p>
            </div>
            {livenessEnabled && (
              <div className="px-4 py-2 bg-blue-600/80 rounded-full backdrop-blur-sm flex items-center gap-2">
                <span className="text-lg">👁️</span>
                <p className="text-white text-sm font-medium">
                  Please blink your eyes
                </p>
              </div>
            )}
          </div>
          
          {/* 타원형 가이드 프레임 */}
          <div className="relative">
            {/* 메인 타원 */}
            <div 
              className="w-48 h-60 border-4 border-blue-500 rounded-full shadow-lg"
              style={{
                boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.3), 0 0 30px rgba(59, 130, 246, 0.5)',
              }}
            />
            
            {/* 코너 마커들 */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-2">
              <div className="w-8 h-1 bg-blue-400 rounded-full" />
            </div>
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-2">
              <div className="w-8 h-1 bg-blue-400 rounded-full" />
            </div>
            <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2">
              <div className="h-8 w-1 bg-blue-400 rounded-full" />
            </div>
            <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-2">
              <div className="h-8 w-1 bg-blue-400 rounded-full" />
            </div>
          </div>
          
          {/* 하단 힌트 */}
          <div className="mt-4 px-3 py-1 bg-black/40 rounded-lg backdrop-blur-sm">
            <p className="text-gray-300 text-xs">
              {livenessEnabled ? 'Please blink your eyes' : 'Look at the camera'}
            </p>
          </div>
        </div>
      </div>

      {/* 로딩 스피너 */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70 z-20">
          <div className="flex flex-col items-center gap-3">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            <p className="text-white text-sm">Processing...</p>
          </div>
        </div>
      )}
    </div>
  );
};