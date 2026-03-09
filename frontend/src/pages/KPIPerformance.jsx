import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { 
  Trophy, Target, TrendingUp, Star, Award, Users,
  Building2, BarChart2, Medal, Crown, AlertCircle,
  CheckCircle, Clock, RefreshCw, Plus
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const KPIPerformance = () => {
  const [loading, setLoading] = useState(true);
  const [employeeRanking, setEmployeeRanking] = useState(null);
  const [branchRanking, setBranchRanking] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [targets, setTargets] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  useEffect(() => {
    fetchData();
  }, [selectedMonth, selectedYear]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [empRes, branchRes, templatesRes, targetsRes] = await Promise.all([
        axios.get(`${API}/api/kpi/ai-ranking/employees?month=${selectedMonth}&year=${selectedYear}`),
        axios.get(`${API}/api/kpi/ai-ranking/branches?month=${selectedMonth}&year=${selectedYear}`),
        axios.get(`${API}/api/kpi/templates`),
        axios.get(`${API}/api/kpi/targets?month=${selectedMonth}&year=${selectedYear}`)
      ]);
      
      setEmployeeRanking(empRes.data);
      setBranchRanking(branchRes.data);
      setTemplates(templatesRes.data.templates || []);
      setTargets(targetsRes.data.targets || []);
    } catch (err) {
      console.error('Error fetching KPI data:', err);
    } finally {
      setLoading(false);
    }
  };

  const seedTemplates = async () => {
    try {
      await axios.post(`${API}/api/kpi/seed-templates`);
      toast.success('Template KPI berhasil dibuat');
      fetchData();
    } catch (err) {
      toast.error('Gagal membuat template');
    }
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return <Crown className="h-5 w-5 text-yellow-400" />;
    if (rank === 2) return <Medal className="h-5 w-5 text-gray-300" />;
    if (rank === 3) return <Medal className="h-5 w-5 text-amber-600" />;
    return <span className="text-gray-400 font-medium">#{rank}</span>;
  };

  const getRankColor = (category) => {
    switch (category) {
      case 'Elite Performer':
      case 'Elite Branch':
        return 'bg-gradient-to-r from-yellow-500 to-amber-500 text-black';
      case 'Top Performer':
      case 'Top Branch':
        return 'bg-green-600';
      case 'Good Performer':
      case 'Good Branch':
        return 'bg-blue-600';
      case 'Average Performer':
      case 'Average Branch':
        return 'bg-yellow-600';
      case 'Under Performance':
      case 'Needs Attention':
        return 'bg-orange-600';
      default:
        return 'bg-red-600';
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(amount);
  };

  const months = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0608] to-[#1a0a0e] p-4" data-testid="kpi-performance-page">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-amber-100 flex items-center gap-2">
              <Trophy className="h-6 w-6 text-yellow-400" />
              KPI & AI Performance System
            </h1>
            <p className="text-sm text-gray-400">Sistem penilaian kinerja dengan AI ranking otomatis</p>
          </div>
          <div className="flex items-center gap-2">
            <Select value={selectedMonth.toString()} onValueChange={(v) => setSelectedMonth(parseInt(v))}>
              <SelectTrigger className="w-32 bg-red-950/50 border-red-700/30">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {months.map((m, i) => (
                  <SelectItem key={i} value={(i + 1).toString()}>{m}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v))}>
              <SelectTrigger className="w-24 bg-red-950/50 border-red-700/30">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[2024, 2025, 2026].map((y) => (
                  <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button 
              onClick={fetchData} 
              disabled={loading}
              className="bg-red-900/50 hover:bg-red-800/50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {employeeRanking?.summary && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-4">
          <Card className="bg-gradient-to-br from-yellow-900/30 to-yellow-950/50 border-yellow-700/30">
            <CardContent className="p-3 text-center">
              <Crown className="h-6 w-6 mx-auto text-yellow-400 mb-1" />
              <p className="text-2xl font-bold text-yellow-400">{employeeRanking.summary.elite || 0}</p>
              <p className="text-xs text-yellow-300">Elite</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-green-900/30 to-green-950/50 border-green-700/30">
            <CardContent className="p-3 text-center">
              <Star className="h-6 w-6 mx-auto text-green-400 mb-1" />
              <p className="text-2xl font-bold text-green-400">{employeeRanking.summary.top || 0}</p>
              <p className="text-xs text-green-300">Top</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-blue-900/30 to-blue-950/50 border-blue-700/30">
            <CardContent className="p-3 text-center">
              <CheckCircle className="h-6 w-6 mx-auto text-blue-400 mb-1" />
              <p className="text-2xl font-bold text-blue-400">{employeeRanking.summary.good || 0}</p>
              <p className="text-xs text-blue-300">Good</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-gray-900/30 to-gray-950/50 border-gray-700/30">
            <CardContent className="p-3 text-center">
              <Clock className="h-6 w-6 mx-auto text-gray-400 mb-1" />
              <p className="text-2xl font-bold text-gray-400">{employeeRanking.summary.average || 0}</p>
              <p className="text-xs text-gray-300">Average</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-orange-900/30 to-orange-950/50 border-orange-700/30">
            <CardContent className="p-3 text-center">
              <AlertCircle className="h-6 w-6 mx-auto text-orange-400 mb-1" />
              <p className="text-2xl font-bold text-orange-400">{employeeRanking.summary.under || 0}</p>
              <p className="text-xs text-orange-300">Under</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-red-900/30 to-red-950/50 border-red-700/30">
            <CardContent className="p-3 text-center">
              <TrendingUp className="h-6 w-6 mx-auto text-red-400 mb-1" />
              <p className="text-2xl font-bold text-red-400">{employeeRanking.summary.needs_improvement || 0}</p>
              <p className="text-xs text-red-300">Needs Imp.</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="employee-ranking" className="space-y-4">
        <TabsList className="bg-red-950/50 p-1">
          <TabsTrigger value="employee-ranking" className="data-[state=active]:bg-red-900/50">
            <Users className="h-4 w-4 mr-1" />
            Ranking Karyawan
          </TabsTrigger>
          <TabsTrigger value="branch-ranking" className="data-[state=active]:bg-red-900/50">
            <Building2 className="h-4 w-4 mr-1" />
            Ranking Cabang
          </TabsTrigger>
          <TabsTrigger value="templates" className="data-[state=active]:bg-red-900/50">
            <Target className="h-4 w-4 mr-1" />
            Template KPI
          </TabsTrigger>
        </TabsList>

        {/* Employee Ranking */}
        <TabsContent value="employee-ranking">
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Award className="h-5 w-5 text-yellow-400" />
                AI Employee Performance Ranking - {months[selectedMonth - 1]} {selectedYear}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {employeeRanking?.rankings?.length > 0 ? (
                <div className="space-y-2">
                  {employeeRanking.rankings.map((emp, idx) => (
                    <div 
                      key={emp.employee_id}
                      className={`flex items-center justify-between p-3 rounded-lg border ${
                        idx < 3 ? 'bg-gradient-to-r from-red-950/50 to-amber-950/30 border-amber-700/30' : 'bg-red-950/20 border-red-900/20'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 text-center">
                          {getRankIcon(emp.rank)}
                        </div>
                        <div>
                          <p className="font-medium text-amber-100">{emp.employee_name}</p>
                          <p className="text-xs text-gray-400">{emp.branch_name}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-lg font-bold text-amber-100">{emp.final_score}%</p>
                          <p className="text-xs text-gray-400">{emp.total_targets} KPI</p>
                        </div>
                        <Badge className={getRankColor(emp.rank_category)}>
                          {emp.rank_category}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Trophy className="h-12 w-12 mx-auto text-gray-600 mb-2" />
                  <p className="text-gray-400">Belum ada data ranking</p>
                  <p className="text-xs text-gray-500 mt-1">Buat target KPI untuk karyawan terlebih dahulu</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Branch Ranking */}
        <TabsContent value="branch-ranking">
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader>
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Building2 className="h-5 w-5 text-blue-400" />
                AI Branch Performance Ranking - {months[selectedMonth - 1]} {selectedYear}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {branchRanking?.rankings?.length > 0 ? (
                <div className="space-y-2">
                  {branchRanking.rankings.map((branch, idx) => (
                    <div 
                      key={branch.branch_id}
                      className={`flex items-center justify-between p-3 rounded-lg border ${
                        idx < 3 ? 'bg-gradient-to-r from-red-950/50 to-blue-950/30 border-blue-700/30' : 'bg-red-950/20 border-red-900/20'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 text-center">
                          {getRankIcon(branch.rank)}
                        </div>
                        <div>
                          <p className="font-medium text-amber-100">{branch.branch_name || branch.branch_code}</p>
                          <p className="text-xs text-gray-400">{formatCurrency(branch.total_sales)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-lg font-bold text-amber-100">{branch.final_score}%</p>
                          <p className="text-xs text-gray-400">{branch.days_reported} hari lapor</p>
                        </div>
                        <Badge className={getRankColor(branch.rank_category)}>
                          {branch.rank_category}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Building2 className="h-12 w-12 mx-auto text-gray-600 mb-2" />
                  <p className="text-gray-400">Belum ada data ranking cabang</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Templates */}
        <TabsContent value="templates">
          <Card className="bg-[#120a0c]/80 border-red-900/30">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-amber-100 flex items-center gap-2">
                <Target className="h-5 w-5" />
                Template KPI
              </CardTitle>
              <Button 
                onClick={seedTemplates}
                className="bg-green-900/50 hover:bg-green-800/50"
              >
                <Plus className="h-4 w-4 mr-1" />
                Generate Default Templates
              </Button>
            </CardHeader>
            <CardContent>
              {templates.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {templates.map((t) => (
                    <div key={t.id} className="p-3 rounded-lg bg-red-950/30 border border-red-900/30">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-amber-100">{t.name}</p>
                          <p className="text-xs text-gray-400">{t.description}</p>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {t.category}
                        </Badge>
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-xs text-gray-400">
                        <span>Target: {t.target_value}</span>
                        <span>•</span>
                        <span>Weight: {t.weight}x</span>
                        <span>•</span>
                        <span>{t.measurement_period}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Target className="h-12 w-12 mx-auto text-gray-600 mb-2" />
                  <p className="text-gray-400">Belum ada template KPI</p>
                  <Button onClick={seedTemplates} className="mt-2 bg-red-900/50">
                    Generate Default Templates
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default KPIPerformance;
