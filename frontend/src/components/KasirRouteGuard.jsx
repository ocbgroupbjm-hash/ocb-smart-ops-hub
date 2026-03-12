// OCB TITAN ERP - Kasir Route Guard Component
// Memaksa kasir ke Kontrol Kas jika belum buka shift

import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { AlertTriangle, Clock } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Routes yang kasir boleh akses TANPA shift aktif
const NO_SHIFT_ALLOWED_ROUTES = [
  '/cash-control',
  '/dashboard',
  '/login'
];

// Routes yang WAJIB ada shift untuk kasir
const SHIFT_REQUIRED_ROUTES = [
  '/kasir',
  '/sales',
  '/pos'
];

const KasirRouteGuard = ({ children }) => {
  const { user } = useAuth();
  const location = useLocation();
  const [shiftStatus, setShiftStatus] = useState({ loading: true, hasActiveShift: false, checked: false });
  const [showBlockModal, setShowBlockModal] = useState(false);

  const userRole = user?.role?.toLowerCase();
  const isKasir = userRole === 'kasir' || userRole === 'cashier';

  useEffect(() => {
    const checkShift = async () => {
      if (!isKasir) {
        setShiftStatus({ loading: false, hasActiveShift: true, checked: true });
        return;
      }

      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/api/cash-control/shift/check`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setShiftStatus({
          loading: false,
          hasActiveShift: response.data.has_active_shift,
          shift: response.data.shift,
          checked: true
        });
      } catch (error) {
        console.error('Shift check failed:', error);
        setShiftStatus({ loading: false, hasActiveShift: false, checked: true });
      }
    };

    checkShift();
  }, [isKasir, location.pathname]);

  // Non-kasir: allow all routes
  if (!isKasir) {
    return children;
  }

  // Loading state
  if (shiftStatus.loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-500"></div>
      </div>
    );
  }

  const currentPath = location.pathname;

  // Check if current route needs shift
  const needsShift = SHIFT_REQUIRED_ROUTES.some(route => currentPath.startsWith(route));
  const allowedWithoutShift = NO_SHIFT_ALLOWED_ROUTES.some(route => currentPath.startsWith(route));

  // GUARD: Kasir mencoba akses route yang butuh shift, tapi belum buka shift
  if (needsShift && !shiftStatus.hasActiveShift) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center px-4">
        <div className="bg-red-900/30 border border-red-700/50 rounded-xl p-8 max-w-md">
          <div className="h-16 w-16 rounded-full bg-red-900/50 flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="h-8 w-8 text-red-400" />
          </div>
          <h2 className="text-xl font-bold text-red-200 mb-2">Shift Belum Dibuka</h2>
          <p className="text-gray-400 mb-6">
            Anda harus membuka shift kasir terlebih dahulu sebelum dapat melakukan transaksi penjualan.
          </p>
          <div className="flex items-center justify-center gap-2 text-amber-300 mb-4">
            <Clock className="h-4 w-4" />
            <span className="text-sm">Buka shift di Kontrol Kas</span>
          </div>
          <a
            href="/cash-control"
            className="inline-block px-6 py-3 bg-red-700 text-white rounded-lg hover:bg-red-600 transition-colors font-medium"
          >
            Buka Shift Sekarang
          </a>
        </div>
      </div>
    );
  }

  // REDIRECT: Kasir login pertama kali tanpa shift → redirect ke Kontrol Kas
  if (!shiftStatus.hasActiveShift && currentPath === '/dashboard') {
    // Show notification but allow dashboard access
    // The sidebar will show a warning banner
  }

  return children;
};

export default KasirRouteGuard;
