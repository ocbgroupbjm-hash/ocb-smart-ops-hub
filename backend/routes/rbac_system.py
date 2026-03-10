# OCB TITAN ERP - ENTERPRISE RBAC SECURITY SYSTEM
# Role Based Access Control dengan Level Hierarchy & Branch Security

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import uuid
import hashlib

router = APIRouter(prefix="/api/rbac", tags=["RBAC - Enterprise Security System"])

def get_db():
    from database import get_db as db_get
    return db_get()

from routes.auth import get_current_user

# ==================== ENTERPRISE ROLE HIERARCHY ====================
# Level 0 = Highest (Super Admin), Level 8 = Lowest (Viewer)

ROLE_HIERARCHY = {
    "super_admin": {"level": 0, "name": "Super Admin", "inherit_all": True, "can_manage_system": True},
    "pemilik": {"level": 1, "name": "Pemilik", "inherit_all": True, "can_manage_system": False},
    "direktur": {"level": 2, "name": "Direktur", "inherit_from": ["manager"], "all_branches": True},
    "manager": {"level": 3, "name": "Manager", "inherit_from": ["supervisor"], "all_branches": False},
    "supervisor": {"level": 4, "name": "Supervisor", "inherit_from": ["admin"], "all_branches": False},
    "admin": {"level": 5, "name": "Admin", "inherit_from": ["gudang", "keuangan"], "all_branches": False},
    "gudang": {"level": 6, "name": "Gudang", "inherit_from": ["kasir"], "all_branches": False},
    "keuangan": {"level": 6, "name": "Keuangan", "inherit_from": [], "all_branches": False},
    "kasir": {"level": 7, "name": "Kasir", "inherit_from": [], "all_branches": False},
    "viewer": {"level": 8, "name": "Viewer", "view_only": True, "all_branches": False}
}

# ==================== COMPLETE ACTION LIST ====================
ACTIONS = [
    "view", "create", "edit", "delete", "approve", "export", "print",
    "lock_number", "lock_date", "override_price", "override_discount",
    "override_stock", "lock_transaction"
]

# ==================== COMPLETE MODULE LIST ====================
MODULES = {
    # Master Data
    "master_supplier": {"name": "Master Supplier", "category": "master_data"},
    "master_customer": {"name": "Master Pelanggan", "category": "master_data"},
    "master_sales": {"name": "Master Sales", "category": "master_data"},
    "master_branch": {"name": "Dept / Gudang / Cabang", "category": "master_data"},
    "master_item": {"name": "Data Item", "category": "master_data"},
    "master_category": {"name": "Kategori Item", "category": "master_data"},
    "master_unit": {"name": "Satuan", "category": "master_data"},
    "master_brand": {"name": "Merk", "category": "master_data"},
    "master_barcode": {"name": "Barcode", "category": "master_data"},
    "master_promo": {"name": "Promo", "category": "master_data"},
    "master_discount": {"name": "Diskon", "category": "master_data"},
    "master_serial": {"name": "Serial Number", "category": "master_data"},
    "stock_card": {"name": "Kartu Stok", "category": "master_data"},
    
    # Pembelian
    "purchase_order": {"name": "Pesanan Pembelian", "category": "pembelian"},
    "purchase": {"name": "Pembelian", "category": "pembelian"},
    "purchase_return": {"name": "Retur Pembelian", "category": "pembelian"},
    "pay_payable": {"name": "Bayar Hutang", "category": "pembelian"},
    "purchase_price_history": {"name": "History Harga Beli", "category": "pembelian"},
    "purchase_import": {"name": "Import Pembelian", "category": "pembelian"},
    "purchase_export": {"name": "Export Pembelian", "category": "pembelian"},
    
    # Penjualan
    "sales_order": {"name": "Pesanan Penjualan", "category": "penjualan"},
    "sales": {"name": "Penjualan", "category": "penjualan"},
    "cashier": {"name": "Kasir", "category": "penjualan"},
    "sales_return": {"name": "Retur Penjualan", "category": "penjualan"},
    "pay_receivable": {"name": "Bayar Piutang", "category": "penjualan"},
    "sales_commission": {"name": "Komisi Sales", "category": "penjualan"},
    "cash_drawer": {"name": "Kas Laci", "category": "penjualan"},
    "customer_points": {"name": "Point Pelanggan", "category": "penjualan"},
    "sales_price_history": {"name": "History Harga Jual", "category": "penjualan"},
    
    # Persediaan
    "stock_in": {"name": "Item Masuk", "category": "persediaan"},
    "stock_out": {"name": "Item Keluar", "category": "persediaan"},
    "stock_transfer": {"name": "Transfer Item", "category": "persediaan"},
    "stock_transfer_branch": {"name": "Transfer Antar Cabang", "category": "persediaan"},
    "stock_opening": {"name": "Saldo Awal Item", "category": "persediaan"},
    "stock_opname": {"name": "Stok Opname", "category": "persediaan"},
    "serial_management": {"name": "Serial Management", "category": "persediaan"},
    "stock_mutation": {"name": "Mutasi Stok", "category": "persediaan"},
    
    # Akuntansi
    "cash_in": {"name": "Kas Masuk", "category": "akuntansi"},
    "cash_out": {"name": "Kas Keluar", "category": "akuntansi"},
    "cash_transfer": {"name": "Kas Transfer", "category": "akuntansi"},
    "customer_deposit": {"name": "Deposit Pelanggan", "category": "akuntansi"},
    "supplier_deposit": {"name": "Deposit Supplier", "category": "akuntansi"},
    "journal": {"name": "Jurnal", "category": "akuntansi"},
    "general_ledger": {"name": "Buku Besar", "category": "akuntansi"},
    "account_opening": {"name": "Saldo Awal Akun", "category": "akuntansi"},
    "account_setting": {"name": "Setting Akun", "category": "akuntansi"},
    "period_closing": {"name": "Proses Tutup Buku", "category": "akuntansi"},
    
    # Laporan
    "report_purchase": {"name": "Laporan Pembelian", "category": "laporan"},
    "report_sales": {"name": "Laporan Penjualan", "category": "laporan"},
    "report_consignment": {"name": "Laporan Konsinyasi", "category": "laporan"},
    "report_inventory": {"name": "Laporan Persediaan", "category": "laporan"},
    "report_payable": {"name": "Laporan Hutang", "category": "laporan"},
    "report_receivable": {"name": "Laporan Piutang", "category": "laporan"},
    "report_finance": {"name": "Laporan Keuangan", "category": "laporan"},
    "report_profit_loss": {"name": "Laporan Laba Rugi", "category": "laporan"},
    "report_balance_sheet": {"name": "Laporan Neraca", "category": "laporan"},
    "report_general_ledger": {"name": "Laporan Buku Besar", "category": "laporan"},
    "report_cash_flow": {"name": "Laporan Arus Kas", "category": "laporan"},
    "report_min_stock": {"name": "Laporan Stok Minimum", "category": "laporan"},
    "report_slow_moving": {"name": "Laporan Item Tidak Laku", "category": "laporan"},
    "report_sales_chart": {"name": "Laporan Grafik Penjualan", "category": "laporan"},
    "report_customer_analysis": {"name": "Laporan Analisa Pelanggan", "category": "laporan"},
    
    # Pengaturan
    "user_management": {"name": "User Management", "category": "pengaturan"},
    "role_management": {"name": "Role Management", "category": "pengaturan"},
    "printer_setting": {"name": "Mini Printer", "category": "pengaturan"},
    "display_setting": {"name": "Customer Display", "category": "pengaturan"},
    "company_setting": {"name": "Data Perusahaan", "category": "pengaturan"},
    "general_setting": {"name": "Pengaturan Umum", "category": "pengaturan"},
    "period_setting": {"name": "Pengaturan Periode", "category": "pengaturan"},
    "transaction_number_setting": {"name": "Pengaturan Nomor Transaksi", "category": "pengaturan"},
    "import_data": {"name": "Import Data", "category": "pengaturan"},
    "export_data": {"name": "Export Data", "category": "pengaturan"},
    "backup_database": {"name": "Backup Database", "category": "pengaturan"},
    "restore_database": {"name": "Restore Database", "category": "pengaturan"},
    "database_setting": {"name": "Pengaturan Database", "category": "pengaturan"},
    "auto_backup": {"name": "Auto Backup", "category": "pengaturan"},
    "activity_log": {"name": "Log Aktivitas", "category": "pengaturan"},
    "error_analysis": {"name": "Analisa Error System", "category": "pengaturan"},
    
    # Menu Visibility
    "menu_master": {"name": "Tampil Menu Master", "category": "menu"},
    "menu_purchase": {"name": "Tampil Menu Pembelian", "category": "menu"},
    "menu_sales": {"name": "Tampil Menu Penjualan", "category": "menu"},
    "menu_inventory": {"name": "Tampil Menu Persediaan", "category": "menu"},
    "menu_accounting": {"name": "Tampil Menu Akuntansi", "category": "menu"},
    "menu_report": {"name": "Tampil Menu Laporan", "category": "menu"},
    "menu_setting": {"name": "Tampil Menu Pengaturan", "category": "menu"},
    
    # AI Modules
    "ai_cfo": {"name": "AI CFO Dashboard", "category": "ai"},
    "ai_war_room": {"name": "AI War Room", "category": "ai"},
    "ai_command": {"name": "AI Command Center", "category": "ai"},
    "ai_photo_studio": {"name": "AI Photo Studio", "category": "ai"},
    "ai_performance": {"name": "AI Employee Performance", "category": "ai"},
    
    # HR & Payroll
    "hr_employee": {"name": "Data Karyawan", "category": "hr"},
    "hr_attendance": {"name": "Absensi", "category": "hr"},
    "hr_payroll": {"name": "Payroll", "category": "hr"},
    "hr_position": {"name": "Master Jabatan", "category": "hr"},
    "hr_shift": {"name": "Master Shift", "category": "hr"},
    
    # Security & System
    "security_rbac": {"name": "RBAC Management", "category": "security"},
    "security_audit": {"name": "Audit Log", "category": "security"},
    "security_session": {"name": "Session Management", "category": "security"},
    "security_alert": {"name": "Security Alerts", "category": "security"},
    
    # Operasional Setoran Harian
    "setoran_harian": {"name": "Setoran Harian", "category": "operasional"},
    "setoran_verify": {"name": "Verifikasi Setoran", "category": "operasional"},
    "setoran_approve": {"name": "Approval Setoran", "category": "operasional"},
    "setoran_post": {"name": "Posting Setoran", "category": "operasional"},
    "setoran_reconcile": {"name": "Rekonsiliasi Setoran", "category": "operasional"},
}

# ==================== CATEGORY LABELS ====================
CATEGORY_LABELS = {
    "master_data": "Master Data",
    "pembelian": "Pembelian",
    "penjualan": "Penjualan",
    "persediaan": "Persediaan",
    "akuntansi": "Akuntansi",
    "laporan": "Laporan",
    "pengaturan": "Pengaturan",
    "menu": "Visibilitas Menu",
    "ai": "AI Modules",
    "hr": "HR & Payroll",
    "security": "Security & System",
    "operasional": "Operasional Keuangan"
}

# ==================== PYDANTIC MODELS ====================

class RoleCreate(BaseModel):
    code: str
    name: str
    description: str = ""
    level: int = 10
    inherit_all: bool = False
    all_branches: bool = False
    view_only: bool = False
    can_manage_system: bool = False
    inherit_from: List[str] = []
    branch_access: List[str] = []
    region_access: List[str] = []

class PermissionUpdate(BaseModel):
    permissions: List[Dict[str, Any]]

class UserRoleUpdate(BaseModel):
    role_id: str
    branch_access: List[str] = []
    region_access: List[str] = []
    all_branches: bool = False

class SecurityAlert(BaseModel):
    alert_type: str
    severity: str  # critical, high, medium, low
    module: str
    description: str
    data: Dict[str, Any] = {}


# ==================== ENTERPRISE AUDIT LOG ====================

async def log_activity(
    db,
    user_id: str,
    user_name: str,
    action: str,
    module: str,
    description: str,
    ip_address: str = "",
    branch_id: str = "",
    device_info: str = "",
    data_before: Dict = None,
    data_after: Dict = None,
    severity: str = "normal"  # normal, warning, critical
):
    """Enterprise-grade audit logging with device tracking"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "module": module,
        "description": description,
        "ip_address": ip_address,
        "branch_id": branch_id,
        "device_info": device_info,
        "data_before": data_before,
        "data_after": data_after,
        "severity": severity,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "checksum": hashlib.sha256(f"{user_id}{action}{module}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    }
    await db["audit_logs"].insert_one(log_entry)
    
    # Auto-create security alert for critical actions
    if severity == "critical" or action in ["delete", "override_price", "override_stock"]:
        await create_security_alert(db, {
            "alert_type": "sensitive_action",
            "severity": "high" if action == "delete" else "medium",
            "module": module,
            "description": f"{user_name} performed {action} on {module}: {description}",
            "user_id": user_id,
            "log_id": log_entry["id"]
        })
    
    return log_entry


async def create_security_alert(db, alert_data: Dict):
    """Create security alert for sensitive activities"""
    alert = {
        "id": str(uuid.uuid4()),
        "alert_type": alert_data.get("alert_type", "unknown"),
        "severity": alert_data.get("severity", "medium"),
        "module": alert_data.get("module", ""),
        "description": alert_data.get("description", ""),
        "user_id": alert_data.get("user_id", ""),
        "log_id": alert_data.get("log_id", ""),
        "acknowledged": False,
        "acknowledged_by": None,
        "acknowledged_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db["security_alerts"].insert_one(alert)
    return alert


# ==================== PERMISSION CHECK ENGINE ====================

async def check_permission(user_id: str, module: str, action: str) -> bool:
    """
    FAIL-SAFE: Default is DENY
    Check permission with role hierarchy support
    """
    db = get_db()
    
    # Get user with role
    user = await db["users"].find_one({"id": user_id}, {"_id": 0, "role_id": 1, "branch_access": 1})
    if not user or not user.get("role_id"):
        return False  # FAIL-SAFE: DENY
    
    # Get role
    role = await db["roles"].find_one({"id": user["role_id"]}, {"_id": 0})
    if not role:
        return False  # FAIL-SAFE: DENY
    
    # SUPER ADMIN / PEMILIK = FULL ACCESS (inherit_all)
    if role.get("inherit_all") or role.get("code") in ["super_admin", "pemilik"]:
        return True
    
    # VIEW ONLY role - only allow view action
    if role.get("view_only") and action != "view":
        return False
    
    # Check specific permission in database
    permission = await db["role_permissions"].find_one({
        "role_id": user["role_id"],
        "module": module,
        "action": action,
        "allowed": True
    }, {"_id": 0})
    
    if permission:
        return True
    
    # Check inherited permissions from lower roles
    inherit_from = role.get("inherit_from", [])
    for inherited_role_code in inherit_from:
        inherited_role = await db["roles"].find_one({"code": inherited_role_code}, {"_id": 0, "id": 1})
        if inherited_role:
            inherited_perm = await db["role_permissions"].find_one({
                "role_id": inherited_role["id"],
                "module": module,
                "action": action,
                "allowed": True
            }, {"_id": 0})
            if inherited_perm:
                return True
    
    return False  # FAIL-SAFE: DENY


async def check_branch_access(user_id: str, branch_id: str) -> bool:
    """Check if user has access to specific branch"""
    db = get_db()
    
    user = await db["users"].find_one({"id": user_id}, {"_id": 0, "role_id": 1, "branch_access": 1, "all_branches": 1})
    if not user:
        return False
    
    # Check if user has all_branches flag
    if user.get("all_branches"):
        return True
    
    # Check role's all_branches flag
    role = await db["roles"].find_one({"id": user.get("role_id")}, {"_id": 0, "all_branches": 1, "inherit_all": 1})
    if role:
        if role.get("all_branches") or role.get("inherit_all"):
            return True
    
    # Check specific branch access
    branch_access = user.get("branch_access", [])
    if not branch_access:  # Empty = access to default branch only
        return True
    
    return branch_id in branch_access


async def get_user_permissions(user_id: str) -> Dict[str, Any]:
    """Get all permissions for a user with hierarchy support"""
    db = get_db()
    
    user = await db["users"].find_one({"id": user_id}, {"_id": 0})
    if not user:
        return {"error": "User not found"}
    
    role = await db["roles"].find_one({"id": user.get("role_id")}, {"_id": 0})
    if not role:
        return {"error": "Role not found", "user_id": user_id}
    
    # SUPER ADMIN / PEMILIK = ALL PERMISSIONS
    if role.get("inherit_all") or role.get("code") in ["super_admin", "pemilik"]:
        all_perms = {}
        for module in MODULES.keys():
            all_perms[module] = ACTIONS.copy()
        
        return {
            "user_id": user_id,
            "role_id": role["id"],
            "role_code": role.get("code"),
            "role_name": role.get("name"),
            "role_level": role.get("level", 99),
            "inherit_all": True,
            "all_branches": True,
            "view_only": False,
            "can_manage_system": role.get("can_manage_system", False),
            "branch_access": [],
            "region_access": [],
            "permissions": all_perms,
            "menu_visibility": {key: True for key in ["master", "purchase", "sales", "inventory", "accounting", "report", "setting"]}
        }
    
    # Get specific permissions
    permissions = await db["role_permissions"].find(
        {"role_id": role["id"], "allowed": True},
        {"_id": 0, "module": 1, "action": 1}
    ).to_list(5000)
    
    # Build permission map
    perm_map = {}
    for p in permissions:
        module = p["module"]
        action = p["action"]
        if module not in perm_map:
            perm_map[module] = []
        perm_map[module].append(action)
    
    # Add inherited permissions
    inherit_from = role.get("inherit_from", [])
    for inherited_code in inherit_from:
        inherited_role = await db["roles"].find_one({"code": inherited_code}, {"_id": 0, "id": 1})
        if inherited_role:
            inherited_perms = await db["role_permissions"].find(
                {"role_id": inherited_role["id"], "allowed": True},
                {"_id": 0, "module": 1, "action": 1}
            ).to_list(5000)
            for p in inherited_perms:
                module = p["module"]
                action = p["action"]
                if module not in perm_map:
                    perm_map[module] = []
                if action not in perm_map[module]:
                    perm_map[module].append(action)
    
    return {
        "user_id": user_id,
        "role_id": role["id"],
        "role_code": role.get("code"),
        "role_name": role.get("name"),
        "role_level": role.get("level", 99),
        "inherit_all": role.get("inherit_all", False),
        "all_branches": role.get("all_branches", False) or user.get("all_branches", False),
        "view_only": role.get("view_only", False),
        "can_manage_system": role.get("can_manage_system", False),
        "branch_access": user.get("branch_access", []),
        "region_access": user.get("region_access", []),
        "permissions": perm_map,
        "menu_visibility": {
            "master": "menu_master" in perm_map and "view" in perm_map.get("menu_master", []),
            "purchase": "menu_purchase" in perm_map and "view" in perm_map.get("menu_purchase", []),
            "sales": "menu_sales" in perm_map and "view" in perm_map.get("menu_sales", []),
            "inventory": "menu_inventory" in perm_map and "view" in perm_map.get("menu_inventory", []),
            "accounting": "menu_accounting" in perm_map and "view" in perm_map.get("menu_accounting", []),
            "report": "menu_report" in perm_map and "view" in perm_map.get("menu_report", []),
            "setting": "menu_setting" in perm_map and "view" in perm_map.get("menu_setting", [])
        }
    }


# ==================== PERMISSION MIDDLEWARE ====================

def require_permission(module: str, action: str):
    """
    FAIL-SAFE Dependency: Default is DENY
    Usage: Depends(require_permission("master_item", "delete"))
    """
    async def permission_dependency(request: Request, user: dict = Depends(get_current_user)):
        user_id = user.get("user_id") or user.get("id")
        has_perm = await check_permission(user_id, module, action)
        
        if not has_perm:
            # Log failed access attempt
            db = get_db()
            await log_activity(
                db, user_id, user.get("name", "Unknown"),
                "access_denied", module,
                f"Akses ditolak untuk {action} pada {module}",
                request.client.host if request.client else "",
                severity="warning"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Akses ditolak: Anda tidak memiliki izin untuk {action} pada {module}"
            )
        return user
    return permission_dependency


def require_branch_access():
    """
    Branch access check middleware
    """
    async def branch_dependency(
        request: Request,
        branch_id: str = Query(None),
        user: dict = Depends(get_current_user)
    ):
        if branch_id:
            user_id = user.get("user_id") or user.get("id")
            has_access = await check_branch_access(user_id, branch_id)
            if not has_access:
                db = get_db()
                await log_activity(
                    db, user_id, user.get("name", "Unknown"),
                    "branch_access_denied", "branch",
                    f"Akses cabang {branch_id} ditolak",
                    request.client.host if request.client else "",
                    severity="warning"
                )
                raise HTTPException(
                    status_code=403,
                    detail="Akses ditolak: Anda tidak memiliki akses ke cabang ini"
                )
        return user
    return branch_dependency


# ==================== SESSION VALIDATION ====================

async def validate_session(user: dict, request: Request) -> bool:
    """Validate user session"""
    db = get_db()
    user_id = user.get("user_id") or user.get("id")
    
    # Check if user exists and is active
    db_user = await db["users"].find_one({"id": user_id}, {"_id": 0, "is_active": 1, "role_id": 1})
    if not db_user:
        return False
    
    if db_user.get("is_active") == False:
        return False
    
    # Check if role still exists
    if db_user.get("role_id"):
        role = await db["roles"].find_one({"id": db_user["role_id"]})
        if not role:
            return False
    
    return True


# ==================== ROLE MANAGEMENT ENDPOINTS ====================

@router.get("/roles")
async def get_roles(user: dict = Depends(get_current_user)):
    """Get all roles with hierarchy info"""
    db = get_db()
    roles = await db["roles"].find({}, {"_id": 0}).sort("level", 1).to_list(100)
    
    # Add hierarchy info
    for role in roles:
        hierarchy_info = ROLE_HIERARCHY.get(role.get("code"), {})
        role["hierarchy_level"] = hierarchy_info.get("level", role.get("level", 99))
        role["inherit_from"] = hierarchy_info.get("inherit_from", [])
    
    return {"roles": roles, "total": len(roles), "hierarchy": ROLE_HIERARCHY}


@router.get("/roles/{role_id}")
async def get_role(role_id: str, user: dict = Depends(get_current_user)):
    """Get single role with full details"""
    db = get_db()
    
    role = await db["roles"].find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    permissions = await db["role_permissions"].find(
        {"role_id": role_id},
        {"_id": 0}
    ).to_list(5000)
    
    role["permissions"] = permissions
    role["hierarchy_info"] = ROLE_HIERARCHY.get(role.get("code"), {})
    
    return role


@router.post("/roles")
async def create_role(data: RoleCreate, request: Request, user: dict = Depends(get_current_user)):
    """Create new role"""
    db = get_db()
    
    existing = await db["roles"].find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode role sudah ada")
    
    role = {
        "id": str(uuid.uuid4()),
        "code": data.code,
        "name": data.name,
        "description": data.description,
        "level": data.level,
        "inherit_all": data.inherit_all,
        "all_branches": data.all_branches,
        "view_only": data.view_only,
        "can_manage_system": data.can_manage_system,
        "inherit_from": data.inherit_from,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("user_id") or user.get("id")
    }
    
    await db["roles"].insert_one(role)
    
    # Auto-generate base permissions for new role
    await auto_generate_permissions(db, role["id"], data.level)
    
    user_id = user.get("user_id") or user.get("id")
    await log_activity(
        db, user_id, user.get("name", ""),
        "create", "role_management",
        f"Membuat role baru: {data.name}",
        request.client.host if request.client else ""
    )
    
    return {"id": role["id"], "message": "Role berhasil dibuat"}


@router.put("/roles/{role_id}")
async def update_role(role_id: str, data: RoleCreate, request: Request, user: dict = Depends(get_current_user)):
    """Update role"""
    db = get_db()
    
    role = await db["roles"].find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    update_data = {
        "name": data.name,
        "description": data.description,
        "level": data.level,
        "inherit_all": data.inherit_all,
        "all_branches": data.all_branches,
        "view_only": data.view_only,
        "can_manage_system": data.can_manage_system,
        "inherit_from": data.inherit_from,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db["roles"].update_one({"id": role_id}, {"$set": update_data})
    
    user_id = user.get("user_id") or user.get("id")
    await log_activity(
        db, user_id, user.get("name", ""),
        "edit", "role_management",
        f"Mengubah role: {data.name}",
        request.client.host if request.client else "",
        data_before=role, data_after=update_data
    )
    
    return {"message": "Role berhasil diupdate"}


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Delete role"""
    db = get_db()
    
    role = await db["roles"].find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    # Prevent deletion of system roles
    if role.get("code") in ["super_admin", "pemilik"]:
        raise HTTPException(status_code=400, detail="Role sistem tidak dapat dihapus")
    
    users_with_role = await db["users"].count_documents({"role_id": role_id})
    if users_with_role > 0:
        raise HTTPException(status_code=400, detail=f"Role sedang digunakan oleh {users_with_role} user")
    
    await db["roles"].delete_one({"id": role_id})
    await db["role_permissions"].delete_many({"role_id": role_id})
    
    user_id = user.get("user_id") or user.get("id")
    await log_activity(
        db, user_id, user.get("name", ""),
        "delete", "role_management",
        f"Menghapus role: {role.get('name')}",
        request.client.host if request.client else "",
        severity="critical"
    )
    
    return {"message": "Role berhasil dihapus"}


# ==================== PERMISSION MANAGEMENT ENDPOINTS ====================

@router.get("/permissions/modules")
async def get_modules(user: dict = Depends(get_current_user)):
    """Get all modules with complete action list"""
    modules_list = []
    for code, info in MODULES.items():
        modules_list.append({
            "code": code,
            "name": info["name"],
            "category": info["category"],
            "actions": ACTIONS
        })
    
    categories = {}
    for m in modules_list:
        cat = m["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(m)
    
    return {
        "modules": modules_list,
        "categories": categories,
        "category_labels": CATEGORY_LABELS,
        "actions": ACTIONS,
        "total_modules": len(MODULES),
        "total_actions": len(ACTIONS)
    }


@router.get("/permissions/matrix/{role_id}")
async def get_permission_matrix(role_id: str, user: dict = Depends(get_current_user)):
    """Get permission matrix for a role"""
    db = get_db()
    
    role = await db["roles"].find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    # PEMILIK / SUPER ADMIN = ALL TRUE
    if role.get("inherit_all") or role.get("code") in ["super_admin", "pemilik"]:
        matrix = []
        for module_code, module_info in MODULES.items():
            row = {
                "module": module_code,
                "name": module_info["name"],
                "category": module_info["category"],
                "permissions": {action: True for action in ACTIONS}
            }
            matrix.append(row)
        
        return {
            "role": role,
            "matrix": matrix,
            "actions": ACTIONS,
            "is_full_access": True
        }
    
    # Get existing permissions
    permissions = await db["role_permissions"].find(
        {"role_id": role_id},
        {"_id": 0}
    ).to_list(10000)
    
    perm_map = {}
    for p in permissions:
        key = f"{p['module']}_{p['action']}"
        perm_map[key] = p.get("allowed", False)
    
    # Build matrix
    matrix = []
    for module_code, module_info in MODULES.items():
        row = {
            "module": module_code,
            "name": module_info["name"],
            "category": module_info["category"],
            "permissions": {}
        }
        for action in ACTIONS:
            key = f"{module_code}_{action}"
            row["permissions"][action] = perm_map.get(key, False)
        matrix.append(row)
    
    return {
        "role": role,
        "matrix": matrix,
        "actions": ACTIONS,
        "is_full_access": False
    }


@router.post("/permissions/{role_id}")
async def update_permissions(
    role_id: str, 
    data: PermissionUpdate, 
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Update permissions for a role"""
    db = get_db()
    
    role = await db["roles"].find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    # Cannot modify PEMILIK/SUPER ADMIN permissions
    if role.get("code") in ["super_admin", "pemilik"]:
        raise HTTPException(status_code=400, detail="Permission role ini tidak dapat diubah manual")
    
    for perm in data.permissions:
        module = perm.get("module")
        action = perm.get("action")
        allowed = perm.get("allowed", False)
        
        if module not in MODULES or action not in ACTIONS:
            continue
        
        await db["role_permissions"].update_one(
            {"role_id": role_id, "module": module, "action": action},
            {
                "$set": {
                    "allowed": allowed,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "role_id": role_id,
                    "module": module,
                    "action": action,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
    
    user_id = user.get("user_id") or user.get("id")
    await log_activity(
        db, user_id, user.get("name", ""),
        "edit", "role_management",
        f"Mengubah {len(data.permissions)} permission untuk role: {role.get('name')}",
        request.client.host if request.client else ""
    )
    
    return {"message": "Permissions berhasil diupdate", "count": len(data.permissions)}


@router.post("/permissions/{role_id}/bulk")
async def bulk_update_permissions(
    role_id: str,
    action: str = Query(..., description="set_all or clear_all"),
    category: str = Query("", description="Category to update (optional)"),
    request: Request = None,
    user: dict = Depends(get_current_user)
):
    """Bulk update permissions"""
    db = get_db()
    
    role = await db["roles"].find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    if role.get("code") in ["super_admin", "pemilik"]:
        raise HTTPException(status_code=400, detail="Permission role ini tidak dapat diubah")
    
    allowed = action == "set_all"
    
    modules_to_update = []
    for code, info in MODULES.items():
        if not category or info["category"] == category:
            modules_to_update.append(code)
    
    count = 0
    for module in modules_to_update:
        for act in ACTIONS:
            await db["role_permissions"].update_one(
                {"role_id": role_id, "module": module, "action": act},
                {
                    "$set": {
                        "allowed": allowed,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    },
                    "$setOnInsert": {
                        "id": str(uuid.uuid4()),
                        "role_id": role_id,
                        "module": module,
                        "action": act,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )
            count += 1
    
    user_id = user.get("user_id") or user.get("id")
    await log_activity(
        db, user_id, user.get("name", ""),
        "edit", "role_management",
        f"Bulk {'enable' if allowed else 'disable'} {count} permissions untuk role: {role.get('name')}",
        request.client.host if request.client else ""
    )
    
    return {"message": f"Berhasil update {count} permissions", "allowed": allowed}


# ==================== USER PERMISSION ENDPOINTS ====================

@router.get("/user/permissions")
async def get_my_permissions(user: dict = Depends(get_current_user)):
    """Get current user's permissions with hierarchy support"""
    user_id = user.get("user_id") or user.get("id")
    return await get_user_permissions(user_id)


@router.get("/user/{user_id}/permissions")
async def get_user_perms(user_id: str, user: dict = Depends(get_current_user)):
    """Get specific user's permissions"""
    return await get_user_permissions(user_id)


@router.put("/user/{user_id}/role")
async def assign_user_role(
    user_id: str, 
    data: UserRoleUpdate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Assign role to user with branch access"""
    db = get_db()
    
    target_user = await db["users"].find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    role = await db["roles"].find_one({"id": data.role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    await db["users"].update_one(
        {"id": user_id},
        {
            "$set": {
                "role_id": data.role_id,
                "role_name": role.get("name"),
                "role_code": role.get("code"),
                "role_level": role.get("level"),
                "branch_access": data.branch_access,
                "region_access": data.region_access,
                "all_branches": data.all_branches,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    current_user_id = user.get("user_id") or user.get("id")
    await log_activity(
        db, current_user_id, user.get("name", ""),
        "edit", "user_management",
        f"Mengubah role user {target_user.get('name')} menjadi {role.get('name')}",
        request.client.host if request.client else "",
        severity="critical" if role.get("level", 99) <= 2 else "normal"
    )
    
    return {"message": f"Role {role.get('name')} berhasil di-assign ke user"}


# ==================== PERMISSION CHECK ENDPOINTS ====================

@router.get("/check")
async def check_user_permission(
    module: str,
    action: str,
    user: dict = Depends(get_current_user)
):
    """Check if current user has specific permission"""
    user_id = user.get("user_id") or user.get("id")
    has_permission = await check_permission(user_id, module, action)
    return {
        "module": module,
        "action": action,
        "allowed": has_permission
    }


@router.get("/check-branch")
async def check_user_branch_access(
    branch_id: str,
    user: dict = Depends(get_current_user)
):
    """Check if current user has access to specific branch"""
    user_id = user.get("user_id") or user.get("id")
    has_access = await check_branch_access(user_id, branch_id)
    return {
        "branch_id": branch_id,
        "allowed": has_access
    }


# ==================== SECURITY ALERT ENDPOINTS ====================

@router.get("/security-alerts")
async def get_security_alerts(
    severity: str = "",
    acknowledged: str = "",
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get security alerts"""
    db = get_db()
    
    query = {}
    if severity:
        query["severity"] = severity
    if acknowledged:
        query["acknowledged"] = acknowledged == "true"
    
    alerts = await db["security_alerts"].find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    total = await db["security_alerts"].count_documents(query)
    unacknowledged = await db["security_alerts"].count_documents({"acknowledged": False})
    
    return {
        "alerts": alerts,
        "total": total,
        "unacknowledged": unacknowledged
    }


@router.put("/security-alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Acknowledge security alert"""
    db = get_db()
    user_id = user.get("user_id") or user.get("id")
    
    result = await db["security_alerts"].update_one(
        {"id": alert_id},
        {
            "$set": {
                "acknowledged": True,
                "acknowledged_by": user_id,
                "acknowledged_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert tidak ditemukan")
    
    return {"message": "Alert berhasil di-acknowledge"}


# ==================== AUDIT LOG ENDPOINTS ====================

@router.get("/audit-logs")
async def get_audit_logs(
    user_id: str = "",
    module: str = "",
    action: str = "",
    severity: str = "",
    branch_id: str = "",
    start_date: str = "",
    end_date: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get audit logs with comprehensive filters"""
    db = get_db()
    
    query = {}
    if user_id:
        query["user_id"] = user_id
    if module:
        query["module"] = module
    if action:
        query["action"] = action
    if severity:
        query["severity"] = severity
    if branch_id:
        query["branch_id"] = branch_id
    
    date_filter = {}
    if start_date:
        date_filter["$gte"] = start_date
    if end_date:
        date_filter["$lt"] = end_date
    if date_filter:
        query["created_at"] = date_filter
    
    logs = await db["audit_logs"].find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db["audit_logs"].count_documents(query)
    
    return {"logs": logs, "total": total}


# ==================== AUTO PERMISSION GENERATOR ====================

async def auto_generate_permissions(db, role_id: str, level: int):
    """Auto-generate base permissions based on role level"""
    
    # Level-based default permissions
    level_permissions = {
        0: ACTIONS,  # Super Admin - all
        1: ACTIONS,  # Pemilik - all
        2: ["view", "create", "edit", "delete", "approve", "export", "print"],  # Direktur
        3: ["view", "create", "edit", "delete", "approve", "export", "print"],  # Manager
        4: ["view", "create", "edit", "approve", "export", "print"],  # Supervisor
        5: ["view", "create", "edit", "export", "print"],  # Admin
        6: ["view", "create", "edit", "print"],  # Gudang/Keuangan
        7: ["view", "create", "print"],  # Kasir
        8: ["view"]  # Viewer
    }
    
    default_actions = level_permissions.get(level, ["view"])
    
    for module in MODULES.keys():
        for action in ACTIONS:
            allowed = action in default_actions
            await db["role_permissions"].update_one(
                {"role_id": role_id, "module": module, "action": action},
                {
                    "$set": {
                        "allowed": allowed,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    },
                    "$setOnInsert": {
                        "id": str(uuid.uuid4()),
                        "role_id": role_id,
                        "module": module,
                        "action": action,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )


# ==================== INITIALIZATION ====================

@router.post("/init")
async def initialize_rbac(request: Request, user: dict = Depends(get_current_user)):
    """Initialize Enterprise RBAC system with role hierarchy"""
    db = get_db()
    
    # Create/update roles based on hierarchy
    roles_created = 0
    roles_updated = 0
    
    for code, hierarchy_info in ROLE_HIERARCHY.items():
        existing = await db["roles"].find_one({"code": code})
        
        role_data = {
            "code": code,
            "name": hierarchy_info.get("name", code.title()),
            "description": f"Role level {hierarchy_info.get('level', 99)}",
            "level": hierarchy_info.get("level", 99),
            "inherit_all": hierarchy_info.get("inherit_all", False),
            "all_branches": hierarchy_info.get("all_branches", False),
            "view_only": hierarchy_info.get("view_only", False),
            "can_manage_system": hierarchy_info.get("can_manage_system", False),
            "inherit_from": hierarchy_info.get("inherit_from", []),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if existing:
            await db["roles"].update_one({"code": code}, {"$set": role_data})
            roles_updated += 1
            role_id = existing.get("id")
        else:
            role_data["id"] = str(uuid.uuid4())
            role_data["created_at"] = datetime.now(timezone.utc).isoformat()
            await db["roles"].insert_one(role_data)
            roles_created += 1
            role_id = role_data["id"]
        
        # Generate permissions based on level (skip for inherit_all roles)
        if not hierarchy_info.get("inherit_all"):
            await auto_generate_permissions(db, role_id, hierarchy_info.get("level", 99))
    
    # Create indexes for performance
    await db["roles"].create_index("code", unique=True)
    await db["roles"].create_index("level")
    await db["role_permissions"].create_index([("role_id", 1), ("module", 1), ("action", 1)], unique=True)
    await db["audit_logs"].create_index("created_at")
    await db["audit_logs"].create_index("user_id")
    await db["security_alerts"].create_index("created_at")
    await db["security_alerts"].create_index("acknowledged")
    
    user_id = user.get("user_id") or user.get("id")
    await log_activity(
        db, user_id, user.get("name", ""),
        "create", "role_management",
        f"Inisialisasi Enterprise RBAC: {roles_created} roles created, {roles_updated} updated",
        request.client.host if request.client else ""
    )
    
    return {
        "message": "Enterprise RBAC system initialized",
        "roles_created": roles_created,
        "roles_updated": roles_updated,
        "total_modules": len(MODULES),
        "total_actions": len(ACTIONS),
        "hierarchy": ROLE_HIERARCHY
    }


@router.post("/validate-system")
async def validate_rbac_system(user: dict = Depends(get_current_user)):
    """Validate RBAC system integrity"""
    db = get_db()
    
    issues = []
    
    # Check all roles have permissions
    roles = await db["roles"].find({}, {"_id": 0, "id": 1, "code": 1, "inherit_all": 1}).to_list(100)
    for role in roles:
        if not role.get("inherit_all"):
            perm_count = await db["role_permissions"].count_documents({"role_id": role["id"]})
            expected = len(MODULES) * len(ACTIONS)
            if perm_count < expected:
                issues.append(f"Role {role['code']} missing {expected - perm_count} permissions")
    
    # Check all users have roles
    users_without_roles = await db["users"].count_documents({"role_id": {"$in": [None, ""]}})
    if users_without_roles > 0:
        issues.append(f"{users_without_roles} users tanpa role assignment")
    
    # Check for orphaned permissions
    role_ids = [r["id"] for r in roles]
    orphaned = await db["role_permissions"].count_documents({"role_id": {"$nin": role_ids}})
    if orphaned > 0:
        issues.append(f"{orphaned} orphaned permissions ditemukan")
    
    return {
        "status": "healthy" if not issues else "issues_found",
        "issues": issues,
        "total_roles": len(roles),
        "total_modules": len(MODULES),
        "total_actions": len(ACTIONS)
    }
