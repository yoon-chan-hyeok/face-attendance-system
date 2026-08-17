import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toggleLiveness } from '../../api/face';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [livenessEnabled, setLivenessEnabled] = useState<boolean | null>(null);

  // 라이브니스 상태 로컬스토리지에서 불러오기
  useEffect(() => {
    const saved = localStorage.getItem('livenessEnabled');
    if (saved !== null) {
      setLivenessEnabled(saved === 'true');
    }
  }, []);

  const handleLiveButtonClick = () => {
    setShowModal(true);
    setPassword('');
    setError(null);
  };

  const handleToggle = async () => {
    if (!password) {
      setError('Please enter password');
      return;
    }

    setLoading(true);
    setError(null);

    // 현재 상태의 반대로 토글
    const newState = !livenessEnabled;

    try {
      const result = await toggleLiveness(password, newState);
      setLivenessEnabled(result.enabled);
      localStorage.setItem('livenessEnabled', result.enabled.toString());
      
      // CustomEvent 발생시켜서 다른 컴포넌트에 알림
      window.dispatchEvent(new CustomEvent('livenessChanged', { 
        detail: { enabled: result.enabled } 
      }));
      
      setShowModal(false);
      setPassword('');
    } catch (err: any) {
      setError(err.message || 'Failed to toggle liveness');
    } finally {
      setLoading(false);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setPassword('');
    setError(null);
  };

  return (
    <>
      <header className="p-4 bg-gray-900 border-b border-gray-800 flex justify-between items-center">
        <div
          className="font-bold text-xl text-white cursor-pointer hover:text-blue-400 transition-colors"
          onClick={() => navigate('/')}
        >
          Face Attendance System
        </div>
        <nav className="flex items-center gap-4">
          {/* 라이브니스 상태 표시 */}
          {livenessEnabled !== null && (
            <div className="flex items-center gap-2 px-3 py-1 bg-gray-800 rounded-md">
              <div className={`w-2 h-2 rounded-full ${livenessEnabled ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
              <span className="text-xs text-gray-300">
                Liveness: {livenessEnabled ? 'ON' : 'OFF'}
              </span>
            </div>
          )}
          
          <button
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            onClick={() => navigate('/register')}
          >
            Register
          </button>
          <button
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
            onClick={() => navigate('/logs')}
          >
            Logs
          </button>
          <button
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
            onClick={() => navigate('/db')}
          >
            DB
          </button>
          <button
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
            onClick={() => navigate('/multi')}
          >
            Multi
          </button>
          <button
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
            onClick={() => navigate('/multi-live')}
          >
            Multi Live
          </button>
          <button
            className={`px-4 py-2 rounded transition-colors ${
              livenessEnabled 
                ? 'bg-green-600 hover:bg-green-700' 
                : 'bg-gray-600 hover:bg-gray-700'
            } text-white`}
            onClick={handleLiveButtonClick}
          >
            Live
          </button>
        </nav>
      </header>

      {/* 모달 */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">Liveness</h2>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Admin Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !loading) {
                    handleToggle();
                  }
                }}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter password"
                disabled={loading}
                autoFocus
              />
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-900/50 text-red-200 rounded-md text-sm border border-red-700">
                {error}
              </div>
            )}

            <div className="mb-4 p-3 bg-gray-900/50 rounded-md">
              <p className="text-sm text-gray-400">
                Current Status: 
                <span className={`ml-2 font-bold ${livenessEnabled ? 'text-green-400' : 'text-gray-400'}`}>
                  {livenessEnabled ? 'ENABLED' : 'DISABLED'}
                </span>
              </p>
            </div>

            <button
              onClick={handleToggle}
              disabled={loading}
              className={`w-full py-3 px-4 rounded-md font-medium transition-colors ${
                loading
                  ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                  : livenessEnabled
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {loading 
                ? 'Processing...' 
                : livenessEnabled 
                  ? '✗ Disable Liveness' 
                  : '✓ Enable Liveness'}
            </button>

            <button
              onClick={closeModal}
              disabled={loading}
              className="w-full mt-3 py-2 px-4 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-md transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default Header;
