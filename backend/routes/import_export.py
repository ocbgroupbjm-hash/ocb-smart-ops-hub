# OCB TITAN ERP - Import/Export Engine
# Handles Excel import/export for master data and transactions
# SECURITY: Tenant-aware, validated, audited

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database import get_db
from utils.auth import get_current_user
from routes.rbac_middleware import require_permission, log_security_event
from datetime import datetime, timezone
import pandas as pd
import io
import uuid

router = APIRouter(prefix="/api", tags=["Import/Export"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# ==================== VALIDATION HELPERS ====================

def validate_file_size(file: UploadFile):
    """Validate file size"""
    # Check content length header if available
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File terlalu besar. Maksimal {MAX_FILE_SIZE // (1024*1024)}MB")

def validate_required_columns(df: pd.DataFrame, required: List[str], entity_name: str):
    """Validate required columns exist"""
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400, 
            detail=f"Kolom wajib tidak ditemukan untuk {entity_name}: {', '.join(missing)}"
        )

def detect_duplicates(df: pd.DataFrame, key_column: str) -> List[str]:
    """Detect duplicate values in key column"""
    duplicates = df[df.duplicated(subset=[key_column], keep=False)][key_column].unique().tolist()
    return duplicates

async def check_existing_codes(db, collection: str, codes: List[str]) -> List[str]:
    """Check which codes already exist in database"""
    existing = await db[collection].find(
        {"code": {"$in": codes}},
        {"code": 1, "_id": 0}
    ).to_list(len(codes))
    return [e["code"] for e in existing]


# ==================== EXPORT ENDPOINTS ====================

@router.get("/export/products")
async def export_products(
    request: Request,
    user: dict = Depends(require_permission("master_product", "view"))
):
    """Export products to Excel"""
    db = get_db()
    
    products = await db["products"].find(
        {},
        {"_id": 0, "id": 1, "code": 1, "barcode": 1, "name": 1, "category_id": 1, 
         "unit": 1, "buy_price": 1, "sell_price": 1, "min_stock": 1, "is_active": 1}
    ).sort("code", 1).to_list(10000)
    
    if not products:
        raise HTTPException(status_code=404, detail="Tidak ada produk untuk diexport")
    
    df = pd.DataFrame(products)
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Products', index=False)
    output.seek(0)
    
    # Log export
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "export", "products",
        f"Export {len(products)} produk ke Excel",
        request.client.host if request.client else ""
    )
    
    filename = f"products_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/customers")
async def export_customers(
    request: Request,
    user: dict = Depends(require_permission("master_customer", "view"))
):
    """Export customers to Excel"""
    db = get_db()
    
    customers = await db["customers"].find(
        {},
        {"_id": 0, "id": 1, "code": 1, "name": 1, "phone": 1, "email": 1, 
         "address": 1, "city": 1, "segment": 1, "credit_limit": 1, "is_active": 1}
    ).sort("code", 1).to_list(10000)
    
    if not customers:
        raise HTTPException(status_code=404, detail="Tidak ada customer untuk diexport")
    
    df = pd.DataFrame(customers)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Customers', index=False)
    output.seek(0)
    
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "export", "customers",
        f"Export {len(customers)} customer ke Excel",
        request.client.host if request.client else ""
    )
    
    filename = f"customers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/suppliers")
async def export_suppliers(
    request: Request,
    user: dict = Depends(require_permission("master_supplier", "view"))
):
    """Export suppliers to Excel"""
    db = get_db()
    
    suppliers = await db["suppliers"].find(
        {},
        {"_id": 0, "id": 1, "code": 1, "name": 1, "contact_person": 1, "phone": 1, 
         "email": 1, "address": 1, "city": 1, "payment_terms": 1, "is_active": 1}
    ).sort("code", 1).to_list(10000)
    
    if not suppliers:
        raise HTTPException(status_code=404, detail="Tidak ada supplier untuk diexport")
    
    df = pd.DataFrame(suppliers)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Suppliers', index=False)
    output.seek(0)
    
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "export", "suppliers",
        f"Export {len(suppliers)} supplier ke Excel",
        request.client.host if request.client else ""
    )
    
    filename = f"suppliers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/branches")
async def export_branches(
    request: Request,
    user: dict = Depends(require_permission("master_branch", "view"))
):
    """Export branches to Excel"""
    db = get_db()
    
    branches = await db["branches"].find(
        {},
        {"_id": 0, "id": 1, "code": 1, "name": 1, "address": 1, "city": 1, 
         "phone": 1, "email": 1, "is_active": 1}
    ).sort("code", 1).to_list(1000)
    
    if not branches:
        raise HTTPException(status_code=404, detail="Tidak ada cabang untuk diexport")
    
    df = pd.DataFrame(branches)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Branches', index=False)
    output.seek(0)
    
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "export", "branches",
        f"Export {len(branches)} cabang ke Excel",
        request.client.host if request.client else ""
    )
    
    filename = f"branches_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/transactions")
async def export_transactions(
    start_date: str = "",
    end_date: str = "",
    branch_id: str = "",
    request: Request = None,
    user: dict = Depends(require_permission("report_sales", "view"))
):
    """Export sales transactions to Excel"""
    db = get_db()
    
    query = {}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    if branch_id:
        query["branch_id"] = branch_id
    
    transactions = await db["sales_invoices"].find(
        query,
        {"_id": 0, "id": 1, "invoice_number": 1, "invoice_date": 1, "customer_name": 1,
         "branch_name": 1, "subtotal": 1, "discount_amount": 1, "tax_amount": 1, 
         "grand_total": 1, "payment_status": 1, "status": 1}
    ).sort("invoice_date", -1).to_list(50000)
    
    if not transactions:
        raise HTTPException(status_code=404, detail="Tidak ada transaksi untuk diexport")
    
    df = pd.DataFrame(transactions)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Transactions', index=False)
    output.seek(0)
    
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "export", "transactions",
        f"Export {len(transactions)} transaksi ke Excel",
        request.client.host if request.client else ""
    )
    
    filename = f"transactions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== TEMPLATE ENDPOINTS ====================

@router.get("/template/products")
async def download_products_template():
    """Download products import template"""
    template_data = {
        "code": ["PRD-001", "PRD-002"],
        "barcode": ["8901234567890", "8901234567891"],
        "name": ["Produk Contoh 1", "Produk Contoh 2"],
        "category_id": ["kategori-uuid-1", "kategori-uuid-2"],
        "unit": ["PCS", "BOX"],
        "buy_price": [10000, 50000],
        "sell_price": [15000, 75000],
        "min_stock": [10, 5],
    }
    
    df = pd.DataFrame(template_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Products', index=False)
        
        # Add instruction sheet
        instructions = pd.DataFrame({
            "Kolom": ["code", "barcode", "name", "category_id", "unit", "buy_price", "sell_price", "min_stock"],
            "Wajib": ["Ya", "Tidak", "Ya", "Tidak", "Ya", "Ya", "Ya", "Tidak"],
            "Keterangan": [
                "Kode unik produk (tidak boleh duplikat)",
                "Barcode produk (opsional)",
                "Nama produk",
                "ID kategori (ambil dari master kategori)",
                "Satuan: PCS, BOX, KG, LTR, dll",
                "Harga beli",
                "Harga jual",
                "Stok minimal untuk alert"
            ]
        })
        instructions.to_excel(writer, sheet_name='Petunjuk', index=False)
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=template_products.xlsx"}
    )


@router.get("/template/customers")
async def download_customers_template():
    """Download customers import template"""
    template_data = {
        "code": ["CUST-001", "CUST-002"],
        "name": ["Customer Contoh 1", "Customer Contoh 2"],
        "phone": ["08123456789", "08234567890"],
        "email": ["customer1@email.com", "customer2@email.com"],
        "address": ["Jl. Contoh No. 1", "Jl. Contoh No. 2"],
        "city": ["Banjarmasin", "Jakarta"],
        "segment": ["regular", "vip"],
        "credit_limit": [1000000, 5000000],
    }
    
    df = pd.DataFrame(template_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Customers', index=False)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=template_customers.xlsx"}
    )


@router.get("/template/suppliers")
async def download_suppliers_template():
    """Download suppliers import template"""
    template_data = {
        "code": ["SUP-001", "SUP-002"],
        "name": ["Supplier Contoh 1", "Supplier Contoh 2"],
        "contact_person": ["Budi", "Andi"],
        "phone": ["08123456789", "08234567890"],
        "email": ["supplier1@email.com", "supplier2@email.com"],
        "address": ["Jl. Supplier No. 1", "Jl. Supplier No. 2"],
        "city": ["Surabaya", "Semarang"],
        "payment_terms": [30, 45],
    }
    
    df = pd.DataFrame(template_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Suppliers', index=False)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=template_suppliers.xlsx"}
    )


# ==================== IMPORT ENDPOINTS ====================

@router.post("/import/products")
async def import_products(
    file: UploadFile = File(...),
    request: Request = None,
    user: dict = Depends(require_permission("master_product", "create"))
):
    """Import products from Excel"""
    db = get_db()
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Format file harus Excel (.xlsx)")
    
    # Read file
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File terlalu besar. Maksimal {MAX_FILE_SIZE // (1024*1024)}MB")
        
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file Excel: {str(e)}")
    
    # Validate required columns
    required_columns = ["code", "name", "unit", "buy_price", "sell_price"]
    validate_required_columns(df, required_columns, "Products")
    
    # Check for duplicates in file
    duplicates = detect_duplicates(df, "code")
    if duplicates:
        raise HTTPException(
            status_code=400, 
            detail=f"Duplikat kode dalam file: {', '.join(duplicates[:10])}"
        )
    
    # Check existing codes
    codes = df["code"].dropna().tolist()
    existing = await check_existing_codes(db, "products", codes)
    
    results = {
        "total_rows": len(df),
        "imported": 0,
        "skipped": 0,
        "errors": [],
        "skipped_codes": existing
    }
    
    now = datetime.now(timezone.utc).isoformat()
    
    for idx, row in df.iterrows():
        try:
            code = str(row.get("code", "")).strip()
            if not code or code in existing:
                results["skipped"] += 1
                continue
            
            product = {
                "id": str(uuid.uuid4()),
                "code": code,
                "barcode": str(row.get("barcode", "")).strip() if pd.notna(row.get("barcode")) else "",
                "name": str(row.get("name", "")).strip(),
                "category_id": str(row.get("category_id", "")).strip() if pd.notna(row.get("category_id")) else "",
                "unit": str(row.get("unit", "PCS")).strip().upper(),
                "buy_price": float(row.get("buy_price", 0)),
                "sell_price": float(row.get("sell_price", 0)),
                "min_stock": int(row.get("min_stock", 0)) if pd.notna(row.get("min_stock")) else 0,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
            
            await db["products"].insert_one(product)
            results["imported"] += 1
            
        except Exception as e:
            results["errors"].append(f"Row {idx + 2}: {str(e)}")
    
    # Log import
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "import", "products",
        f"Import produk: {results['imported']} berhasil, {results['skipped']} dilewati, {len(results['errors'])} error",
        request.client.host if request.client else ""
    )
    
    return results


@router.post("/import/customers")
async def import_customers(
    file: UploadFile = File(...),
    request: Request = None,
    user: dict = Depends(require_permission("master_customer", "create"))
):
    """Import customers from Excel"""
    db = get_db()
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Format file harus Excel (.xlsx)")
    
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File terlalu besar. Maksimal {MAX_FILE_SIZE // (1024*1024)}MB")
        
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file Excel: {str(e)}")
    
    required_columns = ["code", "name"]
    validate_required_columns(df, required_columns, "Customers")
    
    duplicates = detect_duplicates(df, "code")
    if duplicates:
        raise HTTPException(status_code=400, detail=f"Duplikat kode: {', '.join(duplicates[:10])}")
    
    codes = df["code"].dropna().tolist()
    existing = await check_existing_codes(db, "customers", codes)
    
    results = {"total_rows": len(df), "imported": 0, "skipped": 0, "errors": [], "skipped_codes": existing}
    now = datetime.now(timezone.utc).isoformat()
    
    for idx, row in df.iterrows():
        try:
            code = str(row.get("code", "")).strip()
            if not code or code in existing:
                results["skipped"] += 1
                continue
            
            customer = {
                "id": str(uuid.uuid4()),
                "code": code,
                "name": str(row.get("name", "")).strip(),
                "phone": str(row.get("phone", "")).strip() if pd.notna(row.get("phone")) else "",
                "email": str(row.get("email", "")).strip() if pd.notna(row.get("email")) else "",
                "address": str(row.get("address", "")).strip() if pd.notna(row.get("address")) else "",
                "city": str(row.get("city", "")).strip() if pd.notna(row.get("city")) else "",
                "segment": str(row.get("segment", "regular")).strip().lower(),
                "credit_limit": float(row.get("credit_limit", 0)) if pd.notna(row.get("credit_limit")) else 0,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
            
            await db["customers"].insert_one(customer)
            results["imported"] += 1
            
        except Exception as e:
            results["errors"].append(f"Row {idx + 2}: {str(e)}")
    
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "import", "customers",
        f"Import customer: {results['imported']} berhasil, {results['skipped']} dilewati",
        request.client.host if request.client else ""
    )
    
    return results


@router.post("/import/suppliers")
async def import_suppliers(
    file: UploadFile = File(...),
    request: Request = None,
    user: dict = Depends(require_permission("master_supplier", "create"))
):
    """Import suppliers from Excel"""
    db = get_db()
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Format file harus Excel (.xlsx)")
    
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File terlalu besar. Maksimal {MAX_FILE_SIZE // (1024*1024)}MB")
        
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file Excel: {str(e)}")
    
    required_columns = ["code", "name"]
    validate_required_columns(df, required_columns, "Suppliers")
    
    duplicates = detect_duplicates(df, "code")
    if duplicates:
        raise HTTPException(status_code=400, detail=f"Duplikat kode: {', '.join(duplicates[:10])}")
    
    codes = df["code"].dropna().tolist()
    existing = await check_existing_codes(db, "suppliers", codes)
    
    results = {"total_rows": len(df), "imported": 0, "skipped": 0, "errors": [], "skipped_codes": existing}
    now = datetime.now(timezone.utc).isoformat()
    
    for idx, row in df.iterrows():
        try:
            code = str(row.get("code", "")).strip()
            if not code or code in existing:
                results["skipped"] += 1
                continue
            
            supplier = {
                "id": str(uuid.uuid4()),
                "code": code,
                "name": str(row.get("name", "")).strip(),
                "contact_person": str(row.get("contact_person", "")).strip() if pd.notna(row.get("contact_person")) else "",
                "phone": str(row.get("phone", "")).strip() if pd.notna(row.get("phone")) else "",
                "email": str(row.get("email", "")).strip() if pd.notna(row.get("email")) else "",
                "address": str(row.get("address", "")).strip() if pd.notna(row.get("address")) else "",
                "city": str(row.get("city", "")).strip() if pd.notna(row.get("city")) else "",
                "payment_terms": int(row.get("payment_terms", 30)) if pd.notna(row.get("payment_terms")) else 30,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
            
            await db["suppliers"].insert_one(supplier)
            results["imported"] += 1
            
        except Exception as e:
            results["errors"].append(f"Row {idx + 2}: {str(e)}")
    
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "import", "suppliers",
        f"Import supplier: {results['imported']} berhasil, {results['skipped']} dilewati",
        request.client.host if request.client else ""
    )
    
    return results


@router.post("/import/branches")
async def import_branches(
    file: UploadFile = File(...),
    request: Request = None,
    user: dict = Depends(require_permission("master_branch", "create"))
):
    """Import branches from Excel"""
    db = get_db()
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Format file harus Excel (.xlsx)")
    
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File terlalu besar. Maksimal {MAX_FILE_SIZE // (1024*1024)}MB")
        
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file Excel: {str(e)}")
    
    required_columns = ["code", "name"]
    validate_required_columns(df, required_columns, "Branches")
    
    duplicates = detect_duplicates(df, "code")
    if duplicates:
        raise HTTPException(status_code=400, detail=f"Duplikat kode: {', '.join(duplicates[:10])}")
    
    codes = df["code"].dropna().tolist()
    existing = await check_existing_codes(db, "branches", codes)
    
    results = {"total_rows": len(df), "imported": 0, "skipped": 0, "errors": [], "skipped_codes": existing}
    now = datetime.now(timezone.utc).isoformat()
    
    for idx, row in df.iterrows():
        try:
            code = str(row.get("code", "")).strip()
            if not code or code in existing:
                results["skipped"] += 1
                continue
            
            branch = {
                "id": str(uuid.uuid4()),
                "code": code,
                "name": str(row.get("name", "")).strip(),
                "address": str(row.get("address", "")).strip() if pd.notna(row.get("address")) else "",
                "city": str(row.get("city", "")).strip() if pd.notna(row.get("city")) else "",
                "phone": str(row.get("phone", "")).strip() if pd.notna(row.get("phone")) else "",
                "email": str(row.get("email", "")).strip() if pd.notna(row.get("email")) else "",
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
            
            await db["branches"].insert_one(branch)
            results["imported"] += 1
            
        except Exception as e:
            results["errors"].append(f"Row {idx + 2}: {str(e)}")
    
    await log_security_event(
        db, user.get("user_id", ""), user.get("name", ""),
        "import", "branches",
        f"Import cabang: {results['imported']} berhasil, {results['skipped']} dilewati",
        request.client.host if request.client else ""
    )
    
    return results
