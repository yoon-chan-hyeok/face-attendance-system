/**
 * API 설정 파일
 * 개발/프로덕션 모드에 따라 자동으로 URL 전환
 */

// 현재 모드 확인
const IS_PRODUCTION = import.meta.env.PROD;





// 모드에 따라 API URL 자동 선택
export const API_BASE_URL = IS_PRODUCTION
  ? import.meta.env.VITE_API_BASE_URL_PROD  // 프로덕션
  : import.meta.env.VITE_API_BASE_URL_DEV;  // 개발


// 테스트용 하드코딩
// export const API_BASE_URL = 'http://127.0.0.1:8000';

console.log('📍 API Base URL:', API_BASE_URL);



// API 엔드포인트
export const API_ENDPOINTS = {
  HEALTH: '/health',
  LIVE_NESS_TOGGLE: '/api/v1/liveness/toggle',
  LIVENESS_STATUS: '/api/v1/liveness/status',
  IDENTIFY_VISUALIZE: '/api/v1/face/identify/visualize',
  IDENTIFY: '/api/v1/face/identify',
  IDENTIFY_MULTI: '/api/v1/face/identify/multi',
  REGISTER: '/api/v1/face/register',
  REGISTER_V2: '/api/v1/face/register-v2',
  USERS: '/api/v1/face/users',
  CHECK_IN_OUT: '/api/v1/attendance/check-in-out',
  CHECK_IN_OUT_V2: '/api/v1/attendance/check-in-out-v2',
  CHECK_IN_OUT_V3: '/api/v1/attendance/check-in-out-v3',
  CHECK_IN_OUT_V4: '/api/v1/attendance/check-in-out-v4',
  CHECK_IN_OUT_MULTI_IMAGE: '/api/v1/attendance/check-in-out-multi-image',
  LOGS_RECENT: '/api/v1/logs/recent',
  LOGS_CLEAR: '/api/v1/logs/clear',
} as const;

/**
 * API 서버 연결 상태 확인
 */
export async function checkApiConnection(): Promise<boolean> {
  try {        
    if (!IS_PRODUCTION){
        console.log('🔧 Development mode - API Base URL:', API_BASE_URL);
    } else {
        console.log('🔧 Production mode - API Base URL:', API_BASE_URL);
    };

    if (!API_BASE_URL) {
      console.log('❌ API_BASE_URL is undefined!');
      console.log('💡 Please check .env file and restart server.');
      return false;
    }

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.HEALTH}`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000),
    });

    const isConnected = response.ok;

    if (isConnected) {
      console.log('✅ API server connected successfully!');
    } else {
      console.log('❌ API server connection failed! (HTTP Status:', response.status, ')');
    }

    return isConnected;
  } catch (error) {
    console.log('❌ API server connection failed!');
    console.log('💡 Please check if FastAPI server is running.');
    console.log('Error details:', error);
    return false;
  }
}
