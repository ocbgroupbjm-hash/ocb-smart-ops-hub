import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Star, Search, Plus, Edit2, Trash2, Loader2, X, Gift, 
  Settings, ArrowUpCircle, ArrowDownCircle, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';

const MasterCustomerPoints = () => {
  const { api } = useAuth();
  const [customers, setCustomers] = useState([]);
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('customers'); // customers, rules, transactions
  
  // Customer detail modal
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerDetail, setCustomerDetail] = useState(null);
  
  // Rule modal
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [ruleForm, setRuleForm] = useState({
    name: '',
    rule_type: 'earn',
    points_per_amount: 10000,
    min_transaction: 50000,
    multiplier: 1,
    point_value: 100,
    min_redeem: 100,
    max_redeem_percent: 50,
    is_active: true,
    description: ''
  });

  // Adjustment modal
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [adjustForm, setAdjustForm] = useState({
    customer_id: '',
    points: 0,
    description: ''
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [custRes, rulesRes] = await Promise.all([
        api(`/api/loyalty/customers?search=${searchTerm}`),
        api('/api/loyalty/rules')
      ]);
      
      if (custRes.ok) setCustomers(await custRes.json());
      if (rulesRes.ok) setRules(await rulesRes.json());
    } catch (err) { 
      toast.error('Gagal memuat data'); 
    }
    finally { setLoading(false); }
  }, [api, searchTerm]);

  useEffect(() => { loadData(); }, [loadData]);

  const loadCustomerDetail = async (customerId) => {
    try {
      const res = await api(`/api/loyalty/customers/${customerId}`);
      if (res.ok) {
        const data = await res.json();
        setCustomerDetail(data);
        setSelectedCustomer(customerId);
      }
    } catch (err) {
      toast.error('Gagal memuat detail pelanggan');
    }
  };

  const handleSaveRule = async (e) => {
    e.preventDefault();
    try {
      const url = editingRule ? `/api/loyalty/rules/${editingRule.id}` : '/api/loyalty/rules';
      const res = await api(url, { 
        method: editingRule ? 'PUT' : 'POST', 
        body: JSON.stringify(ruleForm) 
      });
      if (res.ok) { 
        toast.success(editingRule ? 'Rule diupdate' : 'Rule ditambahkan'); 
        setShowRuleModal(false);
        resetRuleForm();
        loadData(); 
      }
    } catch (err) { toast.error('Gagal menyimpan'); }
  };

  const handleDeleteRule = async (rule) => {
    if (!confirm(`Hapus rule "${rule.name}"?`)) return;
    try {
      await api(`/api/loyalty/rules/${rule.id}`, { method: 'DELETE' });
      toast.success('Rule dihapus');
      loadData();
    } catch { toast.error('Gagal menghapus'); }
  };

  const handleAdjustPoints = async (e) => {
    e.preventDefault();
    try {
      const res = await api('/api/loyalty/adjust', {
        method: 'POST',
        body: JSON.stringify({
          customer_id: adjustForm.customer_id,
          transaction_type: 'adjustment',
          points: adjustForm.points,
          reference_type: 'manual',
          description: adjustForm.description
        })
      });
      if (res.ok) {
        toast.success('Point berhasil disesuaikan');
        setShowAdjustModal(false);
        setAdjustForm({ customer_id: '', points: 0, description: '' });
        loadData();
        if (selectedCustomer) loadCustomerDetail(selectedCustomer);
      }
    } catch (err) { toast.error('Gagal menyesuaikan point'); }
  };

  const resetRuleForm = () => {
    setEditingRule(null);
    setRuleForm({
      name: '', rule_type: 'earn', points_per_amount: 10000, min_transaction: 50000,
      multiplier: 1, point_value: 100, min_redeem: 100, max_redeem_percent: 50,
      is_active: true, description: ''
    });
  };

  const editRule = (rule) => {
    setEditingRule(rule);
    setRuleForm({
      name: rule.name || '',
      rule_type: rule.rule_type || 'earn',
      points_per_amount: rule.points_per_amount || 10000,
      min_transaction: rule.min_transaction || 50000,
      multiplier: rule.multiplier || 1,
      point_value: rule.point_value || 100,
      min_redeem: rule.min_redeem || 100,
      max_redeem_percent: rule.max_redeem_percent || 50,
      is_active: rule.is_active !== false,
      description: rule.description || ''
    });
    setShowRuleModal(true);
  };

  const formatCurrency = (num) => new Intl.NumberFormat('id-ID').format(num || 0);

  return (
    <div className="space-y-4" data-testid="loyalty-points-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
            <Star className="h-6 w-6 text-yellow-400" />
            Customer Loyalty Points
          </h1>
          <p className="text-gray-400 text-sm">Sistem poin pelanggan untuk reward & loyalty</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="border-red-900/30" onClick={() => setShowAdjustModal(true)}>
            <RefreshCw className="h-4 w-4 mr-2" /> Adjust Point
          </Button>
          <Button onClick={() => { resetRuleForm(); setShowRuleModal(true); }} className="bg-gradient-to-r from-red-600 to-amber-600">
            <Settings className="h-4 w-4 mr-2" /> Kelola Rules
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-red-900/30 pb-2">
        {[
          { id: 'customers', label: 'Pelanggan', icon: Gift },
          { id: 'rules', label: 'Point Rules', icon: Settings },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
              activeTab === tab.id 
                ? 'bg-amber-600/20 text-amber-200' 
                : 'text-gray-400 hover:bg-red-900/20'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'customers' && (
        <>
          {/* Search */}
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input 
                placeholder="Cari pelanggan..." 
                value={searchTerm} 
                onChange={(e) => setSearchTerm(e.target.value)} 
                className="pl-10 bg-[#0a0608] border-red-900/30"
              />
            </div>
          </div>

          {/* Customers Table */}
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead className="bg-red-900/20">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">PELANGGAN</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">SALDO POINT</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">TOTAL EARNED</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">TOTAL REDEEMED</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-900/20">
                {loading ? (
                  <tr><td colSpan={5} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
                ) : customers.length === 0 ? (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Belum ada data pelanggan dengan point</td></tr>
                ) : customers.map(cust => (
                  <tr key={cust.customer_id} className="hover:bg-red-900/10">
                    <td className="px-4 py-3">
                      <div>
                        <span className="font-medium text-gray-200">{cust.customer_name || 'N/A'}</span>
                        <span className="text-xs text-gray-500 ml-2">{cust.customer_code}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="px-3 py-1 bg-yellow-600/20 text-yellow-400 rounded-full font-semibold">
                        {formatCurrency(cust.current_points)} pts
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center text-green-400">
                      +{formatCurrency(cust.total_earned)}
                    </td>
                    <td className="px-4 py-3 text-center text-red-400">
                      -{formatCurrency(cust.total_redeemed)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Button 
                        size="sm" 
                        variant="outline" 
                        className="border-red-900/30"
                        onClick={() => loadCustomerDetail(cust.customer_id)}
                      >
                        Detail
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {activeTab === 'rules' && (
        <>
          <div className="flex justify-end">
            <Button onClick={() => { resetRuleForm(); setShowRuleModal(true); }} className="bg-gradient-to-r from-red-600 to-amber-600">
              <Plus className="h-4 w-4 mr-2" /> Tambah Rule
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {rules.map(rule => (
              <div key={rule.id} className={`bg-[#1a1214] border rounded-xl p-4 ${
                rule.rule_type === 'earn' ? 'border-green-600/30' : 'border-purple-600/30'
              }`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {rule.rule_type === 'earn' ? (
                      <ArrowUpCircle className="h-5 w-5 text-green-400" />
                    ) : (
                      <ArrowDownCircle className="h-5 w-5 text-purple-400" />
                    )}
                    <div>
                      <h3 className="font-semibold text-gray-200">{rule.name}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        rule.rule_type === 'earn' ? 'bg-green-600/20 text-green-400' : 'bg-purple-600/20 text-purple-400'
                      }`}>
                        {rule.rule_type === 'earn' ? 'EARN' : 'REDEEM'}
                      </span>
                    </div>
                  </div>
                  {!rule.is_default && (
                    <div className="flex gap-1">
                      <button onClick={() => editRule(rule)} className="p-1.5 hover:bg-blue-600/20 rounded">
                        <Edit2 className="h-4 w-4 text-blue-400" />
                      </button>
                      <button onClick={() => handleDeleteRule(rule)} className="p-1.5 hover:bg-red-600/20 rounded">
                        <Trash2 className="h-4 w-4 text-red-400" />
                      </button>
                    </div>
                  )}
                </div>
                
                {rule.rule_type === 'earn' ? (
                  <div className="space-y-1 text-sm text-gray-400">
                    <p>Rp {formatCurrency(rule.points_per_amount)} = <span className="text-yellow-400">1 point</span></p>
                    <p>Min. transaksi: Rp {formatCurrency(rule.min_transaction)}</p>
                    <p>Multiplier: {rule.multiplier}x</p>
                  </div>
                ) : (
                  <div className="space-y-1 text-sm text-gray-400">
                    <p>{rule.point_value} point = <span className="text-green-400">Rp 10.000</span></p>
                    <p>Min. redeem: {rule.min_redeem} point</p>
                    <p>Max. discount: {rule.max_redeem_percent}% dari transaksi</p>
                  </div>
                )}
                
                <div className="mt-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    rule.is_active ? 'bg-green-600/20 text-green-400' : 'bg-gray-600/20 text-gray-400'
                  }`}>
                    {rule.is_active ? 'Aktif' : 'Nonaktif'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Customer Detail Modal */}
      {selectedCustomer && customerDetail && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg max-h-[80vh] overflow-y-auto">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between sticky top-0 bg-[#1a1214]">
              <h2 className="text-lg font-semibold text-amber-100">Detail Point Pelanggan</h2>
              <button onClick={() => { setSelectedCustomer(null); setCustomerDetail(null); }} className="p-1 hover:bg-red-900/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div className="text-center">
                <h3 className="text-xl font-bold text-gray-200">{customerDetail.customer?.name}</h3>
                <p className="text-gray-500">{customerDetail.customer?.code}</p>
                <div className="mt-4 p-4 bg-yellow-600/10 rounded-xl">
                  <Star className="h-8 w-8 text-yellow-400 mx-auto mb-2" />
                  <p className="text-3xl font-bold text-yellow-400">{formatCurrency(customerDetail.current_points)}</p>
                  <p className="text-gray-400 text-sm">Point Tersedia</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-green-600/10 rounded-lg text-center">
                  <p className="text-green-400 font-semibold">+{formatCurrency(customerDetail.total_earned)}</p>
                  <p className="text-xs text-gray-500">Total Earned</p>
                </div>
                <div className="p-3 bg-red-600/10 rounded-lg text-center">
                  <p className="text-red-400 font-semibold">-{formatCurrency(customerDetail.total_redeemed)}</p>
                  <p className="text-xs text-gray-500">Total Redeemed</p>
                </div>
              </div>

              <div>
                <h4 className="text-amber-200 font-semibold mb-2">Riwayat Transaksi</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {customerDetail.recent_transactions?.length === 0 ? (
                    <p className="text-gray-500 text-sm text-center py-4">Belum ada transaksi</p>
                  ) : (
                    customerDetail.recent_transactions?.map(trans => (
                      <div key={trans.id} className="flex items-center justify-between p-2 bg-[#0a0608] rounded">
                        <div>
                          <span className={`text-sm font-medium ${trans.points > 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {trans.points > 0 ? '+' : ''}{trans.points} pts
                          </span>
                          <p className="text-xs text-gray-500">{trans.description}</p>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(trans.created_at).toLocaleDateString('id-ID')}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Rule Modal */}
      {showRuleModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">{editingRule ? 'Edit' : 'Tambah'} Point Rule</h2>
              <button onClick={() => setShowRuleModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleSaveRule} className="p-4 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Nama Rule *</label>
                <Input value={ruleForm.name} onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })} 
                  className="bg-[#0a0608] border-red-900/30" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Tipe Rule</label>
                <Select value={ruleForm.rule_type} onValueChange={(v) => setRuleForm({ ...ruleForm, rule_type: v })}>
                  <SelectTrigger className="bg-[#0a0608] border-red-900/30"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="earn">Earn (Dapat Point)</SelectItem>
                    <SelectItem value="redeem">Redeem (Tukar Point)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {ruleForm.rule_type === 'earn' ? (
                <>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Rupiah per 1 Point</label>
                    <Input type="number" value={ruleForm.points_per_amount} 
                      onChange={(e) => setRuleForm({ ...ruleForm, points_per_amount: Number(e.target.value) })}
                      className="bg-[#0a0608] border-red-900/30" />
                    <p className="text-xs text-gray-500 mt-1">Contoh: 10000 = setiap Rp 10.000 dapat 1 point</p>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Min. Transaksi</label>
                    <Input type="number" value={ruleForm.min_transaction}
                      onChange={(e) => setRuleForm({ ...ruleForm, min_transaction: Number(e.target.value) })}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Multiplier</label>
                    <Input type="number" step="0.1" value={ruleForm.multiplier}
                      onChange={(e) => setRuleForm({ ...ruleForm, multiplier: Number(e.target.value) })}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Point Value (point per Rp 10.000)</label>
                    <Input type="number" value={ruleForm.point_value}
                      onChange={(e) => setRuleForm({ ...ruleForm, point_value: Number(e.target.value) })}
                      className="bg-[#0a0608] border-red-900/30" />
                    <p className="text-xs text-gray-500 mt-1">Contoh: 100 = 100 point bernilai Rp 10.000</p>
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Min. Redeem (point)</label>
                    <Input type="number" value={ruleForm.min_redeem}
                      onChange={(e) => setRuleForm({ ...ruleForm, min_redeem: Number(e.target.value) })}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Max Discount (%)</label>
                    <Input type="number" value={ruleForm.max_redeem_percent}
                      onChange={(e) => setRuleForm({ ...ruleForm, max_redeem_percent: Number(e.target.value) })}
                      className="bg-[#0a0608] border-red-900/30" />
                  </div>
                </>
              )}

              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={ruleForm.is_active} 
                  onChange={(e) => setRuleForm({ ...ruleForm, is_active: e.target.checked })} className="w-4 h-4" />
                <span className="text-sm text-gray-300">Aktif</span>
              </label>

              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <Button type="button" variant="outline" onClick={() => setShowRuleModal(false)} className="border-red-900/30">Batal</Button>
                <Button type="submit" className="bg-gradient-to-r from-red-600 to-amber-600">{editingRule ? 'Update' : 'Simpan'}</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Adjust Point Modal */}
      {showAdjustModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-md">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">Adjust Point Manual</h2>
              <button onClick={() => setShowAdjustModal(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <form onSubmit={handleAdjustPoints} className="p-4 space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Pelanggan *</label>
                <select
                  value={adjustForm.customer_id}
                  onChange={(e) => setAdjustForm({ ...adjustForm, customer_id: e.target.value })}
                  className="w-full px-3 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
                  required
                >
                  <option value="">Pilih Pelanggan</option>
                  {customers.map(c => (
                    <option key={c.customer_id} value={c.customer_id}>{c.customer_name} ({c.current_points} pts)</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Jumlah Point (- untuk mengurangi)</label>
                <Input type="number" value={adjustForm.points}
                  onChange={(e) => setAdjustForm({ ...adjustForm, points: Number(e.target.value) })}
                  className="bg-[#0a0608] border-red-900/30" required />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Keterangan</label>
                <Input value={adjustForm.description}
                  onChange={(e) => setAdjustForm({ ...adjustForm, description: e.target.value })}
                  className="bg-[#0a0608] border-red-900/30" placeholder="Alasan adjustment" />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-red-900/30">
                <Button type="button" variant="outline" onClick={() => setShowAdjustModal(false)} className="border-red-900/30">Batal</Button>
                <Button type="submit" className="bg-gradient-to-r from-red-600 to-amber-600">Simpan</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MasterCustomerPoints;
