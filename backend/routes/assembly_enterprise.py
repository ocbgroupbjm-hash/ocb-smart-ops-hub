# ============================================================================
# OCB TITAN ERP - ASSEMBLY MODULE (ENTERPRISE GRADE)
# ============================================================================
# Modul Perakitan dengan standar ERP Enterprise:
# - Multi-komponen support
# - DRAFT → POSTED workflow
# - Reversal untuk koreksi (bukan edit/delete langsung untuk POSTED)
# - Integrasi SSOT: stock_movements & journal_entries
# - Audit trail lengkap
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, timezone
from database import db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/assembly-enterprise", tags=["Assembly Enterprise"])

# ============ COLLECTIONS ============
assembly_formulas = db["assembly_formulas"]
assembly_components = db["assembly_components"]
assembly_transactions = db["assembly_transactions"]
assembly_logs = db["assembly_logs"]
products_collection = db["products"]
stock_movements_collection = db["stock_movements"]
journal_entries_collection = db["journal_entries"]
audit_logs = db["audit_logs"]
# Legacy collection for backward compatibility
assemblies_legacy = db["assemblies"]


# ============ PYDANTIC MODELS ============

class ComponentInput(BaseModel):
    """Model untuk input komponen formula"""
    item_id: str
    quantity_required: float = Field(..., gt=0)
    uom: str = "pcs"
    sequence_no: Optional[int] = 1
    waste_factor: Optional[float] = 0  # Persentase waste (0-100)


class FormulaCreateRequest(BaseModel):
    """Request untuk membuat formula baru"""
    formula_name: str = Field(..., min_length=3)
    product_result_id: str
    result_quantity: float = Field(..., gt=0)
    uom: str = "pcs"
    components: List[ComponentInput] = Field(..., min_items=1)
    warehouse_id: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('components')
    def validate_components(cls, v):
        if len(v) < 1:
            raise ValueError('Formula harus memiliki minimal 1 komponen')
        return v


class FormulaUpdateRequest(BaseModel):
    """Request untuk update formula"""
    formula_name: Optional[str] = None
    product_result_id: Optional[str] = None
    result_quantity: Optional[float] = None
    uom: Optional[str] = None
    components: Optional[List[ComponentInput]] = None
    warehouse_id: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # ACTIVE / INACTIVE


class AssemblyExecutionRequest(BaseModel):
    """Request untuk eksekusi perakitan"""
    formula_id: str
    planned_qty: int = Field(..., gt=0)
    warehouse_id: Optional[str] = None
    notes: Optional[str] = None
    save_as_draft: bool = True  # Default save as DRAFT


class AssemblyPostRequest(BaseModel):
    """Request untuk posting transaksi DRAFT"""
    assembly_id: str


class AssemblyReversalRequest(BaseModel):
    """Request untuk reversal transaksi POSTED"""
    assembly_id: str
    reason: str = Field(..., min_length=5)
    notes: Optional[str] = None


# ============ HELPER FUNCTIONS ============

async def log_assembly_action(
    assembly_id: str, 
    action: str, 
    user_id: str, 
    user_name: str,
    old_value: dict = None,
    new_value: dict = None,
    tenant_id: str = "ocb_titan"
):
    """Log setiap aksi assembly ke audit trail"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "assembly_id": assembly_id,
        "action": action,
        "old_value": old_value,
        "new_value": new_value,
        "user_id": user_id,
        "user_name": user_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tenant_id": tenant_id
    }
    await assembly_logs.insert_one(log_entry)
    return log_entry["id"]


async def calculate_stock_from_movements(product_id: str, branch_id: str = None) -> float:
    """Calculate current stock from stock_movements (SSOT)"""
    query = {"product_id": product_id}
    if branch_id:
        query["branch_id"] = branch_id
    
    pipeline = [
        {"$match": query},
        {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
    ]
    
    result = await stock_movements_collection.aggregate(pipeline).to_list(1)
    return result[0]["total"] if result else 0


async def derive_account(account_type: str, branch_id: str = None) -> dict:
    """Get account codes for accounting entries"""
    account_map = {
        "inventory_finished": {"code": "1-1400", "name": "Persediaan Barang Jadi"},
        "inventory_raw": {"code": "1-1300", "name": "Persediaan Bahan Baku"},
        "wip": {"code": "1-1350", "name": "Barang Dalam Proses (WIP)"},
        "assembly_variance": {"code": "5-3100", "name": "Selisih Assembly"}
    }
    return account_map.get(account_type, {"code": "1-1400", "name": "Persediaan"})


async def create_journal_entry(
    reference_type: str,
    reference_id: str,
    reference_no: str,
    description: str,
    entries: list,
    branch_id: str,
    user_id: str,
    user_name: str,
    tenant_id: str = "ocb_titan"
) -> str:
    """Create journal entry for assembly/disassembly"""
    journal_number = f"JV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{reference_no}"
    
    total_debit = sum(e.get("debit", 0) for e in entries)
    total_credit = sum(e.get("credit", 0) for e in entries)
    
    # Ensure balanced
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(status_code=400, detail=f"Journal tidak balance: Debit={total_debit}, Credit={total_credit}")
    
    journal_doc = {
        "id": str(uuid.uuid4()),
        "journal_number": journal_number,
        "journal_date": datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        "reference_type": reference_type,
        "reference_id": reference_id,
        "reference_no": reference_no,
        "description": description,
        "entries": entries,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "status": "posted",
        "journal_source": reference_type,
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await journal_entries_collection.insert_one(journal_doc)
    return journal_number


# ============ FORMULA ENDPOINTS ============

@router.get("/formulas/v2")
async def list_formulas_v2(
    search: str = "",
    status: str = "ACTIVE",
    skip: int = 0,
    limit: int = 100,
    include_legacy: bool = True,
    user: dict = Depends(get_current_user)
):
    """
    List semua formula perakitan (Enterprise Version)
    
    Filter:
    - search: Cari berdasarkan nama formula atau produk hasil
    - status: ACTIVE / INACTIVE / ALL
    - include_legacy: Include formulas from old collection (default: true)
    """
    tenant_id = user.get("tenant_id", "ocb_titan")
    
    query = {"tenant_id": tenant_id}
    if status != "ALL":
        query["status"] = status
    if search:
        query["$or"] = [
            {"formula_name": {"$regex": search, "$options": "i"}},
            {"result_product_name": {"$regex": search, "$options": "i"}}
        ]
    
    total = await assembly_formulas.count_documents(query)
    formulas = await assembly_formulas.find(query, {"_id": 0}).skip(skip).limit(limit).sort("formula_name", 1).to_list(limit)
    
    # Enrich with components
    for formula in formulas:
        components = await assembly_components.find(
            {"formula_id": formula["id"], "tenant_id": tenant_id},
            {"_id": 0}
        ).sort("sequence_no", 1).to_list(100)
        formula["components"] = components
        formula["component_count"] = len(components)
        formula["source"] = "v2"
    
    # Include legacy formulas from old collection if requested
    if include_legacy:
        legacy_query = {}
        if status != "ALL":
            legacy_query["is_active"] = (status == "ACTIVE")
        if search:
            legacy_query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"result_product_name": {"$regex": search, "$options": "i"}}
            ]
        
        legacy_formulas = await assemblies_legacy.find(legacy_query, {"_id": 0}).to_list(100)
        
        # Convert legacy format to v2 format
        for lf in legacy_formulas:
            converted = {
                "id": lf.get("id"),
                "formula_name": lf.get("name"),
                "product_result_id": lf.get("result_product_id"),
                "result_product_name": lf.get("result_product_name"),
                "result_product_code": lf.get("result_product_code"),
                "result_quantity": lf.get("result_quantity", 1),
                "uom": "pcs",
                "status": "ACTIVE" if lf.get("is_active", True) else "INACTIVE",
                "components": lf.get("components", []),
                "component_count": len(lf.get("components", [])),
                "notes": lf.get("notes"),
                "created_at": lf.get("created_at"),
                "created_by_name": lf.get("created_by"),
                "source": "legacy"
            }
            formulas.append(converted)
        
        total += len(legacy_formulas)
    
    return {
        "formulas": formulas,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/formulas/v2/{formula_id}")
async def get_formula_v2(formula_id: str, user: dict = Depends(get_current_user)):
    """Get detail formula dengan komponen lengkap"""
    tenant_id = user.get("tenant_id", "ocb_titan")
    
    formula = await assembly_formulas.find_one(
        {"id": formula_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not formula:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    # Get components
    components = await assembly_components.find(
        {"formula_id": formula_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("sequence_no", 1).to_list(100)
    
    formula["components"] = components
    
    return formula


@router.post("/formulas/v2")
async def create_formula_v2(
    data: FormulaCreateRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Buat formula perakitan baru
    
    RULES:
    - Minimal 1 komponen (direkomendasikan 2 untuk test)
    - Produk hasil harus item valid dari master
    - Semua komponen harus item valid dari master
    - result_quantity > 0
    """
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Tidak diizinkan membuat formula")
    
    tenant_id = user.get("tenant_id", "ocb_titan")
    user_id = user.get("user_id", "")
    user_name = user.get("name", "")
    
    # Validate result product exists
    result_product = await products_collection.find_one(
        {"id": data.product_result_id},
        {"_id": 0}
    )
    if not result_product:
        raise HTTPException(status_code=404, detail="Produk hasil tidak ditemukan di master data")
    
    # Validate all components exist
    for i, comp in enumerate(data.components):
        product = await products_collection.find_one({"id": comp.item_id}, {"_id": 0})
        if not product:
            raise HTTPException(
                status_code=404, 
                detail=f"Komponen ke-{i+1} dengan ID {comp.item_id} tidak ditemukan di master data"
            )
        if comp.item_id == data.product_result_id:
            raise HTTPException(
                status_code=400,
                detail="Komponen tidak boleh sama dengan produk hasil"
            )
    
    # Create formula
    formula_id = str(uuid.uuid4())
    formula_doc = {
        "id": formula_id,
        "formula_name": data.formula_name,
        "product_result_id": data.product_result_id,
        "result_product_name": result_product.get("name"),
        "result_product_code": result_product.get("code"),
        "result_quantity": data.result_quantity,
        "uom": data.uom,
        "warehouse_id": data.warehouse_id,
        "notes": data.notes,
        "status": "ACTIVE",
        "tenant_id": tenant_id,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await assembly_formulas.insert_one(formula_doc)
    
    # Create components
    for i, comp in enumerate(data.components):
        product = await products_collection.find_one({"id": comp.item_id}, {"_id": 0})
        comp_doc = {
            "id": str(uuid.uuid4()),
            "formula_id": formula_id,
            "item_id": comp.item_id,
            "item_name": product.get("name") if product else "",
            "item_code": product.get("code") if product else "",
            "quantity_required": comp.quantity_required,
            "uom": comp.uom,
            "sequence_no": comp.sequence_no or (i + 1),
            "waste_factor": comp.waste_factor or 0,
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await assembly_components.insert_one(comp_doc)
    
    # Log action
    await log_assembly_action(
        formula_id, "CREATE_FORMULA", user_id, user_name,
        new_value={"formula_name": data.formula_name, "components": len(data.components)},
        tenant_id=tenant_id
    )
    
    return {
        "id": formula_id,
        "message": f"Formula '{data.formula_name}' berhasil dibuat dengan {len(data.components)} komponen",
        "formula_name": data.formula_name,
        "component_count": len(data.components)
    }


@router.put("/formulas/v2/{formula_id}")
async def update_formula_v2(
    formula_id: str,
    data: FormulaUpdateRequest,
    user: dict = Depends(get_current_user)
):
    """Update formula perakitan"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Tidak diizinkan mengubah formula")
    
    tenant_id = user.get("tenant_id", "ocb_titan")
    user_id = user.get("user_id", "")
    user_name = user.get("name", "")
    
    # Get existing formula
    formula = await assembly_formulas.find_one(
        {"id": formula_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not formula:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    old_value = {
        "formula_name": formula.get("formula_name"),
        "status": formula.get("status")
    }
    
    update_data = {}
    
    if data.formula_name:
        update_data["formula_name"] = data.formula_name
    if data.product_result_id:
        result_product = await products_collection.find_one({"id": data.product_result_id}, {"_id": 0})
        if not result_product:
            raise HTTPException(status_code=404, detail="Produk hasil tidak ditemukan")
        update_data["product_result_id"] = data.product_result_id
        update_data["result_product_name"] = result_product.get("name")
        update_data["result_product_code"] = result_product.get("code")
    if data.result_quantity:
        update_data["result_quantity"] = data.result_quantity
    if data.uom:
        update_data["uom"] = data.uom
    if data.notes is not None:
        update_data["notes"] = data.notes
    if data.status:
        update_data["status"] = data.status
    if data.warehouse_id is not None:
        update_data["warehouse_id"] = data.warehouse_id
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = user_id
    update_data["updated_by_name"] = user_name
    
    await assembly_formulas.update_one(
        {"id": formula_id},
        {"$set": update_data}
    )
    
    # Update components if provided
    if data.components:
        # Delete existing components
        await assembly_components.delete_many({"formula_id": formula_id})
        
        # Insert new components
        for i, comp in enumerate(data.components):
            product = await products_collection.find_one({"id": comp.item_id}, {"_id": 0})
            comp_doc = {
                "id": str(uuid.uuid4()),
                "formula_id": formula_id,
                "item_id": comp.item_id,
                "item_name": product.get("name") if product else "",
                "item_code": product.get("code") if product else "",
                "quantity_required": comp.quantity_required,
                "uom": comp.uom,
                "sequence_no": comp.sequence_no or (i + 1),
                "waste_factor": comp.waste_factor or 0,
                "tenant_id": tenant_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            await assembly_components.insert_one(comp_doc)
    
    # Log action
    await log_assembly_action(
        formula_id, "UPDATE_FORMULA", user_id, user_name,
        old_value=old_value,
        new_value=update_data,
        tenant_id=tenant_id
    )
    
    return {"message": "Formula berhasil diupdate"}


@router.patch("/formulas/v2/{formula_id}/deactivate")
async def deactivate_formula(formula_id: str, user: dict = Depends(get_current_user)):
    """Nonaktifkan formula - formula nonaktif tidak bisa digunakan untuk eksekusi baru"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Tidak diizinkan")
    
    tenant_id = user.get("tenant_id", "ocb_titan")
    
    result = await assembly_formulas.update_one(
        {"id": formula_id, "tenant_id": tenant_id},
        {"$set": {
            "status": "INACTIVE",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("user_id", ""),
            "updated_by_name": user.get("name", "")
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    # Log action
    await log_assembly_action(
        formula_id, "DEACTIVATE_FORMULA", user.get("user_id", ""), user.get("name", ""),
        old_value={"status": "ACTIVE"},
        new_value={"status": "INACTIVE"},
        tenant_id=tenant_id
    )
    
    return {"message": "Formula berhasil dinonaktifkan"}


@router.patch("/formulas/v2/{formula_id}/activate")
async def activate_formula(formula_id: str, user: dict = Depends(get_current_user)):
    """Aktifkan kembali formula"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Tidak diizinkan")
    
    tenant_id = user.get("tenant_id", "ocb_titan")
    
    result = await assembly_formulas.update_one(
        {"id": formula_id, "tenant_id": tenant_id},
        {"$set": {
            "status": "ACTIVE",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user.get("user_id", ""),
            "updated_by_name": user.get("name", "")
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    # Log action
    await log_assembly_action(
        formula_id, "ACTIVATE_FORMULA", user.get("user_id", ""), user.get("name", ""),
        old_value={"status": "INACTIVE"},
        new_value={"status": "ACTIVE"},
        tenant_id=tenant_id
    )
    
    return {"message": "Formula berhasil diaktifkan"}


@router.delete("/formulas/v2/{formula_id}/hard-delete")
async def hard_delete_formula(formula_id: str, user: dict = Depends(get_current_user)):
    """
    HARD DELETE formula voucher - menghapus permanen dari database
    
    VALIDASI:
    - Formula tidak boleh sudah digunakan dalam transaksi
    - Jika sudah digunakan, return error
    """
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Tidak diizinkan menghapus formula")
    
    tenant_id = user.get("tenant_id", "ocb_titan")
    user_id = user.get("user_id", "")
    user_name = user.get("name", "")
    
    # Check formula exists
    formula = await assembly_formulas.find_one(
        {"id": formula_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    
    if not formula:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    # VALIDASI: Check if formula is used in any transactions
    transaction_count = await assembly_transactions.count_documents({
        "formula_id": formula_id,
        "tenant_id": tenant_id
    })
    
    if transaction_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Voucher sudah digunakan pada {transaction_count} transaksi dan tidak dapat dihapus."
        )
    
    # Store formula info for logging before delete
    formula_name = formula.get("formula_name", "Unknown")
    component_count = formula.get("component_count", 0)
    
    # HARD DELETE: Delete components first
    await assembly_components.delete_many({
        "formula_id": formula_id,
        "tenant_id": tenant_id
    })
    
    # HARD DELETE: Delete formula
    await assembly_formulas.delete_one({
        "id": formula_id,
        "tenant_id": tenant_id
    })
    
    # Log action (store in audit_logs since formula is deleted)
    try:
        await audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "action": "HARD_DELETE_FORMULA",
            "entity_type": "assembly_formula",
            "entity_id": formula_id,
            "entity_name": formula_name,
            "user_id": user_id,
            "user_name": user_name,
            "old_value": {
                "formula_name": formula_name,
                "status": formula.get("status"),
                "component_count": component_count
            },
            "new_value": None,
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        print(f"Error saving audit log: {e}")
    
    return {
        "message": f"Formula voucher '{formula_name}' berhasil dihapus permanen",
        "deleted_formula_id": formula_id,
        "deleted_formula_name": formula_name
    }


# ============ ASSEMBLY EXECUTION ENDPOINTS ============

@router.post("/execute/v2")
async def execute_assembly_v2(
    data: AssemblyExecutionRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Eksekusi perakitan
    
    FLOW:
    1. Pilih formula
    2. Input jumlah produksi (planned_qty)
    3. Sistem validasi:
       - Formula aktif
       - Stok komponen cukup
       - Gudang valid
    4. Simpan sebagai DRAFT (default) atau langsung POST
    5. Jika POST:
       - Kurangi stok komponen (ASSEMBLY_CONSUME)
       - Tambah stok hasil (ASSEMBLY_PRODUCE)
       - Buat jurnal akuntansi
       - Update status → POSTED
       - Catat audit log
    """
    tenant_id = user.get("tenant_id", "ocb_titan")
    branch_id = user.get("branch_id", data.warehouse_id or "")
    user_id = user.get("user_id", "")
    user_name = user.get("name", "")
    
    # Get and validate formula
    formula = await assembly_formulas.find_one(
        {"id": data.formula_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not formula:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    if formula.get("status") != "ACTIVE":
        raise HTTPException(status_code=400, detail="Formula tidak aktif. Tidak bisa digunakan untuk eksekusi baru.")
    
    # Get components
    components = await assembly_components.find(
        {"formula_id": data.formula_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(100)
    
    if not components:
        raise HTTPException(status_code=400, detail="Formula tidak memiliki komponen")
    
    # Calculate required quantities
    insufficient_stock = []
    total_component_cost = 0
    component_details = []
    
    for comp in components:
        # Include waste factor in calculation
        waste_multiplier = 1 + (comp.get("waste_factor", 0) / 100)
        required_qty = comp["quantity_required"] * data.planned_qty * waste_multiplier
        
        # Get current stock from movements (SSOT)
        current_stock = await calculate_stock_from_movements(comp["item_id"], branch_id)
        
        # Get product cost
        product = await products_collection.find_one({"id": comp["item_id"]}, {"_id": 0})
        unit_cost = product.get("cost_price", 0) if product else 0
        
        component_details.append({
            "item_id": comp["item_id"],
            "item_name": comp.get("item_name"),
            "item_code": comp.get("item_code"),
            "quantity_required": required_qty,
            "current_stock": current_stock,
            "unit_cost": unit_cost,
            "total_cost": unit_cost * required_qty,
            "uom": comp.get("uom", "pcs")
        })
        
        total_component_cost += unit_cost * required_qty
        
        if current_stock < required_qty:
            insufficient_stock.append({
                "item_name": comp.get("item_name"),
                "required": required_qty,
                "available": current_stock,
                "shortage": required_qty - current_stock
            })
    
    # If not saving as draft, validate stock immediately
    if not data.save_as_draft and insufficient_stock:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Stok komponen tidak mencukupi untuk POST langsung",
                "items": insufficient_stock
            }
        )
    
    # Generate assembly number
    assembly_id = str(uuid.uuid4())
    assembly_number = f"ASM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # Calculate result quantity
    produced_qty = formula.get("result_quantity", 1) * data.planned_qty
    
    # Create transaction record
    transaction = {
        "id": assembly_id,
        "assembly_number": assembly_number,
        "formula_id": data.formula_id,
        "formula_name": formula.get("formula_name"),
        "product_result_id": formula.get("product_result_id"),
        "result_product_name": formula.get("result_product_name"),
        "result_product_code": formula.get("result_product_code"),
        "planned_qty": data.planned_qty,
        "produced_qty": produced_qty,
        "assembly_date": datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        "status": "DRAFT",
        "posting_status": None,
        "warehouse_id": branch_id,
        "reference_no": assembly_number,
        "notes": data.notes,
        "components_snapshot": component_details,
        "total_component_cost": total_component_cost,
        "journal_entry_id": None,
        "reversal_journal_entry_id": None,
        "source_ref_type": "assembly",
        "source_ref_id": None,
        "tenant_id": tenant_id,
        "created_by": user_id,
        "created_by_name": user_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "posted_by": None,
        "posted_at": None,
        "reversed_by": None,
        "reversed_at": None
    }
    
    await assembly_transactions.insert_one(transaction)
    
    # Log creation
    await log_assembly_action(
        assembly_id, "CREATE_ASSEMBLY", user_id, user_name,
        new_value={"status": "DRAFT", "planned_qty": data.planned_qty},
        tenant_id=tenant_id
    )
    
    response = {
        "id": assembly_id,
        "assembly_number": assembly_number,
        "status": "DRAFT",
        "message": f"Transaksi assembly '{formula.get('formula_name')}' berhasil dibuat sebagai DRAFT",
        "planned_qty": data.planned_qty,
        "produced_qty": produced_qty,
        "total_component_cost": total_component_cost,
        "components": component_details
    }
    
    # If not save as draft, post immediately
    if not data.save_as_draft:
        post_result = await post_assembly_transaction(
            AssemblyPostRequest(assembly_id=assembly_id),
            request,
            user
        )
        response["status"] = "POSTED"
        response["message"] = f"Transaksi assembly '{formula.get('formula_name')}' berhasil dieksekusi dan POSTED"
        response["journal_number"] = post_result.get("journal_number")
    elif insufficient_stock:
        response["warning"] = {
            "message": "Stok komponen tidak mencukupi untuk POST",
            "items": insufficient_stock
        }
    
    return response


@router.post("/execute/v2/post")
async def post_assembly_transaction(
    data: AssemblyPostRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    POST transaksi assembly DRAFT
    
    RULES:
    - Hanya DRAFT yang bisa di-POST
    - POST akan:
      1. Validasi ulang stok
      2. Tulis stock_movements (ASSEMBLY_CONSUME & ASSEMBLY_PRODUCE)
      3. Buat journal entry (Debit: Finished Goods, Credit: Raw Materials)
      4. Update status → POSTED
      5. Audit log
    """
    tenant_id = user.get("tenant_id", "ocb_titan")
    user_id = user.get("user_id", "")
    user_name = user.get("name", "")
    
    # Get transaction
    transaction = await assembly_transactions.find_one(
        {"id": data.assembly_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi assembly tidak ditemukan")
    
    if transaction.get("status") != "DRAFT":
        raise HTTPException(
            status_code=400, 
            detail=f"Hanya DRAFT yang bisa di-POST. Status saat ini: {transaction.get('status')}"
        )
    
    branch_id = transaction.get("warehouse_id", "")
    
    # Re-validate stock availability
    insufficient_stock = []
    for comp in transaction.get("components_snapshot", []):
        current_stock = await calculate_stock_from_movements(comp["item_id"], branch_id)
        if current_stock < comp["quantity_required"]:
            insufficient_stock.append({
                "item_name": comp.get("item_name"),
                "required": comp["quantity_required"],
                "available": current_stock
            })
    
    if insufficient_stock:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Stok komponen tidak mencukupi",
                "items": insufficient_stock
            }
        )
    
    # ============ WRITE STOCK MOVEMENTS (SSOT) ============
    movement_ids = []
    
    # 1. ASSEMBLY_CONSUME - Komponen keluar
    for comp in transaction.get("components_snapshot", []):
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": comp["item_id"],
            "product_name": comp.get("item_name"),
            "product_code": comp.get("item_code"),
            "movement_type": "ASSEMBLY_CONSUME",
            "quantity": -comp["quantity_required"],  # Negative = stock out
            "reference_id": data.assembly_id,
            "reference_type": "assembly",
            "reference_number": transaction.get("assembly_number"),
            "branch_id": branch_id,
            "notes": f"Komponen untuk assembly {transaction.get('formula_name')}",
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id,
            "created_by_name": user_name
        }
        await stock_movements_collection.insert_one(movement)
        movement_ids.append(movement["id"])
    
    # 2. ASSEMBLY_PRODUCE - Hasil masuk
    result_movement = {
        "id": str(uuid.uuid4()),
        "product_id": transaction.get("product_result_id"),
        "product_name": transaction.get("result_product_name"),
        "product_code": transaction.get("result_product_code"),
        "movement_type": "ASSEMBLY_PRODUCE",
        "quantity": transaction.get("produced_qty"),  # Positive = stock in
        "reference_id": data.assembly_id,
        "reference_type": "assembly",
        "reference_number": transaction.get("assembly_number"),
        "branch_id": branch_id,
        "notes": f"Hasil assembly {transaction.get('formula_name')}",
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
        "created_by_name": user_name
    }
    await stock_movements_collection.insert_one(result_movement)
    movement_ids.append(result_movement["id"])
    
    # ============ CREATE JOURNAL ENTRY (ACCOUNTING SSOT) ============
    total_cost = transaction.get("total_component_cost", 0)
    
    journal_entries = []
    
    # DEBIT: Persediaan Barang Jadi
    finished_account = await derive_account("inventory_finished", branch_id)
    journal_entries.append({
        "account_code": finished_account["code"],
        "account_name": f"{finished_account['name']} - {transaction.get('result_product_name')}",
        "description": f"Assembly: {transaction.get('formula_name')} ({transaction.get('produced_qty')} unit)",
        "debit": total_cost,
        "credit": 0
    })
    
    # CREDIT: Persediaan Bahan Baku (per komponen)
    raw_account = await derive_account("inventory_raw", branch_id)
    for comp in transaction.get("components_snapshot", []):
        journal_entries.append({
            "account_code": raw_account["code"],
            "account_name": f"{raw_account['name']} - {comp.get('item_name')}",
            "description": f"Komponen assembly: {comp.get('item_name')} ({comp.get('quantity_required')} {comp.get('uom')})",
            "debit": 0,
            "credit": comp.get("total_cost", 0)
        })
    
    # Create journal
    journal_number = None
    if total_cost > 0:
        journal_number = await create_journal_entry(
            reference_type="assembly",
            reference_id=data.assembly_id,
            reference_no=transaction.get("assembly_number"),
            description=f"Assembly: {transaction.get('formula_name')} - {transaction.get('produced_qty')} {transaction.get('result_product_name')}",
            entries=journal_entries,
            branch_id=branch_id,
            user_id=user_id,
            user_name=user_name,
            tenant_id=tenant_id
        )
    
    # ============ UPDATE TRANSACTION STATUS ============
    await assembly_transactions.update_one(
        {"id": data.assembly_id},
        {"$set": {
            "status": "POSTED",
            "posting_status": "success",
            "journal_entry_id": journal_number,
            "movement_ids": movement_ids,
            "posted_by": user_id,
            "posted_by_name": user_name,
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log action
    await log_assembly_action(
        data.assembly_id, "POST_ASSEMBLY", user_id, user_name,
        old_value={"status": "DRAFT"},
        new_value={"status": "POSTED", "journal_number": journal_number},
        tenant_id=tenant_id
    )
    
    return {
        "message": "Assembly berhasil di-POST",
        "assembly_id": data.assembly_id,
        "assembly_number": transaction.get("assembly_number"),
        "status": "POSTED",
        "journal_number": journal_number,
        "stock_movements_created": len(movement_ids)
    }


@router.post("/execute/v2/reverse")
async def reverse_assembly_transaction(
    data: AssemblyReversalRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    REVERSAL transaksi assembly POSTED
    
    RULES:
    - Hanya POSTED yang bisa di-reverse
    - TIDAK BOLEH edit/delete langsung untuk POSTED
    - Reversal akan:
      1. Buat reversal stock movements (kebalikan)
      2. Buat reversal journal entry
      3. Update status → REVERSED
      4. Audit log
    """
    tenant_id = user.get("tenant_id", "ocb_titan")
    user_id = user.get("user_id", "")
    user_name = user.get("name", "")
    
    # Get transaction
    transaction = await assembly_transactions.find_one(
        {"id": data.assembly_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi assembly tidak ditemukan")
    
    if transaction.get("status") != "POSTED":
        raise HTTPException(
            status_code=400,
            detail=f"Hanya POSTED yang bisa di-reverse. Status saat ini: {transaction.get('status')}"
        )
    
    branch_id = transaction.get("warehouse_id", "")
    reversal_number = f"REV-{transaction.get('assembly_number')}"
    
    # ============ CREATE REVERSAL STOCK MOVEMENTS ============
    reversal_movement_ids = []
    
    # 1. Reverse ASSEMBLY_CONSUME → Return components
    for comp in transaction.get("components_snapshot", []):
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": comp["item_id"],
            "product_name": comp.get("item_name"),
            "product_code": comp.get("item_code"),
            "movement_type": "ASSEMBLY_CONSUME_REVERSAL",
            "quantity": comp["quantity_required"],  # Positive = return stock
            "reference_id": data.assembly_id,
            "reference_type": "assembly_reversal",
            "reference_number": reversal_number,
            "branch_id": branch_id,
            "notes": f"REVERSAL - Komponen dikembalikan: {data.reason}",
            "tenant_id": tenant_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user_id,
            "created_by_name": user_name
        }
        await stock_movements_collection.insert_one(movement)
        reversal_movement_ids.append(movement["id"])
    
    # 2. Reverse ASSEMBLY_PRODUCE → Remove result product
    result_reversal = {
        "id": str(uuid.uuid4()),
        "product_id": transaction.get("product_result_id"),
        "product_name": transaction.get("result_product_name"),
        "product_code": transaction.get("result_product_code"),
        "movement_type": "ASSEMBLY_PRODUCE_REVERSAL",
        "quantity": -transaction.get("produced_qty"),  # Negative = remove stock
        "reference_id": data.assembly_id,
        "reference_type": "assembly_reversal",
        "reference_number": reversal_number,
        "branch_id": branch_id,
        "notes": f"REVERSAL - Hasil assembly dibatalkan: {data.reason}",
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
        "created_by_name": user_name
    }
    await stock_movements_collection.insert_one(result_reversal)
    reversal_movement_ids.append(result_reversal["id"])
    
    # ============ CREATE REVERSAL JOURNAL ENTRY ============
    total_cost = transaction.get("total_component_cost", 0)
    
    reversal_entries = []
    
    # Kebalikan dari journal asli
    # DEBIT: Persediaan Bahan Baku (mengembalikan komponen)
    raw_account = await derive_account("inventory_raw", branch_id)
    for comp in transaction.get("components_snapshot", []):
        reversal_entries.append({
            "account_code": raw_account["code"],
            "account_name": f"{raw_account['name']} - {comp.get('item_name')}",
            "description": f"REVERSAL Komponen: {comp.get('item_name')}",
            "debit": comp.get("total_cost", 0),
            "credit": 0
        })
    
    # CREDIT: Persediaan Barang Jadi (mengeluarkan hasil)
    finished_account = await derive_account("inventory_finished", branch_id)
    reversal_entries.append({
        "account_code": finished_account["code"],
        "account_name": f"{finished_account['name']} - {transaction.get('result_product_name')}",
        "description": f"REVERSAL Assembly: {transaction.get('formula_name')}",
        "debit": 0,
        "credit": total_cost
    })
    
    # Create reversal journal
    reversal_journal_number = None
    if total_cost > 0:
        reversal_journal_number = await create_journal_entry(
            reference_type="assembly_reversal",
            reference_id=data.assembly_id,
            reference_no=reversal_number,
            description=f"REVERSAL Assembly: {transaction.get('formula_name')} - {data.reason}",
            entries=reversal_entries,
            branch_id=branch_id,
            user_id=user_id,
            user_name=user_name,
            tenant_id=tenant_id
        )
    
    # ============ UPDATE TRANSACTION STATUS ============
    await assembly_transactions.update_one(
        {"id": data.assembly_id},
        {"$set": {
            "status": "REVERSED",
            "reversal_journal_entry_id": reversal_journal_number,
            "reversal_reason": data.reason,
            "reversal_notes": data.notes,
            "reversal_movement_ids": reversal_movement_ids,
            "reversed_by": user_id,
            "reversed_by_name": user_name,
            "reversed_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log action
    await log_assembly_action(
        data.assembly_id, "REVERSE_ASSEMBLY", user_id, user_name,
        old_value={"status": "POSTED"},
        new_value={"status": "REVERSED", "reason": data.reason},
        tenant_id=tenant_id
    )
    
    return {
        "message": "Assembly berhasil di-reverse",
        "assembly_id": data.assembly_id,
        "assembly_number": transaction.get("assembly_number"),
        "reversal_number": reversal_number,
        "status": "REVERSED",
        "reversal_journal_number": reversal_journal_number,
        "reason": data.reason
    }


# ============ DRAFT EDIT/DELETE ENDPOINTS ============

@router.put("/transactions/v2/{assembly_id}")
async def edit_draft_assembly(
    assembly_id: str,
    data: AssemblyExecutionRequest,
    user: dict = Depends(get_current_user)
):
    """
    Edit transaksi assembly DRAFT
    
    RULES:
    - Hanya DRAFT yang bisa di-edit
    - POSTED/REVERSED tidak bisa di-edit
    """
    tenant_id = user.get("tenant_id", "ocb_titan")
    
    transaction = await assembly_transactions.find_one(
        {"id": assembly_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi assembly tidak ditemukan")
    
    if transaction.get("status") != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail=f"Hanya DRAFT yang bisa di-edit. Status saat ini: {transaction.get('status')}. Gunakan REVERSAL untuk koreksi POSTED."
        )
    
    # Update the transaction
    update_data = {
        "planned_qty": data.planned_qty,
        "notes": data.notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user.get("user_id", ""),
        "updated_by_name": user.get("name", "")
    }
    
    # Recalculate if formula changed
    if data.formula_id != transaction.get("formula_id"):
        formula = await assembly_formulas.find_one({"id": data.formula_id}, {"_id": 0})
        if not formula:
            raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
        if formula.get("status") != "ACTIVE":
            raise HTTPException(status_code=400, detail="Formula tidak aktif")
        
        components = await assembly_components.find(
            {"formula_id": data.formula_id, "tenant_id": tenant_id},
            {"_id": 0}
        ).to_list(100)
        
        # Recalculate costs
        component_details = []
        total_cost = 0
        for comp in components:
            required_qty = comp["quantity_required"] * data.planned_qty
            product = await products_collection.find_one({"id": comp["item_id"]}, {"_id": 0})
            unit_cost = product.get("cost_price", 0) if product else 0
            comp_cost = unit_cost * required_qty
            total_cost += comp_cost
            
            component_details.append({
                "item_id": comp["item_id"],
                "item_name": comp.get("item_name"),
                "item_code": comp.get("item_code"),
                "quantity_required": required_qty,
                "unit_cost": unit_cost,
                "total_cost": comp_cost,
                "uom": comp.get("uom", "pcs")
            })
        
        update_data["formula_id"] = data.formula_id
        update_data["formula_name"] = formula.get("formula_name")
        update_data["product_result_id"] = formula.get("product_result_id")
        update_data["result_product_name"] = formula.get("result_product_name")
        update_data["result_product_code"] = formula.get("result_product_code")
        update_data["produced_qty"] = formula.get("result_quantity", 1) * data.planned_qty
        update_data["components_snapshot"] = component_details
        update_data["total_component_cost"] = total_cost
    
    await assembly_transactions.update_one(
        {"id": assembly_id},
        {"$set": update_data}
    )
    
    # Log action
    await log_assembly_action(
        assembly_id, "EDIT_DRAFT", user.get("user_id", ""), user.get("name", ""),
        old_value={"planned_qty": transaction.get("planned_qty")},
        new_value={"planned_qty": data.planned_qty},
        tenant_id=tenant_id
    )
    
    return {"message": "Draft assembly berhasil diupdate"}


@router.delete("/transactions/v2/{assembly_id}")
async def delete_draft_assembly(
    assembly_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Delete/Cancel transaksi assembly DRAFT
    
    RULES:
    - Hanya DRAFT yang bisa di-delete
    - POSTED harus di-reverse, bukan delete
    - Ini adalah SOFT DELETE (status → CANCELLED)
    """
    tenant_id = user.get("tenant_id", "ocb_titan")
    
    transaction = await assembly_transactions.find_one(
        {"id": assembly_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi assembly tidak ditemukan")
    
    if transaction.get("status") != "DRAFT":
        raise HTTPException(
            status_code=400,
            detail=f"Hanya DRAFT yang bisa di-delete. Status saat ini: {transaction.get('status')}. Gunakan REVERSAL untuk membatalkan POSTED."
        )
    
    # Soft delete - change status to CANCELLED
    await assembly_transactions.update_one(
        {"id": assembly_id},
        {"$set": {
            "status": "CANCELLED",
            "cancelled_by": user.get("user_id", ""),
            "cancelled_by_name": user.get("name", ""),
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log action
    await log_assembly_action(
        assembly_id, "DELETE_DRAFT", user.get("user_id", ""), user.get("name", ""),
        old_value={"status": "DRAFT"},
        new_value={"status": "CANCELLED"},
        tenant_id=tenant_id
    )
    
    return {"message": "Draft assembly berhasil dibatalkan"}


# ============ ASSEMBLY HISTORY ENDPOINTS ============

@router.get("/history/v2")
async def list_assembly_history(
    status: str = "",  # DRAFT, POSTED, REVERSED, CANCELLED, ALL
    type: str = "",    # assembly, disassembly
    date_from: str = "",
    date_to: str = "",
    formula_id: str = "",
    search: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """
    List riwayat transaksi assembly
    
    Filter:
    - status: DRAFT / POSTED / REVERSED / CANCELLED / ALL
    - type: assembly / disassembly
    - date_from, date_to: Filter tanggal
    - formula_id: Filter by formula
    - search: Cari berdasarkan nomor assembly atau nama formula
    """
    tenant_id = user.get("tenant_id", "ocb_titan")
    
    query = {"tenant_id": tenant_id}
    
    if status and status != "ALL":
        query["status"] = status
    if type:
        query["source_ref_type"] = type
    if formula_id:
        query["formula_id"] = formula_id
    if date_from:
        query["assembly_date"] = {"$gte": date_from}
    if date_to:
        if "assembly_date" in query:
            query["assembly_date"]["$lte"] = date_to
        else:
            query["assembly_date"] = {"$lte": date_to}
    if search:
        query["$or"] = [
            {"assembly_number": {"$regex": search, "$options": "i"}},
            {"formula_name": {"$regex": search, "$options": "i"}}
        ]
    
    total = await assembly_transactions.count_documents(query)
    transactions = await assembly_transactions.find(query, {"_id": 0}).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
    
    return {
        "transactions": transactions,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/history/v2/{assembly_id}")
async def get_assembly_detail(assembly_id: str, user: dict = Depends(get_current_user)):
    """Get detail transaksi assembly dengan audit log"""
    tenant_id = user.get("tenant_id", "ocb_titan")
    
    transaction = await assembly_transactions.find_one(
        {"id": assembly_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    
    # Get audit logs for this transaction
    logs = await assembly_logs.find(
        {"assembly_id": assembly_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(100)
    
    transaction["audit_logs"] = logs
    
    # Get stock movements
    movements = await stock_movements_collection.find(
        {"reference_id": assembly_id},
        {"_id": 0}
    ).to_list(100)
    
    transaction["stock_movements"] = movements
    
    return transaction


@router.get("/logs/v2/{assembly_id}")
async def get_assembly_logs(assembly_id: str, user: dict = Depends(get_current_user)):
    """Get audit logs untuk transaksi assembly"""
    tenant_id = user.get("tenant_id", "ocb_titan")
    
    logs = await assembly_logs.find(
        {"assembly_id": assembly_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(100)
    
    return {"logs": logs, "total": len(logs)}


# ============ VALIDATION ENDPOINTS ============

@router.get("/validate/stock/{formula_id}")
async def validate_formula_stock(
    formula_id: str,
    planned_qty: int = 1,
    warehouse_id: str = "",
    user: dict = Depends(get_current_user)
):
    """
    Validasi ketersediaan stok komponen untuk formula
    
    Returns:
    - can_execute: true/false
    - components: detail setiap komponen dengan stok tersedia
    - insufficient_items: daftar komponen yang stoknya kurang
    """
    tenant_id = user.get("tenant_id", "ocb_titan")
    branch_id = warehouse_id or user.get("branch_id", "")
    
    formula = await assembly_formulas.find_one(
        {"id": formula_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not formula:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    components = await assembly_components.find(
        {"formula_id": formula_id, "tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(100)
    
    validation_result = []
    insufficient = []
    
    for comp in components:
        required_qty = comp["quantity_required"] * planned_qty
        current_stock = await calculate_stock_from_movements(comp["item_id"], branch_id)
        
        is_sufficient = current_stock >= required_qty
        
        item_validation = {
            "item_id": comp["item_id"],
            "item_name": comp.get("item_name"),
            "quantity_required": required_qty,
            "current_stock": current_stock,
            "is_sufficient": is_sufficient,
            "shortage": max(0, required_qty - current_stock)
        }
        validation_result.append(item_validation)
        
        if not is_sufficient:
            insufficient.append(item_validation)
    
    can_execute = len(insufficient) == 0
    
    return {
        "can_execute": can_execute,
        "formula_id": formula_id,
        "formula_name": formula.get("formula_name"),
        "planned_qty": planned_qty,
        "result_qty": formula.get("result_quantity", 1) * planned_qty,
        "components": validation_result,
        "insufficient_items": insufficient
    }



# ============ STOCK ADJUSTMENT FOR TESTING ============
# Endpoint untuk menambah stok produk via stock_movements (SSOT)

class StockAdjustmentRequest(BaseModel):
    """Request untuk stock adjustment"""
    product_id: str
    quantity: float = Field(..., gt=0)
    adjustment_type: str = "adjustment_in"  # adjustment_in, opening_balance
    notes: Optional[str] = None
    warehouse_id: Optional[str] = None


@router.post("/stock/adjustment")
async def create_stock_adjustment(
    data: StockAdjustmentRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Stock Adjustment - Menambah stok produk via stock_movements (SSOT)
    
    Digunakan untuk:
    - Opening balance
    - Stock adjustment (koreksi stok)
    - Testing purposes
    
    RULE: Semua perubahan stok HARUS melalui stock_movements
    """
    if user.get("role") not in ["owner", "admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Tidak diizinkan")
    
    tenant_id = user.get("tenant_id", "ocb_titan")
    user_id = user.get("user_id", "")
    user_name = user.get("name", "")
    branch_id = data.warehouse_id or user.get("branch_id", "")
    
    # Validate product exists
    product = await products_collection.find_one(
        {"id": data.product_id},
        {"_id": 0}
    )
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    # Generate adjustment number
    adj_number = f"ADJ-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # Create stock movement (SSOT)
    movement = {
        "id": str(uuid.uuid4()),
        "product_id": data.product_id,
        "product_name": product.get("name"),
        "product_code": product.get("code"),
        "movement_type": data.adjustment_type.upper(),
        "quantity": data.quantity,  # Positive = add stock
        "reference_id": adj_number,
        "reference_type": "stock_adjustment",
        "reference_number": adj_number,
        "branch_id": branch_id,
        "notes": data.notes or f"Stock Adjustment: {product.get('name')}",
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
        "created_by_name": user_name
    }
    await stock_movements_collection.insert_one(movement)
    
    # Get new stock level
    new_stock = await calculate_stock_from_movements(data.product_id, branch_id)
    
    # Log activity
    await log_assembly_action(
        adj_number, "STOCK_ADJUSTMENT", user_id, user_name,
        new_value={"product": product.get("name"), "qty_added": data.quantity, "new_stock": new_stock},
        tenant_id=tenant_id
    )
    
    return {
        "message": f"Stock adjustment berhasil",
        "adjustment_number": adj_number,
        "product_id": data.product_id,
        "product_name": product.get("name"),
        "quantity_added": data.quantity,
        "new_stock_level": new_stock,
        "movement_id": movement["id"]
    }


@router.get("/stock/{product_id}")
async def get_product_stock(
    product_id: str,
    warehouse_id: str = "",
    user: dict = Depends(get_current_user)
):
    """Get current stock level for a product (calculated from stock_movements SSOT)"""
    branch_id = warehouse_id or user.get("branch_id", "")
    
    product = await products_collection.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    current_stock = await calculate_stock_from_movements(product_id, branch_id)
    
    # Get recent movements
    movements = await stock_movements_collection.find(
        {"product_id": product_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "product_id": product_id,
        "product_name": product.get("name"),
        "product_code": product.get("code"),
        "current_stock": current_stock,
        "recent_movements": movements
    }
