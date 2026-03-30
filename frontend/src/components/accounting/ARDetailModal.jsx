import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { X, Calendar, User, FileText, DollarSign, CreditCard, RefreshCw } from 'lucide-react';

import { getApiUrl } from '../../utils/apiConfig';
const API = getApiUrl();

// OCB TITAN Design Tokens - Dark Enterprise Theme
const DESIGN = {
  text: {
    primary: 'text-[#E5E7EB]',
    secondary: 'text-[#9CA3AF]',
    accent: 'text-[#F97316]',
  },
  bg: {
    modal: 'bg-[#1E293B]',
    card: 'bg-[#0F172A]',
  },
  border: {
    default: 'border-[#334155]',
  }
};

const STATUS_CONFIG = {
  open: { label: 'Terbuka', color: 'bg-blue-500/20 text-blue-400' },
  partial: { label: 'Sebagian', color: 'bg-amber-500/20 text-amber-400' },
  paid: { label: 'Lunas', color: 'bg-emerald-500/20 text-emerald-400' },
  overdue: { label: 'Jatuh Tempo', color: 'bg-rose-500/20 text-rose-400' },
  written_off: { label: 'Dihapuskan', color: 'bg-slate-500/20 text-slate-400' }
};

export default function ARDetailModal({ ar, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('token');

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const res = await fetch(`${API}/api/ar/${ar.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setDetail(data);
        }
      } catch (err) {
        console.error('Error fetching AR detail:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [ar.id, token]);

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

  const data = detail || ar;
  const statusCfg = STATUS_CONFIG[data.status] || STATUS_CONFIG.open;

  return (
    <div 
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" 
      data-testid="ar-detail-modal"
      onClick={() => onClose(false)}
    >
      <div 
        className={`${DESIGN.bg.modal} ${DESIGN.border.default} border rounded-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#334155] bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-t-xl">
          <div className="flex items-center gap-3">
            <CreditCard className="w-6 h-6" />
            <div>
              <h2 className="text-lg font-semibold">{data.ar_no}</h2>
              <p className="text-sm text-emerald-100">{data.customer_name}</p>
            </div>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => onClose(false)} 
            className="text-white hover:bg-emerald-600/50"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className={`w-6 h-6 animate-spin ${DESIGN.text.accent}`} />
              <span className={`ml-2 ${DESIGN.text.secondary}`}>Memuat...</span>
            </div>
          ) : (
            <>
              {/* Status & Amount Summary */}
              <div className="grid grid-cols-3 gap-4">
                <div className={`${DESIGN.bg.card} ${DESIGN.border.default} border rounded-lg p-4`}>
                  <p className={`text-sm ${DESIGN.text.secondary}`}>Status</p>
                  <Badge className={`mt-1 ${statusCfg.color}`}>{statusCfg.label}</Badge>
                </div>
                <div className={`${DESIGN.bg.card} ${DESIGN.border.default} border rounded-lg p-4`}>
                  <p className={`text-sm ${DESIGN.text.secondary}`}>Total Piutang</p>
                  <p className={`font-mono font-bold text-lg ${DESIGN.text.primary}`}>
                    {formatCurrency(data.original_amount)}
                  </p>
                </div>
                <div className={`${DESIGN.bg.card} ${DESIGN.border.default} border rounded-lg p-4`}>
                  <p className={`text-sm ${DESIGN.text.secondary}`}>Outstanding</p>
                  <p className="font-mono font-bold text-lg text-emerald-400">
                    {formatCurrency(data.outstanding_amount)}
                  </p>
                </div>
              </div>

              {/* Info Grid */}
              <div className={`${DESIGN.bg.card} ${DESIGN.border.default} border rounded-lg p-4`}>
                <h3 className={`font-semibold ${DESIGN.text.primary} mb-4`}>Informasi Piutang</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <User className={`w-4 h-4 ${DESIGN.text.secondary}`} />
                      <span className={`text-sm ${DESIGN.text.secondary}`}>Customer</span>
                    </div>
                    <p className={DESIGN.text.primary}>{data.customer_name || '-'}</p>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <FileText className={`w-4 h-4 ${DESIGN.text.secondary}`} />
                      <span className={`text-sm ${DESIGN.text.secondary}`}>No. Invoice</span>
                    </div>
                    <p className={`font-mono ${DESIGN.text.primary}`}>{data.invoice_no || '-'}</p>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Calendar className={`w-4 h-4 ${DESIGN.text.secondary}`} />
                      <span className={`text-sm ${DESIGN.text.secondary}`}>Tanggal Piutang</span>
                    </div>
                    <p className={DESIGN.text.primary}>{formatDate(data.ar_date)}</p>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Calendar className={`w-4 h-4 ${DESIGN.text.secondary}`} />
                      <span className={`text-sm ${DESIGN.text.secondary}`}>Jatuh Tempo</span>
                    </div>
                    <p className={data.status === 'overdue' ? 'text-rose-400 font-medium' : DESIGN.text.primary}>
                      {formatDate(data.due_date)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Payment History */}
              {data.payments && data.payments.length > 0 && (
                <div className={`${DESIGN.bg.card} ${DESIGN.border.default} border rounded-lg p-4`}>
                  <h3 className={`font-semibold ${DESIGN.text.primary} mb-4 flex items-center gap-2`}>
                    <DollarSign className="w-5 h-5" />
                    Riwayat Pembayaran
                  </h3>
                  <div className="space-y-2">
                    {data.payments.map((pay, idx) => (
                      <div key={idx} className={`flex items-center justify-between p-3 ${DESIGN.bg.modal} rounded-lg border ${DESIGN.border.default}`}>
                        <div>
                          <p className={`font-mono ${DESIGN.text.accent}`}>{pay.payment_no}</p>
                          <p className={`text-sm ${DESIGN.text.secondary}`}>{formatDateTime(pay.payment_date)}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-mono font-bold text-emerald-400">{formatCurrency(pay.amount)}</p>
                          <p className={`text-xs ${DESIGN.text.secondary}`}>{pay.payment_method}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Notes */}
              {data.notes && (
                <div className={`${DESIGN.bg.card} ${DESIGN.border.default} border rounded-lg p-4`}>
                  <h3 className={`font-semibold ${DESIGN.text.primary} mb-2`}>Catatan</h3>
                  <p className={DESIGN.text.secondary}>{data.notes}</p>
                </div>
              )}

              {/* Audit Info */}
              <div className={`text-xs ${DESIGN.text.secondary} ${DESIGN.bg.card} ${DESIGN.border.default} border rounded-lg p-3`}>
                <div className="flex justify-between">
                  <span>Dibuat: {formatDateTime(data.created_at)} oleh {data.created_by_name || '-'}</span>
                  {data.updated_at && (
                    <span>Update: {formatDateTime(data.updated_at)}</span>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className={`px-6 py-4 border-t ${DESIGN.border.default} ${DESIGN.bg.card} rounded-b-xl`}>
          <Button 
            onClick={() => onClose(false)} 
            className={`${DESIGN.bg.modal} ${DESIGN.border.default} border ${DESIGN.text.primary} hover:bg-[#334155]`}
          >
            Tutup
          </Button>
        </div>
      </div>
    </div>
  );
}
