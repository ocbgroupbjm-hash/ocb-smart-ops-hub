import React from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Package } from 'lucide-react';

export default function Inventory() {
  return (
    <div className="space-y-6" data-testid="inventory-page">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-2">Inventory Management</h1>
        <p className="text-muted-foreground">Track and manage your product stock</p>
      </div>

      <Card>
        <CardContent className="flex items-center justify-center py-20">
          <div className="text-center">
            <Package className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Inventory tracking coming soon</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}