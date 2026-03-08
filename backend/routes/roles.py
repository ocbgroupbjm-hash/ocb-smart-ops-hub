# OCB TITAN - Role & Permission Management
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from database import db
from utils.auth import get_current_user
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/roles", tags=["Roles"])

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# Default permissions structure
DEFAULT_PERMISSIONS = {
    "dashboard": {"lihat": True, "export": False},
    "kasir": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "void": False, "retur": False, "cetak": False},
    "produk": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "export": False},
    "stok": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "transfer": False, "opname": False, "export": False},
    "pembelian": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "approve": False, "terima": False},
    "supplier": {"lihat": False, "tambah": False, "edit": False, "hapus": False},
    "pelanggan": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "export": False},
    "keuangan": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "approve": False, "export": False},
    "akuntansi": {"lihat": False, "export": False},
    "laporan": {"lihat": False, "export": False, "cetak": False},
    "cabang": {"lihat": False, "tambah": False, "edit": False, "hapus": False},
    "pengguna": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "reset_password": False},
    "pengaturan": {"lihat": False, "edit": False},
    "ai_bisnis": {"lihat": False}
}

# Default roles with their permissions
DEFAULT_ROLES = {
    "owner": {
        "name": "Pemilik",
        "description": "Akses penuh ke seluruh sistem",
        "is_system": True,
        "permissions": {k: {pk: True for pk in pv.keys()} for k, pv in DEFAULT_PERMISSIONS.items()}
    },
    "admin": {
        "name": "Administrator",
        "description": "Mengelola sistem dan pengguna",
        "is_system": True,
        "permissions": {
            "dashboard": {"lihat": True, "export": True},
            "kasir": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "void": True, "retur": True, "cetak": True},
            "produk": {"lihat": True, "tambah": True, "edit": True, "hapus": True, "export": True},
            "stok": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "transfer": True, "opname": True, "export": True},
            "pembelian": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "approve": True, "terima": True},
            "supplier": {"lihat": True, "tambah": True, "edit": True, "hapus": True},
            "pelanggan": {"lihat": True, "tambah": True, "edit": True, "hapus": True, "export": True},
            "keuangan": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "approve": True, "export": True},
            "akuntansi": {"lihat": True, "export": True},
            "laporan": {"lihat": True, "export": True, "cetak": True},
            "cabang": {"lihat": True, "tambah": True, "edit": True, "hapus": False},
            "pengguna": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "reset_password": True},
            "pengaturan": {"lihat": True, "edit": True},
            "ai_bisnis": {"lihat": True}
        }
    },
    "supervisor": {
        "name": "Supervisor",
        "description": "Mengawasi operasional cabang",
        "is_system": True,
        "permissions": {
            "dashboard": {"lihat": True, "export": False},
            "kasir": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "void": True, "retur": True, "cetak": True},
            "produk": {"lihat": True, "tambah": False, "edit": False, "hapus": False, "export": True},
            "stok": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "transfer": True, "opname": True, "export": True},
            "pembelian": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "approve": False, "terima": True},
            "supplier": {"lihat": True, "tambah": False, "edit": False, "hapus": False},
            "pelanggan": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "export": True},
            "keuangan": {"lihat": True, "tambah": True, "edit": False, "hapus": False, "approve": False, "export": False},
            "akuntansi": {"lihat": False, "export": False},
            "laporan": {"lihat": True, "export": True, "cetak": True},
            "cabang": {"lihat": True, "tambah": False, "edit": False, "hapus": False},
            "pengguna": {"lihat": True, "tambah": False, "edit": False, "hapus": False, "reset_password": False},
            "pengaturan": {"lihat": True, "edit": False},
            "ai_bisnis": {"lihat": True}
        }
    },
    "cashier": {
        "name": "Kasir",
        "description": "Melayani transaksi penjualan",
        "is_system": True,
        "permissions": {
            "dashboard": {"lihat": True, "export": False},
            "kasir": {"lihat": True, "tambah": True, "edit": False, "hapus": False, "void": False, "retur": False, "cetak": True},
            "produk": {"lihat": True, "tambah": False, "edit": False, "hapus": False, "export": False},
            "stok": {"lihat": True, "tambah": False, "edit": False, "hapus": False, "transfer": False, "opname": False, "export": False},
            "pembelian": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "approve": False, "terima": False},
            "supplier": {"lihat": False, "tambah": False, "edit": False, "hapus": False},
            "pelanggan": {"lihat": True, "tambah": True, "edit": False, "hapus": False, "export": False},
            "keuangan": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "approve": False, "export": False},
            "akuntansi": {"lihat": False, "export": False},
            "laporan": {"lihat": False, "export": False, "cetak": False},
            "cabang": {"lihat": False, "tambah": False, "edit": False, "hapus": False},
            "pengguna": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "reset_password": False},
            "pengaturan": {"lihat": False, "edit": False},
            "ai_bisnis": {"lihat": False}
        }
    },
    "finance": {
        "name": "Keuangan",
        "description": "Mengelola keuangan dan akuntansi",
        "is_system": True,
        "permissions": {
            "dashboard": {"lihat": True, "export": True},
            "kasir": {"lihat": True, "tambah": False, "edit": False, "hapus": False, "void": False, "retur": False, "cetak": False},
            "produk": {"lihat": True, "tambah": False, "edit": False, "hapus": False, "export": True},
            "stok": {"lihat": True, "tambah": False, "edit": False, "hapus": False, "transfer": False, "opname": False, "export": True},
            "pembelian": {"lihat": True, "tambah": False, "edit": False, "hapus": False, "approve": True, "terima": False},
            "supplier": {"lihat": True, "tambah": False, "edit": False, "hapus": False},
            "pelanggan": {"lihat": True, "tambah": False, "edit": False, "hapus": False, "export": True},
            "keuangan": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "approve": True, "export": True},
            "akuntansi": {"lihat": True, "export": True},
            "laporan": {"lihat": True, "export": True, "cetak": True},
            "cabang": {"lihat": True, "tambah": False, "edit": False, "hapus": False},
            "pengguna": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "reset_password": False},
            "pengaturan": {"lihat": False, "edit": False},
            "ai_bisnis": {"lihat": True}
        }
    },
    "inventory": {
        "name": "Gudang",
        "description": "Mengelola stok dan inventory",
        "is_system": True,
        "permissions": {
            "dashboard": {"lihat": True, "export": False},
            "kasir": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "void": False, "retur": False, "cetak": False},
            "produk": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "export": True},
            "stok": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "transfer": True, "opname": True, "export": True},
            "pembelian": {"lihat": True, "tambah": True, "edit": True, "hapus": False, "approve": False, "terima": True},
            "supplier": {"lihat": True, "tambah": True, "edit": True, "hapus": False},
            "pelanggan": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "export": False},
            "keuangan": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "approve": False, "export": False},
            "akuntansi": {"lihat": False, "export": False},
            "laporan": {"lihat": True, "export": True, "cetak": False},
            "cabang": {"lihat": True, "tambah": False, "edit": False, "hapus": False},
            "pengguna": {"lihat": False, "tambah": False, "edit": False, "hapus": False, "reset_password": False},
            "pengaturan": {"lihat": False, "edit": False},
            "ai_bisnis": {"lihat": False}
        }
    }
}

class RoleCreate(BaseModel):
    code: str
    name: str
    description: str = ""
    permissions: Dict = Field(default_factory=lambda: DEFAULT_PERMISSIONS)

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict] = None

@router.get("")
async def get_roles(current_user: dict = Depends(get_current_user)):
    """Get all roles"""
    roles_col = db["roles"]
    
    # Initialize default roles if not exists
    existing = await roles_col.find({}, {"_id": 0}).to_list(100)
    if not existing:
        for code, role_data in DEFAULT_ROLES.items():
            await roles_col.insert_one({
                "id": str(uuid.uuid4()),
                "code": code,
                **role_data,
                "created_at": now_iso()
            })
        existing = await roles_col.find({}, {"_id": 0}).to_list(100)
    
    return existing

@router.get("/permissions-template")
async def get_permissions_template(current_user: dict = Depends(get_current_user)):
    """Get default permissions template"""
    return DEFAULT_PERMISSIONS

@router.get("/{role_code}")
async def get_role(role_code: str, current_user: dict = Depends(get_current_user)):
    """Get role by code"""
    roles_col = db["roles"]
    role = await roles_col.find_one({"code": role_code}, {"_id": 0})
    if not role:
        # Return from default if not in DB
        if role_code in DEFAULT_ROLES:
            return {"code": role_code, **DEFAULT_ROLES[role_code]}
        raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    return role

@router.post("")
async def create_role(role: RoleCreate, current_user: dict = Depends(get_current_user)):
    """Create new role"""
    if current_user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    roles_col = db["roles"]
    
    # Check if code exists
    existing = await roles_col.find_one({"code": role.code})
    if existing or role.code in DEFAULT_ROLES:
        raise HTTPException(status_code=400, detail="Kode role sudah digunakan")
    
    role_data = {
        "id": str(uuid.uuid4()),
        "code": role.code,
        "name": role.name,
        "description": role.description,
        "permissions": role.permissions,
        "is_system": False,
        "created_at": now_iso()
    }
    
    await roles_col.insert_one(role_data)
    if "_id" in role_data:
        del role_data["_id"]
    return role_data

@router.put("/{role_code}")
async def update_role(role_code: str, role: RoleUpdate, current_user: dict = Depends(get_current_user)):
    """Update role permissions"""
    if current_user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Akses ditolak")
    
    roles_col = db["roles"]
    
    # Get existing or create from default
    existing = await roles_col.find_one({"code": role_code})
    if not existing:
        if role_code in DEFAULT_ROLES:
            # Insert default role to DB first
            existing = {
                "id": str(uuid.uuid4()),
                "code": role_code,
                **DEFAULT_ROLES[role_code],
                "created_at": now_iso()
            }
            await roles_col.insert_one(existing)
        else:
            raise HTTPException(status_code=404, detail="Role tidak ditemukan")
    
    # Update fields
    update_data = {}
    if role.name is not None:
        update_data["name"] = role.name
    if role.description is not None:
        update_data["description"] = role.description
    if role.permissions is not None:
        update_data["permissions"] = role.permissions
    update_data["updated_at"] = now_iso()
    
    await roles_col.update_one({"code": role_code}, {"$set": update_data})
    
    return {"message": "Role berhasil diperbarui"}

@router.delete("/{role_code}")
async def delete_role(role_code: str, current_user: dict = Depends(get_current_user)):
    """Delete custom role"""
    if current_user.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Hanya pemilik yang dapat menghapus role")
    
    if role_code in DEFAULT_ROLES:
        raise HTTPException(status_code=400, detail="Role sistem tidak dapat dihapus")
    
    roles_col = db["roles"]
    result = await roles_col.delete_one({"code": role_code, "is_system": False})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Role tidak ditemukan atau merupakan role sistem")
    
    return {"message": "Role berhasil dihapus"}

@router.get("/user/{user_id}/permissions")
async def get_user_permissions(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get effective permissions for a user"""
    users_col = db["users"]
    roles_col = db["roles"]
    
    user = await users_col.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    
    role_code = user.get("role", "cashier")
    
    # Get role permissions
    role = await roles_col.find_one({"code": role_code}, {"_id": 0})
    if role:
        return {"user_id": user_id, "role": role_code, "permissions": role.get("permissions", {})}
    
    # Fallback to default
    if role_code in DEFAULT_ROLES:
        return {"user_id": user_id, "role": role_code, "permissions": DEFAULT_ROLES[role_code]["permissions"]}
    
    return {"user_id": user_id, "role": role_code, "permissions": DEFAULT_PERMISSIONS}
