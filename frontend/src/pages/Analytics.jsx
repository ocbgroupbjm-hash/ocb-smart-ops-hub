import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { BarChart, TrendingUp, DollarSign, Package } from 'lucide-react';

export default function Analytics() {
  return (
    <div className="space-y-6" data-testid="analytics-page">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-2">Business Analytics</h1>
        <p className="text-muted-foreground">Comprehensive insights and performance metrics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { title: 'Total Revenue', value: '$0', icon: DollarSign, color: 'from-green-500 to-green-600' },
          { title: 'Growth Rate', value: '+0%', icon: TrendingUp, color: 'from-blue-500 to-blue-600' },
          { title: 'Products Sold', value: '0', icon: Package, color: 'from-purple-500 to-purple-600' },
          { title: 'Avg Order Value', value: '$0', icon: BarChart, color: 'from-orange-500 to-orange-600' },
        ].map((stat, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
              <div className={`p-2 rounded-lg bg-gradient-to-br ${stat.color}`}>
                <stat.icon className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardContent className="flex items-center justify-center py-20">
          <div className="text-center">
            <BarChart className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Advanced analytics coming soon</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}