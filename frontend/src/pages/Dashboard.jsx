import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Users, MessageSquare, Store, TrendingUp, Bot, BarChart } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';
import {
  LineChart,
  Line,
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const response = await api.get('/analytics/dashboard/');
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
      console.error('Dashboard data error:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Total Customers',
      value: stats?.total_customers || 0,
      icon: Users,
      color: 'from-blue-500 to-blue-600',
      change: '+12%'
    },
    {
      title: 'Conversations',
      value: stats?.total_conversations || 0,
      icon: MessageSquare,
      color: 'from-purple-500 to-purple-600',
      change: '+23%'
    },
    {
      title: 'Active Branches',
      value: stats?.active_branches || 0,
      icon: Store,
      color: 'from-green-500 to-green-600',
      change: '+5%'
    },
    {
      title: 'AI Queries Today',
      value: stats?.ai_queries_today || 0,
      icon: Bot,
      color: 'from-orange-500 to-orange-600',
      change: '+45%'
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="dashboard-page">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Dashboard</h1>
        <p className="text-gray-500">Welcome back! Here's your business overview.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <Card 
            key={index} 
            className="hover:shadow-xl hover:shadow-primary/5 transition-all duration-300 hover:-translate-y-1 bg-card/50 backdrop-blur-sm border-border/50"
            data-testid={`stat-card-${stat.title.toLowerCase().replace(' ', '-')}`}
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-400">
                {stat.title}
              </CardTitle>
              <div className={`p-2 rounded-lg bg-gradient-to-br ${stat.color} shadow-lg`}>
                <stat.icon className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">{stat.value}</div>
              <p className="text-xs text-gray-500 mt-1">
                <span className="text-green-400 font-medium">{stat.change}</span> from last month
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-white">Conversation Trends</CardTitle>
            <CardDescription className="text-gray-500">Daily conversation volume over the last week</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={[
                    { date: 'Mon', count: 45 },
                    { date: 'Tue', count: 52 },
                    { date: 'Wed', count: 48 },
                    { date: 'Thu', count: 61 },
                    { date: 'Fri', count: 55 },
                    { date: 'Sat', count: 38 },
                    { date: 'Sun', count: 42 },
                  ]}
                  margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="hsl(var(--primary))" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-white">Customer Segments</CardTitle>
            <CardDescription className="text-gray-500">Distribution of customers by segment</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsBarChart
                  data={[
                    { segment: 'VIP', count: 120 },
                    { segment: 'Regular', count: 350 },
                    { segment: 'New', count: 180 },
                    { segment: 'At Risk', count: 45 },
                  ]}
                  margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                  <XAxis dataKey="segment" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
                </RechartsBarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardHeader>
          <CardTitle className="text-white">Quick Actions</CardTitle>
          <CardDescription className="text-gray-500">Frequently used features</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Start AI Chat', icon: Bot, href: '/ai-chat' },
              { label: 'Add Customer', icon: Users, href: '/crm' },
              { label: 'View Analytics', icon: BarChart, href: '/analytics' },
              { label: 'Manage Branches', icon: Store, href: '/branches' },
            ].map((action, index) => (
              <button
                key={index}
                onClick={() => window.location.href = action.href}
                className="flex flex-col items-center gap-2 p-6 rounded-xl border border-border/50 hover:border-primary/50 hover:bg-white/5 transition-all duration-200 group"
              >
                <action.icon className="h-6 w-6 text-primary group-hover:scale-110 transition-transform" />
                <span className="text-sm font-medium text-gray-300 group-hover:text-white">{action.label}</span>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}