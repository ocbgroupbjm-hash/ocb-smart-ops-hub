import React from 'react';
import { usePermission } from '../contexts/PermissionContext';
import { 
  Plus, Edit2, Trash2, Copy, Printer, FileSpreadsheet, 
  Upload, CheckCircle, Package, RotateCcw, ClipboardList
} from 'lucide-react';
import { toast } from 'sonner';

/**
 * ERPActionToolbar - Komponen Toolbar Standar ERP OCB TITAN
 * 
 * STANDAR WARNA:
 * - Tambah: Hijau (#22c55e)
 * - Edit: Ungu (#a855f7)
 * - Hapus: Merah (#ef4444)
 * - Duplikasi: Orange (#f97316)
 * - Print: Biru (#3b82f6)
 * - Approve: Cyan (#06b6d4)
 * - Receive: Teal (#14b8a6)
 * - Kartu Stok: Amber (#f59e0b)
 * - Import: Emerald (#10b981)
 * - Export: Sky (#0ea5e9)
 * - Retur: Rose (#f43f5e)
 * 
 * @param {Object} props
 * @param {string} props.module - Nama modul untuk RBAC (e.g., 'master_item', 'purchase_order')
 * @param {Object|null} props.selectedItem - Item yang dipilih dari tabel
 * @param {Function} props.onAdd - Handler untuk tombol Tambah
 * @param {Function} props.onEdit - Handler untuk tombol Edit
 * @param {Function} props.onDelete - Handler untuk tombol Hapus
 * @param {Function} props.onDuplicate - Handler untuk tombol Duplikasi
 * @param {Function} props.onPrint - Handler untuk tombol Print
 * @param {Function} props.onStockCard - Handler untuk tombol Kartu Stok
 * @param {Function} props.onImport - Handler untuk tombol Import
 * @param {Function} props.onExport - Handler untuk tombol Export
 * @param {Function} props.onApprove - Handler untuk tombol Approve
 * @param {Function} props.onReceive - Handler untuk tombol Receive/Terima
 * @param {Function} props.onReturn - Handler untuk tombol Retur
 * @param {Object} props.customButtons - Tombol custom tambahan [{label, icon, color, onClick, permission}]
 * @param {string} props.addLabel - Label tombol tambah (default: "Tambah")
 * @param {string} props.editLabel - Label tombol edit (default: "Edit")
 * @param {string} props.deleteLabel - Label tombol hapus (default: "Hapus")
 */
const ERPActionToolbar = ({
  module,
  selectedItem = null,
  onAdd,
  onEdit,
  onDelete,
  onDuplicate,
  onPrint,
  onStockCard,
  onImport,
  onExport,
  onApprove,
  onReceive,
  onReturn,
  customButtons = [],
  addLabel = "Tambah",
  editLabel = "Edit",
  deleteLabel = "Hapus",
}) => {
  const { hasPermission } = usePermission();
  
  // Check if item is selected
  const hasSelection = selectedItem !== null && selectedItem !== undefined;
  
  // Warn user if trying to use action without selection
  const requireSelection = (action, callback) => {
    if (!hasSelection) {
      toast.warning(`Pilih satu baris data terlebih dahulu untuk ${action}`);
      return;
    }
    callback(selectedItem);
  };

  // Button style generator based on color scheme
  const getButtonStyle = (color, disabled = false) => {
    const baseStyle = "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200";
    
    if (disabled) {
      return `${baseStyle} bg-gray-700/50 text-gray-500 cursor-not-allowed`;
    }
    
    const colorStyles = {
      green: "bg-green-600 hover:bg-green-700 text-white shadow-sm shadow-green-900/30",
      purple: "bg-purple-600 hover:bg-purple-700 text-white shadow-sm shadow-purple-900/30",
      red: "bg-red-600 hover:bg-red-700 text-white shadow-sm shadow-red-900/30",
      orange: "bg-orange-500 hover:bg-orange-600 text-white shadow-sm shadow-orange-900/30",
      blue: "bg-blue-600 hover:bg-blue-700 text-white shadow-sm shadow-blue-900/30",
      cyan: "bg-cyan-600 hover:bg-cyan-700 text-white shadow-sm shadow-cyan-900/30",
      teal: "bg-teal-600 hover:bg-teal-700 text-white shadow-sm shadow-teal-900/30",
      amber: "bg-amber-600 hover:bg-amber-700 text-white shadow-sm shadow-amber-900/30",
      emerald: "bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm shadow-emerald-900/30",
      sky: "bg-sky-600 hover:bg-sky-700 text-white shadow-sm shadow-sky-900/30",
      rose: "bg-rose-600 hover:bg-rose-700 text-white shadow-sm shadow-rose-900/30",
      gray: "bg-gray-600 hover:bg-gray-700 text-white shadow-sm shadow-gray-900/30",
    };
    
    return `${baseStyle} ${colorStyles[color] || colorStyles.gray}`;
  };

  // Icon size standard
  const iconSize = "h-4 w-4";

  return (
    <div 
      className="flex items-center gap-2 flex-wrap p-3 bg-[#1a1214] border border-red-900/30 rounded-lg mb-3"
      data-testid="erp-action-toolbar"
    >
      {/* === PRIMARY ACTIONS === */}
      
      {/* TAMBAH - Always visible if has permission */}
      {onAdd && hasPermission(module, 'create') && (
        <button
          onClick={onAdd}
          className={getButtonStyle('green')}
          data-testid="btn-toolbar-add"
        >
          <Plus className={iconSize} />
          {addLabel}
        </button>
      )}

      {/* EDIT - Requires selection */}
      {onEdit && hasPermission(module, 'edit') && (
        <button
          onClick={() => requireSelection('edit', onEdit)}
          className={getButtonStyle('purple', !hasSelection)}
          disabled={!hasSelection}
          data-testid="btn-toolbar-edit"
        >
          <Edit2 className={iconSize} />
          {editLabel}
        </button>
      )}

      {/* DUPLIKASI - Requires selection */}
      {onDuplicate && hasPermission(module, 'create') && (
        <button
          onClick={() => requireSelection('duplikasi', onDuplicate)}
          className={getButtonStyle('orange', !hasSelection)}
          disabled={!hasSelection}
          data-testid="btn-toolbar-duplicate"
        >
          <Copy className={iconSize} />
          Duplikasi
        </button>
      )}

      {/* HAPUS - Requires selection */}
      {onDelete && hasPermission(module, 'delete') && (
        <button
          onClick={() => requireSelection('hapus', onDelete)}
          className={getButtonStyle('red', !hasSelection)}
          disabled={!hasSelection}
          data-testid="btn-toolbar-delete"
        >
          <Trash2 className={iconSize} />
          {deleteLabel}
        </button>
      )}

      {/* === DIVIDER === */}
      {(onAdd || onEdit || onDelete || onDuplicate) && (onPrint || onStockCard || onApprove || onReceive || onReturn) && (
        <div className="h-6 w-px bg-red-900/50 mx-1" />
      )}

      {/* === SECONDARY ACTIONS === */}

      {/* KARTU STOK - Requires selection */}
      {onStockCard && hasPermission(module, 'view') && (
        <button
          onClick={() => requireSelection('kartu stok', onStockCard)}
          className={getButtonStyle('amber', !hasSelection)}
          disabled={!hasSelection}
          data-testid="btn-toolbar-stock-card"
        >
          <ClipboardList className={iconSize} />
          Kartu Stok
        </button>
      )}

      {/* PRINT - Requires selection */}
      {onPrint && hasPermission(module, 'view') && (
        <button
          onClick={() => requireSelection('print', onPrint)}
          className={getButtonStyle('blue', !hasSelection)}
          disabled={!hasSelection}
          data-testid="btn-toolbar-print"
        >
          <Printer className={iconSize} />
          Print
        </button>
      )}

      {/* APPROVE - Requires selection */}
      {onApprove && hasPermission(module, 'approve') && (
        <button
          onClick={() => requireSelection('approve', onApprove)}
          className={getButtonStyle('cyan', !hasSelection)}
          disabled={!hasSelection}
          data-testid="btn-toolbar-approve"
        >
          <CheckCircle className={iconSize} />
          Approve
        </button>
      )}

      {/* RECEIVE / TERIMA BARANG - Requires selection */}
      {onReceive && hasPermission(module, 'edit') && (
        <button
          onClick={() => requireSelection('terima barang', onReceive)}
          className={getButtonStyle('teal', !hasSelection)}
          disabled={!hasSelection}
          data-testid="btn-toolbar-receive"
        >
          <Package className={iconSize} />
          Terima
        </button>
      )}

      {/* RETUR - Requires selection */}
      {onReturn && hasPermission(module, 'create') && (
        <button
          onClick={() => requireSelection('retur', onReturn)}
          className={getButtonStyle('rose', !hasSelection)}
          disabled={!hasSelection}
          data-testid="btn-toolbar-return"
        >
          <RotateCcw className={iconSize} />
          Retur
        </button>
      )}

      {/* === DIVIDER FOR IMPORT/EXPORT === */}
      {(onImport || onExport) && (
        <div className="h-6 w-px bg-red-900/50 mx-1" />
      )}

      {/* IMPORT */}
      {onImport && hasPermission(module, 'create') && (
        <button
          onClick={onImport}
          className={getButtonStyle('emerald')}
          data-testid="btn-toolbar-import"
        >
          <Upload className={iconSize} />
          Import
        </button>
      )}

      {/* EXPORT */}
      {onExport && hasPermission(module, 'view') && (
        <button
          onClick={onExport}
          className={getButtonStyle('sky')}
          data-testid="btn-toolbar-export"
        >
          <FileSpreadsheet className={iconSize} />
          Export
        </button>
      )}

      {/* === CUSTOM BUTTONS === */}
      {customButtons.length > 0 && (
        <>
          <div className="h-6 w-px bg-red-900/50 mx-1" />
          {customButtons.map((btn, idx) => {
            const hasAccess = btn.permission ? hasPermission(module, btn.permission) : true;
            const needsSelection = btn.requireSelection !== false;
            const isDisabled = needsSelection && !hasSelection;
            
            if (!hasAccess) return null;
            
            return (
              <button
                key={idx}
                onClick={() => {
                  if (needsSelection) {
                    requireSelection(btn.label.toLowerCase(), btn.onClick);
                  } else {
                    btn.onClick();
                  }
                }}
                className={getButtonStyle(btn.color || 'gray', isDisabled)}
                disabled={isDisabled}
                data-testid={`btn-toolbar-custom-${idx}`}
              >
                {btn.icon}
                {btn.label}
              </button>
            );
          })}
        </>
      )}

      {/* === SELECTION INDICATOR === */}
      <div className="flex-1" />
      {hasSelection && (
        <div className="text-xs text-amber-400 bg-amber-900/20 px-2 py-1 rounded">
          1 item dipilih: <span className="font-medium text-amber-300">{selectedItem?.name || selectedItem?.code || selectedItem?.invoice_number || selectedItem?.po_number || 'ID: ' + selectedItem?.id}</span>
        </div>
      )}
    </div>
  );
};

export default ERPActionToolbar;
