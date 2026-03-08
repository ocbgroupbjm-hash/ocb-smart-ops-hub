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
      const response = await api.get('/customers', { params: { search } });
      setCustomers(response.data);
    } catch (error) {
      toast.error('Failed to load customers');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCustomer = async (e) => {
    e.preventDefault();
    try {
      await api.post('/customers', newCustomer);
      toast.success('Customer added successfully');
      setIsAddOpen(false);
      setNewCustomer({ name: '', phone: '', email: '', location: '', segment: 'regular' });
      loadCustomers();
    } catch (error) {
      toast.error('Failed to add customer');
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
          <h1 className="text-4xl font-bold tracking-tight mb-2">Customer CRM</h1>
          <p className="text-muted-foreground">Manage and track your customer relationships</p>
        </div>
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-customer-button">
              <Plus className="h-4 w-4 mr-2" />
              Add Customer
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add New Customer</DialogTitle>
              <DialogDescription>Create a new customer record in your CRM</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleAddCustomer}>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={newCustomer.name}
                    onChange={(e) => setNewCustomer({ ...newCustomer, name: e.target.value })}
                    required
                    data-testid="customer-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    value={newCustomer.phone}
                    onChange={(e) => setNewCustomer({ ...newCustomer, phone: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={newCustomer.email}
                    onChange={(e) => setNewCustomer({ ...newCustomer, email: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    value={newCustomer.location}
                    onChange={(e) => setNewCustomer({ ...newCustomer, location: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="segment">Segment</Label>
                  <Select value={newCustomer.segment} onValueChange={(value) => setNewCustomer({ ...newCustomer, segment: value })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="regular">Regular</SelectItem>
                      <SelectItem value="vip">VIP</SelectItem>
                      <SelectItem value="new">New</SelectItem>
                      <SelectItem value="at_risk">At Risk</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" data-testid="save-customer-button">Save Customer</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search customers by name, phone, or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
              data-testid="customer-search-input"
            />
          </div>
        </CardContent>
      </Card>

      {/* Customer List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : customers.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-muted-foreground mb-4">No customers found</p>
              <Button onClick={() => setIsAddOpen(true)}>Add Your First Customer</Button>
            </CardContent>
          </Card>
        ) : (
          customers.map((customer) => (
            <Card key={customer.id} className="hover:shadow-lg transition-all duration-300" data-testid="customer-card">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{customer.name}</CardTitle>
                    {customer.segment && (
                      <Badge className={`mt-2 ${segmentColors[customer.segment] || ''}`}>
                        {customer.segment.replace('_', ' ').toUpperCase()}
                      </Badge>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-primary">
                      ${customer.lifetime_value.toFixed(0)}
                    </div>
                    <div className="text-xs text-muted-foreground">LTV</div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {customer.phone && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Phone className="h-4 w-4" />
                    {customer.phone}
                  </div>
                )}
                {customer.email && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Mail className="h-4 w-4" />
                    {customer.email}
                  </div>
                )}
                {customer.location && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    {customer.location}
                  </div>
                )}
                <div className="pt-2 mt-2 border-t">
                  <div className="text-xs text-muted-foreground">
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