import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Store, MapPin, Phone, User, Plus } from 'lucide-react';
import api from '../services/api';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Label } from '../components/ui/label';

export default function Branches() {
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newBranch, setNewBranch] = useState({
    name: '',
    location: '',
    address: '',
    phone: '',
    manager_name: ''
  });

  useEffect(() => {
    loadBranches();
  }, []);

  const loadBranches = async () => {
    try {
      const response = await api.get('/branches/');
      setBranches(response.data);
    } catch (error) {
      toast.error('Failed to load branches');
      console.error('Load branches error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddBranch = async (e) => {
    e.preventDefault();
    try {
      await api.post('/branches/', newBranch);
      toast.success('Branch added successfully');
      setIsAddOpen(false);
      setNewBranch({ name: '', location: '', address: '', phone: '', manager_name: '' });
      loadBranches();
    } catch (error) {
      toast.error('Failed to add branch');
      console.error('Add branch error:', error);
    }
  };

  return (
    <div className="space-y-6" data-testid="branches-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2 bg-gradient-to-r from-red-400 via-amber-400 to-yellow-300 bg-clip-text text-transparent">Branch Management</h1>
          <p className="text-red-300/60">Monitor and manage all your business locations</p>
        </div>
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-branch-button" className="bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500 shadow-lg shadow-red-900/30">
              <Plus className="h-4 w-4 mr-2" />
              Add Branch
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gradient-to-b from-red-950/95 to-red-950/90 border-red-900/30">
            <DialogHeader>
              <DialogTitle className="text-amber-100">Add New Branch</DialogTitle>
              <DialogDescription className="text-red-300/60">Create a new branch location</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleAddBranch}>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="branch-name" className="text-red-200/80">Branch Name</Label>
                  <Input
                    id="branch-name"
                    value={newBranch.name}
                    onChange={(e) => setNewBranch({ ...newBranch, name: e.target.value })}
                    required
                    placeholder="Downtown Store"
                    data-testid="branch-name-input"
                    className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location" className="text-red-200/80">Location</Label>
                  <Input
                    id="location"
                    value={newBranch.location}
                    onChange={(e) => setNewBranch({ ...newBranch, location: e.target.value })}
                    required
                    placeholder="Jakarta"
                    className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address" className="text-red-200/80">Address</Label>
                  <Input
                    id="address"
                    value={newBranch.address}
                    onChange={(e) => setNewBranch({ ...newBranch, address: e.target.value })}
                    placeholder="Full address"
                    className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone" className="text-red-200/80">Phone</Label>
                  <Input
                    id="phone"
                    value={newBranch.phone}
                    onChange={(e) => setNewBranch({ ...newBranch, phone: e.target.value })}
                    placeholder="+62 xxx xxx"
                    className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="manager" className="text-red-200/80">Manager Name</Label>
                  <Input
                    id="manager"
                    value={newBranch.manager_name}
                    onChange={(e) => setNewBranch({ ...newBranch, manager_name: e.target.value })}
                    placeholder="Manager name"
                    className="bg-red-950/30 border-red-900/30 text-amber-50 placeholder:text-red-300/40"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" data-testid="save-branch-button" className="bg-gradient-to-r from-red-700 to-red-600 hover:from-red-600 hover:to-red-500">Save Branch</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Branch Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600"></div>
          </div>
        ) : branches.length === 0 ? (
          <Card className="col-span-full bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Store className="h-16 w-16 text-red-400/50 mb-4" />
              <p className="text-red-300/60 mb-4">No branches found</p>
              <Button onClick={() => setIsAddOpen(true)} className="bg-gradient-to-r from-red-700 to-red-600">Add Your First Branch</Button>
            </CardContent>
          </Card>
        ) : (
          branches.map((branch) => (
            <Card key={branch.id} className="hover:shadow-xl hover:shadow-red-900/20 transition-all duration-300 bg-gradient-to-br from-red-950/40 to-red-950/20 border-red-900/30" data-testid="branch-card">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-gradient-to-br from-red-600 to-amber-500">
                      <Store className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <CardTitle className="text-lg text-amber-100">{branch.name}</CardTitle>
                      <p className="text-sm text-red-300/60">{branch.location}</p>
                    </div>
                  </div>
                  {branch.is_active && (
                    <span className="px-2 py-1 text-xs rounded-full bg-green-900/30 text-green-400 border border-green-700/30">
                      Active
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {branch.address && (
                  <div className="flex items-start gap-2 text-sm text-red-200/70">
                    <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>{branch.address}</span>
                  </div>
                )}
                {branch.phone && (
                  <div className="flex items-center gap-2 text-sm text-red-200/70">
                    <Phone className="h-4 w-4" />
                    {branch.phone}
                  </div>
                )}
                {branch.manager_name && (
                  <div className="flex items-center gap-2 text-sm text-red-200/70">
                    <User className="h-4 w-4" />
                    {branch.manager_name}
                  </div>
                )}
                <div className="pt-3 mt-3 border-t border-red-900/30">
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-amber-400">0</div>
                      <div className="text-xs text-red-300/50">Sales Today</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-amber-400">0</div>
                      <div className="text-xs text-red-300/50">Staff</div>
                    </div>
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