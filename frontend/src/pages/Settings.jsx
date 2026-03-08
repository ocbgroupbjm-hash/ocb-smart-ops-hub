import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useAuth } from '../contexts/AuthContext';

export default function Settings() {
  const { user } = useAuth();

  return (
    <div className="space-y-6" data-testid="settings-page">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-2">Settings</h1>
        <p className="text-muted-foreground">Manage your account and preferences</p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
            <CardDescription>Update your personal details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Full Name</Label>
              <Input defaultValue={user?.full_name} />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input defaultValue={user?.email} disabled />
            </div>
            <div className="space-y-2">
              <Label>Role</Label>
              <Input defaultValue={user?.role} disabled className="capitalize" />
            </div>
            <Button>Save Changes</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Company Settings</CardTitle>
            <CardDescription>Manage your company information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Company Name</Label>
              <Input placeholder="Your Company Name" />
            </div>
            <div className="space-y-2">
              <Label>Industry</Label>
              <Input placeholder="Retail, Telecom, etc." />
            </div>
            <Button>Save Changes</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Subscription Plan</CardTitle>
            <CardDescription>Current plan: Starter</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">AI Message Quota: 10,000 messages/month</p>
                <p className="text-sm text-muted-foreground">Team Members: Unlimited</p>
              </div>
              <Button variant="outline">Upgrade Plan</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}