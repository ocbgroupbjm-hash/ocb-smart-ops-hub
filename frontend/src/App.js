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
import Purchase from './pages/Purchase';
import Suppliers from './pages/Suppliers';
import Customers from './pages/Customers';
import Finance from './pages/Finance';
import Accounting from './pages/Accounting';
import Reports from './pages/Reports';
import Branches from './pages/Branches';
import Users from './pages/Users';
import RolePermission from './pages/RolePermission';
import AIBusiness from './pages/AIBusiness';
import Settings from './pages/Settings';
import './index.css';

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

// Access denied component
const AccessDenied = () => (
  <div className="flex flex-col items-center justify-center h-64 text-center">
    <div className="text-6xl mb-4">🚫</div>
    <h2 className="text-2xl font-bold text-red-400 mb-2">Akses Ditolak</h2>
    <p className="text-gray-400">Anda tidak memiliki izin untuk mengakses halaman ini.</p>
  </div>
);

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
            <Route path="kasir" element={<POS />} />
            <Route path="produk" element={<Products />} />
            <Route path="stok" element={<Inventory />} />
            <Route path="pembelian" element={<Purchase />} />
            <Route path="supplier" element={<Suppliers />} />
            <Route path="pelanggan" element={<Customers />} />
            <Route path="keuangan" element={<Finance />} />
            <Route path="akuntansi" element={<Accounting />} />
            <Route path="laporan" element={<Reports />} />
            <Route path="ai-bisnis" element={<AIBusiness />} />
            <Route path="cabang" element={<Branches />} />
            <Route path="pengguna" element={<Users />} />
            <Route path="hak-akses" element={<RolePermission />} />
            <Route path="pengaturan" element={<Settings />} />
            <Route path="akses-ditolak" element={<AccessDenied />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </AuthProvider>
  );
}

export default App;
