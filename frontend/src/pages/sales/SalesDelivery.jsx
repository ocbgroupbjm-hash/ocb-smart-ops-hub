import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Search, Truck, Eye, Loader2, Package, MapPin, Check, X } from 'lucide-react';
import { toast } from 'sonner';

const SalesDelivery = () => {
  const { api } = useAuth();
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedDelivery, setSelectedDelivery] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  const loadDeliveries = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchTerm && { search: searchTerm }),
        ...(statusFilter && { status: statusFilter })
      });
      const res = await api(`/api/sales/deliveries?${params}`);
      if (res.ok) {
        const data = await res.json();
        setDeliveries(data.items || data || []);
      }
    } catch (err) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, [api, searchTerm, statusFilter]);

  useEffect(() => {
    loadDeliveries();
  }, [loadDeliveries]);

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'bg-yellow-600/20 text-yellow-400',
      shipped: 'bg-blue-600/20 text-blue-400',
      delivered: 'bg-green-600/20 text-green-400',
      failed: 'bg-red-600/20 text-red-400'
    };
    const labels = {
      pending: 'Menunggu',
      shipped: 'Dikirim',
      delivered: 'Terkirim',
      failed: 'Gagal'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs ${badges[status] || badges.pending}`}>
        {labels[status] || status}
      </span>
    );
  };

  const updateDeliveryStatus = async (deliveryId, newStatus) => {
    try {
      const res = await api(`/api/sales/deliveries/${deliveryId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        toast.success(`Status diupdate ke ${newStatus}`);
        loadDeliveries();
      }
    } catch (err) {
      toast.error('Gagal update status');
    }
  };

  return (
    <div className="space-y-4" data-testid="sales-delivery-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-amber-100">Data Pengiriman</h1>
          <p className="text-gray-400 text-sm">Lacak status pengiriman barang</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Total Pengiriman</p>
          <p className="text-2xl font-bold text-amber-200">{deliveries.length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Menunggu</p>
          <p className="text-2xl font-bold text-yellow-400">{deliveries.filter(d => d.status === 'pending').length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Dikirim</p>
          <p className="text-2xl font-bold text-blue-400">{deliveries.filter(d => d.status === 'shipped').length}</p>
        </div>
        <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
          <p className="text-gray-400 text-sm">Terkirim</p>
          <p className="text-2xl font-bold text-green-400">{deliveries.filter(d => d.status === 'delivered').length}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cari no. pengiriman, pelanggan..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 bg-[#0a0608] border border-red-900/30 rounded-lg text-gray-200"
          >
            <option value="">Semua Status</option>
            <option value="pending">Menunggu</option>
            <option value="shipped">Dikirim</option>
            <option value="delivered">Terkirim</option>
            <option value="failed">Gagal</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1214] border border-red-900/30 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-red-900/20">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. KIRIM</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">NO. FAKTUR</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">PELANGGAN</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">ALAMAT</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-amber-200">KURIR</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">STATUS</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-amber-200">AKSI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-red-900/20">
              {loading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" /></td></tr>
              ) : deliveries.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Belum ada data pengiriman</td></tr>
              ) : deliveries.map(delivery => (
                <tr key={delivery.id} className="hover:bg-red-900/10">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Truck className="h-4 w-4 text-gray-500" />
                      <span className="font-medium text-amber-300 font-mono">{delivery.delivery_number || '-'}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-300">{delivery.invoice_number}</td>
                  <td className="px-4 py-3 text-sm text-gray-200">{delivery.customer_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-400 max-w-[200px] truncate">
                    <div className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {delivery.address || '-'}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-400">{delivery.courier || '-'}</td>
                  <td className="px-4 py-3 text-center">{getStatusBadge(delivery.status)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-1">
                      {delivery.status === 'pending' && (
                        <button 
                          onClick={() => updateDeliveryStatus(delivery.id, 'shipped')}
                          className="p-1.5 hover:bg-blue-600/20 rounded text-blue-400"
                          title="Tandai Dikirim"
                        >
                          <Truck className="h-4 w-4" />
                        </button>
                      )}
                      {delivery.status === 'shipped' && (
                        <button 
                          onClick={() => updateDeliveryStatus(delivery.id, 'delivered')}
                          className="p-1.5 hover:bg-green-600/20 rounded text-green-400"
                          title="Tandai Terkirim"
                        >
                          <Check className="h-4 w-4" />
                        </button>
                      )}
                      <button 
                        onClick={() => { setSelectedDelivery(delivery); setShowDetail(true); }}
                        className="p-1.5 hover:bg-gray-600/20 rounded text-gray-400"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Modal */}
      {showDetail && selectedDelivery && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl w-full max-w-lg">
            <div className="p-4 border-b border-red-900/30 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-100">Detail Pengiriman</h2>
              <button onClick={() => setShowDetail(false)} className="p-1 hover:bg-red-900/20 rounded"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-400">No. Pengiriman</p>
                  <p className="font-mono text-amber-300">{selectedDelivery.delivery_number}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">No. Faktur</p>
                  <p className="font-mono text-gray-300">{selectedDelivery.invoice_number}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Pelanggan</p>
                  <p className="text-gray-200">{selectedDelivery.customer_name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Status</p>
                  {getStatusBadge(selectedDelivery.status)}
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-400">Alamat Pengiriman</p>
                <p className="text-gray-200">{selectedDelivery.address || '-'}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-400">Kurir</p>
                  <p className="text-gray-200">{selectedDelivery.courier || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">No. Resi</p>
                  <p className="font-mono text-gray-300">{selectedDelivery.tracking_number || '-'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesDelivery;
