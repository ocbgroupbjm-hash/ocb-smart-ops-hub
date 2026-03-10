# OCB TITAN ERP - ROLE BASED ACCESS CONTROL (RBAC) SYSTEM
# Enterprise Level Permission Management

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/rbac", tags=["RBAC - Role Based Access Control"])

def get_db():
    from database import get_db as db_get
    return db_get()

from routes.auth import get_current_user

# ==================== PERMISSION DEFINITIONS ====================

# All available actions
ACTIONS = [
    "view", "create", "edit", "delete", "approve", "export", "print",
    "lock_number", "lock_date", "override_price", "override_discount"
]

# All modules with their permissions
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
}

# Default role templates
DEFAULT_ROLES = {
    "super_admin": {
        "name": "Super Admin",
        "description": "Full access to all modules and features",
        "level": 1,
        "all_permissions": True,
        "all_branches": True
    },
    "owner": {
        "name": "Owner",
        "description": "Business owner with full access",
        "level": 2,
        "all_permissions": True,
        "all_branches": True
    },
    "director": {
        "name": "Direktur",
        "description": "Director level access",
        "level": 3,
        "all_branches": True
    },
    "manager": {
        "name": "Manager",
        "description": "Manager with branch-level access",
        "level": 4,
        "all_branches": False
    },
    "supervisor": {
        "name": "Supervisor",
        "description": "Supervisor with limited management access",
        "level": 5,
        "all_branches": False
    },
    "admin": {
        "name": "Admin",
        "description": "Administrative staff",
        "level": 6,
        "all_branches": False
    },
    "cashier": {
        "name": "Kasir",
        "description": "Cashier with POS access only",
        "level": 7,
        "all_branches": False,
        "direct_cashier": True
    },
    "warehouse": {
        "name": "Gudang",
        "description": "Warehouse staff with inventory access",
        "level": 8,
        "all_branches": False
    },
    "accounting": {
        "name": "Akunting",
        "description": "Accounting staff with finance access",
        "level": 9,
        "all_branches": False
    },
    "marketing": {
        "name": "Marketing",
        "description": "Marketing staff with limited access",
        "level": 10,
        "all_branches": False
    },
    "viewer": {
        "name": "Viewer",
        "description": "View-only access",
        "level": 11,
        "all_branches": False,
        "view_only": True
    }
}


# ==================== PYDANTIC MODELS ====================

class RoleCreate(BaseModel):
    code: str
    name: str
    description: str = ""
    level: int = 10
    all_permissions: bool = False
    all_branches: bool = False
    direct_cashier: bool = False
    view_only: bool = False
    branch_access: List[str] = []
    account_access: List[str] = []

class PermissionUpdate(BaseModel):
    permissions: List[Dict[str, Any]]  # [{module, action, allowed}]

class UserRoleUpdate(BaseModel):
    role_id: str
    branch_access: List[str] = []


# ==================== AUDIT LOG ====================

async def log_activity(
    db,
    user_id: str,
    user_name: str,
    action: str,
    module: str,
    description: str,
    ip_address: str = "",
    data_before: Dict = None,
    data_after: Dict = None
):
    """Log all user activities for audit trail"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "module": module,
        "description": description,
        "ip_address": ip_address,
        "data_before": data_before,
        "data_after": data_after,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db["audit_logs"].insert_one(log_entry)
    return log_entry


# ==================== PERMISSION CHECK ====================

async def check_permission(user_id: str, module: str, action: str) -> bool:
    """Check if user has permission for specific module and action"""
    db = get_db()
    
    # Get user with role
    user = await db["users"].find_one({"id": user_id}, {"_id": 0, "role_id": 1})
    if not user or not user.get("role_id"):
        return False
    
    # Get role
    role = await db["roles"].find_one({"id": user["role_id"]}, {"_id": 0})
    if not role:
        return False
    
    # Super admin / all permissions
    if role.get("all_permissions"):
        return True
    
    # View only role
    if role.get("view_only") and action != "view":
        return False
    
    # Check specific permission
    permission = await db["role_permissions"].find_one({
        "role_id": user["role_id"],
        "module": module,
        "action": action,
        "allowed": True
    }, {"_id": 0})
    
    return permission is not None


async def check_branch_access(user_id: str, branch_id: str) -> bool:
    """Check if user has access to specific branch"""
    db = get_db()
    
    user = await db["users"].find_one({"id": user_id}, {"_id": 0, "role_id": 1, "branch_access": 1})
    if not user:
        return False
    
    role = await db["roles"].find_one({"id": user.get("role_id")}, {"_id": 0, "all_branches": 1})
    if role and role.get("all_branches"):
        return True
    
    branch_access = user.get("branch_access", [])
    return branch_id in branch_access or not branch_access


async def get_user_permissions(user_id: str) -> Dict[str, Any]:
    """Get all permissions for a user"""
    db = get_db()
    
    user = await db["users"].find_one({"id": user_id}, {"_id": 0})
    if not user:
        return {}
    
    role = await db["roles"].find_one({"id": user.get("role_id")}, {"_id": 0})
    if not role:
        return {}
    
    # Get all permissions for role
    permissions = await db["role_permissions"].find(
        {"role_id": role["id"], "allowed": True},
        {"_id": 0, "module": 1, "action": 1}
    ).to_list(1000)
    
    # Build permission map
    perm_map = {}
    for p in permissions:
        module = p["module"]
        action = p["action"]
        if module not in perm_map:
            perm_map[module] = []
        perm_map[module].append(action)
    
    return {
        "user_id": user_id,
        "role_id": role["id"],
        "role_name": role.get("name"),
        "all_permissions": role.get("all_permissions", False),
        "all_branches": role.get("all_branches", False),
        "view_only": role.get("view_only", False),
        "direct_cashier": role.get("direct_cashier", False),
        "branch_access": user.get("branch_access", []),
        "account_access": user.get("account_access", []),
        "permissions": perm_map,
        "menu_visibility": {
            "master": await check_permission(user_id, "menu_master", "view"),
            "purchase": await check_permission(user_id, "menu_purchase", "view"),
            "sales": await check_permission(user_id, "menu_sales", "view"),
            "inventory": await check_permission(user_id, "menu_inventory", "view"),
            "accounting": await check_permission(user_id, "menu_accounting", "view"),
            "report": await check_permission(user_id, "menu_report", "view"),
            "setting": await check_permission(user_id, "menu_setting", "view")
        }
    }


# ==================== ROLE MANAGEMENT ENDPOINTS ====================

@router.get("/roles")
async def get_roles(user: dict = Depends(get_current_user)):
    """Get all roles"""
    db = get_db()
    roles = await db["roles"].find({}, {"_id": 0}).sort("level", 1).to_list(100)
    return {"roles": roles, "total": len(roles)}


@router.get("/roles/{role_id}")
async def get_role(role_id: str, user: dict = Depends(get_current_user)):
    """Get single role with permissions"""
    db = get_db()
    
    role = await db["roles"].find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    # Get permissions
    permissions = await db["role_permissions"].find(
        {"role_id": role_id},
        {"_id": 0}
    ).to_list(1000)
    
    role["permissions"] = permissions
    return role


@router.post("/roles")
async def create_role(data: RoleCreate, request: Request, user: dict = Depends(get_current_user)):
    """Create new role"""
    db = get_db()
    
    # Check if code exists
    existing = await db["roles"].find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Kode role sudah ada")
    
    role = {
        "id": str(uuid.uuid4()),
        "code": data.code,
        "name": data.name,
        "description": data.description,
        "level": data.level,
        "all_permissions": data.all_permissions,
        "all_branches": data.all_branches,
        "direct_cashier": data.direct_cashier,
        "view_only": data.view_only,
        "branch_access": data.branch_access,
        "account_access": data.account_access,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("id")
    }
    
    await db["roles"].insert_one(role)
    
    # Log activity
    await log_activity(
        db, user.get("id"), user.get("name", ""),
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
        "all_permissions": data.all_permissions,
        "all_branches": data.all_branches,
        "direct_cashier": data.direct_cashier,
        "view_only": data.view_only,
        "branch_access": data.branch_access,
        "account_access": data.account_access,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db["roles"].update_one({"id": role_id}, {"$set": update_data})
    
    # Log activity
    await log_activity(
        db, user.get("id"), user.get("name", ""),
        "edit", "role_management",
        f"Mengubah role: {data.name}",
        request.client.host if request.client else "",
        role, update_data
    )
    
    return {"message": "Role berhasil diupdate"}


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Delete role"""
    db = get_db()
    
    role = await db["roles"].find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    # Check if role is in use
    users_with_role = await db["users"].count_documents({"role_id": role_id})
    if users_with_role > 0:
        raise HTTPException(status_code=400, detail=f"Role sedang digunakan oleh {users_with_role} user")
    
    await db["roles"].delete_one({"id": role_id})
    await db["role_permissions"].delete_many({"role_id": role_id})
    
    # Log activity
    await log_activity(
        db, user.get("id"), user.get("name", ""),
        "delete", "role_management",
        f"Menghapus role: {role.get('name')}",
        request.client.host if request.client else ""
    )
    
    return {"message": "Role berhasil dihapus"}


# ==================== PERMISSION MANAGEMENT ENDPOINTS ====================

@router.get("/permissions/modules")
async def get_modules(user: dict = Depends(get_current_user)):
    """Get all available modules and their permissions"""
    modules_list = []
    for code, info in MODULES.items():
        modules_list.append({
            "code": code,
            "name": info["name"],
            "category": info["category"],
            "actions": ACTIONS
        })
    
    # Group by category
    categories = {}
    for m in modules_list:
        cat = m["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(m)
    
    return {
        "modules": modules_list,
        "categories": categories,
        "actions": ACTIONS
    }


@router.get("/permissions/matrix/{role_id}")
async def get_permission_matrix(role_id: str, user: dict = Depends(get_current_user)):
    """Get permission matrix for a role"""
    db = get_db()
    
    role = await db["roles"].find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    # Get existing permissions
    permissions = await db["role_permissions"].find(
        {"role_id": role_id},
        {"_id": 0}
    ).to_list(5000)
    
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
        "actions": ACTIONS
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
    
    # Update each permission
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
    
    # Log activity
    await log_activity(
        db, user.get("id"), user.get("name", ""),
        "edit", "role_management",
        f"Mengubah permission role: {role.get('name')} ({len(data.permissions)} permissions)",
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
    """Bulk update permissions (set all or clear all)"""
    db = get_db()
    
    role = await db["roles"].find_one({"id": role_id}, {"_id": 0})
    if not role:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    allowed = action == "set_all"
    
    # Filter by category if specified
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
    
    # Log activity
    await log_activity(
        db, user.get("id"), user.get("name", ""),
        "edit", "role_management",
        f"Bulk {'enable' if allowed else 'disable'} permissions role: {role.get('name')} ({count} permissions)",
        request.client.host if request.client else ""
    )
    
    return {"message": f"Berhasil update {count} permissions", "allowed": allowed}


# ==================== USER PERMISSION ENDPOINTS ====================

@router.get("/user/permissions")
async def get_my_permissions(user: dict = Depends(get_current_user)):
    """Get current user's permissions"""
    return await get_user_permissions(user.get("id"))


@router.get("/user/{user_id}/permissions")
async def get_user_perms(user_id: str, user: dict = Depends(get_current_user)):
    """Get specific user's permissions (admin only)"""
    return await get_user_permissions(user_id)


@router.put("/user/{user_id}/role")
async def assign_user_role(
    user_id: str, 
    data: UserRoleUpdate,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """Assign role to user"""
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
                "branch_access": data.branch_access,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Log activity
    await log_activity(
        db, user.get("id"), user.get("name", ""),
        "edit", "user_management",
        f"Mengubah role user {target_user.get('name')} menjadi {role.get('name')}",
        request.client.host if request.client else ""
    )
    
    return {"message": f"Role {role.get('name')} berhasil di-assign ke user"}


# ==================== PERMISSION CHECK ENDPOINT ====================

@router.get("/check")
async def check_user_permission(
    module: str,
    action: str,
    user: dict = Depends(get_current_user)
):
    """Check if current user has specific permission"""
    has_permission = await check_permission(user.get("id"), module, action)
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
    has_access = await check_branch_access(user.get("id"), branch_id)
    return {
        "branch_id": branch_id,
        "allowed": has_access
    }


# ==================== AUDIT LOG ENDPOINTS ====================

@router.get("/audit-logs")
async def get_audit_logs(
    user_id: str = "",
    module: str = "",
    action: str = "",
    start_date: str = "",
    end_date: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get audit logs"""
    db = get_db()
    
    query = {}
    if user_id:
        query["user_id"] = user_id
    if module:
        query["module"] = module
    if action:
        query["action"] = action
    
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


# ==================== INITIALIZATION ====================

@router.post("/init")
async def initialize_rbac(request: Request, user: dict = Depends(get_current_user)):
    """Initialize RBAC system with default roles and permissions"""
    db = get_db()
    
    # Create default roles
    roles_created = 0
    for code, role_data in DEFAULT_ROLES.items():
        existing = await db["roles"].find_one({"code": code})
        if not existing:
            role = {
                "id": str(uuid.uuid4()),
                "code": code,
                **role_data,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db["roles"].insert_one(role)
            roles_created += 1
    
    # Create default permissions for super_admin (all permissions)
    super_admin = await db["roles"].find_one({"code": "super_admin"}, {"_id": 0, "id": 1})
    if super_admin:
        perms_created = 0
        for module in MODULES.keys():
            for action in ACTIONS:
                existing = await db["role_permissions"].find_one({
                    "role_id": super_admin["id"],
                    "module": module,
                    "action": action
                })
                if not existing:
                    await db["role_permissions"].insert_one({
                        "id": str(uuid.uuid4()),
                        "role_id": super_admin["id"],
                        "module": module,
                        "action": action,
                        "allowed": True,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
                    perms_created += 1
    
    # Create viewer role permissions (view only)
    viewer = await db["roles"].find_one({"code": "viewer"}, {"_id": 0, "id": 1})
    if viewer:
        for module in MODULES.keys():
            existing = await db["role_permissions"].find_one({
                "role_id": viewer["id"],
                "module": module,
                "action": "view"
            })
            if not existing:
                await db["role_permissions"].insert_one({
                    "id": str(uuid.uuid4()),
                    "role_id": viewer["id"],
                    "module": module,
                    "action": "view",
                    "allowed": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
    
    # Create cashier role permissions
    cashier = await db["roles"].find_one({"code": "cashier"}, {"_id": 0, "id": 1})
    if cashier:
        cashier_modules = ["cashier", "sales", "sales_return", "cash_drawer", "customer_points"]
        cashier_actions = ["view", "create", "edit", "print"]
        for module in cashier_modules:
            for action in cashier_actions:
                existing = await db["role_permissions"].find_one({
                    "role_id": cashier["id"],
                    "module": module,
                    "action": action
                })
                if not existing:
                    await db["role_permissions"].insert_one({
                        "id": str(uuid.uuid4()),
                        "role_id": cashier["id"],
                        "module": module,
                        "action": action,
                        "allowed": True,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    })
    
    # Log activity
    await log_activity(
        db, user.get("id"), user.get("name", ""),
        "create", "role_management",
        f"Inisialisasi RBAC system: {roles_created} roles created",
        request.client.host if request.client else ""
    )
    
    return {
        "message": "RBAC system initialized",
        "roles_created": roles_created,
        "total_modules": len(MODULES),
        "total_actions": len(ACTIONS)
    }
