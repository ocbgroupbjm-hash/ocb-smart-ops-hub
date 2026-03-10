import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';

const PermissionContext = createContext(null);

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function PermissionProvider({ children }) {
  const { user, token, logout } = useAuth();
  const [permissions, setPermissions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [securityAlerts, setSecurityAlerts] = useState([]);

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
        
        // Check for error response
        if (data.error) {
          console.warn('Permission error:', data.error);
          setPermissions(null);
        } else {
          setPermissions(data);
        }
      } else if (res.status === 401) {
        // Session invalid - force logout
        logout();
      } else {
        setPermissions(null);
      }
    } catch (err) {
      console.error('Failed to fetch permissions:', err);
      setPermissions(null);
    } finally {
      setLoading(false);
    }
  }, [token, user, logout]);

  // Fetch security alerts for owner/admin
  const fetchSecurityAlerts = useCallback(async () => {
    if (!token || !permissions?.can_manage_system) return;
    
    try {
      const res = await fetch(`${API_URL}/api/rbac/security-alerts?limit=10`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSecurityAlerts(data.alerts || []);
      }
    } catch (err) {
      console.error('Failed to fetch security alerts:', err);
    }
  }, [token, permissions?.can_manage_system]);

  useEffect(() => {
    fetchPermissions();
  }, [fetchPermissions]);

  useEffect(() => {
    if (permissions?.role_level <= 1) {
      fetchSecurityAlerts();
    }
  }, [permissions?.role_level, fetchSecurityAlerts]);

  // FAIL-SAFE: Default is DENY
  const hasPermission = useCallback((module, action = 'view') => {
    // Not loaded yet = DENY
    if (!permissions) return false;
    
    // Super admin / Pemilik = FULL ACCESS (inherit_all)
    if (permissions.inherit_all) return true;
    
    // View only check
    if (permissions.view_only && action !== 'view') return false;
    
    // Check specific permission
    const modulePerms = permissions.permissions?.[module];
    if (!modulePerms) return false;
    
    return modulePerms.includes(action);
  }, [permissions]);

  // Branch access check
  const hasBranchAccess = useCallback((branchId) => {
    if (!permissions) return false;
    if (permissions.all_branches || permissions.inherit_all) return true;
    
    const branchAccess = permissions.branch_access || [];
    return branchAccess.length === 0 || branchAccess.includes(branchId);
  }, [permissions]);

  // Menu visibility check
  const canSeeMenu = useCallback((menuKey) => {
    if (!permissions) return false;
    if (permissions.inherit_all) return true;
    
    return permissions.menu_visibility?.[menuKey] !== false;
  }, [permissions]);

  // Role info
  const getRoleInfo = useCallback(() => {
    return {
      roleId: permissions?.role_id,
      roleCode: permissions?.role_code,
      roleName: permissions?.role_name,
      roleLevel: permissions?.role_level,
      inheritAll: permissions?.inherit_all,
      allBranches: permissions?.all_branches,
      viewOnly: permissions?.view_only,
      canManageSystem: permissions?.can_manage_system
    };
  }, [permissions]);

  // Check if user is owner or higher
  const isOwnerOrHigher = useCallback(() => {
    return permissions?.role_level <= 1;
  }, [permissions]);

  // Check if user can manage users/roles
  const canManageUsers = useCallback(() => {
    return permissions?.inherit_all || hasPermission('user_management', 'edit');
  }, [permissions, hasPermission]);

  const value = {
    permissions,
    loading,
    hasPermission,
    hasBranchAccess,
    canSeeMenu,
    getRoleInfo,
    isOwnerOrHigher,
    canManageUsers,
    securityAlerts,
    refreshPermissions: fetchPermissions,
    refreshAlerts: fetchSecurityAlerts
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
          <p className="text-xs text-gray-500 mt-2">Module: {module}, Action: {action}</p>
        </div>
      );
    }
    
    return <WrappedComponent {...props} />;
  };
}

// Component for conditional rendering based on permission
export function PermissionGate({ module, action = 'view', children, fallback = null, showDenied = false }) {
  const { hasPermission, loading } = usePermission();
  
  if (loading) return null;
  
  if (!hasPermission(module, action)) {
    if (showDenied) {
      return (
        <div className="text-center py-4 text-gray-500">
          <span className="text-red-400">🚫</span> Akses ditolak
        </div>
      );
    }
    return fallback;
  }
  
  return children;
}

// Component for branch-level access control
export function BranchGate({ branchId, children, fallback = null }) {
  const { hasBranchAccess, loading } = usePermission();
  
  if (loading) return null;
  if (!hasBranchAccess(branchId)) return fallback;
  
  return children;
}

// Hook for checking multiple permissions at once
export function usePermissions(checks) {
  const { hasPermission } = usePermission();
  
  return checks.map(({ module, action = 'view' }) => hasPermission(module, action));
}

// Hook for role-based checks
export function useRoleCheck() {
  const { permissions } = usePermission();
  
  return {
    isSuperAdmin: permissions?.role_code === 'super_admin',
    isPemilik: permissions?.role_code === 'pemilik',
    isDirektur: permissions?.role_code === 'direktur',
    isManager: permissions?.role_code === 'manager',
    isSupervisor: permissions?.role_code === 'supervisor',
    isAdmin: permissions?.role_code === 'admin',
    isGudang: permissions?.role_code === 'gudang',
    isKeuangan: permissions?.role_code === 'keuangan',
    isKasir: permissions?.role_code === 'kasir',
    isViewer: permissions?.role_code === 'viewer',
    roleLevel: permissions?.role_level,
    canManageSystem: permissions?.can_manage_system
  };
}
