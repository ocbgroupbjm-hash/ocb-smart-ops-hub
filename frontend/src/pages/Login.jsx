import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Loader2, Eye, EyeOff, Sparkles, Brain, BarChart3, ShoppingCart, Building2, ChevronRight, Database, Store, Shirt, Smartphone, Coffee, ShoppingBag, Briefcase } from 'lucide-react';
import { toast } from 'sonner';

const Login = () => {
  const [step, setStep] = useState(1); // 1 = pilih bisnis, 2 = login
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [businesses, setBusinesses] = useState([]);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [loadingBusinesses, setLoadingBusinesses] = useState(true);
  const { login, register } = useAuth();
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

  useEffect(() => {
    loadBusinesses();
  }, []);

  const loadBusinesses = async () => {
    setLoadingBusinesses(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/business/list`);
      if (res.ok) {
        const data = await res.json();
        setBusinesses(data.businesses || []);
        // Auto-select if only one business
        if (data.businesses?.length === 1) {
          setSelectedBusiness(data.businesses[0]);
        }
      }
    } catch (err) { 
      console.error(err); 
      // If error, still allow login with default
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

  const selectBusiness = async (business) => {
    setSelectedBusiness(business);
    setLoading(true);
    
    try {
      // Switch database before login
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/business/switch/${business.db_name}`, {
        method: 'POST'
      });
      
      if (res.ok) {
        // Wait for backend to restart with new DB
        toast.success(`Database: ${business.name}`);
        setTimeout(() => {
          setStep(2);
          setLoading(false);
        }, 1500);
      } else {
        // Still proceed to login even if switch fails
        setStep(2);
        setLoading(false);
      }
    } catch (err) {
      // Still proceed to login
      setStep(2);
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (isLogin) {
        await login(email, password);
        toast.success(`Selamat datang di ${selectedBusiness?.name || 'OCB AI TITAN'}!`);
      } else {
        await register({ email, password, name, role: 'cashier' });
        toast.success('Akun berhasil dibuat!');
      }
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.message || 'Autentikasi gagal');
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
          
          <div className="space-y-4 text-left">
            <div className="flex items-center gap-4 p-4 bg-red-900/20 border border-red-700/30 rounded-xl">
              <div className="p-2 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="font-semibold text-amber-100">Hallo AI - AI Perusahaan</div>
                <div className="text-sm text-gray-400">CEO, CFO, COO, Marketing, Sales AI</div>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-red-900/20 border border-red-700/30 rounded-xl">
              <div className="p-2 bg-gradient-to-br from-green-600 to-emerald-600 rounded-lg">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="font-semibold text-amber-100">Multi-Bisnis</div>
                <div className="text-sm text-gray-400">Kelola banyak bisnis dalam 1 aplikasi</div>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-red-900/20 border border-red-700/30 rounded-xl">
              <div className="p-2 bg-gradient-to-br from-amber-600 to-orange-600 rounded-lg">
                <ShoppingCart className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="font-semibold text-amber-100">ERP Lengkap</div>
                <div className="text-sm text-gray-400">POS, Inventory, Keuangan, Multi-Cabang</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
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
            <p className="text-gray-400 mt-2">Enterprise Retail AI System</p>
          </div>

          {/* STEP 1: Pilih Bisnis */}
          {step === 1 && (
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 shadow-xl">
              <div className="flex items-center gap-3 mb-2">
                <Database className="h-6 w-6 text-amber-400" />
                <h2 className="text-2xl font-bold text-amber-100">Pilih Bisnis</h2>
              </div>
              <p className="text-gray-400 mb-6">
                Pilih bisnis yang ingin Anda akses
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
                        {loading && isSelected ? (
                          <Loader2 className="h-5 w-5 animate-spin text-amber-400" />
                        ) : (
                          <ChevronRight className="h-5 w-5 text-gray-500" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )}

              <div className="mt-6 p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
                <div className="text-xs text-blue-300 mb-1">Info:</div>
                <div className="text-sm text-gray-300">Setiap bisnis memiliki database & user terpisah</div>
              </div>
            </div>
          )}

          {/* STEP 2: Login Form */}
          {step === 2 && (
            <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 shadow-xl">
              {/* Selected Business Badge */}
              {selectedBusiness && (
                <button
                  onClick={() => setStep(1)}
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
                    <div className="text-sm text-gray-400">Bisnis:</div>
                    <div className="font-semibold text-amber-100">{selectedBusiness.name}</div>
                  </div>
                  <span className="text-xs text-amber-400">Ganti</span>
                </button>
              )}

              <h2 className="text-2xl font-bold text-amber-100 mb-2">
                {isLogin ? 'Masuk' : 'Daftar Akun'}
              </h2>
              <p className="text-gray-400 mb-6">
                {isLogin ? `Login ke ${selectedBusiness?.name || 'sistem'}` : 'Buat akun baru'}
              </p>

              {/* Tabs */}
              <div className="flex mb-6 border border-red-900/30 rounded-lg overflow-hidden">
                <button
                  onClick={() => setIsLogin(true)}
                  className={`flex-1 py-2 text-sm font-semibold transition-colors ${
                    isLogin ? 'bg-red-900/30 text-amber-400' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Masuk
                </button>
                <button
                  onClick={() => setIsLogin(false)}
                  className={`flex-1 py-2 text-sm font-semibold transition-colors ${
                    !isLogin ? 'bg-red-900/30 text-amber-400' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Daftar
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                {!isLogin && (
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Nama Lengkap</label>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg focus:outline-none focus:border-red-500"
                      placeholder="Masukkan nama lengkap"
                      required={!isLogin}
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg focus:outline-none focus:border-red-500"
                    placeholder="email@perusahaan.com"
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
                      className="w-full px-4 py-3 bg-[#0a0608] border border-red-900/30 rounded-lg focus:outline-none focus:border-red-500 pr-12"
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
                  {loading && <Loader2 className="h-5 w-5 animate-spin" />}
                  {isLogin ? 'Masuk' : 'Daftar Akun'}
                </button>
              </form>

              {isLogin && (
                <div className="mt-6 p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
                  <div className="text-xs text-blue-300 mb-2">Demo Account:</div>
                  <div className="text-sm text-gray-300">ocbgroupbjm@gmail.com / admin123</div>
                </div>
              )}
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
