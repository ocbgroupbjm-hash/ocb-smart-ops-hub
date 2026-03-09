import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  MapPin, Building2, Users, Package, AlertTriangle, 
  TrendingUp, RefreshCw, Eye, Navigation, Bell,
  CheckCircle, XCircle, Clock
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Fix default marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons for different status
const createIcon = (color) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background-color: ${color}; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);"></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

const greenIcon = createIcon('#22c55e');
const yellowIcon = createIcon('#eab308');
const redIcon = createIcon('#ef4444');
const blueIcon = createIcon('#3b82f6');

// Map center component
function MapCenter({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, map.getZoom());
    }
  }, [center, map]);
  return null;
}

const GlobalMap = () => {
  const [activeTab, setActiveTab] = useState('branches');
  const [branches, setBranches] = useState([]);
  const [personnel, setPersonnel] = useState([]);
  const [stockMap, setStockMap] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [spvAlerts, setSPVAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBranch, setSelectedBranch] = useState(null);
  const [branchDetail, setBranchDetail] = useState(null);
  const [mapCenter, setMapCenter] = useState([-3.3167, 114.5900]); // Banjarmasin

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [branchRes, gpsRes, stockRes, alertRes, spvRes] = await Promise.all([
        axios.get(`${API}/api/global-map/branches`),
        axios.get(`${API}/api/global-map/gps/realtime`),
        axios.get(`${API}/api/global-map/stock/map`),
        axios.get(`${API}/api/global-map/stock/alerts`),
        axios.get(`${API}/api/global-map/spv/alerts`),
      ]);
      
      setBranches(branchRes.data);
      setPersonnel(gpsRes.data);
      setStockMap(stockRes.data);
      setAlerts(alertRes.data);
      setSPVAlerts(spvRes.data);
    } catch (err) {
      console.error('Error fetching map data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [fetchData]);

  const fetchBranchDetail = async (branchId) => {
    try {
      const res = await axios.get(`${API}/api/global-map/branches/${branchId}`);
      setBranchDetail(res.data);
      setSelectedBranch(branchId);
    } catch (err) {
      console.error('Error fetching branch detail:', err);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'green': return greenIcon;
      case 'yellow': return yellowIcon;
      case 'red': return redIcon;
      default: return greenIcon;
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0608] to-[#1a0a0e] p-4" data-testid="global-map-page">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
              <MapPin className="h-6 w-6 text-red-400" />
              Global Map Monitoring
            </h1>
            <p className="text-sm text-gray-400">Real-time monitoring seluruh cabang & personnel</p>
          </div>
          <Button 
            onClick={fetchData} 
            disabled={loading}
            className="bg-red-900/50 hover:bg-red-800/50 text-amber-100"
            data-testid="refresh-map-btn"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <Card className="bg-gradient-to-br from-green-900/30 to-green-950/50 border-green-700/30">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-green-300">Normal</p>
                <p className="text-2xl font-bold text-green-400">{branches?.status_summary?.green || 0}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500/50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-yellow-900/30 to-yellow-950/50 border-yellow-700/30">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-yellow-300">Warning</p>
                <p className="text-2xl font-bold text-yellow-400">{branches?.status_summary?.yellow || 0}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-yellow-500/50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-red-900/30 to-red-950/50 border-red-700/30">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-red-300">Bermasalah</p>
                <p className="text-2xl font-bold text-red-400">{branches?.status_summary?.red || 0}</p>
              </div>
              <XCircle className="h-8 w-8 text-red-500/50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-900/30 to-blue-950/50 border-blue-700/30">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-300">Personnel Aktif</p>
                <p className="text-2xl font-bold text-blue-400">{personnel?.active_count || 0}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500/50" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Map */}
        <div className="lg:col-span-2">
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-amber-100 text-lg flex items-center gap-2">
                  <Navigation className="h-5 w-5" />
                  Peta Indonesia - {branches?.total_branches || 0} Cabang
                </CardTitle>
                <div className="flex gap-2">
                  <Badge variant="outline" className="text-green-400 border-green-700">● Normal</Badge>
                  <Badge variant="outline" className="text-yellow-400 border-yellow-700">● Warning</Badge>
                  <Badge variant="outline" className="text-red-400 border-red-700">● Masalah</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-[500px] rounded-lg overflow-hidden border border-red-900/30">
                <MapContainer 
                  center={mapCenter} 
                  zoom={12} 
                  style={{ height: '100%', width: '100%' }}
                  className="z-10"
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; OpenStreetMap'
                  />
                  <MapCenter center={mapCenter} />
                  
                  {/* Branch markers */}
                  {activeTab === 'branches' && branches?.branches?.map((branch) => (
                    <Marker
                      key={branch.id}
                      position={[branch.latitude, branch.longitude]}
                      icon={getStatusIcon(branch.status)}
                      eventHandlers={{
                        click: () => fetchBranchDetail(branch.id),
                      }}
                    >
                      <Popup>
                        <div className="p-2 min-w-[200px]">
                          <h3 className="font-bold text-gray-800">{branch.name}</h3>
                          <p className="text-xs text-gray-600">{branch.code} - {branch.city}</p>
                          <div className="mt-2 space-y-1 text-xs">
                            <p>Penjualan Hari Ini: <span className="font-semibold">{formatCurrency(branch.sales_today)}</span></p>
                            <p>Transaksi: <span className="font-semibold">{branch.transactions_today}</span></p>
                            <p>Karyawan: <span className="font-semibold">{branch.employee_count}</span></p>
                            <p>Stok Kosong: <span className={`font-semibold ${branch.stock_empty > 0 ? 'text-red-600' : ''}`}>{branch.stock_empty}</span></p>
                            <p>Selisih: <span className={`font-semibold ${branch.selisih_today < 0 ? 'text-red-600' : branch.selisih_today > 0 ? 'text-green-600' : ''}`}>
                              {formatCurrency(branch.selisih_today)}
                            </span></p>
                          </div>
                          <Badge className={`mt-2 ${
                            branch.status === 'green' ? 'bg-green-600' :
                            branch.status === 'yellow' ? 'bg-yellow-600' : 'bg-red-600'
                          }`}>
                            {branch.status_text}
                          </Badge>
                        </div>
                      </Popup>
                    </Marker>
                  ))}

                  {/* Personnel markers */}
                  {activeTab === 'personnel' && personnel?.locations?.map((p) => (
                    <CircleMarker
                      key={p.employee_id}
                      center={[p.latitude, p.longitude]}
                      radius={8}
                      fillColor={p.is_active ? '#3b82f6' : '#6b7280'}
                      color="#fff"
                      weight={2}
                      fillOpacity={0.8}
                    >
                      <Popup>
                        <div className="p-2">
                          <h3 className="font-bold text-gray-800">{p.employee_name}</h3>
                          <p className="text-xs text-gray-600">{p.jabatan}</p>
                          <p className="text-xs text-gray-500">{p.branch_name}</p>
                          <p className="text-xs mt-1">
                            Status: <span className={p.is_active ? 'text-green-600' : 'text-gray-500'}>
                              {p.is_active ? 'Aktif' : 'Tidak Aktif'}
                            </span>
                          </p>
                          <p className="text-xs">Aktivitas: {p.activity || '-'}</p>
                          <p className="text-xs">Waktu: {p.waktu}</p>
                        </div>
                      </Popup>
                    </CircleMarker>
                  ))}

                  {/* Stock map markers */}
                  {activeTab === 'stock' && stockMap?.branches?.map((s) => (
                    <Marker
                      key={s.branch_id}
                      position={[s.latitude, s.longitude]}
                      icon={getStatusIcon(s.status)}
                    >
                      <Popup>
                        <div className="p-2 min-w-[180px]">
                          <h3 className="font-bold text-gray-800">{s.branch_name}</h3>
                          <p className="text-xs text-gray-600">{s.branch_code}</p>
                          <div className="mt-2 space-y-1 text-xs">
                            <p>Total Produk: <span className="font-semibold">{s.total_products}</span></p>
                            <p className="text-red-600">Stok Kosong: <span className="font-semibold">{s.empty_count}</span></p>
                            <p className="text-yellow-600">Stok Rendah: <span className="font-semibold">{s.low_count}</span></p>
                          </div>
                          {s.empty_items?.length > 0 && (
                            <div className="mt-2 text-xs">
                              <p className="font-semibold text-red-600">Item Kosong:</p>
                              <ul className="list-disc list-inside">
                                {s.empty_items.slice(0, 3).map((item, i) => (
                                  <li key={i}>{item.name}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                </MapContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Side Panel */}
        <div className="space-y-4">
          {/* View Toggle */}
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardContent className="p-3">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid grid-cols-3 bg-red-950/50">
                  <TabsTrigger value="branches" className="data-[state=active]:bg-red-900/50">
                    <Building2 className="h-4 w-4 mr-1" />
                    Cabang
                  </TabsTrigger>
                  <TabsTrigger value="personnel" className="data-[state=active]:bg-red-900/50">
                    <Users className="h-4 w-4 mr-1" />
                    Personnel
                  </TabsTrigger>
                  <TabsTrigger value="stock" className="data-[state=active]:bg-red-900/50">
                    <Package className="h-4 w-4 mr-1" />
                    Stok
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </CardContent>
          </Card>

          {/* Branch Detail */}
          {branchDetail && (
            <Card className="bg-[#120a0c]/80 border-red-900/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  Detail: {branchDetail?.branch?.name || 'N/A'}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-red-950/30 p-2 rounded">
                    <p className="text-xs text-gray-400">Karyawan</p>
                    <p className="text-lg font-bold text-amber-100">{branchDetail?.employee_count || 0}</p>
                  </div>
                  <div className="bg-red-950/30 p-2 rounded">
                    <p className="text-xs text-gray-400">Produk</p>
                    <p className="text-lg font-bold text-amber-100">{branchDetail?.stock_summary?.total_products || 0}</p>
                  </div>
                </div>
                
                {branchDetail?.setoran_today && (
                  <div className="bg-green-900/20 p-2 rounded border border-green-700/30">
                    <p className="text-xs text-green-400">Setoran Hari Ini</p>
                    <p className="text-lg font-bold text-green-300">
                      {formatCurrency(branchDetail.setoran_today.total_penjualan)}
                    </p>
                    <p className="text-xs text-gray-400">
                      {branchDetail.setoran_today.total_transaksi} transaksi
                    </p>
                  </div>
                )}

                {branchDetail?.stock_summary?.empty_count > 0 && (
                  <div className="bg-red-900/20 p-2 rounded border border-red-700/30">
                    <p className="text-xs text-red-400">Stok Kosong: {branchDetail.stock_summary.empty_count}</p>
                    <ul className="text-xs text-gray-300 mt-1 space-y-0.5">
                      {branchDetail?.empty_stock_items?.slice(0, 5).map((item, i) => (
                        <li key={i}>• {item.name}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Alerts */}
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                <Bell className="h-4 w-4 text-red-400" />
                Alert Terbaru ({alerts?.total + spvAlerts?.total || 0})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {spvAlerts?.alerts?.slice(0, 3).map((alert) => (
                  <div key={alert.id} className="bg-yellow-900/20 p-2 rounded border border-yellow-700/30">
                    <div className="flex items-start gap-2">
                      <Navigation className="h-4 w-4 text-yellow-400 mt-0.5" />
                      <div>
                        <p className="text-xs font-medium text-yellow-300">{alert.title}</p>
                        <p className="text-xs text-gray-400">{alert.message}</p>
                      </div>
                    </div>
                  </div>
                ))}
                
                {alerts?.alerts?.slice(0, 3).map((alert) => (
                  <div key={alert.id} className="bg-red-900/20 p-2 rounded border border-red-700/30">
                    <div className="flex items-start gap-2">
                      <Package className="h-4 w-4 text-red-400 mt-0.5" />
                      <div>
                        <p className="text-xs font-medium text-red-300">{alert.title}</p>
                        <p className="text-xs text-gray-400">{alert.message}</p>
                      </div>
                    </div>
                  </div>
                ))}

                {(alerts?.total || 0) + (spvAlerts?.total || 0) === 0 && (
                  <p className="text-xs text-gray-500 text-center py-4">Tidak ada alert</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Branch List */}
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader className="pb-2">
              <CardTitle className="text-amber-100 text-sm flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                Daftar Cabang
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 max-h-[250px] overflow-y-auto">
                {branches?.branches?.map((branch) => (
                  <button
                    key={branch.id}
                    onClick={() => {
                      fetchBranchDetail(branch.id);
                      setMapCenter([branch.latitude, branch.longitude]);
                    }}
                    className={`w-full text-left p-2 rounded hover:bg-red-900/30 transition flex items-center justify-between ${
                      selectedBranch === branch.id ? 'bg-red-900/40' : ''
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        branch.status === 'green' ? 'bg-green-500' :
                        branch.status === 'yellow' ? 'bg-yellow-500' : 'bg-red-500'
                      }`} />
                      <div>
                        <p className="text-xs font-medium text-amber-100">{branch.code}</p>
                        <p className="text-[10px] text-gray-500">{branch.city}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-green-400">{formatCurrency(branch.sales_today)}</p>
                      <p className="text-[10px] text-gray-500">{branch.transactions_today} trx</p>
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default GlobalMap;
