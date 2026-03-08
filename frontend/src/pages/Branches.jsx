import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Edit, Building2, MapPin, Phone, Users, Loader2, X, Save } from 'lucide-react';
import { toast } from 'sonner';

const Branches = () => {
  const { api } = useAuth();
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingBranch, setEditingBranch] = useState(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ code: '', name: '', address: '', city: '', phone: '', email: '', is_warehouse: false });

  useEffect(() => { loadBranches(); }, []);

  const loadBranches = async () => {
    setLoading(true);
    try {
      const res = await api('/api/branches');
      if (res.ok) setBranches(await res.json());
    } catch (err) {
      toast.error('Failed to load branches');
    } finally {
      setLoading(false);
    }
  };

  const openModal = (branch = null) => {
    if (branch) {
      setEditingBranch(branch);
      setForm({ ...branch });
    } else {
      setEditingBranch(null);
      setForm({ code: '', name: '', address: '', city: '', phone: '', email: '', is_warehouse: false });
    }
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.code || !form.name) {
      toast.error('Code and name are required');
      return;
    }

    setSaving(true);
    try {
      const url = editingBranch ? `/api/branches/${editingBranch.id}` : '/api/branches';
      const method = editingBranch ? 'PUT' : 'POST';
      const res = await api(url, { method, body: JSON.stringify(form) });
      
      if (res.ok) {
        toast.success(editingBranch ? 'Branch updated' : 'Branch created');
        setShowModal(false);
        loadBranches();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Failed to save');
      }
    } catch (err) {
      toast.error('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Branches</h1>
          <p className="text-gray-400">Manage your retail locations</p>
        </div>
        <button onClick={() => openModal()} className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2" data-testid="add-branch-btn">
          <Plus className="h-5 w-5" /> Add Branch
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-red-400" />
          </div>
        ) : branches.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-400">
            <Building2 className="h-16 w-16 mx-auto mb-4 opacity-30" />
            <p>No branches yet</p>
          </div>
        ) : (
          branches.map(branch => (
            <div key={branch.id} className="bg-[#1a1214] border border-red-900/30 rounded-xl p-5 hover:border-red-700/50 transition-colors" data-testid={`branch-card-${branch.id}`}>
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${branch.is_warehouse ? 'bg-purple-900/30' : 'bg-red-900/30'}`}>
                    <Building2 className={`h-6 w-6 ${branch.is_warehouse ? 'text-purple-400' : 'text-red-400'}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{branch.name}</h3>
                    <span className="text-sm text-gray-400">{branch.code}</span>
                  </div>
                </div>
                <button onClick={() => openModal(branch)} className="p-2 text-blue-400 hover:bg-blue-900/20 rounded">
                  <Edit className="h-4 w-4" />
                </button>
              </div>
              
              <div className="space-y-2 text-sm text-gray-400">
                {branch.city && <div className="flex items-center gap-2"><MapPin className="h-4 w-4" />{branch.city}</div>}
                {branch.phone && <div className="flex items-center gap-2"><Phone className="h-4 w-4" />{branch.phone}</div>}
                <div className="flex items-center gap-2"><Users className="h-4 w-4" />{branch.employee_count || 0} employees</div>
              </div>

              <div className="mt-4 pt-3 border-t border-red-900/30 flex justify-between items-center">
                <span className={`text-xs px-2 py-1 rounded ${branch.is_warehouse ? 'bg-purple-900/30 text-purple-400' : 'bg-green-900/30 text-green-400'}`}>
                  {branch.is_warehouse ? 'Warehouse' : 'Retail'}
                </span>
                <div className="text-right">
                  <div className="text-xs text-gray-400">Cash Balance</div>
                  <div className="font-semibold text-amber-400">Rp {(branch.cash_balance || 0).toLocaleString()}</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-6 border-b border-red-900/30 flex justify-between items-center">
              <h2 className="text-xl font-bold">{editingBranch ? 'Edit Branch' : 'Add Branch'}</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white"><X className="h-6 w-6" /></button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Branch Code *</label>
                  <input type="text" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required disabled={!!editingBranch} />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Branch Name *</label>
                  <input type="text" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" required />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">City</label>
                <input type="text" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Address</label>
                <textarea value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Phone</label>
                  <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email</label>
                  <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="is_warehouse" checked={form.is_warehouse} onChange={(e) => setForm({ ...form, is_warehouse: e.target.checked })} className="w-4 h-4" />
                <label htmlFor="is_warehouse" className="text-sm text-gray-400">This is a warehouse (not a retail location)</label>
              </div>
              
              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-2 border border-red-900/30 rounded-lg hover:bg-red-900/20">Cancel</button>
                <button type="submit" disabled={saving} className="flex-1 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2">
                  {saving ? <Loader2 className="h-5 w-5 animate-spin" /> : <Save className="h-5 w-5" />}
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Branches;
