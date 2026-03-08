import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Loader2, Eye, EyeOff, Sparkles, Brain, BarChart3, ShoppingCart, Building2, ChevronRight, Database, Store, Shirt, Smartphone, Coffee, ShoppingBag, Briefcase, User, Lock, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

const Login = () => {
  const [step, setStep] = useState(1); // 1 = login owner, 2 = pilih bisnis, 3 = login database
  const [ownerEmail, setOwnerEmail] = useState('');
  const [ownerPassword, setOwnerPassword] = useState('');
  const [ownerVerified, setOwnerVerified] = useState(false);
  const [ownerName, setOwnerName] = useState('');
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [businesses, setBusinesses] = useState([]);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [loadingBusinesses, setLoadingBusinesses] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const icons = {
    store: Store,
    building: Building2,
    shirt: Shirt,
    smartphone: Smartphone,
    coffee: Coffee,
    shopping: ShoppingBag,
    briefcase: Briefcase,
  };

  const loadBusinesses = async () => {
    setLoadingBusinesses(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/business/list`);
      if (res.ok) {
        const data = await res.json();
        setBusinesses(data.businesses || []);
      }
    } catch (err) { 
      console.error(err); 
      setBusinesses([{
        id: 'default',
        name: 'OCB GROUP',
        db_name: 'ocb_titan',
        description: 'Database utama',
        icon: 'building',
        color: '#991B1B'
      }]);
    }
    finally { setLoadingBusinesses(false); }
  };

  // Step 1: Verify Owner
  const verifyOwner = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Try to login to verify owner credentials
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: ownerEmail, password: ownerPassword })
      });
      
      if (res.ok) {
        const data = await res.json();
        // Check if user is owner
        if (data.user?.role === 'owner' || data.user?.role === 'admin') {
          setOwnerVerified(true);
          setOwnerName(data.user?.name || 'Owner');
          toast.success(`Selamat datang, ${data.user?.name || 'Owner'}!`);
          // Load businesses and go to step 2
          await loadBusinesses();
          setStep(2);
        } else {
          toast.error('Hanya Owner/Admin yang dapat mengakses multi-bisnis');
        }
      } else {
        toast.error('Email atau password salah');
      }
    } catch (err) {
      toast.error('Gagal verifikasi. Coba lagi.');
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Select Business
  const selectBusiness = async (business) => {
    setSelectedBusiness(business);
    setLoading(true);
    
    try {
      // Switch database
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/business/switch/${business.db_name}`, {
        method: 'POST'
      });
      
      if (res.ok) {
        toast.success(`Database: ${business.name}`);
        // Wait for backend to apply new DB
        setTimeout(() => {
          setStep(3);
          setLoading(false);
        }, 1500);
      } else {
        setStep(3);
        setLoading(false);
      }
    } catch (err) {
      setStep(3);
      setLoading(false);
    }
  };

  // Step 3: Login to selected database
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await login(email, password);
      toast.success(`Berhasil masuk ke ${selectedBusiness?.name || 'sistem'}!`);
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.message || 'Login gagal. Periksa email dan password.');
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (iconName) => {
    return icons[iconName] || Store;
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
            OCB AI TITAN
          </h1>
          <p className="text-xl text-amber-100/80 mb-8">Enterprise Retail AI System</p>
          
          {/* Steps indicator */}
          <div className="flex justify-center gap-4 mb-8">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${step >= 1 ? 'bg-green-600/30 text-green-400' : 'bg-gray-800 text-gray-500'}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step >= 1 ? 'bg-green-600' : 'bg-gray-700'}`}>1</div>
              <span className="text-sm">Login Owner</span>
            </div>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${step >= 2 ? 'bg-green-600/30 text-green-400' : 'bg-gray-800 text-gray-500'}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step >= 2 ? 'bg-green-600' : 'bg-gray-700'}`}>2</div>
              <span className="text-sm">Pilih Bisnis</span>
            </div>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${step >= 3 ? 'bg-green-600/30 text-green-400' : 'bg-gray-800 text-gray-500'}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${step >= 3 ? 'bg-green-600' : 'bg-gray-700'}`}>3</div>
              <span className="text-sm">Masuk Sistem</span>
            </div>
          </div>
          
          <div className="space-y-4 text-left">
            <div className="flex items-center gap-4 p-4 bg-red-900/20 border border-red-700/30 rounded-xl">
              <div className="p-2 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="font-semibold text-amber-100">Multi-Bisnis</div>
                <div className="text-sm text-gray-400">1 Aplikasi untuk banyak bisnis</div>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-red-900/20 border border-red-700/30 rounded-xl">
              <div className="p-2 bg-gradient-to-br from-green-600 to-emerald-600 rounded-lg">
                <Database className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="font-semibold text-amber-100">Database Terpisah</div>
                <div className="text-sm text-gray-400">Data tidak tercampur antar bisnis</div>
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

      {/* Right Side - Forms */}
      <div className="flex-1 flex items-center justify-center p-4 lg:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="text-center mb-8 lg:hidden">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-red-600 to-amber-500 rounded-xl mb-4 shadow-lg shadow-red-900/50">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent">
              OCB AI TITAN
            </h1>
          </div>

          {/* ==================== STEP 1: Login Owner ==================== */}
          {step === 1 && (
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 shadow-xl">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-amber-600/20 rounded-lg">
                  <User className="h-5 w-5 text-amber-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-amber-100">Login Owner</h2>
                  <p className="text-sm text-gray-400">Step 1 dari 3</p>
                </div>
              </div>
              <p className="text-gray-400 mb-6 mt-4">
                Masuk dengan akun Owner untuk mengakses multi-bisnis
              </p>

              <form onSubmit={verifyOwner} className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email Owner</label>
                  <input
                    type="email"
                    value={ownerEmail}
                    onChange={(e) => setOwnerEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg focus:outline-none focus:border-amber-500"
                    placeholder="owner@perusahaan.com"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-1">Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={ownerPassword}
                      onChange={(e) => setOwnerPassword(e.target.value)}
                      className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg focus:outline-none focus:border-amber-500 pr-12"
                      placeholder="••••••••"
                      required
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
                  className="w-full py-3 bg-gradient-to-r from-amber-600 to-orange-600 text-white rounded-lg font-semibold hover:from-amber-500 hover:to-orange-500 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Lock className="h-5 w-5" />}
                  Verifikasi Owner
                </button>
              </form>

              <div className="mt-6 p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
                <div className="text-xs text-blue-300 mb-2">Demo Owner Account:</div>
                <div className="text-sm text-gray-300">ocbgroupbjm@gmail.com / admin123</div>
              </div>
            </div>
          )}

          {/* ==================== STEP 2: Pilih Bisnis ==================== */}
          {step === 2 && (
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 shadow-xl">
              {/* Owner badge */}
              <div className="mb-6 p-3 bg-green-900/20 border border-green-700/30 rounded-lg flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-green-400" />
                <div>
                  <div className="text-sm text-green-400">Owner Terverifikasi</div>
                  <div className="text-white font-medium">{ownerName}</div>
                </div>
              </div>

              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-blue-600/20 rounded-lg">
                  <Database className="h-5 w-5 text-blue-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-amber-100">Pilih Bisnis</h2>
                  <p className="text-sm text-gray-400">Step 2 dari 3</p>
                </div>
              </div>
              <p className="text-gray-400 mb-6 mt-4">
                Pilih bisnis/database yang ingin Anda akses
              </p>

              {loadingBusinesses ? (
                <div className="text-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto text-amber-400" />
                  <p className="text-gray-400 mt-2">Memuat daftar bisnis...</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {businesses.map((business) => {
                    const IconComp = getIcon(business.icon);
                    const isSelected = selectedBusiness?.id === business.id;
                    const isSwitching = loading && isSelected;
                    
                    return (
                      <button
                        key={business.id}
                        onClick={() => selectBusiness(business)}
                        disabled={loading}
                        className={`w-full p-4 rounded-xl border transition-all text-left flex items-center gap-4 ${
                          isSelected 
                            ? 'border-amber-500 bg-amber-900/20' 
                            : 'border-red-900/30 hover:border-red-700/50 hover:bg-red-900/10'
                        } disabled:opacity-50`}
                      >
                        <div 
                          className="p-3 rounded-xl"
                          style={{ backgroundColor: `${business.color}30` }}
                        >
                          <IconComp className="h-6 w-6" style={{ color: business.color }} />
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-amber-100">{business.name}</div>
                          <div className="text-sm text-gray-400">{business.description || business.db_name}</div>
                        </div>
                        {isSwitching ? (
                          <Loader2 className="h-5 w-5 animate-spin text-amber-400" />
                        ) : (
                          <ChevronRight className="h-5 w-5 text-gray-500" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )}

              <button
                onClick={() => setStep(1)}
                className="w-full mt-4 py-2 text-gray-400 hover:text-white text-sm"
              >
                ← Kembali ke Login Owner
              </button>
            </div>
          )}

          {/* ==================== STEP 3: Login ke Database ==================== */}
          {step === 3 && (
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 shadow-xl">
              {/* Selected Business badge */}
              {selectedBusiness && (
                <button
                  onClick={() => setStep(2)}
                  className="w-full mb-6 p-3 bg-gradient-to-r from-red-900/30 to-amber-900/20 border border-red-700/30 rounded-lg flex items-center gap-3 hover:border-amber-500/50 transition-colors"
                >
                  {(() => {
                    const IconComp = getIcon(selectedBusiness.icon);
                    return (
                      <div 
                        className="p-2 rounded-lg"
                        style={{ backgroundColor: `${selectedBusiness.color}30` }}
                      >
                        <IconComp className="h-5 w-5" style={{ color: selectedBusiness.color }} />
                      </div>
                    );
                  })()}
                  <div className="flex-1 text-left">
                    <div className="text-sm text-gray-400">Database:</div>
                    <div className="font-semibold text-amber-100">{selectedBusiness.name}</div>
                  </div>
                  <span className="text-xs text-amber-400">Ganti</span>
                </button>
              )}

              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-green-600/20 rounded-lg">
                  <Lock className="h-5 w-5 text-green-400" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-amber-100">Masuk Sistem</h2>
                  <p className="text-sm text-gray-400">Step 3 dari 3</p>
                </div>
              </div>
              <p className="text-gray-400 mb-6 mt-4">
                Login dengan akun yang ada di database <strong className="text-amber-300">{selectedBusiness?.name}</strong>
              </p>

              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg focus:outline-none focus:border-green-500"
                    placeholder="user@perusahaan.com"
                    required
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
                      className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg focus:outline-none focus:border-green-500 pr-12"
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
                  className="w-full py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-semibold hover:from-green-500 hover:to-emerald-500 disabled:opacity-50 flex items-center justify-center gap-2"
                  data-testid="submit-btn"
                >
                  {loading && <Loader2 className="h-5 w-5 animate-spin" />}
                  Masuk ke {selectedBusiness?.name}
                </button>
              </form>

              <div className="mt-6 p-4 bg-amber-900/20 border border-amber-700/30 rounded-lg">
                <div className="text-xs text-amber-300 mb-2">Info:</div>
                <div className="text-sm text-gray-300">Gunakan akun yang terdaftar di database "{selectedBusiness?.name}"</div>
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
