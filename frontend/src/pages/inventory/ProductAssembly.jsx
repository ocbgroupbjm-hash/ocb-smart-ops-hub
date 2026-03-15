import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Boxes, Plus, Loader2, Edit, Trash2, Play, Undo, Search, Package } from 'lucide-react';
import { toast } from 'sonner';

const ProductAssembly = () => {
  const { api } = useAuth();
  const [formulas, setFormulas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState([]);
  const [showFormModal, setShowFormModal] = useState(false);
  const [showAssembleModal, setShowAssembleModal] = useState(false);
  const [selectedFormula, setSelectedFormula] = useState(null);
  const [assemblyQty, setAssemblyQty] = useState(1);
  const [isDisassembly, setIsDisassembly] = useState(false);
  const [transactions, setTransactions] = useState([]);
  const [activeTab, setActiveTab] = useState('formulas');
  
  const [formData, setFormData] = useState({
    name: '',
    result_product_id: '',
    result_quantity: 1,
    components: [],
    notes: '',
    is_active: true
  });

  const [newComponent, setNewComponent] = useState({
    product_id: '',
    quantity: 1,
    unit: 'pcs'
  });

  // ============================================================
  // ENTERPRISE ASSEMBLY API - Using /api/assembly-enterprise/*
  // Legacy API /api/assembly/* still works for backward compatibility
  // ============================================================
  
  const API_PREFIX = '/api/assembly-enterprise'; // Enterprise API
  const API_LEGACY = '/api/assembly'; // Legacy fallback

  useEffect(() => {
    loadFormulas();
    loadProducts();
    loadTransactions();
  }, []);

  const loadFormulas = async () => {
    setLoading(true);
    try {
      // Try enterprise API first, fallback to legacy
      let res = await api(`${API_PREFIX}/formulas/v2?status=ALL`);
      if (!res.ok) {
        res = await api(`${API_LEGACY}/formulas`);
      }
      if (res.ok) {
        const data = await res.json();
        setFormulas(data.formulas || []);
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const loadProducts = async () => {
    try {
      const res = await api('/api/products?limit=500');
      if (res.ok) {
        const data = await res.json();
        setProducts(data.items || []);
      }
    } catch (err) { console.error(err); }
  };

  const loadTransactions = async () => {
    try {
      // Try enterprise API first, fallback to legacy
      let res = await api(`${API_PREFIX}/history/v2?status=ALL`);
      if (!res.ok) {
        res = await api(`${API_LEGACY}/transactions?limit=50`);
      }
      if (res.ok) {
        const data = await res.json();
        setTransactions(data.transactions || []);
      }
    } catch (err) { console.error(err); }
  };

  const addComponent = () => {
    if (!newComponent.product_id || newComponent.quantity < 1) {
      toast.error('Pilih produk dan masukkan jumlah');
      return;
    }
    const product = products.find(p => p.id === newComponent.product_id);
    setFormData({
      ...formData,
      components: [...formData.components, {
        ...newComponent,
        product_name: product?.name,
        product_code: product?.code
      }]
    });
    setNewComponent({ product_id: '', quantity: 1, unit: 'pcs' });
  };

  const removeComponent = (index) => {
    setFormData({
      ...formData,
      components: formData.components.filter((_, i) => i !== index)
    });
  };

  const saveFormula = async () => {
    if (!formData.name || !formData.result_product_id || formData.components.length === 0) {
      toast.error('Lengkapi semua data');
      return;
    }
    try {
      const method = selectedFormula ? 'PUT' : 'POST';
      
      // Use enterprise API for create/update
      let url;
      let payload;
      
      if (selectedFormula) {
        url = `${API_PREFIX}/formulas/v2/${selectedFormula.id}`;
        payload = {
          formula_name: formData.name,
          product_result_id: formData.result_product_id,
          result_quantity: formData.result_quantity,
          components: formData.components.map((c, i) => ({
            item_id: c.product_id,
            quantity_required: c.quantity,
            uom: c.unit || 'pcs',
            sequence_no: i + 1
          })),
          notes: formData.notes,
          status: formData.is_active ? 'ACTIVE' : 'INACTIVE'
        };
      } else {
        url = `${API_PREFIX}/formulas/v2`;
        payload = {
          formula_name: formData.name,
          product_result_id: formData.result_product_id,
          result_quantity: formData.result_quantity,
          uom: 'pcs',
          components: formData.components.map((c, i) => ({
            item_id: c.product_id,
            quantity_required: c.quantity,
            uom: c.unit || 'pcs',
            sequence_no: i + 1
          })),
          notes: formData.notes
        };
      }
      
      const res = await api(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        toast.success(selectedFormula ? 'Formula diupdate' : 'Formula dibuat');
        setShowFormModal(false);
        resetForm();
        loadFormulas();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Gagal menyimpan');
      }
    } catch (err) { toast.error('Gagal menyimpan'); }
  };

  const deleteFormula = async (id) => {
    // HARD DELETE - Confirm with user
    if (!window.confirm('HAPUS PERMANEN formula voucher ini?\n\nPerhatian: Data akan dihapus selamanya dan tidak dapat dikembalikan.')) return;
    
    try {
      // Use HARD DELETE endpoint (will validate if used in transactions)
      const res = await api(`${API_PREFIX}/formulas/v2/${id}/hard-delete`, { method: 'DELETE' });
      
      if (res.ok) {
        toast.success('Formula voucher berhasil dihapus permanen');
        loadFormulas();
      } else {
        const err = await res.json();
        // Check if validation error (voucher used in transactions)
        if (err.detail && err.detail.includes('digunakan pada transaksi')) {
          toast.error(err.detail);
        } else if (err.detail && err.detail.includes('used in')) {
          toast.error('Voucher sudah digunakan pada transaksi dan tidak dapat dihapus.');
        } else {
          // Fallback to legacy delete
          const legacyRes = await api(`${API_LEGACY}/formulas/${id}`, { method: 'DELETE' });
          if (legacyRes.ok) {
            toast.success('Formula voucher dihapus');
            loadFormulas();
          } else {
            const legacyErr = await legacyRes.json();
            toast.error(legacyErr.detail || 'Gagal menghapus formula voucher');
          }
        }
      }
    } catch (err) { 
      toast.error('Gagal menghapus formula voucher'); 
    }
  };

  const processAssembly = async () => {
    if (assemblyQty < 1) {
      toast.error('Jumlah minimal 1');
      return;
    }
    try {
      // Use enterprise API for assembly execution
      const endpoint = isDisassembly 
        ? `${API_LEGACY}/disassemble` // Disassembly still uses legacy for now
        : `${API_PREFIX}/execute/v2`;
      
      const payload = isDisassembly 
        ? { formula_id: selectedFormula.id, quantity: assemblyQty, notes: '' }
        : { 
            formula_id: selectedFormula.id, 
            planned_qty: assemblyQty, 
            notes: '',
            save_as_draft: false // Direct POST instead of DRAFT
          };
      
      const res = await api(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        setShowAssembleModal(false);
        setSelectedFormula(null);
        setAssemblyQty(1);
        loadTransactions();
      } else {
        const err = await res.json();
        // Handle detailed error for stock insufficient
        if (err.detail?.items) {
          const items = err.detail.items.map(i => `${i.item_name}: butuh ${i.required}, ada ${i.available}`).join('\n');
          toast.error(`Stok tidak cukup:\n${items}`);
        } else {
          toast.error(err.detail?.message || err.detail || 'Proses gagal');
        }
      }
    } catch (err) { toast.error('Proses gagal'); }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      result_product_id: '',
      result_quantity: 1,
      components: [],
      notes: '',
      is_active: true
    });
    setSelectedFormula(null);
  };

  const editFormula = (formula) => {
    setSelectedFormula(formula);
    setFormData({
      name: formula.name,
      result_product_id: formula.result_product_id,
      result_quantity: formula.result_quantity,
      components: formula.components || [],
      notes: formula.notes || '',
      is_active: formula.is_active
    });
    setShowFormModal(true);
  };

  const openAssemble = (formula, disassembly = false) => {
    setSelectedFormula(formula);
    setIsDisassembly(disassembly);
    setAssemblyQty(1);
    setShowAssembleModal(true);
  };

  const formatRupiah = (num) => `Rp ${(num || 0).toLocaleString('id-ID')}`;

  return (
    <div className="space-y-6" data-testid="assembly-voucher-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Perakitan Voucher</h1>
          <p className="text-gray-400">Kelola formula perakitan voucher dan komponen</p>
        </div>
        <button
          onClick={() => { resetForm(); setShowFormModal(true); }}
          className="px-4 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 flex items-center gap-2"
          data-testid="add-voucher-btn"
        >
          <Plus className="h-4 w-4" /> Tambah Perakitan Voucher
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        <button
          onClick={() => setActiveTab('formulas')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${activeTab === 'formulas' ? 'bg-red-900/30 text-amber-400' : 'text-gray-400 hover:text-white'}`}
          data-testid="tab-formula-voucher"
        >
          Formula Voucher
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 rounded-t-lg transition-colors ${activeTab === 'history' ? 'bg-red-900/30 text-amber-400' : 'text-gray-400 hover:text-white'}`}
          data-testid="tab-history"
        >
          Riwayat Transaksi
        </button>
      </div>

      {/* Formulas Tab */}
      {activeTab === 'formulas' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading ? (
            <div className="col-span-full text-center py-8">
              <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
            </div>
          ) : formulas.length === 0 ? (
            <div className="col-span-full text-center py-8 text-gray-400">
              <Boxes className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>Belum ada formula voucher</p>
            </div>
          ) : (
            formulas.map((formula) => (
              <div key={formula.id} className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-amber-100">{formula.name}</h3>
                    <p className="text-sm text-gray-400">Hasil: {formula.result_product_name}</p>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => editFormula(formula)} className="p-1 text-blue-400 hover:bg-blue-600/20 rounded">
                      <Edit className="h-4 w-4" />
                    </button>
                    <button onClick={() => deleteFormula(formula.id)} className="p-1 text-red-400 hover:bg-red-600/20 rounded">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                
                <div className="text-sm text-gray-400 mb-3">
                  <div className="font-medium text-white mb-1">Komponen:</div>
                  {formula.components?.map((comp, idx) => (
                    <div key={idx} className="flex justify-between">
                      <span>{comp.product_name}</span>
                      <span>{comp.quantity} {comp.unit}</span>
                    </div>
                  ))}
                </div>

                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => openAssemble(formula, false)}
                    className="flex-1 px-3 py-2 bg-green-600/20 text-green-400 rounded-lg hover:bg-green-600/30 flex items-center justify-center gap-1 text-sm"
                  >
                    <Play className="h-4 w-4" /> Rakit
                  </button>
                  <button
                    onClick={() => openAssemble(formula, true)}
                    className="flex-1 px-3 py-2 bg-amber-600/20 text-amber-400 rounded-lg hover:bg-amber-600/30 flex items-center justify-center gap-1 text-sm"
                  >
                    <Undo className="h-4 w-4" /> Bongkar
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">No. Transaksi</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Formula</th>
                <th className="px-4 py-3 text-center text-sm font-semibold">Tipe</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Qty</th>
                <th className="px-4 py-3 text-right text-sm font-semibold">Biaya</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Tanggal</th>
              </tr>
            </thead>
            <tbody>
              {transactions.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Tidak ada transaksi</td></tr>
              ) : (
                transactions.map((tx) => (
                  <tr key={tx.id} className="border-t border-red-900/10 hover:bg-red-900/10">
                    <td className="px-4 py-3 font-mono text-amber-300">{tx.assembly_number}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{tx.formula_name}</div>
                      <div className="text-sm text-gray-400">{tx.result_product_name}</div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        tx.type === 'assembly' ? 'bg-green-600/20 text-green-400' : 'bg-amber-600/20 text-amber-400'
                      }`}>
                        {tx.type === 'assembly' ? 'Rakitan' : 'Bongkar'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-semibold">{tx.result_quantity}</td>
                    <td className="px-4 py-3 text-right">{formatRupiah(tx.total_cost)}</td>
                    <td className="px-4 py-3 text-gray-400">{new Date(tx.created_at).toLocaleString('id-ID')}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Formula Modal */}
      {showFormModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6 w-[600px] max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-amber-100 mb-4">
              {selectedFormula ? 'Edit Formula' : 'Buat Formula Rakitan'}
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Formula *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  placeholder="Paket Komputer Gaming"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Produk Hasil *</label>
                  <select
                    value={formData.result_product_id}
                    onChange={(e) => setFormData({ ...formData, result_product_id: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  >
                    <option value="">Pilih Produk</option>
                    {products.map(p => (
                      <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Jumlah Hasil</label>
                  <input
                    type="number"
                    value={formData.result_quantity}
                    onChange={(e) => setFormData({ ...formData, result_quantity: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    min={1}
                  />
                </div>
              </div>

              {/* Components */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">Komponen *</label>
                <div className="space-y-2 mb-3">
                  {formData.components.map((comp, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-2 bg-[#0a0608] rounded-lg">
                      <Package className="h-4 w-4 text-amber-400" />
                      <span className="flex-1">{comp.product_name}</span>
                      <span className="text-gray-400">{comp.quantity} {comp.unit}</span>
                      <button onClick={() => removeComponent(idx)} className="text-red-400 hover:text-red-300">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <select
                    value={newComponent.product_id}
                    onChange={(e) => setNewComponent({ ...newComponent, product_id: e.target.value })}
                    className="flex-1 px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  >
                    <option value="">Pilih Komponen</option>
                    {products.map(p => (
                      <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                    ))}
                  </select>
                  <input
                    type="number"
                    value={newComponent.quantity}
                    onChange={(e) => setNewComponent({ ...newComponent, quantity: Number(e.target.value) })}
                    className="w-24 px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                    min={1}
                    placeholder="Qty"
                  />
                  <button onClick={addComponent} className="px-3 py-2 bg-blue-600 text-white rounded-lg">
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => { setShowFormModal(false); resetForm(); }} className="px-4 py-2 bg-gray-600 text-white rounded-lg">Batal</button>
              <button onClick={saveFormula} className="px-4 py-2 bg-green-600 text-white rounded-lg">Simpan</button>
            </div>
          </div>
        </div>
      )}

      {/* Assemble/Disassemble Modal */}
      {showAssembleModal && selectedFormula && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6 w-[400px]">
            <h2 className="text-xl font-bold text-amber-100 mb-4">
              {isDisassembly ? 'Pembongkaran' : 'Proses Rakitan'}: {selectedFormula.name}
            </h2>
            <div className="space-y-4">
              <div className="p-3 bg-[#0a0608] rounded-lg">
                <div className="text-sm text-gray-400 mb-2">
                  {isDisassembly ? 'Produk yang akan dibongkar:' : 'Produk yang akan dihasilkan:'}
                </div>
                <div className="font-medium text-amber-100">{selectedFormula.result_product_name}</div>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah Siklus</label>
                <input
                  type="number"
                  value={assemblyQty}
                  onChange={(e) => setAssemblyQty(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg"
                  min={1}
                />
              </div>

              <div className="p-3 bg-amber-900/20 rounded-lg text-sm">
                {isDisassembly ? (
                  <p className="text-amber-400">
                    Akan membongkar {assemblyQty * selectedFormula.result_quantity} {selectedFormula.result_product_name} menjadi komponen-komponennya.
                  </p>
                ) : (
                  <p className="text-amber-400">
                    Akan menghasilkan {assemblyQty * selectedFormula.result_quantity} {selectedFormula.result_product_name}
                  </p>
                )}
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowAssembleModal(false)} className="px-4 py-2 bg-gray-600 text-white rounded-lg">Batal</button>
              <button 
                onClick={processAssembly} 
                className={`px-4 py-2 ${isDisassembly ? 'bg-amber-600' : 'bg-green-600'} text-white rounded-lg`}
              >
                {isDisassembly ? 'Bongkar' : 'Rakit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductAssembly;
