# OCB AI TITAN - Product Assembly (Rakitan Produk) Routes
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from database import db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/assembly", tags=["Product Assembly"])

assemblies_collection = db["assemblies"]
assembly_transactions_collection = db["assembly_transactions"]
products_collection = db["products"]
stock_movements_collection = db["stock_movements"]

class AssemblyComponent(BaseModel):
    product_id: str
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    quantity: float
    unit: str = "pcs"

class AssemblyFormula(BaseModel):
    name: str
    result_product_id: str
    result_quantity: float = 1
    components: List[AssemblyComponent]
    notes: Optional[str] = None
    is_active: bool = True

class AssemblyTransaction(BaseModel):
    formula_id: str
    quantity: int = 1  # Number of assembly cycles
    notes: Optional[str] = None

@router.get("/formulas")
async def list_formulas(
    search: str = "",
    is_active: bool = True,
    user: dict = Depends(get_current_user)
):
    """List all assembly formulas"""
    query = {"is_active": is_active}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"result_product_name": {"$regex": search, "$options": "i"}}
        ]
    
    formulas = await assemblies_collection.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return {"formulas": formulas, "total": len(formulas)}

@router.get("/formulas/{formula_id}")
async def get_formula(formula_id: str, user: dict = Depends(get_current_user)):
    """Get assembly formula details"""
    formula = await assemblies_collection.find_one({"id": formula_id}, {"_id": 0})
    if not formula:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    return formula

@router.post("/formulas")
async def create_formula(data: AssemblyFormula, user: dict = Depends(get_current_user)):
    """Create new assembly formula"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Tidak diizinkan")
    
    # Get result product info
    result_product = await products_collection.find_one({"id": data.result_product_id}, {"_id": 0})
    if not result_product:
        raise HTTPException(status_code=404, detail="Produk hasil tidak ditemukan")
    
    formula_data = data.dict()
    formula_data["id"] = str(uuid.uuid4())
    formula_data["result_product_name"] = result_product.get("name")
    formula_data["result_product_code"] = result_product.get("code")
    
    # Populate component product info
    for comp in formula_data["components"]:
        product = await products_collection.find_one({"id": comp["product_id"]}, {"_id": 0})
        if product:
            comp["product_name"] = product.get("name")
            comp["product_code"] = product.get("code")
    
    formula_data["created_at"] = datetime.now(timezone.utc).isoformat()
    formula_data["created_by"] = user.get("name")
    
    await assemblies_collection.insert_one(formula_data)
    
    return {"id": formula_data["id"], "message": "Formula rakitan berhasil dibuat"}

@router.put("/formulas/{formula_id}")
async def update_formula(formula_id: str, data: AssemblyFormula, user: dict = Depends(get_current_user)):
    """Update assembly formula"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Tidak diizinkan")
    
    update_data = data.dict()
    
    # Update product info
    result_product = await products_collection.find_one({"id": data.result_product_id}, {"_id": 0})
    if result_product:
        update_data["result_product_name"] = result_product.get("name")
        update_data["result_product_code"] = result_product.get("code")
    
    for comp in update_data["components"]:
        product = await products_collection.find_one({"id": comp["product_id"]}, {"_id": 0})
        if product:
            comp["product_name"] = product.get("name")
            comp["product_code"] = product.get("code")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = user.get("name")
    
    result = await assemblies_collection.update_one(
        {"id": formula_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    return {"message": "Formula rakitan berhasil diupdate"}

@router.delete("/formulas/{formula_id}")
async def delete_formula(formula_id: str, user: dict = Depends(get_current_user)):
    """Delete assembly formula"""
    if user.get("role") not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Tidak diizinkan")
    
    result = await assemblies_collection.delete_one({"id": formula_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    return {"message": "Formula rakitan berhasil dihapus"}

@router.post("/assemble")
async def process_assembly(data: AssemblyTransaction, user: dict = Depends(get_current_user)):
    """Process assembly - consume components and produce result"""
    branch_id = user.get("branch_id")
    
    # Get formula
    formula = await assemblies_collection.find_one({"id": data.formula_id}, {"_id": 0})
    if not formula:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    if not formula.get("is_active"):
        raise HTTPException(status_code=400, detail="Formula tidak aktif")
    
    # Check component stock availability
    insufficient_stock = []
    for comp in formula.get("components", []):
        required_qty = comp["quantity"] * data.quantity
        product = await products_collection.find_one(
            {"id": comp["product_id"]},
            {"_id": 0, "stock": 1, "name": 1}
        )
        if product:
            current_stock = product.get("stock", 0)
            if current_stock < required_qty:
                insufficient_stock.append({
                    "product": comp["product_name"],
                    "required": required_qty,
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
    
    # Process assembly
    transaction_id = str(uuid.uuid4())
    assembly_number = f"ASM{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # Deduct component stock
    component_movements = []
    total_cost = 0
    for comp in formula.get("components", []):
        qty_to_deduct = comp["quantity"] * data.quantity
        
        # Get product cost
        product = await products_collection.find_one({"id": comp["product_id"]}, {"_id": 0})
        unit_cost = product.get("cost_price", 0) if product else 0
        total_cost += unit_cost * qty_to_deduct
        
        # Deduct stock
        await products_collection.update_one(
            {"id": comp["product_id"]},
            {"$inc": {"stock": -qty_to_deduct}}
        )
        
        # Record movement
        movement = {
            "id": str(uuid.uuid4()),
            "product_id": comp["product_id"],
            "product_name": comp["product_name"],
            "product_code": comp.get("product_code"),
            "type": "assembly_out",
            "quantity": -qty_to_deduct,
            "reference_id": transaction_id,
            "reference_type": "assembly",
            "reference_number": assembly_number,
            "branch_id": branch_id,
            "notes": f"Komponen untuk rakitan {formula['name']}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("name")
        }
        component_movements.append(movement)
        await stock_movements_collection.insert_one(movement)
    
    # Add result product stock
    result_qty = formula.get("result_quantity", 1) * data.quantity
    await products_collection.update_one(
        {"id": formula["result_product_id"]},
        {"$inc": {"stock": result_qty}}
    )
    
    # Record result movement
    result_movement = {
        "id": str(uuid.uuid4()),
        "product_id": formula["result_product_id"],
        "product_name": formula.get("result_product_name"),
        "product_code": formula.get("result_product_code"),
        "type": "assembly_in",
        "quantity": result_qty,
        "reference_id": transaction_id,
        "reference_type": "assembly",
        "reference_number": assembly_number,
        "branch_id": branch_id,
        "notes": f"Hasil rakitan {formula['name']}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("name")
    }
    await stock_movements_collection.insert_one(result_movement)
    
    # Record assembly transaction
    transaction = {
        "id": transaction_id,
        "assembly_number": assembly_number,
        "formula_id": data.formula_id,
        "formula_name": formula.get("name"),
        "quantity": data.quantity,
        "result_product_id": formula["result_product_id"],
        "result_product_name": formula.get("result_product_name"),
        "result_quantity": result_qty,
        "total_cost": total_cost,
        "components_used": formula.get("components"),
        "type": "assembly",
        "notes": data.notes,
        "branch_id": branch_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("name")
    }
    await assembly_transactions_collection.insert_one(transaction)
    
    return {
        "id": transaction_id,
        "assembly_number": assembly_number,
        "message": f"Rakitan berhasil. {result_qty} {formula.get('result_product_name')} ditambahkan ke stok",
        "result_quantity": result_qty,
        "total_cost": total_cost
    }

@router.post("/disassemble")
async def process_disassembly(data: AssemblyTransaction, user: dict = Depends(get_current_user)):
    """Process disassembly - break down product into components"""
    branch_id = user.get("branch_id")
    
    # Get formula
    formula = await assemblies_collection.find_one({"id": data.formula_id}, {"_id": 0})
    if not formula:
        raise HTTPException(status_code=404, detail="Formula tidak ditemukan")
    
    # Check result product stock
    result_qty_needed = formula.get("result_quantity", 1) * data.quantity
    product = await products_collection.find_one(
        {"id": formula["result_product_id"]},
        {"_id": 0, "stock": 1}
    )
    
    if not product or product.get("stock", 0) < result_qty_needed:
        raise HTTPException(
            status_code=400,
            detail=f"Stok {formula.get('result_product_name')} tidak mencukupi"
        )
    
    # Process disassembly
    transaction_id = str(uuid.uuid4())
    disassembly_number = f"DSM{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # Deduct result product stock
    await products_collection.update_one(
        {"id": formula["result_product_id"]},
        {"$inc": {"stock": -result_qty_needed}}
    )
    
    # Record result product movement
    await stock_movements_collection.insert_one({
        "id": str(uuid.uuid4()),
        "product_id": formula["result_product_id"],
        "product_name": formula.get("result_product_name"),
        "product_code": formula.get("result_product_code"),
        "type": "disassembly_out",
        "quantity": -result_qty_needed,
        "reference_id": transaction_id,
        "reference_type": "disassembly",
        "reference_number": disassembly_number,
        "branch_id": branch_id,
        "notes": f"Pembongkaran {formula['name']}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("name")
    })
    
    # Add component stocks
    for comp in formula.get("components", []):
        qty_to_add = comp["quantity"] * data.quantity
        
        await products_collection.update_one(
            {"id": comp["product_id"]},
            {"$inc": {"stock": qty_to_add}}
        )
        
        await stock_movements_collection.insert_one({
            "id": str(uuid.uuid4()),
            "product_id": comp["product_id"],
            "product_name": comp["product_name"],
            "product_code": comp.get("product_code"),
            "type": "disassembly_in",
            "quantity": qty_to_add,
            "reference_id": transaction_id,
            "reference_type": "disassembly",
            "reference_number": disassembly_number,
            "branch_id": branch_id,
            "notes": f"Komponen dari pembongkaran {formula['name']}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": user.get("name")
        })
    
    # Record disassembly transaction
    transaction = {
        "id": transaction_id,
        "assembly_number": disassembly_number,
        "formula_id": data.formula_id,
        "formula_name": formula.get("name"),
        "quantity": data.quantity,
        "result_product_id": formula["result_product_id"],
        "result_product_name": formula.get("result_product_name"),
        "result_quantity": result_qty_needed,
        "components_produced": formula.get("components"),
        "type": "disassembly",
        "notes": data.notes,
        "branch_id": branch_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("name")
    }
    await assembly_transactions_collection.insert_one(transaction)
    
    return {
        "id": transaction_id,
        "assembly_number": disassembly_number,
        "message": "Pembongkaran berhasil. Komponen ditambahkan ke stok"
    }

@router.get("/transactions")
async def list_assembly_transactions(
    type: str = "",  # assembly, disassembly
    date_from: str = "",
    date_to: str = "",
    branch_id: str = "",
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """List assembly transactions"""
    query = {}
    if type:
        query["type"] = type
    if branch_id:
        query["branch_id"] = branch_id
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["created_at"] = {"$lte": date_to + "T23:59:59"}
    
    total = await assembly_transactions_collection.count_documents(query)
    transactions = await assembly_transactions_collection.find(query, {"_id": 0}).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
    
    return {
        "transactions": transactions,
        "total": total,
        "skip": skip,
        "limit": limit
    }
