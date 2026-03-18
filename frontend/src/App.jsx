import { useState, useEffect } from 'react';
import './App.css';
import VideoGenerator from './VideoGenerator';
import AdminPanel from './AdminPanel';
import LandingPage from './LandingPage';
import LoginPage from './LoginPage';
import SignupPage from './SignupPage';

function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    const handleLocationChange = () => {
      setCurrentPath(window.location.pathname);
    };

    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, []);

  const navigate = (path) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
  };

  const getSession = () => {
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');
    let user = null;
    try {
      user = userStr ? JSON.parse(userStr) : null;
    } catch {
      user = null;
    }
    return { token, user };
  };

  // Route guards + redirects must NOT run during render
  useEffect(() => {
    const { token, user } = getSession();
    // App area only needs a user session; manager area requires token (backend is protected)
    const hasUserSession = Boolean(user?.email);
    const hasToken = Boolean(token);

    // Keep a separate manager URL for admin
    if (currentPath === '/admin') {
      navigate('/manager');
      return;
    }

    if (currentPath === '/app' && !hasUserSession) {
      navigate('/login');
      return;
    }

    if (currentPath === '/manager') {
      if (!hasUserSession || !hasToken) {
        navigate('/login');
        return;
      }
      if (user?.role !== 'admin') {
        navigate('/app');
        return;
      }
    }
  }, [currentPath]);

  const renderComponent = () => {
    switch (currentPath) {
      case '/':
        return <LandingPage navigate={navigate} />;
      case '/login':
        return <LoginPage navigate={navigate} />;
      case '/signup':
        return <SignupPage navigate={navigate} />;
      case '/app':
        return <VideoGenerator navigate={navigate} />;
      case '/manager':
        return <AdminPanel navigate={navigate} />;
      default:
        // Default to landing page or app if path not found
        return <LandingPage navigate={navigate} />;
    }
  };

  return (
    <div className="App">
      {renderComponent()}
    </div>
  );
}

export default App;
