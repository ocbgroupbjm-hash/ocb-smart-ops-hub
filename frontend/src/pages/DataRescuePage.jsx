import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Database, 
  RefreshCw, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle,
  FileText,
  Download,
  Play,
  Loader2,
  ArrowRight,
  BarChart3,
  Package,
  Receipt,
  Wallet,
  BookOpen
} from 'lucide-react';
import { toast } from 'sonner';

import { getApiUrl } from '../utils/apiConfig';
const API_URL = getApiUrl();

export default function DataRescuePage() {
  const [status, setStatus] = useState(null);
  const [iposStats, setIposStats] = useState(null);
  const [reconciliation, setReconciliation] = useState(null);
  const [stagingData, setStagingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [reconciling, setReconciling] = useState(false);

  const token = localStorage.getItem('token');
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
    'X-Tenant-ID': 'ocb_titan'
  };

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [statusRes, statsRes, reconRes, summaryRes] = await Promise.all([
        fetch(`${API_URL}/api/data-rescue/status`, { headers }),
        fetch(`${API_URL}/api/data-rescue/stats/ipos`, { headers }),
        fetch(`${API_URL}/api/data-rescue/reconcile/latest`, { headers }),
        fetch(`${API_URL}/api/data-rescue/staging/summary`, { headers })
      ]);

      if (statusRes.ok) setStatus(await statusRes.json());
      if (statsRes.ok) setIposStats(await statsRes.json());
      if (reconRes.ok) setReconciliation(await reconRes.json());
      if (summaryRes.ok) setStagingData(await summaryRes.json());
    } catch (error) {
      toast.error('Gagal memuat data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const startExtraction = async () => {
    setExtracting(true);
    try {
      const res = await fetch(`${API_URL}/api/data-rescue/extract`, {
        method: 'POST',
        headers
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Extraction dimulai! Batch: ${data.batch_id}`);
        setTimeout(fetchAll, 5000);
      } else {
        toast.error('Gagal memulai extraction');
      }
    } catch (error) {
      toast.error('Error: ' + error.message);
    } finally {
      setExtracting(false);
    }
  };

  const runReconciliation = async () => {
    setReconciling(true);
    try {
      const res = await fetch(`${API_URL}/api/data-rescue/reconcile`, {
        method: 'POST',
        headers
      });
      if (res.ok) {
        const data = await res.json();
        setReconciliation(data);
        toast.success('Reconciliation selesai!');
      } else {
        toast.error('Gagal menjalankan reconciliation');
      }
    } catch (error) {
      toast.error('Error: ' + error.message);
    } finally {
      setReconciling(false);
    }
  };

  const downloadReport = async () => {
    try {
      const res = await fetch(`${API_URL}/api/data-rescue/report`, { headers });
      if (res.ok) {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `data_rescue_report_${new Date().toISOString().slice(0,10)}.json`;
        a.click();
        toast.success('Report downloaded!');
      }
    } catch (error) {
      toast.error('Gagal download report');
    }
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return '0';
    return new Intl.NumberFormat('id-ID').format(num);
  };

  const formatCurrency = (num) => {
    if (num === null || num === undefined) return 'Rp 0';
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(num);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2 text-lg">Memuat Data Rescue Dashboard...</span>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-slate-50 dark:bg-slate-900 min-h-screen" data-testid="data-rescue-page">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
            <Database className="h-8 w-8 text-blue-500" />
            Data Rescue Center
          </h1>
          <p className="text-slate-500 mt-1">
            iPOS 5 Ultimate → OCB TITAN Migration & Reconciliation
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchAll} data-testid="refresh-btn">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={downloadReport} data-testid="download-report-btn">
            <Download className="h-4 w-4 mr-2" />
            Download Report
          </Button>
        </div>
      </div>

      {/* Status Banner */}
      {status && (
        <Alert className={status.backup_exists ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}>
          <Database className="h-4 w-4" />
          <AlertDescription>
            <strong>Backup File:</strong> {status.backup_path}
            <Badge className="ml-2" variant={status.backup_exists ? 'default' : 'destructive'}>
              {status.backup_exists ? 'TERSEDIA' : 'TIDAK DITEMUKAN'}
            </Badge>
          </AlertDescription>
        </Alert>
      )}

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* iPOS Stock */}
        <Card data-testid="ipos-stock-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
              <Package className="h-4 w-4" />
              iPOS Stock
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatNumber(iposStats?.inventory?.total_qty || 0)}
            </div>
            <p className="text-xs text-slate-500">Total units dari backup</p>
          </CardContent>
        </Card>

        {/* iPOS Sales */}
        <Card data-testid="ipos-sales-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
              <Receipt className="h-4 w-4" />
              iPOS Sales
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatNumber(iposStats?.sales?.count || 0)}
            </div>
            <p className="text-xs text-slate-500">Transaksi penjualan</p>
          </CardContent>
        </Card>

        {/* iPOS Journals */}
        <Card data-testid="ipos-journals-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              iPOS Journals
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatNumber(iposStats?.journals?.count || 0)}
            </div>
            <p className="text-xs text-slate-500">
              Balance: {formatCurrency(iposStats?.journals?.balance || 0)}
            </p>
          </CardContent>
        </Card>

        {/* Journal Status */}
        <Card data-testid="journal-status-card" className={
          iposStats?.journals?.balance === 0 ? 'border-green-500' : 'border-red-500'
        }>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500 flex items-center gap-2">
              <Wallet className="h-4 w-4" />
              Journal Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {Math.abs(iposStats?.journals?.balance || 0) < 1 ? (
                <>
                  <CheckCircle2 className="h-6 w-6 text-green-500" />
                  <span className="text-lg font-bold text-green-600">BALANCED</span>
                </>
              ) : (
                <>
                  <XCircle className="h-6 w-6 text-red-500" />
                  <span className="text-lg font-bold text-red-600">UNBALANCED</span>
                </>
              )}
            </div>
            {Math.abs(iposStats?.journals?.balance || 0) >= 1 && (
              <p className="text-xs text-red-500 mt-1">
                Selisih: {formatCurrency(iposStats?.journals?.balance || 0)}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="staging" className="space-y-4">
        <TabsList>
          <TabsTrigger value="staging">Staging Data</TabsTrigger>
          <TabsTrigger value="reconciliation">Reconciliation</TabsTrigger>
          <TabsTrigger value="actions">Actions</TabsTrigger>
        </TabsList>

        {/* Staging Tab */}
        <TabsContent value="staging" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Staging Collections</CardTitle>
              <CardDescription>
                Data yang telah diekstrak dari iPOS 5 backup dan disimpan di staging area
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {stagingData?.collections && Object.entries(stagingData.collections).map(([name, count]) => (
                  <div key={name} className="p-4 bg-slate-100 dark:bg-slate-800 rounded-lg" data-testid={`staging-${name}`}>
                    <div className="text-lg font-bold">{formatNumber(count)}</div>
                    <div className="text-sm text-slate-500">{name.replace(/_/g, ' ')}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reconciliation Tab */}
        <TabsContent value="reconciliation" className="space-y-4">
          {reconciliation?.overall_status ? (
            <>
              {/* Overall Status */}
              <Alert className={reconciliation.overall_status === 'PASS' ? 'border-green-500' : 'border-red-500'}>
                {reconciliation.overall_status === 'PASS' ? (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                )}
                <AlertDescription>
                  <strong>Overall Status: {reconciliation.overall_status}</strong>
                  <span className="ml-2 text-sm text-slate-500">
                    ({reconciliation.summary?.passed || 0} passed, {reconciliation.summary?.failed || 0} failed)
                  </span>
                </AlertDescription>
              </Alert>

              {/* Check Results */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {reconciliation.checks && Object.entries(reconciliation.checks).map(([name, check]) => (
                  <Card key={name} className={check.status === 'PASS' ? '' : 'border-red-300'} data-testid={`check-${name}`}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center justify-between">
                        <span>{check.check_name}</span>
                        <Badge variant={check.status === 'PASS' ? 'default' : 'destructive'}>
                          {check.status}
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm">
                      {check.ipos_total !== undefined && (
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span>iPOS:</span>
                            <span className="font-mono">{formatNumber(check.ipos_total)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>TITAN:</span>
                            <span className="font-mono">{formatNumber(check.titan_total)}</span>
                          </div>
                          {check.difference !== 0 && (
                            <div className="flex justify-between text-red-500">
                              <span>Selisih:</span>
                              <span className="font-mono">{formatNumber(check.difference)}</span>
                            </div>
                          )}
                        </div>
                      )}
                      {check.ipos_value !== undefined && (
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span>iPOS:</span>
                            <span className="font-mono">{formatCurrency(check.ipos_value)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>TITAN:</span>
                            <span className="font-mono">{formatCurrency(check.titan_value)}</span>
                          </div>
                        </div>
                      )}
                      {check.ipos_debit !== undefined && (
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span>Debit:</span>
                            <span className="font-mono">{formatCurrency(check.ipos_debit)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Credit:</span>
                            <span className="font-mono">{formatCurrency(check.ipos_credit)}</span>
                          </div>
                          <div className="flex justify-between font-bold">
                            <span>Balance:</span>
                            <span className={`font-mono ${check.ipos_balance !== 0 ? 'text-red-500' : 'text-green-500'}`}>
                              {formatCurrency(check.ipos_balance)}
                            </span>
                          </div>
                        </div>
                      )}
                      {check.counts && (
                        <div className="space-y-1">
                          {Object.entries(check.counts).map(([entity, counts]) => (
                            <div key={entity} className="flex justify-between text-xs">
                              <span>{entity}:</span>
                              <span>
                                iPOS={counts.ipos}, TITAN={counts.titan}
                                {counts.difference !== 0 && (
                                  <span className="text-red-500 ml-1">(diff: {counts.difference})</span>
                                )}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                      {check.mismatch_count > 0 && (
                        <div className="mt-2 text-red-500 text-xs">
                          {check.mismatch_count} item berbeda
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Critical Issues */}
              {reconciliation.summary?.critical_issues?.length > 0 && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Critical Issues:</strong>
                    <ul className="list-disc ml-4 mt-2">
                      {reconciliation.summary.critical_issues.map((issue, i) => (
                        <li key={i}>{issue}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              {/* Recommendations */}
              {reconciliation.summary?.recommendations?.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {reconciliation.summary.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <ArrowRight className="h-4 w-4 mt-0.5 text-blue-500" />
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="py-8 text-center">
                <BarChart3 className="h-12 w-12 mx-auto text-slate-400 mb-4" />
                <p className="text-slate-500">Belum ada hasil reconciliation.</p>
                <Button className="mt-4" onClick={runReconciliation} disabled={reconciling}>
                  {reconciling ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
                  Jalankan Reconciliation
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Actions Tab */}
        <TabsContent value="actions" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Extract Data
                </CardTitle>
                <CardDescription>
                  Ekstrak data dari backup iPOS 5 ke staging area
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button onClick={startExtraction} disabled={extracting} className="w-full" data-testid="extract-btn">
                  {extracting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Extracting...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Start Extraction
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Run Reconciliation
                </CardTitle>
                <CardDescription>
                  Bandingkan data staging dengan OCB TITAN production
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button onClick={runReconciliation} disabled={reconciling} className="w-full" data-testid="reconcile-btn">
                  {reconciling ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Run Reconciliation
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Batch History */}
          {status?.latest_batch && (
            <Card>
              <CardHeader>
                <CardTitle>Latest Batch</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500">Batch ID</div>
                    <div className="font-mono text-sm">{status.latest_batch.batch_id}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500">Status</div>
                    <Badge>{status.latest_batch.status}</Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500">Created At</div>
                    <div className="text-sm">{status.latest_batch.created_at}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
