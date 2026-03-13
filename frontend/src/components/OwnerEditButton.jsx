// OCB TITAN ERP - Owner Edit Button Component
// Tombol edit yang hanya muncul untuk role owner/pemilik/super_admin
// Setiap edit memicu recalculation dan audit log

import React, { useState } from 'react';
import { Edit, Loader2, Check, X, AlertTriangle, History } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ==================== PERMISSION CHECK ====================
const OWNER_ROLES = ['owner', 'pemilik', 'super_admin'];

export const isOwner = (user) => {
  const role = user?.role?.toLowerCase();
  return OWNER_ROLES.includes(role);
};

// ==================== OWNER EDIT BUTTON ====================
export const OwnerEditButton = ({ 
  item, 
  module, 
  onEdit, 
  onSuccess,
  size = 'md',
  showLabel = true,
  className = ''
}) => {
  const { user, api } = useAuth();
  const [loading, setLoading] = useState(false);
  
  // Hide if not owner
  if (!isOwner(user)) {
    return null;
  }
  
  const handleClick = async () => {
    if (onEdit) {
      onEdit(item);
    }
  };
  
  const sizeClasses = {
    sm: 'p-1 text-xs',
    md: 'p-1.5 text-sm',
    lg: 'p-2 text-base'
  };
  
  return (
    <button
      onClick={handleClick}
      disabled={loading}
      data-testid={`owner-edit-${module}-${item?.id}`}
      className={`flex items-center gap-1.5 bg-amber-600/20 hover:bg-amber-600/40 text-amber-400 
                  rounded transition-colors border border-amber-600/30 ${sizeClasses[size]} ${className}`}
      title="Edit (Owner)"
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Edit className="h-4 w-4" />
      )}
      {showLabel && <span>Edit</span>}
    </button>
  );
};

// ==================== OWNER EDIT MODAL ====================
export const OwnerEditModal = ({
  isOpen,
  onClose,
  module,
  item,
  fields,
  onSave
}) => {
  const { api } = useAuth();
  const [formData, setFormData] = useState(item || {});
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);
  
  if (!isOpen) return null;
  
  const handleSave = async () => {
    setSaving(true);
    try {
      // Call owner edit API
      const endpoint = `/api/owner/edit/${module}/${item.id}`;
      const response = await api.put(endpoint, formData);
      
      setResult(response.data);
      toast.success('Data berhasil diupdate');
      
      if (onSave) {
        onSave(response.data);
      }
      
      // Close after showing result
      setTimeout(() => {
        onClose();
        setResult(null);
      }, 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Gagal update data');
    } finally {
      setSaving(false);
    }
  };
  
  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };
  
  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
      <div className="bg-[#1a1012] border border-amber-700/30 rounded-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-amber-900/30 flex items-center justify-center">
              <Edit className="h-5 w-5 text-amber-400" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-amber-200">Owner Edit</h3>
              <p className="text-sm text-gray-400">Perubahan akan tercatat di audit log</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>
        
        {/* Warning */}
        <div className="bg-amber-900/20 border border-amber-700/30 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-amber-200 text-sm font-medium">Perhatian</p>
              <p className="text-gray-400 text-sm">
                Perubahan ini akan memicu recalculation pada stock, journal, dan AP/AR yang terkait.
                Semua perubahan akan dicatat di audit log.
              </p>
            </div>
          </div>
        </div>
        
        {/* Form Fields */}
        <div className="space-y-4 mb-6">
          {fields?.map((field) => (
            <div key={field.name}>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                {field.label}
              </label>
              {field.type === 'textarea' ? (
                <textarea
                  value={formData[field.name] || ''}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  rows={3}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                  placeholder={field.placeholder}
                />
              ) : field.type === 'number' ? (
                <input
                  type="number"
                  value={formData[field.name] || ''}
                  onChange={(e) => handleChange(field.name, parseFloat(e.target.value) || 0)}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                  placeholder={field.placeholder}
                />
              ) : field.type === 'select' ? (
                <select
                  value={formData[field.name] || ''}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                >
                  <option value="">-- Pilih --</option>
                  {field.options?.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.type || 'text'}
                  value={formData[field.name] || ''}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                  placeholder={field.placeholder}
                />
              )}
            </div>
          ))}
        </div>
        
        {/* Result */}
        {result && (
          <div className="bg-green-900/20 border border-green-700/30 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2 text-green-400 mb-2">
              <Check className="h-5 w-5" />
              <span className="font-medium">Update Berhasil</span>
            </div>
            {result.recalculation && (
              <p className="text-sm text-gray-400">
                Recalculation: {JSON.stringify(result.recalculation)}
              </p>
            )}
            {result.audit_logged && (
              <p className="text-sm text-gray-400">Audit log tercatat</p>
            )}
          </div>
        )}
        
        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
          >
            Batal
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-500 transition-colors disabled:opacity-50"
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Menyimpan...
              </>
            ) : (
              <>
                <Check className="h-4 w-4" />
                Simpan Perubahan
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== AUDIT LOG VIEWER ====================
export const AuditLogButton = ({ recordId, module }) => {
  const { user } = useAuth();
  const [showLogs, setShowLogs] = useState(false);
  
  if (!isOwner(user)) return null;
  
  return (
    <>
      <button
        onClick={() => setShowLogs(true)}
        className="flex items-center gap-1 p-1.5 bg-gray-800 hover:bg-gray-700 rounded text-gray-400"
        title="Lihat Audit Log"
      >
        <History className="h-4 w-4" />
      </button>
      
      {showLogs && (
        <AuditLogModal
          recordId={recordId}
          module={module}
          onClose={() => setShowLogs(false)}
        />
      )}
    </>
  );
};

export const AuditLogModal = ({ recordId, module, onClose }) => {
  const { api } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  
  React.useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await api.get(`/api/owner/audit-logs/${recordId}`);
        setLogs(response.data.history || []);
      } catch (error) {
        console.error('Failed to fetch audit logs:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [recordId]);
  
  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
      <div className="bg-[#1a1012] border border-gray-700 rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <History className="h-6 w-6 text-gray-400" />
            <div>
              <h3 className="text-lg font-bold text-gray-200">Audit Log</h3>
              <p className="text-sm text-gray-400">Riwayat perubahan data</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-lg">
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>
        
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : logs.length === 0 ? (
          <p className="text-center text-gray-400 py-8">Tidak ada riwayat perubahan</p>
        ) : (
          <div className="space-y-4">
            {logs.map((log, index) => (
              <div key={log.id || index} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-300">{log.action?.toUpperCase()}</span>
                  <span className="text-xs text-gray-500">{log.timestamp?.slice(0, 19)}</span>
                </div>
                <p className="text-sm text-gray-400 mb-1">By: {log.user_name}</p>
                {log.description && (
                  <p className="text-sm text-gray-400">{log.description}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default { OwnerEditButton, OwnerEditModal, AuditLogButton, AuditLogModal, isOwner };
