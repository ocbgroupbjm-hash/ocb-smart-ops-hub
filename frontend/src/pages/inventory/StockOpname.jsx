import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Plus, Search, Loader2, Check, X, FileText, Package, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const StockOpname = () => {
  const { api } = useAuth();
  const [opnames, setOpnames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [branches, setBranches] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [opnameItems, setOpnameItems] = useState([]);
  const [notes, setNotes] = useState('');

  const loadOpnames = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api(`/api/inventory/opnames?search=${searchTerm}`);
      if (res.ok) {
        const data = await res.json();
        setOpnames(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm]);

  const loadMasterData = useCallback(async () => {
    try {
      const [branchRes, prodRes] = await Promise.all([
        api('/api/branches'),
        api('/api/products')
      ]);
      if (branchRes.ok) {
        const data = await branchRes.json();
        setBranches(data.items || data || []);
      }
      if (prodRes.ok) {
        const data = await prodRes.json();
        setProducts(data.items || data || []);
      }
    } catch (err) { console.error('Error loading master data'); }
  }, [api]);

  useEffect(() => {
    loadOpnames();
    loadMasterData();
  }, [loadOpnames, loadMasterData]);

  const handleStartOpname = async (branchId) => {
    setSelectedBranch(branchId);
    try {
      // Use correct endpoint: /api/inventory/stock (without 's')
      const res = await api(`/api/inventory/stock?branch_id=${branchId}&limit=500`);
      if (res.ok) {
        const data = await res.json();
        const stocks = data.items || [];
        if (stocks.length === 0) {
          // Fallback: get all products and set system_qty to 0
          const prodRes = await api('/api/products?limit=500');
          if (prodRes.ok) {
            const prodData = await prodRes.json();
            const prods = prodData.items || [];
            setOpnameItems(prods.map(p => ({
              product_id: p.id,
              product_name: p.name,
              product_code: p.code,
              system_qty: 0,
              actual_qty: 0,
              difference: 0
            })));
          }
        } else {
          setOpnameItems(stocks.map(s => ({
            product_id: s.product_id,
            product_name: s.product_name,
            product_code: s.product_code,
            system_qty: s.quantity || 0,
            actual_qty: s.quantity || 0,
            difference: 0
          })));
        }
      }
    } catch (err) { 
      console.error('Error loading stock:', err);
      toast.error('Gagal memuat stok'); 
    }
    setShowModal(true);
  };

  const updateActualQty = (index, qty) => {
    const newItems = [...opnameItems];
    newItems[index].actual_qty = qty;
    newItems[index].difference = qty - newItems[index].system_qty;
    setOpnameItems(newItems);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await api('/api/inventory/opnames', {
        method: 'POST',
        body: JSON.stringify({
          branch_id: selectedBranch,
          notes,
          items: opnameItems.map(i => ({
            product_id: i.product_id,
            system_qty: i.system_qty,
            actual_qty: i.actual_qty,
            difference: i.difference
          }))
        })
      });
      if (res.ok) {
        toast.success('Stok opname berhasil disimpan');
        setShowModal(false);
        setOpnameItems([]);
        setNotes('');
        loadOpnames();
      }
    } catch (err) {
      toast.error('Gagal menyimpan');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: 'bg-gray-600/20 text-gray-400',
      submitted: 'bg-blue-600/20 text-blue-400',
      approved: 'bg-green-600/20 text-green-400',
      rejected: 'bg-red-600/20 text-red-400'
    };
    const labels = { draft: 'Draft', submitted: 'Disubmit', approved: 'Disetujui', rejected: 'Ditolak' };
    return <span className={`px-2 py-1 rounded-full text-xs ${badges[status] || badges.draft}`}>{labels[status] || status}</span>;
  };

  return (
    <div className="space-y-4" data-testid="stock-opname-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Stok Opname</h1>
          <p className="text-gray-400 text-sm">Pencocokan stok fisik dengan sistem</p>
        </div>
        <div className="flex gap-2">
          {branches.slice(0, 3).map(b => (
            <button key={b.id} onClick={() => handleStartOpname(b.id)}
              className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg flex items-center gap-2 text-sm">
              <Plus className="h-4 w-4" /> Opname {b.name}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Cari opname..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. OPNAME</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">TANGGAL</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">CABANG</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">TOTAL ITEM</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-amber-200">SELISIH</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : opnames.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Belum ada data stok opname</td></tr>
              ) : opnames.map(opname => (
                <tr key={opname.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3 text-sm font-mono text-amber-300">{opname.opname_number || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-400">
                    {new Date(opname.created_at).toLocaleDateString('id-ID')}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-200">{opname.branch_name}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-300">{opname.total_items || 0}</td>
                  <td className="px-4 py-3 text-sm text-right">
                    <span className={opname.total_difference > 0 ? 'text-green-400' : opname.total_difference < 0 ? 'text-red-400' : 'text-gray-400'}>
                      {opname.total_difference > 0 ? '+' : ''}{opname.total_difference || 0}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">{getStatusBadge(opname.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Opname Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">Stok Opname</h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSubmit} className="p-4 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Catatan</label>
                <textarea value={notes} onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg" rows={2}
                  placeholder="Catatan tambahan untuk opname ini" />
              </div>
              
              <div className="border border-red-900/30 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-red-900/20">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs text-amber-200">PRODUK</th>
                      <th className="px-4 py-2 text-center text-xs text-amber-200">STOK SISTEM</th>
                      <th className="px-4 py-2 text-center text-xs text-amber-200">STOK FISIK</th>
                      <th className="px-4 py-2 text-center text-xs text-amber-200">SELISIH</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-red-900/20">
                    {opnameItems.length === 0 ? (
                      <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">Belum ada produk</td></tr>
                    ) : opnameItems.map((item, idx) => (
                      <tr key={idx} className={item.difference !== 0 ? 'bg-yellow-600/5' : ''}>
                        <td className="px-4 py-2">
                          <div className="flex items-center gap-2">
                            <Package className="h-4 w-4 text-gray-500" />
                            <span className="text-gray-200">{item.product_name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-2 text-center text-gray-400">{item.system_qty}</td>
                        <td className="px-4 py-2">
                          <input
                            type="number"
                            min="0"
                            value={item.actual_qty}
                            onChange={(e) => updateActualQty(idx, Number(e.target.value))}
                            className="w-24 px-2 py-1 bg-[#0a0608] border border-red-900/30 rounded text-center text-sm mx-auto block"
                          />
                        </td>
                        <td className="px-4 py-2 text-center">
                          {item.difference !== 0 && (
                            <span className={`flex items-center justify-center gap-1 ${item.difference > 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {item.difference > 0 ? '+' : ''}{item.difference}
                              <AlertTriangle className="h-3 w-3" />
                            </span>
                          )}
                          {item.difference === 0 && <span className="text-gray-500">0</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 border border-red-900/30 rounded-lg">Batal</button>
                <button type="submit" className="px-4 py-2 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg">
                  Simpan Opname
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockOpname;
