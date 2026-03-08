import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { Sparkles } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [loading, setLoading] = useState(false);

  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [registerData, setRegisterData] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'owner'
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await login(loginData.email, loginData.password);
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await register(registerData);
      toast.success('Registration successful!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #080406 0%, #120a0c 50%, #0c0608 100%)' }}>
      {/* Elegant gradient background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(185,28,28,0.15),transparent_50%)]"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(252,211,77,0.08),transparent_50%)]"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(127,29,29,0.1),transparent_60%)]"></div>
      
      <div className="relative w-full max-w-md px-4 z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-red-700 to-amber-500 mb-6 shadow-lg shadow-red-900/30">
            <Sparkles className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent mb-3">
            OCB AI
          </h1>
          <p className="text-red-300/60 text-sm">AI-Powered Super Business Platform</p>
        </div>

        <Tabs defaultValue="login" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-red-950/30 backdrop-blur-sm border border-red-900/30">
            <TabsTrigger value="login" className="data-[state=active]:bg-red-900/40 data-[state=active]:text-amber-200">Login</TabsTrigger>
            <TabsTrigger value="register" className="data-[state=active]:bg-red-900/40 data-[state=active]:text-amber-200">Register</TabsTrigger>
          </TabsList>

          <TabsContent value="login">
            <Card className="bg-gradient-to-b from-red-950/40 to-red-950/20 backdrop-blur-xl border-red-900/30 shadow-2xl shadow-red-900/20">
              <CardHeader>
                <CardTitle className="text-2xl text-amber-100">Welcome Back</CardTitle>
                <CardDescription className="text-red-300/60">Enter your credentials to access your account</CardDescription>
              </CardHeader>
              <form onSubmit={handleLogin}>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email" className="text-red-200/80">Email</Label>
                    <Input
                      id="login-email"
                      type="email"
                      placeholder="you@company.com"
                      value={loginData.email}
                      onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                      required
                      data-testid="login-email-input"
                      className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40 focus:border-amber-500/50 focus:ring-amber-500/20"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password" className="text-red-200/80">Password</Label>
                    <Input
                      id="login-password"
                      type="password"
                      value={loginData.password}
                      onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                      required
                      data-testid="login-password-input"
                      className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40 focus:border-amber-500/50 focus:ring-amber-500/20"
                    />
                  </div>
                </CardContent>
                <CardFooter>
                  <Button 
                    type="submit" 
                    className="w-full bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500 shadow-lg shadow-red-900/30 text-white" 
                    disabled={loading} 
                    data-testid="login-submit-button"
                  >
                    {loading ? 'Logging in...' : 'Login'}
                  </Button>
                </CardFooter>
              </form>
            </Card>
          </TabsContent>

          <TabsContent value="register">
            <Card className="bg-gradient-to-b from-red-950/40 to-red-950/20 backdrop-blur-xl border-red-900/30 shadow-2xl shadow-red-900/20">
              <CardHeader>
                <CardTitle className="text-2xl text-amber-100">Create Account</CardTitle>
                <CardDescription className="text-red-300/60">Start your AI-powered business journey</CardDescription>
              </CardHeader>
              <form onSubmit={handleRegister}>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="register-name" className="text-red-200/80">Full Name</Label>
                    <Input
                      id="register-name"
                      type="text"
                      placeholder="John Doe"
                      value={registerData.full_name}
                      onChange={(e) => setRegisterData({ ...registerData, full_name: e.target.value })}
                      required
                      data-testid="register-name-input"
                      className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40 focus:border-amber-500/50 focus:ring-amber-500/20"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-email" className="text-red-200/80">Email</Label>
                    <Input
                      id="register-email"
                      type="email"
                      placeholder="you@company.com"
                      value={registerData.email}
                      onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                      required
                      data-testid="register-email-input"
                      className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40 focus:border-amber-500/50 focus:ring-amber-500/20"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-password" className="text-red-200/80">Password</Label>
                    <Input
                      id="register-password"
                      type="password"
                      value={registerData.password}
                      onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                      required
                      data-testid="register-password-input"
                      className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40 focus:border-amber-500/50 focus:ring-amber-500/20"
                    />
                  </div>
                </CardContent>
                <CardFooter>
                  <Button 
                    type="submit" 
                    className="w-full bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500 shadow-lg shadow-red-900/30 text-white" 
                    disabled={loading} 
                    data-testid="register-submit-button"
                  >
                    {loading ? 'Creating account...' : 'Create Account'}
                  </Button>
                </CardFooter>
              </form>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}