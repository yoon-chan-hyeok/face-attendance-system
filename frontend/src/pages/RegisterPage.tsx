import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCamera } from '../hooks/useCamera';
import { registerUserV2 } from '../api/face';
import { CameraView } from '../components/homepage/CameraView';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { videoRef, startCamera, captureFrames } = useCamera();
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [redirectCountdown, setRedirectCountdown] = useState<number | null>(null);

  const REGISTER_CAPTURE_DURATION = 1000; // 1 second
  const REGISTER_CAPTURE_INTERVAL = 100;  // ~10 frames

  useEffect(() => {
    startCamera();
  }, []);

  useEffect(() => {
    if (redirectCountdown === null || redirectCountdown <= 0) return;

    const timer = setInterval(() => {
      setRedirectCountdown((prev) => {
        if (prev === null || prev <= 1) {
          return null;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [redirectCountdown]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name) {
      setMessage({ text: 'Please enter a name.', type: 'error' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const captureStartedAt = performance.now();
      const frames = await captureFrames(
        REGISTER_CAPTURE_DURATION,
        REGISTER_CAPTURE_INTERVAL
      );
      const captureElapsedMs = performance.now() - captureStartedAt;
      console.log(`[Register] Capture done: frames=${frames.length}, elapsed=${Math.round(captureElapsedMs)}ms`);

      const employeeId = crypto.randomUUID();
      const result = await registerUserV2(name, employeeId, frames, captureElapsedMs);
      const statsText = result.stats
        ? ` (saved_npy=${result.stats.saved_npy}, failed_frames=${result.stats.failed_frames})`
        : '';
      setMessage({ text: `Registration successful: ${result.message}${statsText}`, type: 'success' });
      setName('');
      setRedirectCountdown(3);

      setTimeout(() => {
        navigate('/');
      }, 3000);
    } catch (err: any) {
      setMessage({ text: err.message || 'An error occurred during registration.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full w-full p-4">
      <h1 className="text-3xl font-bold mb-6 text-white">User Registration</h1>

      <div className="flex flex-col lg:flex-row gap-8 w-full max-w-5xl">
        <div className="flex-1">
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <h2 className="text-xl font-semibold text-gray-200 mb-4">Face Capture</h2>
            <CameraView videoRef={videoRef as React.RefObject<HTMLVideoElement>} loading={loading} />
          </div>
        </div>

        <div className="flex-1">
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 h-full">
            <h2 className="text-xl font-semibold text-gray-200 mb-6">Employee Info</h2>

            <form onSubmit={handleRegister} className="space-y-6">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-2">
                  Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter name"
                  disabled={loading}
                  autoFocus
                />
              </div>

              <div className="text-sm text-gray-400 bg-gray-900/50 p-3 rounded">
                Capture runs for about 1 second and stores multiple high-quality embeddings.
              </div>

              {message && (
                <div className="space-y-2">
                  <div className={`p-4 rounded-md ${
                    message.type === 'success' ? 'bg-green-900/50 text-green-200 border border-green-700' : 'bg-red-900/50 text-red-200 border border-red-700'
                  }`}>
                    {message.text}
                  </div>
                  {message.type === 'success' && redirectCountdown !== null && (
                    <div className="text-sm text-gray-400 bg-blue-900/30 p-3 rounded border border-blue-700/50">
                      Redirecting to main page in {redirectCountdown} second{redirectCountdown !== 1 ? 's' : ''}...
                    </div>
                  )}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className={`w-full py-3 px-4 rounded-md text-white font-medium transition-colors ${
                  loading
                    ? 'bg-gray-600 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500'
                }`}
              >
                {loading ? 'Registering...' : 'Register User'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
