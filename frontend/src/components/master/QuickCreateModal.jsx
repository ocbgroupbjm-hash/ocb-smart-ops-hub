// ============================================================================
// OCB TITAN ERP - Quick Create Master Reference Component
// ============================================================================
// Komponen untuk membuat master reference (Kategori, Satuan, Merek, Tipe Item)
// langsung dari form Tambah Item tanpa harus keluar dari form.
// ============================================================================

import React, { useState } from 'react';
import { X, Plus, AlertCircle, Check, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ============ QUICK CREATE MODAL ============

export function QuickCreateModal({ 
  isOpen, 
  onClose, 
  type, 
  token, 
  onSuccess 
}) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: '',
    symbol: '',
    contact_person: '',
    phone: '',
    email: '',
    address: ''
  });
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const typeConfig = {
    category: {
      title: 'Tambah Kategori Baru',
      endpoint: '/api/master/categories',
      fields: ['code', 'name', 'description'],
      validation: { name: 'Nama kategori wajib diisi' }
    },
    unit: {
      title: 'Tambah Satuan Baru',
      endpoint: '/api/master/units',
      fields: ['code', 'name', 'symbol'],
      validation: { name: 'Nama satuan wajib diisi' }
    },
    brand: {
      title: 'Tambah Merek Baru',
      endpoint: '/api/master/brands',
      fields: ['code', 'name'],
      validation: { name: 'Nama merek wajib diisi' }
    },
    supplier: {
      title: 'Tambah Supplier Baru',
      endpoint: '/api/suppliers',
      fields: ['code', 'name', 'contact_person', 'phone', 'email', 'address'],
      validation: { name: 'Nama supplier wajib diisi' }
    }
  };

  const config = typeConfig[type];
  if (!config) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validate
    if (!formData.name.trim()) {
      setError(config.validation.name);
      return;
    }
    
    setLoading(true);
    try {
      const payload = {};
      config.fields.forEach(field => {
        if (formData[field]) {
          payload[field] = formData[field].trim();
        }
      });
      
      // Generate code from name if not provided
      if (!payload.code) {
        payload.code = formData.name.substring(0, 10).toUpperCase().replace(/\s+/g, '-');
      }
      
      const response = await fetch(`${API_URL}${config.endpoint}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Gagal membuat data baru');
      }
      
      const newItem = await response.json();
      toast.success(`${config.title.replace('Tambah ', '')} berhasil!`);
      
      // Reset form
      setFormData({ code: '', name: '', description: '', symbol: '', contact_person: '', phone: '', email: '', address: '' });
      
      // Callback with new item - parent will handle closing
      if (onSuccess) {
        onSuccess(newItem);
      }
      
      // Note: Don't call onClose() here - parent (SearchableSelectWithCreate) will handle it
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60">
      <div className="bg-[#1a1a1a] border border-[#333] rounded-xl w-full max-w-md shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#333]">
          <div className="flex items-center gap-2">
            <Plus className="w-5 h-5 text-green-400" />
            <h3 className="text-white font-medium">{config.title}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-[#333] transition-colors"
            data-testid="quick-create-close"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>
        
        {/* Form - Using div instead of form to avoid nested form HTML violation */}
        <div className="p-4 space-y-4">
          {/* Error message */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-300 text-sm">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}
          
          {/* Code field (optional) */}
          {config.fields.includes('code') && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Kode <span className="text-gray-500">(opsional, auto-generate jika kosong)</span>
              </label>
              <input
                type="text"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                placeholder="Contoh: KAT-001"
                data-testid="quick-create-code"
              />
            </div>
          )}
          
          {/* Name field (required) */}
          {config.fields.includes('name') && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Nama <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                placeholder={`Nama ${type === 'category' ? 'kategori' : type === 'unit' ? 'satuan' : type === 'supplier' ? 'supplier' : 'merek'}`}
                autoFocus
                required
                data-testid="quick-create-name"
              />
            </div>
          )}
          
          {/* Contact Person field (for suppliers) */}
          {config.fields.includes('contact_person') && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Contact Person
              </label>
              <input
                type="text"
                value={formData.contact_person || ''}
                onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                placeholder="Nama kontak"
                data-testid="quick-create-contact-person"
              />
            </div>
          )}
          
          {/* Phone field (for suppliers) */}
          {config.fields.includes('phone') && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Telepon
              </label>
              <input
                type="tel"
                value={formData.phone || ''}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                placeholder="08xx-xxxx-xxxx"
                data-testid="quick-create-phone"
              />
            </div>
          )}
          
          {/* Email field (for suppliers) */}
          {config.fields.includes('email') && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Email
              </label>
              <input
                type="email"
                value={formData.email || ''}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                placeholder="email@supplier.com"
                data-testid="quick-create-email"
              />
            </div>
          )}
          
          {/* Address field (for suppliers) */}
          {config.fields.includes('address') && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Alamat
              </label>
              <textarea
                value={formData.address || ''}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm resize-none"
                placeholder="Alamat supplier"
                rows={2}
                data-testid="quick-create-address"
              />
            </div>
          )}
          
          {/* Symbol field (for units) */}
          {config.fields.includes('symbol') && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Simbol/Singkatan
              </label>
              <input
                type="text"
                value={formData.symbol}
                onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm"
                placeholder="Contoh: pcs, kg, ltr"
                data-testid="quick-create-symbol"
              />
            </div>
          )}
          
          {/* Description field */}
          {config.fields.includes('description') && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">
                Deskripsi
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-white text-sm resize-none"
                placeholder="Deskripsi (opsional)"
                rows={2}
                data-testid="quick-create-description"
              />
            </div>
          )}
          
          {/* Actions */}
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-[#333] text-gray-300 rounded-lg hover:bg-[#444] transition-colors text-sm"
              disabled={loading}
            >
              Batal
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading || !formData.name.trim()}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm flex items-center justify-center gap-2 disabled:opacity-50"
              data-testid="quick-create-submit"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Menyimpan...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Simpan
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============ SEARCHABLE SELECT WITH QUICK CREATE ============

export function SearchableSelectWithCreate({
  options,
  value,
  onValueChange,
  placeholder,
  searchPlaceholder,
  type, // 'category', 'unit', 'brand'
  token,
  onItemCreated,
  disabled = false,
  className = '',
  'data-testid': testId
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [showQuickCreate, setShowQuickCreate] = useState(false);
  
  const filteredOptions = options.filter(opt => {
    // Defensive check for undefined label (can happen during quick create)
    if (!opt || !opt.label) return false;
    return opt.label.toLowerCase().includes(search.toLowerCase()) ||
      (opt.sublabel && opt.sublabel.toLowerCase().includes(search.toLowerCase()));
  });
  
  const selectedOption = options.find(opt => opt && opt.value === value);
  
  const handleQuickCreateSuccess = (newItem) => {
    // Format the new item as an option
    const newOption = {
      value: newItem.id,
      label: newItem.name,
      sublabel: newItem.code
    };
    
    // Select the new item
    onValueChange(newItem.id);
    
    // Notify parent to refresh options
    if (onItemCreated) {
      onItemCreated(type, newItem);
    }
    
    setShowQuickCreate(false);
    setIsOpen(false);
  };
  
  const typeLabels = {
    category: 'Kategori',
    unit: 'Satuan',
    brand: 'Merek',
    supplier: 'Supplier'
  };

  return (
    <>
      <div className={`relative ${className}`}>
        {/* Trigger button */}
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          className={`w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-lg text-left flex items-center justify-between ${
            disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-[#555]'
          }`}
          data-testid={testId}
        >
          <span className={selectedOption?.label ? 'text-white text-sm' : 'text-gray-500 text-sm'}>
            {selectedOption?.label || placeholder}
          </span>
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        {/* Dropdown */}
        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-[#1a1a1a] border border-[#333] rounded-lg shadow-xl max-h-60 overflow-hidden">
            {/* Search input */}
            <div className="p-2 border-b border-[#333]">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded text-white text-sm"
                placeholder={searchPlaceholder || 'Cari...'}
                autoFocus
              />
            </div>
            
            {/* Options */}
            <div className="max-h-40 overflow-y-auto">
              {/* Quick Create Button - Always at top */}
              <button
                type="button"
                onClick={() => {
                  setShowQuickCreate(true);
                  setIsOpen(false);
                }}
                className="w-full px-3 py-2 text-left text-green-400 hover:bg-green-900/30 flex items-center gap-2 text-sm border-b border-[#333]"
                data-testid={`quick-create-${type}-btn`}
              >
                <Plus className="w-4 h-4" />
                Tambah {typeLabels[type]} Baru
              </button>
              
              {filteredOptions.length === 0 ? (
                <div className="px-3 py-4 text-gray-500 text-sm text-center">
                  Tidak ada hasil
                </div>
              ) : (
                filteredOptions.map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => {
                      onValueChange(opt.value);
                      setIsOpen(false);
                      setSearch('');
                    }}
                    className={`w-full px-3 py-2 text-left hover:bg-[#333] flex items-center justify-between ${
                      value === opt.value ? 'bg-[#333]' : ''
                    }`}
                  >
                    <div>
                      <span className="text-white text-sm">{opt.label}</span>
                      {opt.sublabel && (
                        <span className="text-gray-500 text-xs ml-2">({opt.sublabel})</span>
                      )}
                    </div>
                    {value === opt.value && (
                      <Check className="w-4 h-4 text-green-400" />
                    )}
                  </button>
                ))
              )}
            </div>
          </div>
        )}
        
        {/* Backdrop */}
        {isOpen && (
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => {
              setIsOpen(false);
              setSearch('');
            }}
          />
        )}
      </div>
      
      {/* Quick Create Modal */}
      <QuickCreateModal
        isOpen={showQuickCreate}
        onClose={() => setShowQuickCreate(false)}
        type={type}
        token={token}
        onSuccess={handleQuickCreateSuccess}
      />
    </>
  );
}

export default QuickCreateModal;
