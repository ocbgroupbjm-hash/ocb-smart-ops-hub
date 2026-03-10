import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { X, Calendar, Building2, FileText, DollarSign, Wallet } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  open: { label: 'Terbuka', color: 'bg-blue-100 text-blue-800' },
  partial: { label: 'Sebagian', color: 'bg-yellow-100 text-yellow-800' },
  paid: { label: 'Lunas', color: 'bg-green-100 text-green-800' },
  overdue: { label: 'Jatuh Tempo', color: 'bg-red-100 text-red-800' }
};

export default function APDetailModal({ ap, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('token');

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const res = await fetch(`${API}/api/ap/${ap.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setDetail(data);
        }
      } catch (err) {
        console.error('Error fetching AP detail:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [ap.id, token]);

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', { 
      style: 'currency', 
      currency: 'IDR',
      minimumFractionDigits: 0 
    }).format(val || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('id-ID');
  };

  const data = detail || ap;
  const statusCfg = STATUS_CONFIG[data.status] || STATUS_CONFIG.open;

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" 
      data-testid="ap-detail-modal"
      onClick={() => onClose(false)}
    >
      <div 
        className="bg-white rounded-lg w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-purple-600 to-purple-700 text-white">
          <div className="flex items-center gap-3">
            <Wallet className="w-6 h-6" />
            <div>
              <h2 className="text-lg font-semibold">{data.ap_no}</h2>
              <Badge className={`${statusCfg.color} text-xs`}>{statusCfg.label}</Badge>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onClose(false)} className="text-white hover:bg-purple-500">
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="text-center py-8">Memuat...</div>
          ) : (
            <>
              {/* Info Grid */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center gap-2 text-gray-500 text-sm">
                      <Building2 className="w-4 h-4" />
                      Supplier
                    </div>
                    <p className="font-medium text-lg">{data.supplier_name}</p>
                    {data.supplier_invoice_no && (
                      <p className="text-sm text-gray-500">Invoice: {data.supplier_invoice_no}</p>
                    )}
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center gap-2 text-gray-500 text-sm">
                      <Calendar className="w-4 h-4" />
                      Tanggal & Jatuh Tempo
                    </div>
                    <p className="font-medium">{formatDate(data.ap_date)}</p>
                    <p className="text-sm text-red-600">Due: {formatDate(data.due_date)}</p>
                  </CardContent>
                </Card>
              </div>

              {/* Amount Summary */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Ringkasan Nilai</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <p className="text-sm text-gray-500 mb-1">Original</p>
                      <p className="text-xl font-mono font-bold text-purple-700">
                        {formatCurrency(data.original_amount)}
                      </p>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <p className="text-sm text-gray-500 mb-1">Terbayar</p>
                      <p className="text-xl font-mono font-bold text-green-700">
                        {formatCurrency(data.paid_amount)}
                      </p>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <p className="text-sm text-gray-500 mb-1">Outstanding</p>
                      <p className="text-xl font-mono font-bold text-red-700">
                        {formatCurrency(data.outstanding_amount)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Source Info */}
              {data.source_no && (
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
                      <FileText className="w-4 h-4" />
                      Sumber Dokumen
                    </div>
                    <p className="font-medium">{data.source_type}: {data.source_no}</p>
                  </CardContent>
                </Card>
              )}

              {/* Payment History */}
              {detail?.payments && detail.payments.length > 0 && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base flex items-center gap-2">
                      <DollarSign className="w-5 h-5" />
                      Riwayat Pembayaran ({detail.payment_count})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {detail.payments.map((pay, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <p className="font-medium">{pay.payment_no}</p>
                            <p className="text-sm text-gray-500">{formatDate(pay.payment_date)}</p>
                            <p className="text-xs text-gray-400">{pay.payment_method} - {pay.reference_no || '-'}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-mono font-bold text-green-600">
                              {formatCurrency(pay.amount)}
                            </p>
                            {pay.journal_id && (
                              <p className="text-xs text-gray-400">Journal: {pay.journal_id}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Notes */}
              {data.notes && (
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-gray-500 mb-1">Catatan</p>
                    <p className="text-gray-700">{data.notes}</p>
                  </CardContent>
                </Card>
              )}

              {/* Meta Info */}
              <div className="text-xs text-gray-400 space-y-1">
                <p>Dibuat oleh: {data.created_by_name} pada {formatDateTime(data.created_at)}</p>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50">
          <Button variant="outline" onClick={() => onClose(false)}>
            Tutup
          </Button>
        </div>
      </div>
    </div>
  );
}
