import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import BottomLogPanel from './BottomLogPanel';

const Layout: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Header />
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <main style={{ flex: 1, padding: '2rem', overflow: 'auto' }}>
          {/* The Outlet component renders the matching child route */}
          <Outlet />
        </main>
      </div>
      <BottomLogPanel />
    </div>
  );
};

export default Layout;
