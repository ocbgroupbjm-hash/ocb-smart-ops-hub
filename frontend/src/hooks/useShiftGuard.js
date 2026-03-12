// OCB TITAN ERP - Cashier Flow Guard
// RULE: Kasir WAJIB buka shift sebelum transaksi, tutup shift sebelum logout

import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Context for shift state
const ShiftContext = createContext();

export const ShiftProvider = ({ children }) => {
  const [shiftState, setShiftState] = useState({
    hasActiveShift: false,
    shift: null,
    loading: true,
    error: null
  });

  const checkShift = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setShiftState({ hasActiveShift: false, shift: null, loading: false, error: null });
        return;
      }

      const response = await axios.get(`${API_URL}/api/cash-control/shift/check`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setShiftState({
        hasActiveShift: response.data.has_active_shift,
        shift: response.data.shift,
        loading: false,
        error: null
      });
    } catch (error) {
      console.error('Shift check error:', error);
      setShiftState({
        hasActiveShift: false,
        shift: null,
        loading: false,
        error: error.message
      });
    }
  }, []);

  useEffect(() => {
    checkShift();
  }, [checkShift]);

  const refreshShift = () => {
    checkShift();
  };

  return (
    <ShiftContext.Provider value={{ ...shiftState, refreshShift }}>
      {children}
    </ShiftContext.Provider>
  );
};

export const useShift = () => {
  const context = useContext(ShiftContext);
  if (!context) {
    throw new Error('useShift must be used within ShiftProvider');
  }
  return context;
};

// Hook untuk validasi shift sebelum transaksi
export const useShiftGuard = () => {
  const { hasActiveShift, shift, refreshShift } = useShift();

  const requireShift = useCallback((action) => {
    if (!hasActiveShift) {
      return {
        allowed: false,
        message: 'Anda harus membuka shift kasir terlebih dahulu',
        redirect: '/cash-control'
      };
    }
    return { allowed: true, shift };
  }, [hasActiveShift, shift]);

  return { requireShift, hasActiveShift, shift, refreshShift };
};

// Hook untuk validasi logout
export const useLogoutGuard = () => {
  const { hasActiveShift, shift } = useShift();

  const canLogout = useCallback(() => {
    if (hasActiveShift) {
      return {
        allowed: false,
        message: 'Anda harus menutup shift kasir terlebih dahulu sebelum logout',
        redirect: '/cash-control'
      };
    }
    return { allowed: true };
  }, [hasActiveShift]);

  return { canLogout, hasActiveShift, shift };
};

// Constant: Role yang WAJIB punya shift untuk transaksi
export const SHIFT_REQUIRED_ROLES = ['kasir', 'cashier'];

// Check if role requires shift
export const roleRequiresShift = (role) => {
  return SHIFT_REQUIRED_ROLES.includes(role?.toLowerCase());
};

export default ShiftProvider;
