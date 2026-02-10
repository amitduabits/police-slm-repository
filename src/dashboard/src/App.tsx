import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import LoginPage from './pages/LoginPage';
import DashboardLayout from './components/DashboardLayout';
import HomePage from './pages/HomePage';
import SOPPage from './pages/SOPPage';
import ChargesheetPage from './pages/ChargesheetPage';
import SearchPage from './pages/SearchPage';
import SectionConverterPage from './pages/SectionConverterPage';
import { getAccessToken } from './lib/api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check if user is authenticated on mount
    setIsAuthenticated(!!getAccessToken());
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/" replace />
            ) : (
              <LoginPage onLogin={() => setIsAuthenticated(true)} />
            )
          }
        />

        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <DashboardLayout onLogout={() => setIsAuthenticated(false)}>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/sop" element={<SOPPage />} />
                  <Route path="/chargesheet" element={<ChargesheetPage />} />
                  <Route path="/search" element={<SearchPage />} />
                  <Route path="/tools/sections" element={<SectionConverterPage />} />
                </Routes>
              </DashboardLayout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
