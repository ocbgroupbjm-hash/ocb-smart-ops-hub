import React, { useState, useEffect } from 'react';
import { Settings, Save, RefreshCw, Copy, ChevronDown, Package, ShoppingCart, Receipt, RotateCcw, Handshake, Wallet, MoreHorizontal, Building2, Warehouse, Tags, CreditCard, Percent, Check } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AccountSettingRow = ({ setting, chartOfAccounts, onUpdate }) => {
  const [accountCode, setAccountCode] = useState(setting.account_code);
  const [isChanged, setIsChanged] = useState(false);

  const handleChange = (code) => {
    setAccountCode(code);
    setIsChanged(code !== setting.account_code);
    const account = chartOfAccounts.find(a => a.code === code);
    if (account) {
      onUpdate(setting.account_key, code, account.name);
    }
  };

  return (
    <tr className="border-t border-gray-700 hover:bg-gray-700/30">
      <td className="px-4 py-3 text-gray-300">{setting.description || setting.account_key}</td>
      <td className="px-4 py-3">
        <Select value={accountCode} onValueChange={handleChange}>
          <SelectTrigger className="w-full bg-gray-900 border-gray-600">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="max-h-60">
            {chartOfAccounts.map(acc => (
              <SelectItem key={acc.code} value={acc.code}>
                {acc.code} - {acc.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </td>
      <td className="px-4 py-3 text-center">
        {isChanged && <span className="text-yellow-400 text-sm">*</span>}
      </td>
    </tr>
  );
};

const AccountMappingSection = ({ title, mappingType, items, references, chartOfAccounts, onAdd, onRefresh }) => {
  const [selectedRef, setSelectedRef] = useState('');
  const [selectedKey, setSelectedKey] = useState('');
  const [selectedAccount, setSelectedAccount] = useState('');

  const accountKeys = [
    { key: 'kas', label: 'Kas' },
    { key: 'bank', label: 'Bank' },
    { key: 'pendapatan', label: 'Pendapatan' },
    { key: 'hpp', label: 'HPP' },
    { key: 'persediaan', label: 'Persediaan' },
    { key: 'piutang', label: 'Piutang' },
    { key: 'hutang', label: 'Hutang' },
  ];

  const handleAdd = () => {
    if (!selectedRef || !selectedKey || !selectedAccount) {
      toast.error('Lengkapi semua field');
      return;
    }
    const ref = references.find(r => r.id === selectedRef);
    const acc = chartOfAccounts.find(a => a.code === selectedAccount);
    onAdd({
      reference_id: selectedRef,
      reference_name: ref?.name || '',
      account_key: selectedKey,
      account_code: selectedAccount,
      account_name: acc?.name || ''
    });
    setSelectedRef('');
    setSelectedKey('');
    setSelectedAccount('');
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
        <Select value={selectedRef} onValueChange={setSelectedRef}>
          <SelectTrigger className="w-48 bg-gray-900 border-gray-600">
            <SelectValue placeholder={`Pilih ${title}`} />
          </SelectTrigger>
          <SelectContent>
            {references.map(r => (
              <SelectItem key={r.id} value={r.id}>{r.name || r.code}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={selectedKey} onValueChange={setSelectedKey}>
          <SelectTrigger className="w-40 bg-gray-900 border-gray-600">
            <SelectValue placeholder="Jenis Akun" />
          </SelectTrigger>
          <SelectContent>
            {accountKeys.map(k => (
              <SelectItem key={k.key} value={k.key}>{k.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={selectedAccount} onValueChange={setSelectedAccount}>
          <SelectTrigger className="flex-1 bg-gray-900 border-gray-600">
            <SelectValue placeholder="Pilih Akun" />
          </SelectTrigger>
          <SelectContent>
            {chartOfAccounts.map(acc => (
              <SelectItem key={acc.code} value={acc.code}>{acc.code} - {acc.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button onClick={handleAdd} className="bg-green-600 hover:bg-green-700">
          Tambah
        </Button>
      </div>

      <table className="w-full">
        <thead className="bg-gray-900 text-gray-400 text-sm">
          <tr>
            <th className="px-4 py-3 text-left">{title}</th>
            <th className="px-4 py-3 text-left">Jenis Akun</th>
            <th className="px-4 py-3 text-left">Kode Akun</th>
            <th className="px-4 py-3 text-left">Nama Akun</th>
          </tr>
        </thead>
        <tbody className="text-white">
          {items.length === 0 ? (
            <tr><td colSpan="4" className="px-4 py-8 text-center text-gray-400">Belum ada mapping</td></tr>
          ) : (
            items.map((item, idx) => (
              <tr key={idx} className="border-t border-gray-700 hover:bg-gray-700/30">
                <td className="px-4 py-3">{item[`${mappingType}_name`] || item.reference_name}</td>
                <td className="px-4 py-3 text-gray-400">{item.account_key}</td>
                <td className="px-4 py-3 font-mono text-yellow-400">{item.account_code}</td>
                <td className="px-4 py-3">{item.account_name}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

const SettingAkunERP = () => {
  const [activeTab, setActiveTab] = useState('data_item');
  const [settings, setSettings] = useState({});
  const [chartOfAccounts, setChartOfAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pendingChanges, setPendingChanges] = useState({});
  
  // Mapping data
  const [branches, setBranches] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [branchMappings, setBranchMappings] = useState([]);
  const [warehouseMappings, setWarehouseMappings] = useState([]);
  const [categoryMappings, setCategoryMappings] = useState([]);
  const [paymentMappings, setPaymentMappings] = useState([]);
  const [taxMappings, setTaxMappings] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [settingsRes, coaRes, branchesRes, warehousesRes, categoriesRes] = await Promise.all([
        axios.get(`${API_URL}/api/account-settings/`, { headers }),
        axios.get(`${API_URL}/api/account-settings/chart-of-accounts`, { headers }),
        axios.get(`${API_URL}/api/branches`, { headers }).catch(() => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/master/warehouses`, { headers }).catch(() => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/master/categories`, { headers }).catch(() => ({ data: { items: [] } })),
      ]);

      setSettings(settingsRes.data.settings || {});
      setChartOfAccounts(coaRes.data.items || []);
      setBranches(branchesRes.data.items || branchesRes.data || []);
      setWarehouses(warehousesRes.data.items || warehousesRes.data || []);
      setCategories(categoriesRes.data.items || categoriesRes.data || []);

      // Payment methods
      setPaymentMethods([
        { id: 'cash', name: 'Tunai' },
        { id: 'debit', name: 'Kartu Debit' },
        { id: 'credit_card', name: 'Kartu Kredit' },
        { id: 'emoney', name: 'E-Money' },
        { id: 'qris', name: 'QRIS' },
        { id: 'transfer', name: 'Transfer Bank' },
      ]);

      // Fetch mappings
      const [branchMap, warehouseMap, categoryMap, paymentMap, taxMap] = await Promise.all([
        axios.get(`${API_URL}/api/account-settings/branch-mapping`, { headers }).catch(() => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/account-settings/warehouse-mapping`, { headers }).catch(() => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/account-settings/category-mapping`, { headers }).catch(() => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/account-settings/payment-mapping`, { headers }).catch(() => ({ data: { items: [] } })),
        axios.get(`${API_URL}/api/account-settings/tax-mapping`, { headers }).catch(() => ({ data: { items: [] } })),
      ]);

      setBranchMappings(branchMap.data.items || []);
      setWarehouseMappings(warehouseMap.data.items || []);
      setCategoryMappings(categoryMap.data.items || []);
      setPaymentMappings(paymentMap.data.items || []);
      setTaxMappings(taxMap.data.items || []);

    } catch (err) {
      console.error('Error fetching data:', err);
      toast.error('Gagal memuat data setting akun');
    } finally {
      setLoading(false);
    }
  };

  const handleAccountUpdate = (key, code, name) => {
    setPendingChanges(prev => ({
      ...prev,
      [key]: { account_code: code, account_name: name }
    }));
  };

  const handleSave = async () => {
    if (Object.keys(pendingChanges).length === 0) {
      toast.info('Tidak ada perubahan untuk disimpan');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      for (const [key, value] of Object.entries(pendingChanges)) {
        await axios.post(`${API_URL}/api/account-settings/`, {
          module: activeTab,
          account_key: key,
          account_code: value.account_code,
          account_name: value.account_name,
          tab_group: activeTab
        }, { headers });
      }

      toast.success('Setting akun berhasil disimpan');
      setPendingChanges({});
      fetchData();
    } catch (err) {
      toast.error('Gagal menyimpan setting akun');
    } finally {
      setSaving(false);
    }
  };

  const handleInitialize = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/api/account-settings/initialize-defaults`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Setting akun default berhasil diinisialisasi');
      fetchData();
    } catch (err) {
      toast.error('Gagal inisialisasi setting akun');
    }
  };

  const handleAddMapping = async (type, data) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/api/account-settings/${type}-mapping`, {
        mapping_type: type,
        ...data
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Mapping berhasil ditambahkan');
      fetchData();
    } catch (err) {
      toast.error('Gagal menambah mapping');
    }
  };

  const tabs = [
    { id: 'data_item', label: 'Data Item', icon: Package },
    { id: 'pembelian', label: 'Pembelian', icon: ShoppingCart },
    { id: 'penjualan_1', label: 'Penjualan', icon: Receipt },
    { id: 'penjualan_2', label: 'Penjualan 2', icon: RotateCcw },
    { id: 'kas_bank', label: 'Kas/Bank', icon: Wallet },
    { id: 'hutang_piutang', label: 'Hutang Piutang', icon: CreditCard },
    { id: 'operasional', label: 'Operasional', icon: MoreHorizontal },
    { id: 'konsinyasi', label: 'Konsinyasi', icon: Handshake },
    { id: 'lain_lain', label: 'Lain-lain', icon: MoreHorizontal },
    { id: 'cabang', label: 'Cabang', icon: Building2 },
    { id: 'gudang', label: 'Gudang', icon: Warehouse },
    { id: 'kategori', label: 'Kategori', icon: Tags },
    { id: 'payment', label: 'Payment', icon: CreditCard },
    { id: 'pajak', label: 'Pajak', icon: Percent },
  ];

  const renderTabContent = (tabId) => {
    const tabSettings = settings[tabId] || [];

    // Mapping tabs
    if (tabId === 'cabang') {
      return (
        <AccountMappingSection
          title="Cabang"
          mappingType="branch"
          items={branchMappings}
          references={branches}
          chartOfAccounts={chartOfAccounts}
          onAdd={(data) => handleAddMapping('branch', data)}
          onRefresh={fetchData}
        />
      );
    }
    if (tabId === 'gudang') {
      return (
        <AccountMappingSection
          title="Gudang"
          mappingType="warehouse"
          items={warehouseMappings}
          references={warehouses}
          chartOfAccounts={chartOfAccounts}
          onAdd={(data) => handleAddMapping('warehouse', data)}
          onRefresh={fetchData}
        />
      );
    }
    if (tabId === 'kategori') {
      return (
        <AccountMappingSection
          title="Kategori"
          mappingType="category"
          items={categoryMappings}
          references={categories}
          chartOfAccounts={chartOfAccounts}
          onAdd={(data) => handleAddMapping('category', data)}
          onRefresh={fetchData}
        />
      );
    }
    if (tabId === 'payment') {
      return (
        <AccountMappingSection
          title="Payment Method"
          mappingType="payment_method"
          items={paymentMappings}
          references={paymentMethods}
          chartOfAccounts={chartOfAccounts}
          onAdd={(data) => handleAddMapping('payment', data)}
          onRefresh={fetchData}
        />
      );
    }
    if (tabId === 'pajak') {
      const taxTypes = [
        { id: 'ppn', name: 'PPN' },
        { id: 'pph23', name: 'PPh 23' },
        { id: 'ppnbm', name: 'PPnBM' },
      ];
      return (
        <AccountMappingSection
          title="Jenis Pajak"
          mappingType="tax_type"
          items={taxMappings}
          references={taxTypes}
          chartOfAccounts={chartOfAccounts}
          onAdd={(data) => handleAddMapping('tax', data)}
          onRefresh={fetchData}
        />
      );
    }

    // Global setting tabs
    return (
      <table className="w-full">
        <thead className="bg-gray-900 text-gray-400 text-sm">
          <tr>
            <th className="px-4 py-3 text-left w-1/2">Deskripsi Akun</th>
            <th className="px-4 py-3 text-left">Akun Perkiraan</th>
            <th className="px-4 py-3 text-center w-12"></th>
          </tr>
        </thead>
        <tbody className="text-white">
          {tabSettings.length === 0 ? (
            <tr><td colSpan="3" className="px-4 py-8 text-center text-gray-400">Tidak ada setting. Klik "Inisialisasi Default" untuk setup awal.</td></tr>
          ) : (
            tabSettings.map((setting, idx) => (
              <AccountSettingRow
                key={setting.id || idx}
                setting={setting}
                chartOfAccounts={chartOfAccounts}
                onUpdate={handleAccountUpdate}
              />
            ))
          )}
        </tbody>
      </table>
    );
  };

  return (
    <div className="p-6" data-testid="setting-akun-erp">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-yellow-500" />
          Setting Akun ERP
        </h1>
        <div className="flex gap-2">
          <Button onClick={handleInitialize} variant="outline" className="border-gray-600">
            <RefreshCw className="w-4 h-4 mr-2" /> Inisialisasi Default
          </Button>
          <Button onClick={fetchData} variant="outline" className="border-gray-600">
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
          <Button onClick={handleSave} disabled={saving || Object.keys(pendingChanges).length === 0} className="bg-green-600 hover:bg-green-700">
            <Save className="w-4 h-4 mr-2" /> {saving ? 'Menyimpan...' : 'Simpan'}
          </Button>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-3 mb-6">
        <p className="text-blue-300 text-sm">
          <strong>Account Derivation Priority:</strong> Cabang → Gudang → Kategori → Payment Method → Global Setting
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-gray-400">Memuat data...</div>
      ) : (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <div className="border-b border-gray-700 overflow-x-auto">
              <TabsList className="bg-transparent p-0 h-auto flex-nowrap">
                {tabs.map(tab => (
                  <TabsTrigger
                    key={tab.id}
                    value={tab.id}
                    className="px-4 py-3 text-sm rounded-none border-b-2 border-transparent data-[state=active]:border-yellow-500 data-[state=active]:bg-gray-700/50 whitespace-nowrap"
                  >
                    <tab.icon className="w-4 h-4 mr-2" />
                    {tab.label}
                  </TabsTrigger>
                ))}
              </TabsList>
            </div>

            {tabs.map(tab => (
              <TabsContent key={tab.id} value={tab.id} className="p-4 m-0">
                {renderTabContent(tab.id)}
              </TabsContent>
            ))}
          </Tabs>
        </div>
      )}

      {/* Pending Changes Indicator */}
      {Object.keys(pendingChanges).length > 0 && (
        <div className="fixed bottom-6 right-6 bg-yellow-600 text-white px-4 py-2 rounded-lg shadow-lg">
          {Object.keys(pendingChanges).length} perubahan belum disimpan
        </div>
      )}
    </div>
  );
};

export default SettingAkunERP;
