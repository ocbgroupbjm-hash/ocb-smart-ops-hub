import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Toaster } from './components/ui/sonner';
import { DashboardLayout } from './components/layout/DashboardLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import POS from './pages/POS';
import Products from './pages/Products';
import Inventory from './pages/Inventory';
import Customers from './pages/Customers';
import Branches from './pages/Branches';
import './index.css';

// Placeholder pages
const Finance = () => <PlaceholderPage title="Finance" desc="Financial management coming soon" />;
const Reports = () => <PlaceholderPage title="Reports" desc="Business reports coming soon" />;
const Purchase = () => <PlaceholderPage title="Purchase" desc="Purchase management coming soon" />;
const Users = () => <PlaceholderPage title="Users" desc="User management coming soon" />;
const Settings = () => <PlaceholderPage title="Settings" desc="System settings coming soon" />;

const PlaceholderPage = ({ title, desc }) => (
  <div className="flex items-center justify-center h-64">
    <div className="text-center">
      <h1 className="text-2xl font-bold text-amber-100 mb-2">{title}</h1>
      <p className="text-gray-400">{desc}</p>
    </div>
  </div>
);

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0608]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
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
            <Route path="pos" element={<POS />} />
            <Route path="products" element={<Products />} />
            <Route path="inventory" element={<Inventory />} />
            <Route path="purchase" element={<Purchase />} />
            <Route path="customers" element={<Customers />} />
            <Route path="branches" element={<Branches />} />
            <Route path="finance" element={<Finance />} />
            <Route path="reports" element={<Reports />} />
            <Route path="users" element={<Users />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </AuthProvider>
  );
}

export default App;
