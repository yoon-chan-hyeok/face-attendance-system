import React, { Suspense } from 'react';
import { useRoutes } from 'react-router-dom';
import Layout from '../components/layout/Layout';

// Lazy load pages
const HomePage = React.lazy( () => import('../pages/HomePage') );
const RegisterPage = React.lazy( () => import('../pages/RegisterPage') );
const LoginPage = React.lazy( () => import('../pages/LoginPage') );
const LogsPage = React.lazy( () => import('../pages/LogsPage') );
const DbPage = React.lazy( () => import('../pages/DbPage') );
const MultiIdentifyPage = React.lazy( () => import('../pages/MultiIdentifyPage') );
const MultiLiveAttendancePage = React.lazy( () => import('../pages/MultiLiveAttendancePage') );
const NotFoundPage = React.lazy( () => import('../pages/NotFoundPage') );

const AppRoutes = () => {
  const routes = useRoutes([
    {
      element: <Layout />, // 부모
      children: [ // 자식 컴포넌트, Layout 내부에 Outlet 컴포넌트가 있어서 이곳에 렌더링됨
        {
          path: '/',
          element: <HomePage />, 
        },
        {
          path: '/register',
          element: <RegisterPage />,
        },
        {
          path: '/login',
          element: <LoginPage />,
        },
        {
          path: '/logs',
          element: <LogsPage />,
        },
        {
          path: '/db',
          element: <DbPage />,
        },
        {
          path: '/multi',
          element: <MultiIdentifyPage />,
        },
        {
          path: '/multi-live',
          element: <MultiLiveAttendancePage />,
        },
        {
          path: '*',
          element: <NotFoundPage />,
        },
      ],
    },
  ]);

  return (
    <Suspense fallback={<div>Loading...</div>}>
      {routes}
    </Suspense>
  );
};

export default AppRoutes;
