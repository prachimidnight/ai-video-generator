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
      case '/admin':
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
