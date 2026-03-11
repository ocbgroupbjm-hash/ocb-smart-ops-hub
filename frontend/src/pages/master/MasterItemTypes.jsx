import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Search, Package } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MasterItemTypes = () => {
  
  const [types, setTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState(null);
  const [search, setSearch] = useState('');
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: ''
  });

  useEffect(() => {
    fetchTypes();
  }, []);

  const fetchTypes = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/api/master/item-types`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTypes(res.data.items || res.data || []);
    } catch (err) {
      // Default item types if not yet in database
      setTypes([
        { id: '1', code: 'AKS', name: 'Aksesoris', description: 'Aksesoris HP dan gadget' },
        { id: '2', code: 'PLS', name: 'Pulsa', description: 'Pulsa dan voucher' },
        { id: '3', code: 'KOT', name: 'Kuota', description: 'Paket data internet' },
        { id: '4', code: 'HP', name: 'Handphone', description: 'Handphone dan smartphone' },
        { id: '5', code: 'TAB', name: 'Tablet', description: 'Tablet dan iPad' },
        { id: '6', code: 'LAP', name: 'Laptop', description: 'Laptop dan notebook' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      if (editId) {
        await axios.put(`${API_URL}/api/master/item-types/${editId}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Jenis barang berhasil diupdate');
      } else {
        await axios.post(`${API_URL}/api/master/item-types`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Jenis barang berhasil ditambahkan');
      }
      fetchTypes();
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal menyimpan');
    }
  };

  const handleEdit = (item) => {
    setFormData({ code: item.code, name: item.name, description: item.description || '' });
    setEditId(item.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Hapus jenis barang ini?')) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/master/item-types/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Jenis barang dihapus');
      fetchTypes();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Gagal menghapus');
    }
  };

  const resetForm = () => {
    setFormData({ code: '', name: '', description: '' });
    setEditId(null);
    setShowForm(false);
  };

  const filteredTypes = types.filter(t =>
    t.name?.toLowerCase().includes(search.toLowerCase()) ||
    t.code?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-6" data-testid="master-item-types">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Package className="w-6 h-6 text-yellow-500" />
          Jenis Barang
        </h1>
        <Button onClick={() => setShowForm(true)} className="bg-yellow-600 hover:bg-yellow-700">
          <Plus className="w-4 h-4 mr-2" /> Tambah Jenis
        </Button>
      </div>

      {showForm && (
        <div className="bg-gray-800 rounded-lg p-6 mb-6 border border-gray-700">
          <h2 className="text-lg font-semibold mb-4 text-white">
            {editId ? 'Edit Jenis Barang' : 'Tambah Jenis Barang'}
          </h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-3 gap-4">
            <Input
              placeholder="Kode Jenis"
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value })}
              required
              className="bg-gray-900 border-gray-700"
            />
            <Input
              placeholder="Nama Jenis"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className="bg-gray-900 border-gray-700"
            />
            <Input
              placeholder="Deskripsi"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="bg-gray-900 border-gray-700"
            />
            <div className="col-span-3 flex gap-2">
              <Button type="submit" className="bg-green-600 hover:bg-green-700">Simpan</Button>
              <Button type="button" variant="outline" onClick={resetForm}>Batal</Button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="p-4 border-b border-gray-700">
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Cari jenis barang..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-gray-900 border-gray-700"
            />
          </div>
        </div>
        <table className="w-full">
          <thead className="bg-gray-900 text-gray-400 text-sm">
            <tr>
              <th className="px-4 py-3 text-left">Kode</th>
              <th className="px-4 py-3 text-left">Nama Jenis</th>
              <th className="px-4 py-3 text-left">Deskripsi</th>
              <th className="px-4 py-3 text-center">Aksi</th>
            </tr>
          </thead>
          <tbody className="text-white">
            {loading ? (
              <tr><td colSpan="4" className="px-4 py-8 text-center text-gray-400">Memuat data...</td></tr>
            ) : filteredTypes.length === 0 ? (
              <tr><td colSpan="4" className="px-4 py-8 text-center text-gray-400">Tidak ada data</td></tr>
            ) : (
              filteredTypes.map((item) => (
                <tr key={item.id} className="border-t border-gray-700 hover:bg-gray-700/50">
                  <td className="px-4 py-3 font-mono text-yellow-400">{item.code}</td>
                  <td className="px-4 py-3">{item.name}</td>
                  <td className="px-4 py-3 text-gray-400">{item.description || '-'}</td>
                  <td className="px-4 py-3 text-center">
                    <Button size="sm" variant="ghost" onClick={() => handleEdit(item)}>
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button size="sm" variant="ghost" className="text-red-400" onClick={() => handleDelete(item.id)}>
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MasterItemTypes;
