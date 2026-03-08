import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Loader2, Eye, EyeOff, Sparkles, Brain, BarChart3, ShoppingCart, Lock } from 'lucide-react';
import { toast } from 'sonner';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await login(email, password);
      toast.success('Berhasil masuk!');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.message || 'Login gagal. Periksa email dan password.');
    } finally {
      setLoading(false);
    }
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
                <div className="font-semibold text-amber-100">Hallo OCB AI</div>
                <div className="text-sm text-gray-400">CEO, CFO, COO, Marketing, Sales AI</div>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-red-900/20 border border-red-700/30 rounded-xl">
              <div className="p-2 bg-gradient-to-br from-green-600 to-emerald-600 rounded-lg">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <div>
                <div className="font-semibold text-amber-100">AI Bisnis</div>
                <div className="text-sm text-gray-400">Analisa & Rekomendasi Otomatis</div>
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
          </div>

          {/* Login Form */}
          <div className="bg-[#1a1214] border border-red-900/30 rounded-xl p-8 shadow-xl">
            <h2 className="text-2xl font-bold text-amber-100 mb-2">Masuk</h2>
            <p className="text-gray-400 mb-6">Login ke OCB AI TITAN</p>

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
                Masuk
              </button>
            </form>

            <div className="mt-6 p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg">
              <div className="text-xs text-blue-300 mb-2">Demo Account:</div>
              <div className="text-sm text-gray-300">ocbgroupbjm@gmail.com / admin123</div>
            </div>
          </div>

          <p className="text-center text-gray-500 text-sm mt-6">
            OCB GROUP © 2026. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
