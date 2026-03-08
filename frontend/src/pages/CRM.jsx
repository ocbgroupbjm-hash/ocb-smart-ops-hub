import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Plus, Search, Mail, Phone, MapPin } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

export default function CRM() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newCustomer, setNewCustomer] = useState({
    name: '',
    phone: '',
    email: '',
    location: '',
    segment: 'regular'
  });

  useEffect(() => {
    loadCustomers();
  }, [search]);

  const loadCustomers = async () => {
    try {
      const response = await api.get('/customers/', { params: { search } });
      setCustomers(response.data);
    } catch (error) {
      toast.error('Failed to load customers');
      console.error('Load customers error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCustomer = async (e) => {
    e.preventDefault();
    try {
      await api.post('/customers/', newCustomer);
      toast.success('Customer added successfully');
      setIsAddOpen(false);
      setNewCustomer({ name: '', phone: '', email: '', location: '', segment: 'regular' });
      loadCustomers();
    } catch (error) {
      toast.error('Failed to add customer');
      console.error('Add customer error:', error);
    }
  };

  const segmentColors = {
    vip: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100',
    regular: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100',
    new: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100',
    at_risk: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100'
  };

  return (
    <div className="space-y-6" data-testid="crm-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2 bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent">Customer CRM</h1>
          <p className="text-red-300/60">Manage and track your customer relationships</p>
        </div>
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-customer-button" className="bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500 shadow-lg shadow-red-900/30">
              <Plus className="h-4 w-4 mr-2" />
              Add Customer
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gradient-to-b from-red-950/95 to-red-950/90 border-red-900/30">
            <DialogHeader>
              <DialogTitle className="text-amber-100">Add New Customer</DialogTitle>
              <DialogDescription className="text-red-300/60">Create a new customer record in your CRM</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleAddCustomer}>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name" className="text-red-200/80">Name</Label>
                  <Input
                    id="name"
                    value={newCustomer.name}
                    onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
                    required
                    data-testid="customer-name-input"
                    className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone" className="text-red-200/80">Phone</Label>
                  <Input
                    id="phone"
                    value={newCustomer.phone}
                    onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
                    className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-red-200/80">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={newCustomer.email}
                    onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
                    className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location" className="text-red-200/80">Location</Label>
                  <Input
                    id="location"
                    value={newCustomer.location}
                    onChange={(e) => setNewCustomer({ ...newCustomer, location: e.target.value })}
                    className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="segment" className="text-red-200/80">Segment</Label>
                  <Select value={newCustomer.segment} onValueChange={(value) => setNewCustomer({ ...newCustomer, segment: value })}>
                    <SelectTrigger className="bg-red-950/30 border-red-900/30 text-amber-50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-red-950/95 border-red-900/30">
                      <SelectItem value="regular">Regular</SelectItem>
                      <SelectItem value="vip">VIP</SelectItem>
                      <SelectItem value="new">New</SelectItem>
                      <SelectItem value="at_risk">At Risk</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" data-testid="save-customer-button" className="bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500">Save Customer</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <Card className="bg-gradient-to-br from-red-950/40 to-red-950/20 backdrop-blur-sm border-red-900/30">
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-red-400/60" />
            <Input
              placeholder="Search customers by name, phone, or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40"
              data-testid="customer-search-input"
            />
          </div>
        </CardContent>
      </Card>

      {/* Customer List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
          </div>
        ) : customers.length === 0 ? (
          <Card className="col-span-full bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-red-300/60 mb-4">No customers found</p>
              <Button onClick={() => setIsAddOpen(true)} className="bg-gradient-to-r from-red-700 to-red-600">Add Your First Customer</Button>
            </CardContent>
          </Card>
        ) : (
          customers.map((customer) => (
            <Card key={customer.id} className="hover:shadow-xl hover:shadow-red-900/20 transition-all duration-300 bg-gradient-to-br from-red-950/40 to-red-950/20 backdrop-blur-sm border-red-900/30" data-testid="customer-card">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg text-amber-100">{customer.name}</CardTitle>
                    {customer.segment && (
                      <Badge className={`mt-2 ${segmentColors[customer.segment] || ''}`}>
                        {customer.segment.replace('_', ' ').toUpperCase()}
                      </Badge>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-amber-400">
                      ${customer.lifetime_value.toFixed(0)}
                    </div>
                    <div className="text-xs text-red-300/50">LTV</div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {customer.phone && (
                  <div className="flex items-center gap-2 text-sm text-red-200/70">
                    <Phone className="h-4 w-4" />
                    {customer.phone}
                  </div>
                )}
                {customer.email && (
                  <div className="flex items-center gap-2 text-sm text-red-200/70">
                    <Mail className="h-4 w-4" />
                    {customer.email}
                  </div>
                )}
                {customer.location && (
                  <div className="flex items-center gap-2 text-sm text-red-200/70">
                    <MapPin className="h-4 w-4" />
                    {customer.location}
                  </div>
                )}
                <div className="pt-2 mt-2 border-t border-red-900/30">
                  <div className="text-xs text-red-300/50">
                    {customer.total_orders} orders · Joined {new Date(customer.created_at).toLocaleDateString()}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}