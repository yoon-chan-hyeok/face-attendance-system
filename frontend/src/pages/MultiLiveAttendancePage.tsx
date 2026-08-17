import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CameraView } from '../components/homepage/CameraView';
import { checkInOutMultiFromPhoto, getLivenessStatus, type MultiAttendanceResponse } from '../api/face';
import { useCamera } from '../hooks/useCamera';

const base64ToBlob = (base64: string, mimeType: string = 'image/jpeg'): Blob => {
  const byteString = atob(base64.split(',')[1]);
  const ab = new ArrayBuffer(byteString.length);
  const ia = new Uint8Array(ab);
  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i);
  }
  return new Blob([ab], { type: mimeType });
};

const MultiLiveAttendancePage: React.FC = () => {
  const navigate = useNavigate();
  const { videoRef, startCamera, captureImage } = useCamera();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MultiAttendanceResponse | null>(null);
  const [livenessEnabled, setLivenessEnabled] = useState(false);

  useEffect(() => {
    startCamera().catch((err) => {
      setError(err?.message || 'Failed to start camera.');
    });

    const checkLivenessStatus = () => {
      getLivenessStatus()
        .then((status) => setLivenessEnabled(status.enabled))
        .catch(() => {
          const saved = localStorage.getItem('livenessEnabled');
          if (saved !== null) {
            setLivenessEnabled(saved === 'true');
          }
        });
    };
    checkLivenessStatus();

    const handleLivenessChange = (event: CustomEvent) => {
      setLivenessEnabled(event.detail.enabled);
    };
    window.addEventListener('livenessChanged', handleLivenessChange as EventListener);
    return () => {
      window.removeEventListener('livenessChanged', handleLivenessChange as EventListener);
    };
  }, []);

  const handleIdentifyMulti = async () => {
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      const captured = captureImage();
      if (!captured) {
        throw new Error('Camera frame capture failed.');
      }

      const blob = base64ToBlob(captured, 'image/jpeg');
      const file = new File([blob], `multi_live_${Date.now()}.jpg`, { type: 'image/jpeg' });
      const data = await checkInOutMultiFromPhoto(file);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Multi live check-in/out failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full w-full">
      <h1 className="text-3xl font-bold mb-6 text-white">Face Attendance</h1>

      <div className="w-full max-w-2xl overflow-hidden">
        <CameraView
          videoRef={videoRef as React.RefObject<HTMLVideoElement>}
          loading={loading}
          livenessEnabled={livenessEnabled}
        />

        <div className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <button
              onClick={handleIdentifyMulti}
              disabled={loading}
              className={`py-3 px-4 rounded-md text-white font-medium transition-colors ${
                loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              }`}
            >
              {loading ? 'Processing...' : 'Check In/Out (Multi)'}
            </button>
            <button
              onClick={() => navigate('/multi')}
              className="py-3 px-4 rounded-md text-white font-medium bg-violet-600 hover:bg-violet-700 transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2"
            >
              Upload Image (Multi-Face)
            </button>
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
              {error}
            </div>
          )}

          {result && (
            <div className="mt-4 p-4 bg-gray-900/50 border border-gray-700 rounded-md text-gray-100">
              <div className="text-sm">
                faces={result.face_count}, identified={result.identified_count}, unknown={result.unknown_count}, recorded={result.attendance_recorded_count}
              </div>
              <div className="mt-3 space-y-2">
                {result.results.map((item) => (
                  <div key={`multi-live-${item.face_index}`} className="text-sm border border-gray-700 rounded p-2 bg-gray-800/50">
                    <div className="font-medium">
                      Face #{item.face_index + 1}: {item.message}
                    </div>
                    {item.user && (
                      <div className="text-xs text-gray-300 mt-1">
                        {item.user.name} ({item.user.employee_id})
                      </div>
                    )}
                    {item.action_type && (
                      <div className="text-xs text-emerald-300 mt-1">
                        action={item.action_type}, at={item.action_at ?? 'N/A'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MultiLiveAttendancePage;
