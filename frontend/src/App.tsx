import { useEffect } from 'react';
import AppRoutes from './routes';
import './styles/global.css';
import { checkApiConnection } from './config/api';

function App() {
  useEffect(() => {
    // 앱 시작 시 API 서버 연결 확인
    checkApiConnection();
  }, []);

  return <AppRoutes />;
}

export default App;
