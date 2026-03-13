/**
 * OCB TITAN AI - Backup Manager Page
 * ===================================
 * System → Backup Manager
 * 
 * Features:
 * - Create Backup (3 levels)
 * - Download Backup
 * - Restore Backup
 * - Schedule Backup
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../../components/ui/dialog';
import { Switch } from '../../components/ui/switch';
import { Label } from '../../components/ui/label';
import { 
  Database, Download, Upload, Clock, Trash2, RefreshCw, 
  Archive, FileJson, HardDrive, CheckCircle, AlertCircle,
  Calendar, Settings
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function BackupManager() {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [schedule, setSchedule] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [backupType, setBackupType] = useState('full');
  const [message, setMessage] = useState({ type: '', text: '' });

  const getToken = () => localStorage.getItem('token');

  const fetchBackups = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/api/backup/list`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await response.json();
      setBackups(data.backups || []);
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to load backups' });
    } finally {
      setLoading(false);
    }
  };

  const fetchSchedule = async () => {
    try {
      const response = await fetch(`${API_URL}/api/backup/schedule`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await response.json();
      setSchedule(data);
    } catch (err) {
      console.error('Failed to load schedule');
    }
  };

  useEffect(() => {
    fetchBackups();
    fetchSchedule();
  }, []);

  const handleCreateBackup = async () => {
    setCreating(true);
    try {
      const response = await fetch(`${API_URL}/api/backup/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({
          backup_type: backupType,
          tenants: null
        })
      });
      const data = await response.json();
      
      if (data.status === 'SUCCESS') {
        setMessage({ type: 'success', text: `Backup created: ${data.file?.split('/').pop()}` });
        fetchBackups();
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to create backup' });
      }
      setShowCreateDialog(false);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setCreating(false);
    }
  };

  const handleDownload = (filename) => {
    window.open(`${API_URL}/api/backup/download/${filename}`, '_blank');
  };

  const handleDelete = async (filename) => {
    if (!window.confirm(`Delete backup ${filename}?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/api/backup/${filename}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      
      if (response.ok) {
        setMessage({ type: 'success', text: 'Backup deleted' });
        fetchBackups();
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to delete backup' });
    }
  };

  const handleRestore = async (dryRun = true) => {
    if (!selectedBackup) return;
    
    setRestoring(true);
    try {
      const response = await fetch(`${API_URL}/api/backup/restore`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({
          filename: selectedBackup,
          dry_run: dryRun
        })
      });
      const data = await response.json();
      
      if (data.status === 'DRY_RUN_COMPLETE') {
        setMessage({ 
          type: 'info', 
          text: `Dry run complete. Package contains ${data.tenants_in_package?.length || 0} tenants.` 
        });
      } else if (data.status === 'SUCCESS') {
        setMessage({ type: 'success', text: 'Restore completed successfully!' });
      } else {
        setMessage({ type: 'error', text: data.error || 'Restore failed' });
      }
      
      if (!dryRun) setShowRestoreDialog(false);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setRestoring(false);
    }
  };

  const handleSaveSchedule = async () => {
    try {
      const response = await fetch(`${API_URL}/api/backup/schedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify(schedule)
      });
      
      if (response.ok) {
        setMessage({ type: 'success', text: 'Schedule saved' });
        setShowScheduleDialog(false);
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to save schedule' });
    }
  };

  const getBackupIcon = (type) => {
    if (type === 'ocb') return <Archive className="w-5 h-5 text-blue-500" />;
    if (type === 'json') return <FileJson className="w-5 h-5 text-green-500" />;
    return <Database className="w-5 h-5 text-purple-500" />;
  };

  const getBackupTypeBadge = (filename) => {
    if (filename.startsWith('system_backup')) return <Badge className="bg-blue-500">Full Package</Badge>;
    if (filename.startsWith('snapshot_')) return <Badge className="bg-green-500">Snapshot</Badge>;
    if (filename.startsWith('backup_')) return <Badge className="bg-purple-500">Database</Badge>;
    return <Badge>Unknown</Badge>;
  };

  return (
    <div className="p-6 space-y-6" data-testid="backup-manager-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <HardDrive className="w-6 h-6" />
            Backup Manager
          </h1>
          <p className="text-gray-500">Kelola backup dan restore system</p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            data-testid="btn-schedule"
            onClick={() => setShowScheduleDialog(true)}
          >
            <Calendar className="w-4 h-4 mr-2" />
            Schedule
          </Button>
          
          <Button
            data-testid="btn-create-backup"
            onClick={() => setShowCreateDialog(true)}
          >
            <Archive className="w-4 h-4 mr-2" />
            Create Backup
          </Button>
        </div>
      </div>

      {/* Message */}
      {message.text && (
        <div className={`p-4 rounded flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-50 text-green-700' :
          message.type === 'error' ? 'bg-red-50 text-red-700' :
          'bg-blue-50 text-blue-700'
        }`}>
          {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
          {message.text}
          <button onClick={() => setMessage({ type: '', text: '' })} className="ml-auto">×</button>
        </div>
      )}

      {/* Schedule Status */}
      {schedule && (
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-gray-500" />
              <span>Auto Backup: {schedule.enabled ? `${schedule.frequency} at ${schedule.time}` : 'Disabled'}</span>
            </div>
            <Badge className={schedule.enabled ? 'bg-green-500' : 'bg-gray-500'}>
              {schedule.enabled ? 'Active' : 'Inactive'}
            </Badge>
          </CardContent>
        </Card>
      )}

      {/* Backup List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Available Backups</span>
            <Button variant="ghost" size="sm" onClick={fetchBackups}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-center text-gray-500 py-8">Loading backups...</p>
          ) : backups.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No backups found</p>
          ) : (
            <div className="space-y-3">
              {backups.map((backup) => (
                <div 
                  key={backup.filename}
                  data-testid={`backup-item-${backup.filename}`}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    {getBackupIcon(backup.type)}
                    <div>
                      <p className="font-medium">{backup.filename}</p>
                      <p className="text-sm text-gray-500">
                        {backup.size_mb} MB • {new Date(backup.created).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getBackupTypeBadge(backup.filename)}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDownload(backup.filename)}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                    {backup.type === 'ocb' && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setSelectedBackup(backup.filename);
                          setShowRestoreDialog(true);
                        }}
                      >
                        <Upload className="w-4 h-4" />
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDelete(backup.filename)}
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Backup Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Backup</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Backup Type</Label>
              <Select value={backupType} onValueChange={setBackupType}>
                <SelectTrigger data-testid="select-backup-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="database">
                    <div className="flex items-center gap-2">
                      <Database className="w-4 h-4" />
                      Database Backup (tar.gz)
                    </div>
                  </SelectItem>
                  <SelectItem value="snapshot">
                    <div className="flex items-center gap-2">
                      <FileJson className="w-4 h-4" />
                      Business Snapshot (JSON)
                    </div>
                  </SelectItem>
                  <SelectItem value="full">
                    <div className="flex items-center gap-2">
                      <Archive className="w-4 h-4" />
                      Full Restore Package (.ocb)
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="text-sm text-gray-500">
              {backupType === 'database' && 'Creates a MongoDB dump of the current database.'}
              {backupType === 'snapshot' && 'Creates a readable snapshot with TB, BS, P&L, Inventory.'}
              {backupType === 'full' && 'Creates a complete restore package with all tenants.'}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateBackup} disabled={creating} data-testid="btn-confirm-backup">
              {creating ? 'Creating...' : 'Create Backup'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Restore Dialog */}
      <Dialog open={showRestoreDialog} onOpenChange={setShowRestoreDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Restore from Backup</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p>
              <strong>File:</strong> {selectedBackup}
            </p>
            <div className="bg-yellow-50 border border-yellow-200 p-3 rounded text-sm">
              <p className="font-medium text-yellow-800">Warning</p>
              <p className="text-yellow-700">
                Restoring will overwrite existing data. Run a dry run first to verify.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRestoreDialog(false)}>Cancel</Button>
            <Button variant="outline" onClick={() => handleRestore(true)} disabled={restoring}>
              {restoring ? 'Checking...' : 'Dry Run'}
            </Button>
            <Button onClick={() => handleRestore(false)} disabled={restoring} className="bg-red-500 hover:bg-red-600">
              {restoring ? 'Restoring...' : 'Restore Now'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Schedule Dialog */}
      <Dialog open={showScheduleDialog} onOpenChange={setShowScheduleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Backup Schedule</DialogTitle>
          </DialogHeader>
          {schedule && (
            <div className="space-y-4 py-4">
              <div className="flex items-center justify-between">
                <Label>Enable Auto Backup</Label>
                <Switch
                  checked={schedule.enabled}
                  onCheckedChange={(v) => setSchedule({ ...schedule, enabled: v })}
                />
              </div>
              <div>
                <Label>Frequency</Label>
                <Select 
                  value={schedule.frequency} 
                  onValueChange={(v) => setSchedule({ ...schedule, frequency: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Time</Label>
                <Select 
                  value={schedule.time} 
                  onValueChange={(v) => setSchedule({ ...schedule, time: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="00:00">00:00</SelectItem>
                    <SelectItem value="02:00">02:00</SelectItem>
                    <SelectItem value="04:00">04:00</SelectItem>
                    <SelectItem value="06:00">06:00</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowScheduleDialog(false)}>Cancel</Button>
            <Button onClick={handleSaveSchedule}>Save Schedule</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
