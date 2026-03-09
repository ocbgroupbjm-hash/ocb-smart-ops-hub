# OCB GROUP SUPER ERP + AI TITAN WAR ROOM
# Complete Enterprise Models

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, date, time
from enum import Enum
import uuid

def gen_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ==================== ENUMS ====================

class ShiftType(str, Enum):
    PAGI = "pagi"
    SIANG = "siang"
    MALAM = "malam"
    FULL = "full"

class SelisihStatus(str, Enum):
    BALANCE = "balance"
    PLUS = "plus"
    MINUS = "minus"

class SelisihResolution(str, Enum):
    PENDING = "pending"
    BEBAN = "beban"
    PIUTANG_KARYAWAN = "piutang_karyawan"
    POTONG_GAJI = "potong_gaji"
    PENDAPATAN_LAIN = "pendapatan_lain"
    KOREKSI = "koreksi"
    CLOSED = "closed"

class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class AttendanceStatus(str, Enum):
    HADIR = "hadir"
    TELAT = "telat"
    ALPHA = "alpha"
    IZIN = "izin"
    CUTI = "cuti"
    SAKIT = "sakit"
    LIBUR = "libur"

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"

class AlertType(str, Enum):
    MINUS_KAS = "minus_kas"
    BELUM_SETOR = "belum_setor"
    TIDAK_ABSEN = "tidak_absen"
    SERING_TELAT = "sering_telat"
    PENJUALAN_TURUN = "penjualan_turun"
    FRAUD_PATTERN = "fraud_pattern"
    ANOMALI = "anomali"
    AUDIT_REQUIRED = "audit_required"

# ==================== MASTER DATA ====================

class MasterShift(BaseModel):
    id: str = Field(default_factory=gen_id)
    code: str
    name: str
    start_time: str  # "08:00"
    end_time: str    # "16:00"
    break_minutes: int = 60
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)

class MasterJabatan(BaseModel):
    id: str = Field(default_factory=gen_id)
    code: str
    name: str
    level: int = 1  # 1=staff, 2=supervisor, 3=manager, 4=director, 5=owner
    department: str = ""
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)

class MasterLokasiAbsensi(BaseModel):
    id: str = Field(default_factory=gen_id)
    branch_id: str
    branch_name: str
    latitude: float
    longitude: float
    radius_meters: int = 100
    address: str = ""
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)

class MasterTargetCabang(BaseModel):
    id: str = Field(default_factory=gen_id)
    branch_id: str
    branch_name: str
    period_month: int
    period_year: int
    target_revenue: float = 0
    target_transactions: int = 0
    target_profit: float = 0
    created_at: str = Field(default_factory=now_iso)

class MasterTargetKaryawan(BaseModel):
    id: str = Field(default_factory=gen_id)
    employee_id: str
    employee_name: str
    period_month: int
    period_year: int
    target_revenue: float = 0
    target_transactions: int = 0
    bonus_percentage: float = 0
    created_at: str = Field(default_factory=now_iso)

class MasterBiayaOperasional(BaseModel):
    id: str = Field(default_factory=gen_id)
    code: str
    name: str
    category: str  # listrik, sewa, gaji, transport, dll
    account_id: str = ""
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)

class MasterPayrollRule(BaseModel):
    id: str = Field(default_factory=gen_id)
    jabatan_id: str
    jabatan_name: str
    gaji_pokok: float = 0
    tunjangan_jabatan: float = 0
    tunjangan_transport: float = 0
    tunjangan_makan: float = 0
    bonus_kehadiran_full: float = 0
    potongan_telat_per_menit: float = 0
    potongan_alpha_per_hari: float = 0
    is_active: bool = True
    created_at: str = Field(default_factory=now_iso)

# ==================== EMPLOYEE ====================

class Employee(BaseModel):
    id: str = Field(default_factory=gen_id)
    nik: str  # Nomor Induk Karyawan
    name: str
    email: str = ""
    phone: str = ""
    whatsapp: str = ""
    
    # Position
    jabatan_id: str = ""
    jabatan_name: str = ""
    department: str = ""
    branch_id: str = ""
    branch_name: str = ""
    
    # Personal
    ktp_number: str = ""
    birth_date: str = ""
    birth_place: str = ""
    gender: str = ""
    religion: str = ""
    marital_status: str = ""
    address: str = ""
    
    # Employment
    join_date: str = ""
    contract_type: str = "tetap"  # tetap, kontrak, magang
    contract_end_date: str = ""
    status: str = "active"  # active, resigned, terminated
    
    # Bank
    bank_name: str = ""
    bank_account: str = ""
    bank_holder: str = ""
    
    # Payroll
    gaji_pokok: float = 0
    tunjangan_total: float = 0
    
    # Performance
    total_minus: float = 0
    total_plus: float = 0
    piutang_karyawan: float = 0
    
    # Photo
    photo_url: str = ""
    
    # User account link
    user_id: str = ""
    
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== SETORAN HARIAN ====================

class SetoranHarian(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    # Date & Time
    tanggal: str  # YYYY-MM-DD
    jam_buka: str = ""
    jam_tutup: str = ""
    
    # Branch
    branch_id: str
    branch_code: str
    branch_name: str
    
    # Penjaga
    penjaga_id: str
    penjaga_name: str
    shift: str = ""
    
    # Sales Data
    total_penjualan: float = 0
    total_transaksi: int = 0
    
    # Breakdown by payment
    penjualan_cash: float = 0
    penjualan_transfer: float = 0
    penjualan_ewallet: float = 0
    penjualan_debit: float = 0
    penjualan_credit: float = 0
    penjualan_piutang: float = 0
    
    # Setoran
    total_setoran: float = 0
    metode_setoran: str = ""  # cash, transfer
    rekening_tujuan: str = ""
    bukti_setoran_url: str = ""
    
    # Selisih
    selisih: float = 0  # setoran - penjualan
    selisih_status: SelisihStatus = SelisihStatus.BALANCE
    selisih_resolution: SelisihResolution = SelisihResolution.PENDING
    
    # Notes
    catatan_penjaga: str = ""
    catatan_admin: str = ""
    catatan_supervisor: str = ""
    
    # Audit Trail
    input_by_id: str = ""
    input_by_name: str = ""
    input_at: str = Field(default_factory=now_iso)
    
    verified_by_id: str = ""
    verified_by_name: str = ""
    verified_at: str = ""
    
    approved_by_id: str = ""
    approved_by_name: str = ""
    approved_at: str = ""
    
    # Status
    status: ApprovalStatus = ApprovalStatus.DRAFT
    
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== SELISIH KAS ====================

class SelisihKas(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    # Reference
    setoran_id: str
    tanggal: str
    
    # Branch
    branch_id: str
    branch_code: str
    branch_name: str
    
    # Employee
    penjaga_id: str
    penjaga_name: str
    shift: str = ""
    
    # Amount
    nominal: float = 0
    jenis: SelisihStatus = SelisihStatus.BALANCE  # plus/minus
    
    # Resolution
    resolution: SelisihResolution = SelisihResolution.PENDING
    resolution_note: str = ""
    
    # If piutang
    is_piutang: bool = False
    piutang_paid: float = 0
    piutang_remaining: float = 0
    
    # If potong gaji
    is_potong_gaji: bool = False
    potong_gaji_month: str = ""
    potong_gaji_amount: float = 0
    
    # Accounting
    journal_id: str = ""
    account_debit: str = ""
    account_credit: str = ""
    
    # Investigation
    investigation_status: str = "open"  # open, investigating, closed
    investigation_note: str = ""
    investigation_by: str = ""
    investigation_at: str = ""
    
    # Approval
    approved_by_id: str = ""
    approved_by_name: str = ""
    approved_at: str = ""
    
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== ABSENSI ====================

class Attendance(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    # Employee
    employee_id: str
    employee_nik: str
    employee_name: str
    jabatan: str = ""
    
    # Branch
    branch_id: str
    branch_name: str
    
    # Shift
    shift_id: str = ""
    shift_name: str = ""
    jadwal_masuk: str = ""  # "08:00"
    jadwal_pulang: str = ""  # "17:00"
    
    # Date
    tanggal: str  # YYYY-MM-DD
    
    # Check In
    check_in_time: str = ""
    check_in_lat: float = 0
    check_in_lng: float = 0
    check_in_address: str = ""
    check_in_photo_url: str = ""
    check_in_device: str = ""
    check_in_valid_location: bool = False
    check_in_distance_meters: int = 0
    
    # Check Out
    check_out_time: str = ""
    check_out_lat: float = 0
    check_out_lng: float = 0
    check_out_address: str = ""
    check_out_photo_url: str = ""
    check_out_device: str = ""
    check_out_valid_location: bool = False
    check_out_distance_meters: int = 0
    
    # Status
    status: AttendanceStatus = AttendanceStatus.ALPHA
    
    # Late/Early
    telat_menit: int = 0
    pulang_cepat_menit: int = 0
    lembur_menit: int = 0
    
    # Working hours
    total_jam_kerja: float = 0
    
    # Notes
    keterangan: str = ""
    catatan_supervisor: str = ""
    
    # Approval (for izin/cuti)
    approval_status: ApprovalStatus = ApprovalStatus.APPROVED
    approved_by: str = ""
    approved_at: str = ""
    
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== PAYROLL ====================

class PayrollPeriod(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    period_month: int
    period_year: int
    period_name: str  # "Januari 2026"
    
    start_date: str
    end_date: str
    
    status: str = "draft"  # draft, processing, approved, paid
    
    total_employees: int = 0
    total_gross: float = 0
    total_deductions: float = 0
    total_net: float = 0
    
    approved_by: str = ""
    approved_at: str = ""
    
    paid_at: str = ""
    
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

class PayrollDetail(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    period_id: str
    period_name: str
    
    # Employee
    employee_id: str
    employee_nik: str
    employee_name: str
    jabatan: str = ""
    branch_id: str = ""
    branch_name: str = ""
    
    # Bank
    bank_name: str = ""
    bank_account: str = ""
    
    # Earnings
    gaji_pokok: float = 0
    tunjangan_jabatan: float = 0
    tunjangan_transport: float = 0
    tunjangan_makan: float = 0
    tunjangan_lainnya: float = 0
    
    # Performance Bonus
    bonus_kehadiran: float = 0
    bonus_performa: float = 0
    bonus_cabang: float = 0
    bonus_lainnya: float = 0
    
    # Overtime
    lembur_jam: float = 0
    lembur_nominal: float = 0
    
    # Deductions
    potongan_telat: float = 0
    potongan_alpha: float = 0
    potongan_pinjaman: float = 0
    potongan_minus_kas: float = 0
    potongan_bpjs: float = 0
    potongan_pph21: float = 0
    potongan_lainnya: float = 0
    
    # Attendance Summary
    hari_kerja: int = 0
    hari_hadir: int = 0
    hari_telat: int = 0
    hari_alpha: int = 0
    hari_izin: int = 0
    hari_cuti: int = 0
    hari_sakit: int = 0
    total_menit_telat: int = 0
    total_menit_lembur: int = 0
    
    # Totals
    total_earnings: float = 0
    total_deductions: float = 0
    take_home_pay: float = 0
    
    # Notes
    notes: str = ""
    
    # Status
    status: str = "draft"  # draft, approved, paid
    
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)

# ==================== ALERTS ====================

class SystemAlert(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    alert_type: AlertType
    severity: AlertSeverity
    
    title: str
    message: str
    
    # Target
    branch_id: str = ""
    branch_name: str = ""
    employee_id: str = ""
    employee_name: str = ""
    
    # Reference
    reference_type: str = ""  # setoran, attendance, transaction
    reference_id: str = ""
    
    # Data
    data: Dict = {}
    
    # Status
    is_read: bool = False
    is_resolved: bool = False
    
    read_by: str = ""
    read_at: str = ""
    
    resolved_by: str = ""
    resolved_at: str = ""
    resolved_note: str = ""
    
    # Notification
    notified_whatsapp: bool = False
    notified_email: bool = False
    
    created_at: str = Field(default_factory=now_iso)

# ==================== WAR ROOM ====================

class WarRoomSnapshot(BaseModel):
    id: str = Field(default_factory=gen_id)
    snapshot_date: str
    snapshot_time: str = Field(default_factory=now_iso)
    
    # Overview
    total_cabang: int = 0
    cabang_aktif: int = 0
    cabang_bermasalah: int = 0
    total_karyawan: int = 0
    karyawan_hadir: int = 0
    
    # Sales Today
    penjualan_hari_ini: float = 0
    transaksi_hari_ini: int = 0
    rata_rata_transaksi: float = 0
    
    # Sales MTD
    penjualan_bulan_ini: float = 0
    target_bulan_ini: float = 0
    achievement_percent: float = 0
    
    # Setoran
    total_setoran_hari_ini: float = 0
    cabang_sudah_setor: int = 0
    cabang_belum_setor: int = 0
    
    # Selisih
    total_minus_hari_ini: float = 0
    total_plus_hari_ini: float = 0
    total_minus_bulan_ini: float = 0
    total_plus_bulan_ini: float = 0
    
    # Alerts
    total_alerts: int = 0
    critical_alerts: int = 0
    
    # Rankings
    top_cabang: List[Dict] = []
    bottom_cabang: List[Dict] = []
    top_karyawan: List[Dict] = []
    karyawan_bermasalah: List[Dict] = []
    
    # Trends
    trend_penjualan_7_hari: List[Dict] = []
    trend_minus_7_hari: List[Dict] = []
    
    created_at: str = Field(default_factory=now_iso)

# ==================== AI INSIGHTS ====================

class AIInsight(BaseModel):
    id: str = Field(default_factory=gen_id)
    
    insight_type: str  # performance, risk, fraud, recommendation
    category: str  # cabang, karyawan, keuangan, operasional
    
    title: str
    summary: str
    detail: str
    
    # Target
    branch_id: str = ""
    branch_name: str = ""
    employee_id: str = ""
    employee_name: str = ""
    
    # Severity
    severity: str = "info"  # info, warning, critical
    priority: int = 1  # 1-5
    
    # Action
    recommended_action: str = ""
    action_taken: str = ""
    action_by: str = ""
    action_at: str = ""
    
    # Data
    data: Dict = {}
    metrics: Dict = {}
    
    # Status
    is_acknowledged: bool = False
    acknowledged_by: str = ""
    acknowledged_at: str = ""
    
    valid_until: str = ""
    
    created_at: str = Field(default_factory=now_iso)
