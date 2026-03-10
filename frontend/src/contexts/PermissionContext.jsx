import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';

const PermissionContext = createContext(null);

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function PermissionProvider({ children }) {
  const { user, token } = useAuth();
  const [permissions, setPermissions] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchPermissions = useCallback(async () => {
    if (!token || !user) {
      setPermissions(null);
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/rbac/user/permissions`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setPermissions(data);
      } else {
        setPermissions(null);
      }
    } catch (err) {
      console.error('Failed to fetch permissions:', err);
      setPermissions(null);
    } finally {
      setLoading(false);
    }
  }, [token, user]);

  useEffect(() => {
    fetchPermissions();
  }, [fetchPermissions]);

  // Check if user has permission for module and action
  const hasPermission = useCallback((module, action = 'view') => {
    if (!permissions) return false;
    
    // Super admin / all_permissions always has access
    if (permissions.all_permissions) return true;
    
    // View only check
    if (permissions.view_only && action !== 'view') return false;
    
    // Check specific permission
    const modulePerms = permissions.permissions?.[module];
    if (!modulePerms) return false;
    
    return modulePerms.includes(action);
  }, [permissions]);

  // Check if user has access to branch
  const hasBranchAccess = useCallback((branchId) => {
    if (!permissions) return false;
    if (permissions.all_branches) return true;
    
    const branchAccess = permissions.branch_access || [];
    return branchAccess.length === 0 || branchAccess.includes(branchId);
  }, [permissions]);

  // Check menu visibility
  const canSeeMenu = useCallback((menuKey) => {
    if (!permissions) return false;
    if (permissions.all_permissions) return true;
    
    return permissions.menu_visibility?.[menuKey] !== false;
  }, [permissions]);

  // Get role info
  const getRoleInfo = useCallback(() => {
    return {
      roleId: permissions?.role_id,
      roleName: permissions?.role_name,
      allPermissions: permissions?.all_permissions,
      allBranches: permissions?.all_branches,
      viewOnly: permissions?.view_only,
      directCashier: permissions?.direct_cashier
    };
  }, [permissions]);

  const value = {
    permissions,
    loading,
    hasPermission,
    hasBranchAccess,
    canSeeMenu,
    getRoleInfo,
    refreshPermissions: fetchPermissions
  };

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
}

export function usePermission() {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermission must be used within a PermissionProvider');
  }
  return context;
}

// HOC for permission-based rendering
export function withPermission(WrappedComponent, module, action = 'view') {
  return function PermissionWrappedComponent(props) {
    const { hasPermission, loading } = usePermission();
    
    if (loading) {
      return (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-500"></div>
        </div>
      );
    }
    
    if (!hasPermission(module, action)) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <div className="text-6xl mb-4">🚫</div>
          <h2 className="text-xl font-bold text-red-400 mb-2">Akses Ditolak</h2>
          <p className="text-gray-400">Anda tidak memiliki izin untuk mengakses fitur ini.</p>
        </div>
      );
    }
    
    return <WrappedComponent {...props} />;
  };
}

// Component for conditional rendering based on permission
export function PermissionGate({ module, action = 'view', children, fallback = null }) {
  const { hasPermission, loading } = usePermission();
  
  if (loading) return null;
  if (!hasPermission(module, action)) return fallback;
  
  return children;
}

// Hook for checking multiple permissions
export function usePermissions(checks) {
  const { hasPermission } = usePermission();
  
  return checks.map(({ module, action = 'view' }) => hasPermission(module, action));
}
