import { API_BASE_URL, API_ENDPOINTS } from '../config/api';

export interface IdentifyUserResponse {
  success: boolean;
  identified: boolean;
  message: string;
  user?: {
    name: string;
    employee_id: string;
    profile_image: string;
  };
  distance?: number;
  facial_area?: any;
}

export interface MultiIdentifyFaceResult {
  face_index: number;
  identified: boolean;
  message: string;
  failure_reason?: string;
  distance?: number;
  second_distance?: number;
  margin?: number;
  facial_area?: any;
  user?: {
    id: number;
    name: string;
    employee_id: string;
    profile_image: string;
  };
}

export interface MultiIdentifyResponse {
  success: boolean;
  face_count: number;
  results: MultiIdentifyFaceResult[];
}

export interface MultiAttendanceFaceResult extends MultiIdentifyFaceResult {
  attendance_recorded?: boolean;
  duplicate_skipped?: boolean;
  action_type?: 'IN' | 'OUT';
  action_at?: string;
}

export interface MultiAttendanceResponse {
  success: boolean;
  message: string;
  face_count: number;
  identified_count: number;
  unknown_count: number;
  attendance_recorded_count: number;
  duplicate_skipped_count: number;
  results: MultiAttendanceFaceResult[];
}

export interface CheckInOutResponse {
  success: boolean;
  message: string;
  action_type: 'IN' | 'OUT';
  employee_id: string;
  employee_name: string;
  action_at: string;
}

export interface RegisterUserResponse {
  success: boolean;
  message: string;
  user_id?: number;
  face_image_path?: string;
  stats?: {
    saved_npy: number;
    saved_sample_npy: number;
    failed_frames: number;
    rejected_no_face: number;
    rejected_low_quality: number;
  };
  user?: {
    id: number;
    employee_id: string;
    name: string;
    profile_image: string;
    sample_count?: number;
  };
}

export interface LivenessToggleRequest {
  password: string;
  enabled: boolean;
}

export interface LivenessToggleResponse {
  success: boolean;
  enabled: boolean;
  message: string;
}

export interface LivenessStatusResponse {
  enabled: boolean;
  threshold: number;
}

export interface LogItem {
  timestamp: string;
  level: string;
  source: string;
  message: string;
}

export interface RegisteredUserItem {
  id: number;
  employee_id: string;
  name: string;
  centroid_path: string | null;
  embedding_count: number;
  created_at: string | null;
}

export interface CapturedFrame {
  blob: Blob;
  timestamp: number;
}



/**
 * Base64 이미지를 Blob으로 변환
 */
function base64ToBlob(base64: string, mimeType: string = 'image/jpeg'): Blob {
  const byteString = atob(base64.split(',')[1]);
  const ab = new ArrayBuffer(byteString.length);
  const ia = new Uint8Array(ab);
  
  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i);
  }
  
  return new Blob([ab], { type: mimeType });
}

/**
 * 얼굴 식별 API 호출
 * @param imageBase64 - Base64 인코딩된 이미지
 * @returns 식별 결과
 */
export async function identifyUser(imageBase64: string): Promise<IdentifyUserResponse> {
  try {
    const blob = base64ToBlob(imageBase64);
    const formData = new FormData();
    formData.append('file', blob, 'capture.jpg');

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.IDENTIFY}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API call failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Face identification failed:', error);
    throw error;
  }
}

export async function identifyUsersFromPhoto(file: File): Promise<MultiIdentifyResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file, file.name || 'group.jpg');

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.IDENTIFY_MULTI}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Multi identify failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Multi identify failed:', error);
    throw error;
  }
}

export async function checkInOutMultiFromPhoto(file: File): Promise<MultiAttendanceResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file, file.name || 'group.jpg');

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHECK_IN_OUT_MULTI_IMAGE}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Multi check-in/out failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Multi check-in/out failed:', error);
    throw error;
  }
}

/**
 * 출퇴근 체크 API 호출
 * @param imageBase64 - Base64 인코딩된 이미지
 * @returns 출퇴근 체크 결과
 */
export async function checkInOut(imageBase64: string): Promise<CheckInOutResponse> {
  try {
    const blob = base64ToBlob(imageBase64);
    const formData = new FormData();
    formData.append('file', blob, 'capture.jpg');

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHECK_IN_OUT}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Check-in/out failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Check-in/out failed:', error);
    throw error;
  }
}

/**
 * 사용자 등록 API 호출
 * @param name - 사용자 이름
 * @param employeeId - 사원 번호
 * @param imageBase64 - Base64 인코딩된 이미지
 */
export async function registerUser(name: string, employeeId: string, imageBase64: string): Promise<RegisterUserResponse> {
  try {
    const blob = base64ToBlob(imageBase64);
    const formData = new FormData();
    formData.append('file', blob, 'register.jpg');
    formData.append('employee_id', employeeId);
    formData.append('name', name);    

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.REGISTER}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Registration failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('User registration failed:', error);
    throw error;
  }
}

/**
 * 사용자 다중 프레임 등록 API 호출
 * @param name - 사용자 이름
 * @param employeeId - 사원 번호
 * @param frames - 캡처된 프레임 배열
 */
export async function registerUserV2(
  name: string,
  employeeId: string,
  frames: CapturedFrame[],
  captureElapsedMs?: number
): Promise<RegisterUserResponse> {
  try {
    const formData = new FormData();
    formData.append('employee_id', employeeId);
    formData.append('name', name);
    formData.append('captured_frame_count', String(frames.length));
    if (typeof captureElapsedMs === 'number') {
      formData.append('capture_elapsed_ms', String(Math.round(captureElapsedMs)));
    }
    frames.forEach((frame, index) => {
      formData.append('files', frame.blob, `register_${index}.jpg`);
    });

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.REGISTER_V2}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Registration V2 failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('User registration V2 failed:', error);
    throw error;
  }
}

/**
 * 라이브니스 모드 토글 API 호출
 * @param password - 관리자 비밀번호
 * @param enabled - true면 활성화, false면 비활성화
 * @returns 토글 결과
 */
export async function toggleLiveness(
  password: string,
  enabled: boolean
): Promise<LivenessToggleResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.LIVE_NESS_TOGGLE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        password,
        enabled,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Liveness toggle failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Liveness toggle failed:', error);
    throw error;
  }
}




/**
 * Blob URL 메모리 해제
 */
export function revokeImageUrl(url: string) {
  URL.revokeObjectURL(url);
}

/**
 * 라이브니스 상태 조회 API 호출
 * @returns 라이브니스 상태
 */
export async function getLivenessStatus(): Promise<LivenessStatusResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.LIVENESS_STATUS}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Liveness status check failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Liveness status check failed:', error);
    throw error;
  }
}

/**
 * 출퇴근 체크 V2 API 호출 (눈 깜빡임 라이브니스)
 * @param frames - 캡처된 프레임 배열
 * @returns 출퇴근 체크 결과
 */
export async function checkInOutV2(frames: CapturedFrame[]): Promise<CheckInOutResponse> {
  try {
    const formData = new FormData();
    
    // 각 프레임을 'files' 필드로 추가
    frames.forEach((frame, index) => {
      formData.append('files', frame.blob, `frame_${index}.jpg`);
    });

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHECK_IN_OUT_V2}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Check-in/out V2 failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Check-in/out V2 failed:', error);
    throw error;
  }
}

/**
 * 출퇴근 체크 V3 API 호출 (다중 프레임 평균 임베딩)
 * @param frames - 캡처된 프레임 배열
 * @returns 출퇴근 체크 결과
 */
export async function checkInOutV3(frames: CapturedFrame[]): Promise<CheckInOutResponse> {
  try {
    const formData = new FormData();

    frames.forEach((frame, index) => {
      formData.append('files', frame.blob, `frame_${index}.jpg`);
    });

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHECK_IN_OUT_V3}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Check-in/out V3 failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Check-in/out V3 failed:', error);
    throw error;
  }
}

/**
 * 출퇴근 체크 V4 API 호출 (베스트 프레임 1회 임베딩)
 * @param frames - 캡처된 프레임 배열
 * @returns 출퇴근 체크 결과
 */
export async function checkInOutV4(frames: CapturedFrame[]): Promise<CheckInOutResponse> {
  try {
    const formData = new FormData();

    frames.forEach((frame, index) => {
      formData.append('files', frame.blob, `frame_${index}.jpg`);
    });

    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.CHECK_IN_OUT_V4}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Check-in/out V4 failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Check-in/out V4 failed:', error);
    throw error;
  }
}

export async function getRecentLogs(limit: number = 300): Promise<LogItem[]> {
  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.LOGS_RECENT}?limit=${limit}`, {
    method: 'GET',
  });
  if (!response.ok) {
    throw new Error(`Failed to load logs: ${response.status}`);
  }
  const data = await response.json();
  return data.logs || [];
}

export async function clearLogs(): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.LOGS_CLEAR}`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to clear logs: ${response.status}`);
  }
  return true;
}

export async function getRegisteredUsers(): Promise<RegisteredUserItem[]> {
  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.USERS}`, {
    method: 'GET',
  });
  if (!response.ok) {
    throw new Error(`Failed to load users: ${response.status}`);
  }
  const data = await response.json();
  return data.users || [];
}

export async function deleteRegisteredUser(userId: number): Promise<boolean> {
  const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.USERS}/${userId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete user: ${response.status}`);
  }
  return true;
}
