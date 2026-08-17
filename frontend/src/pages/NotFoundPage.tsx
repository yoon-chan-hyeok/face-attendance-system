import React from 'react';
import { Link } from 'react-router-dom';

// 404 Not Found Page Component
// Displayed when the user navigates to a route that doesn't exist.
const NotFoundPage: React.FC = () => {
  return (
    <div>
      <h1>404 - Not Found</h1>
      <p>The page you are looking for does not exist.</p>
      <Link to="/">Go back home</Link>
    </div>
  );
};

export default NotFoundPage;

