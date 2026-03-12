// OCB TITAN ERP - RBAC Permission Helper
// SINGLE SOURCE OF TRUTH untuk permission di seluruh sistem
// Semua check permission WAJIB menggunakan helper ini

import { usePermission } from '../contexts/PermissionContext';

// ==================== PERMISSION ACTIONS ====================
export const ACTIONS = {
  VIEW: 'view',
  CREATE: 'create',
  EDIT: 'edit',
  DELETE: 'delete',
  APPROVE: 'approve',
  PRINT: 'print',
  EXPORT: 'export'
};

// ==================== MODULE CODES ====================
export const MODULES = {
  DASHBOARD: 'dashboard',
  MASTER: 'master',
  SALES: 'sales',
  PURCHASE: 'purchase',
  INVENTORY: 'inventory',
  ACCOUNTING: 'accounting',
  AP: 'ap',
  AR: 'ar',
  KAS: 'kas',
  REPORT: 'report',
  HR: 'hr',
  SETTING: 'setting',
  CASH_CONTROL: 'cash_control',
  CREDIT_CONTROL: 'credit_control',
  AI_TOOLS: 'ai_tools'
};

// ==================== ROLE DEFINITIONS ====================
// Definisi hak akses per role - SATU SUMBER KEBENARAN
export const ROLE_PERMISSIONS = {
  // OWNER/PEMILIK - FULL ACCESS
  owner: {
    level: 0,
    inherit_all: true,
    all_branches: true,
    modules: '*', // Semua modul
    actions: '*'  // Semua aksi
  },
  pemilik: {
    level: 0,
    inherit_all: true,
    all_branches: true,
    modules: '*',
    actions: '*'
  },
  super_admin: {
    level: 0,
    inherit_all: true,
    all_branches: true,
    modules: '*',
    actions: '*'
  },

  // ADMIN - Full access kecuali owner-only
  admin: {
    level: 1,
    all_branches: true,
    modules: [
      'dashboard', 'master', 'sales', 'purchase', 'inventory',
      'accounting', 'ap', 'ar', 'kas', 'report', 'hr', 'setting',
      'cash_control', 'credit_control', 'ai_tools'
    ],
    actions: ['view', 'create', 'edit', 'delete', 'approve', 'print', 'export']
  },

  // DIREKTUR - Strategic view, limited edit
  direktur: {
    level: 2,
    all_branches: true,
    modules: [
      'dashboard', 'report', 'accounting', 'ap', 'ar', 
      'credit_control', 'ai_tools'
    ],
    actions: ['view', 'approve', 'print', 'export']
  },

  // MANAGER - Operational management
  manager: {
    level: 3,
    all_branches: false,
    modules: [
      'dashboard', 'sales', 'purchase', 'inventory', 
      'report', 'cash_control', 'credit_control'
    ],
    actions: ['view', 'create', 'edit', 'approve', 'print', 'export']
  },

  // SUPERVISOR - Team supervision
  supervisor: {
    level: 4,
    all_branches: false,
    modules: [
      'dashboard', 'sales', 'purchase', 'inventory', 
      'report', 'cash_control'
    ],
    actions: ['view', 'create', 'edit', 'approve', 'print']
  },

  // FINANCE/KEUANGAN - Financial operations
  finance: {
    level: 5,
    all_branches: false,
    modules: [
      'dashboard', 'accounting', 'ap', 'ar', 'kas', 
      'report', 'cash_control'
    ],
    actions: ['view', 'create', 'edit', 'print', 'export']
  },
  keuangan: {
    level: 5,
    all_branches: false,
    modules: [
      'dashboard', 'accounting', 'ap', 'ar', 'kas', 
      'report', 'cash_control'
    ],
    actions: ['view', 'create', 'edit', 'print', 'export']
  },

  // GUDANG/INVENTORY - Warehouse operations
  gudang: {
    level: 6,
    all_branches: false,
    modules: [
      'dashboard', 'inventory', 'purchase', 'master'
    ],
    actions: ['view', 'create', 'edit', 'print']
  },
  inventory: {
    level: 6,
    all_branches: false,
    modules: [
      'dashboard', 'inventory', 'purchase', 'master'
    ],
    actions: ['view', 'create', 'edit', 'print']
  },

  // KASIR - MINIMAL ACCESS (Operasional saja)
  kasir: {
    level: 7,
    all_branches: false,
    requires_shift: true, // WAJIB buka shift
    modules: [
      'dashboard',      // Dashboard ringkas
      'sales',          // POS/Penjualan
      'cash_control'    // Kontrol Kas (shift)
    ],
    actions: ['view', 'create', 'print'],
    // Explicit forbidden
    forbidden_modules: [
      'accounting', 'ap', 'ar', 'master', 'purchase', 
      'setting', 'hr', 'credit_control', 'ai_tools'
    ]
  },
  cashier: {
    level: 7,
    all_branches: false,
    requires_shift: true,
    modules: [
      'dashboard', 'sales', 'cash_control'
    ],
    actions: ['view', 'create', 'print'],
    forbidden_modules: [
      'accounting', 'ap', 'ar', 'master', 'purchase', 
      'setting', 'hr', 'credit_control', 'ai_tools'
    ]
  },

  // SALES - Sales operations
  sales: {
    level: 6,
    all_branches: false,
    modules: [
      'dashboard', 'sales', 'report'
    ],
    actions: ['view', 'create', 'edit', 'print']
  }
};

// ==================== PERMISSION CHECK FUNCTIONS ====================

/**
 * Check if role can access module
 */
export const canAccessModule = (role, module) => {
  const roleConfig = ROLE_PERMISSIONS[role?.toLowerCase()];
  if (!roleConfig) return false;

  // Full access
  if (roleConfig.inherit_all || roleConfig.modules === '*') {
    return true;
  }

  // Check forbidden
  if (roleConfig.forbidden_modules?.includes(module)) {
    return false;
  }

  // Check allowed
  return roleConfig.modules?.includes(module) || false;
};

/**
 * Check if role can perform action on module
 */
export const canPerformAction = (role, module, action) => {
  const roleConfig = ROLE_PERMISSIONS[role?.toLowerCase()];
  if (!roleConfig) return false;

  // Full access
  if (roleConfig.inherit_all || roleConfig.actions === '*') {
    return true;
  }

  // Must have module access
  if (!canAccessModule(role, module)) {
    return false;
  }

  // Check action
  return roleConfig.actions?.includes(action) || false;
};

/**
 * Get allowed menus for role
 */
export const getAllowedMenus = (role) => {
  const roleConfig = ROLE_PERMISSIONS[role?.toLowerCase()];
  if (!roleConfig) return [];

  if (roleConfig.inherit_all || roleConfig.modules === '*') {
    return Object.values(MODULES);
  }

  return roleConfig.modules || [];
};

/**
 * Check if role requires shift for transaction
 */
export const requiresShiftForTransaction = (role) => {
  const roleConfig = ROLE_PERMISSIONS[role?.toLowerCase()];
  return roleConfig?.requires_shift || false;
};

/**
 * Get role level (0 = highest, 9 = lowest)
 */
export const getRoleLevel = (role) => {
  const roleConfig = ROLE_PERMISSIONS[role?.toLowerCase()];
  return roleConfig?.level ?? 99;
};

// ==================== MENU VISIBILITY MAPPING ====================
// Map menu name ke module code untuk filtering

export const MENU_TO_MODULE = {
  'Dashboard': 'dashboard',
  'Master Data': 'master',
  'Penjualan': 'sales',
  'Pembelian': 'purchase',
  'Inventory': 'inventory',
  'Akuntansi': 'accounting',
  'Hutang': 'ap',
  'Piutang': 'ar',
  'Kas / Bank': 'kas',
  'Laporan': 'report',
  'HR & Payroll': 'hr',
  'Pengaturan': 'setting',
  'Kontrol Kas': 'cash_control',
  'Credit Control': 'credit_control',
  'Stock Reorder': 'inventory',
  'Branch Inventory Control': 'inventory',
  'Purchase Planning': 'purchase',
  'KPI Dashboard': 'report',
  'AI Tools': 'ai_tools'
};

/**
 * Check if menu should be visible for role
 */
export const shouldShowMenu = (role, menuName) => {
  const module = MENU_TO_MODULE[menuName];
  if (!module) return true; // Unknown menu, show by default
  
  return canAccessModule(role, module);
};

// ==================== KASIR SPECIFIC CHECKS ====================

/**
 * Get kasir-specific allowed menu items
 */
export const getKasirAllowedMenus = () => {
  return [
    'Dashboard',
    'Penjualan',    // POS
    'Kontrol Kas'   // Shift
  ];
};

/**
 * Check if kasir can access route
 */
export const isKasirAllowedRoute = (path) => {
  const allowedPaths = [
    '/dashboard',
    '/kasir',
    '/sales',
    '/cash-control',
    '/login'
  ];
  
  return allowedPaths.some(allowed => path.startsWith(allowed));
};

export default {
  ACTIONS,
  MODULES,
  ROLE_PERMISSIONS,
  canAccessModule,
  canPerformAction,
  getAllowedMenus,
  requiresShiftForTransaction,
  getRoleLevel,
  shouldShowMenu,
  getKasirAllowedMenus,
  isKasirAllowedRoute
};
