import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { Toaster } from './components/ui/sonner';
import { DashboardLayout } from './components/layout/DashboardLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AIChat from './pages/AIChat';
import CRM from './pages/CRM';
import Branches from './pages/Branches';
import KnowledgeBase from './pages/KnowledgeBase';
import Analytics from './pages/Analytics';
import Inventory from './pages/Inventory';
import Settings from './pages/Settings';
import WhatsAppIntegration from './pages/WhatsAppIntegration';
import './index.css';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <PrivateRoute>
                  <DashboardLayout />
                </PrivateRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="ai-chat" element={<AIChat />} />
              <Route path="crm" element={<CRM />} />
              <Route path="branches" element={<Branches />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="inventory" element={<Inventory />} />
              <Route path="knowledge" element={<KnowledgeBase />} />
              <Route path="whatsapp" element={<WhatsAppIntegration />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;