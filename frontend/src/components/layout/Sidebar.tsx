import React from 'react';
import { Link } from 'react-router-dom';

const Sidebar: React.FC = () => {
  return (
    <aside style={{ width: '200px', backgroundColor: 'var(--surface-color)', borderRight: '1px solid var(--border-color)', padding: '1rem', height: 'calc(100vh - 60px)' }}>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <Link to="/" style={{ color: 'var(--text-color)' }}>Home</Link>
        <Link to="/login" style={{ color: 'var(--text-color)' }}>Login</Link>
        <Link to="/unknown" style={{ color: 'var(--text-color)' }}>404 Test</Link>
      </nav>
    </aside>
  );
};

export default Sidebar;

