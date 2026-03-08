import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { BarChart, TrendingUp, DollarSign, Package } from 'lucide-react';

export default function Analytics() {
  return (
    <div className="space-y-6" data-testid="analytics-page">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-2 bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent">Business Analytics</h1>
        <p className="text-red-300/60">Comprehensive insights and performance metrics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: 'Total Revenue', value: '$0', icon: DollarSign, color: 'from-green-600 to-green-700' },
          { title: 'Growth Rate', value: '+0%', icon: TrendingUp, color: 'from-red-600 to-red-700' },
          { title: 'Products Sold', value: '0', icon: Package, color: 'from-amber-500 to-amber-600' },
          { title: 'Avg Order Value', value: '$0', icon: BarChart, color: 'from-red-700 to-red-800' },
        ].map((stat, index) => (
          <Card key={index} className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-red-200/70">{stat.title}</CardTitle>
              <div className={`p-2 rounded-lg bg-gradient-to-br ${stat.color}`}>
                <stat.icon className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-amber-100">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
        <CardContent className="flex items-center justify-center py-20">
          <div className="text-center">
            <BarChart className="h-16 w-16 text-red-400/50 mx-auto mb-4" />
            <p className="text-red-300/60">Advanced analytics coming soon</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}