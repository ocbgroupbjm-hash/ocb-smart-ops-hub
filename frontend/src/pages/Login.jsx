import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Loader2, Eye, EyeOff, Sparkles, Brain, BarChart3, ShoppingCart, Lock, Building2, ChevronRight, Store, Shirt, Smartphone, Coffee, ShoppingBag, Briefcase, CheckCircle, Truck, Monitor } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const iconMap = {
  building: Building2,
  building2: Building2,
  store: Store,
  shirt: Shirt,
  smartphone: Smartphone,
  coffee: Coffee,
  shoppingbag: ShoppingBag,
  briefcase: Briefcase,
  truck: Truck,
  monitor: Monitor
};

const Login = () => {
  const [step, setStep] = useState(1); // 1 = pilih bisnis, 2 = login
  const [businesses, setBusinesses] = useState([]);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [loadingBusinesses, setLoadingBusinesses] = useState(true);
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  // Load businesses on mount
  useEffect(() => {
    loadBusinesses();
  }, []);

  const loadBusinesses = async () => {
    try {
      const res = await fetch(`${API_URL}/api/business/list`);
      if (res.ok) {
        const data = await res.json();
        setBusinesses(data.businesses || []);
        // Auto-select current active business
        const currentDb = data.current_db;
        const activeBiz = data.businesses?.find(b => b.db_name === currentDb);
        if (activeBiz) {
          setSelectedBusiness(activeBiz);
        }
      }
    } catch (err) {
      console.error('Failed to load businesses:', err);
      toast.error('Gagal memuat daftar bisnis');
    } finally {
      setLoadingBusinesses(false);
    }
  };

  const selectBusiness = async (business) => {
    setSelectedBusiness(business);
    
    try {
      // Switch database
      const switchRes = await fetch(`${API_URL}/api/business/switch/${business.db_name}`, {
        method: 'POST'
      });
      
      if (!switchRes.ok) {
        toast.error('Gagal memilih bisnis');
        return;
      }
      
      // Ensure admin user exists in this database
      await fetch(`${API_URL}/api/business/ensure-admin/${business.db_name}`, {
        method: 'POST'
      });
      
      // Dispatch event to update header
      window.dispatchEvent(new CustomEvent('tenant-switched'));
      
      toast.success(`Database: ${business.name}`);
      setStep(2); // Move to login step
    } catch (err) {
      console.error('Switch business error:', err);
      toast.error('Gagal memilih bisnis');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!selectedBusiness) {
      toast.error('Pilih bisnis terlebih dahulu');
      setStep(1);
      return;
    }
    
    setLoading(true);
    
    try {
      await login(email, password);
      toast.success(`Berhasil masuk ke ${selectedBusiness.name}!`);
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.message || 'Login gagal. Periksa email dan password.');
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (iconName) => {
    const Icon = iconMap[iconName?.toLowerCase()] || Building2;
    return Icon;
  };

  return (
    <div className="min-h-screen flex bg-gradient-to-br from-[#0a0608] via-[#1a0a0e] to-[#0a0608]">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-red-900/20 to-amber-900/10" />
        <div className="absolute top-20 left-20 w-72 h-72 bg-red-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-20 w-72 h-72 bg-amber-600/10 rounded-full blur-3xl" />
        
        <div className="relative z-10 text-center max-w-lg">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-red-600 to-amber-500 rounded-2xl mb-6 shadow-2xl shadow-red-900/50">
            <Sparkles className="h-12 w-12 text-white" />
          </div>
          
          <h1 className="text-5xl font-bold bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent mb-4">
            OCB SUPER AI
          </h1>
          <p className="text-xl text-amber-100/80 mb-8">Enterprise AI Operating System</p>
          
          <div className="space-y-4 text-left">
            <div className="flex items-center gap-4 p-4 bg-red-900/20 border border-red-700/30 rounded-xl">
              <div className="p-2 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="font-semibold text-amber-100">AI Sales Otomatis</div>
                <div className="text-sm text-gray-400">Jual otomatis sampai closing</div>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-red-900/20 border border-red-700/30 rounded-xl">
              <div className="p-2 bg-gradient-to-br from-green-600 to-emerald-600 rounded-lg">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="font-semibold text-amber-100">Warroom Dashboard</div>
                <div className="text-sm text-gray-400">Monitor 40+ cabang real-time</div>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-red-900/20 border border-red-700/30 rounded-xl">
              <div className="p-2 bg-gradient-to-br from-amber-600 to-orange-600 rounded-lg">
                <ShoppingCart className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="font-semibold text-amber-100">ERP Lengkap</div>
                <div className="text-sm text-gray-400">POS, Inventory, Keuangan, Akuntansi</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Business Selection & Login Form */}
      <div className="flex-1 flex items-center justify-center p-4 lg:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="text-center mb-8 lg:hidden">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-red-600 to-amber-500 rounded-xl mb-4 shadow-lg shadow-red-900/50">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent">
              OCB SUPER AI
            </h1>
          </div>

          {/* Step 1: Business Selection */}
          {step === 1 && (
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-2">
                <Building2 className="h-6 w-6 text-amber-500" />
                <h2 className="text-2xl font-bold text-amber-100">Pilih Bisnis</h2>
              </div>
              <p className="text-gray-400 mb-6">Pilih database bisnis yang ingin diakses</p>

              {loadingBusinesses ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 text-amber-500 animate-spin" />
                </div>
              ) : (
                <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                  {businesses.filter(b => b.show_in_login_selector !== false && b.is_test !== true && b.is_internal !== true).map((business) => {
                    const Icon = getIcon(business.icon);
                    const isSelected = selectedBusiness?.id === business.id;
                    
                    return (
                      <button
                        key={business.id}
                        data-testid={`business-card-${business.db_name}`}
                        onClick={() => selectBusiness(business)}
                        className={`w-full p-4 rounded-xl border transition-all text-left flex items-center gap-4 ${
                          isSelected 
                            ? 'bg-amber-600/20 border-amber-500' 
                            : 'bg-[#0a0608] border-red-900/30 hover:border-amber-600/50 hover:bg-red-900/10'
                        }`}
                      >
                        <div 
                          className="p-3 rounded-lg"
                          style={{ backgroundColor: `${business.color || '#991B1B'}30` }}
                        >
                          <Icon className="h-6 w-6" style={{ color: business.color || '#991B1B' }} />
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-amber-100">{business.name}</span>
                            {business.business_type && (
                              <span className="px-2 py-0.5 text-xs rounded-full bg-amber-600/20 text-amber-400 border border-amber-600/30">
                                {business.business_type}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-gray-500 font-mono">{business.db_name}</div>
                          {business.description && (
                            <div className="text-sm text-gray-400 mt-1">{business.description}</div>
                          )}
                        </div>
                        
                        {isSelected ? (
                          <CheckCircle className="h-5 w-5 text-amber-500" />
                        ) : (
                          <ChevronRight className="h-5 w-5 text-gray-600" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )}

              {businesses.length === 0 && !loadingBusinesses && (
                <div className="text-center py-8 text-gray-400">
                  Tidak ada bisnis tersedia
                </div>
              )}
            </div>
          )}

          {/* Step 2: Login Form */}
          {step === 2 && (
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-6 shadow-xl">
              {/* Selected Business Badge */}
              {selectedBusiness && (
                <button
                  onClick={() => setStep(1)}
                  className="w-full mb-6 p-3 bg-amber-600/10 border border-amber-600/30 rounded-lg flex items-center gap-3 hover:bg-amber-600/20 transition-all"
                >
                  {(() => {
                    const Icon = getIcon(selectedBusiness.icon);
                    return <Icon className="h-5 w-5 text-amber-500" />;
                  })()}
                  <div className="flex-1 text-left">
                    <div className="font-medium text-amber-100">{selectedBusiness.name}</div>
                    <div className="text-xs text-gray-500">Klik untuk ganti bisnis</div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-gray-500" />
                </button>
              )}

              <h2 className="text-2xl font-bold text-amber-100 mb-2">Masuk</h2>
              <p className="text-gray-400 mb-6">Login ke {selectedBusiness?.name || 'OCB SUPER AI'}</p>

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg focus:outline-none focus:border-amber-500"
                    placeholder="email@perusahaan.com"
                    required
                    autoFocus
                    data-testid="email-input"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-1">Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg focus:outline-none focus:border-amber-500 pr-12"
                      placeholder="••••••••"
                      required
                      data-testid="password-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-gradient-to-r from-red-600 to-amber-600 text-white rounded-lg font-semibold hover:from-red-500 hover:to-amber-500 disabled:opacity-50 flex items-center justify-center gap-2"
                  data-testid="submit-btn"
                >
                  {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Lock className="h-5 w-5" />}
                  Masuk ke {selectedBusiness?.name || 'Sistem'}
                </button>
              </form>

              <div className="mt-6 p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
                <div className="text-xs text-blue-300 mb-2">Demo Account:</div>
                <div className="text-sm text-gray-300">ocbgroupbjm@gmail.com / admin123</div>
              </div>
            </div>
          )}

          <p className="text-center text-gray-500 text-sm mt-6">
            OCB GROUP © 2026. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
