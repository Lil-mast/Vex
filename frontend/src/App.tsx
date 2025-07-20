import { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { LandingPage } from './components/LandingPage';

function App() {
  const [showDashboard, setShowDashboard] = useState(false);

  const handleEnterApp = () => {
    setShowDashboard(true);
  };

  const handleBackToLanding = () => {
    setShowDashboard(false);
  };

  if (showDashboard) {
    return <Dashboard onBackToLanding={handleBackToLanding} />;
  }

  return <LandingPage onEnterApp={handleEnterApp} />;
}

export default App;