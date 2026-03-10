# OCB TITAN AI - Import System
# Import data from Excel, CSV, JSON with validation

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import json
import csv
import io
import uuid
import pandas as pd

from database import get_db

router = APIRouter(prefix="/api/import", tags=["Import System"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def import_logs_col():
    return get_db()['import_logs']

def import_templates_col():
    return get_db()['import_templates']

# ==================== IMPORT TEMPLATES ====================

IMPORT_TEMPLATES = {
    "products": {
        "name": "Products / Items",
        "required_columns": ["code", "name", "category", "price"],
        "optional_columns": ["brand", "unit", "min_stock", "description", "barcode", "cost_price"],
        "collection": "products",
        "unique_field": "code"
    },
    "suppliers": {
        "name": "Suppliers",
        "required_columns": ["code", "name"],
        "optional_columns": ["phone", "email", "address", "contact_person", "payment_terms"],
        "collection": "suppliers",
        "unique_field": "code"
    },
    "customers": {
        "name": "Customers / Pelanggan",
        "required_columns": ["name"],
        "optional_columns": ["phone", "email", "address", "type", "credit_limit"],
        "collection": "customers",
        "unique_field": "phone"
    },
    "branches": {
        "name": "Cabang",
        "required_columns": ["code", "name", "city"],
        "optional_columns": ["address", "phone", "latitude", "longitude", "manager"],
        "collection": "branches",
        "unique_field": "code"
    },
    "employees": {
        "name": "Karyawan",
        "required_columns": ["nik", "name", "branch_code", "jabatan"],
        "optional_columns": ["phone", "email", "address", "tanggal_masuk", "gaji_pokok", "bank_account"],
        "collection": "employees",
        "unique_field": "nik"
    },
    "stock_awal": {
        "name": "Stok Awal",
        "required_columns": ["product_code", "branch_code", "quantity"],
        "optional_columns": ["location", "batch_number", "expiry_date"],
        "collection": "stock",
        "unique_field": None  # No unique, will update existing
    },
    "saldo_awal": {
        "name": "Saldo Awal",
        "required_columns": ["account_code", "account_name", "debit", "credit"],
        "optional_columns": ["branch_code", "description"],
        "collection": "account_balances",
        "unique_field": "account_code"
    },
    "kpi_targets": {
        "name": "KPI Targets",
        "required_columns": ["employee_id", "kpi_name", "target_value", "period_month", "period_year"],
        "optional_columns": ["weight", "kpi_category"],
        "collection": "kpi_targets",
        "unique_field": None
    }
}

@router.get("/templates")
async def get_import_templates():
    """Get all available import templates"""
    templates = []
    for key, template in IMPORT_TEMPLATES.items():
        templates.append({
            "key": key,
            "name": template["name"],
            "required_columns": template["required_columns"],
            "optional_columns": template["optional_columns"],
            "all_columns": template["required_columns"] + template["optional_columns"]
        })
    return {"templates": templates}

@router.get("/templates/{template_key}/download")
async def download_import_template(template_key: str, format: str = "xlsx"):
    """Download empty template for import"""
    from fastapi.responses import StreamingResponse
    import xlsxwriter
    
    if template_key not in IMPORT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template tidak ditemukan")
    
    template = IMPORT_TEMPLATES[template_key]
    columns = template["required_columns"] + template["optional_columns"]
    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Template")
    
    # Header format
    required_format = workbook.add_format({
        'bold': True,
        'bg_color': '#8B0000',
        'font_color': 'white',
        'border': 1
    })
    optional_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4A4A4A',
        'font_color': 'white',
        'border': 1
    })
    
    # Write headers
    for col, header in enumerate(columns):
        if header in template["required_columns"]:
            worksheet.write(0, col, f"{header} *", required_format)
        else:
            worksheet.write(0, col, header, optional_format)
        worksheet.set_column(col, col, 15)
    
    # Add sample row
    worksheet.write(1, 0, "SAMPLE_DATA")
    
    # Add instructions sheet
    instructions = workbook.add_worksheet("Instructions")
    instructions.write(0, 0, f"Import Template: {template['name']}")
    instructions.write(2, 0, "Required Columns (marked with *):")
    for i, col in enumerate(template["required_columns"]):
        instructions.write(3 + i, 0, f"  - {col}")
    instructions.write(5 + len(template["required_columns"]), 0, "Optional Columns:")
    for i, col in enumerate(template["optional_columns"]):
        instructions.write(6 + len(template["required_columns"]) + i, 0, f"  - {col}")
    
    workbook.close()
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=template_{template_key}.xlsx"}
    )

# ==================== FILE PARSING ====================

async def parse_file(file: UploadFile) -> List[dict]:
    """Parse uploaded file to list of dicts"""
    content = await file.read()
    filename = file.filename.lower()
    
    if filename.endswith('.xlsx') or filename.endswith('.xls'):
        df = pd.read_excel(io.BytesIO(content))
        return df.fillna('').to_dict('records')
    elif filename.endswith('.csv'):
        df = pd.read_csv(io.BytesIO(content))
        return df.fillna('').to_dict('records')
    elif filename.endswith('.json'):
        data = json.loads(content.decode('utf-8'))
        return data if isinstance(data, list) else [data]
    else:
        raise HTTPException(status_code=400, detail="Format file tidak didukung. Gunakan Excel, CSV, atau JSON.")

# ==================== PREVIEW IMPORT ====================

@router.post("/preview/{template_key}")
async def preview_import(template_key: str, file: UploadFile = File(...)):
    """Preview data before import with validation"""
    if template_key not in IMPORT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template tidak ditemukan")
    
    template = IMPORT_TEMPLATES[template_key]
    
    try:
        data = await parse_file(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file: {str(e)}")
    
    if not data:
        raise HTTPException(status_code=400, detail="File kosong")
    
    # Validate columns
    file_columns = list(data[0].keys())
    missing_required = [col for col in template["required_columns"] if col not in file_columns]
    
    if missing_required:
        return {
            "valid": False,
            "error": f"Kolom wajib tidak ditemukan: {', '.join(missing_required)}",
            "file_columns": file_columns,
            "required_columns": template["required_columns"]
        }
    
    # Validate data rows
    validation_results = []
    valid_count = 0
    invalid_count = 0
    
    for i, row in enumerate(data):
        row_errors = []
        
        # Check required fields
        for col in template["required_columns"]:
            if not row.get(col) or str(row.get(col)).strip() == '':
                row_errors.append(f"Kolom '{col}' kosong")
        
        if row_errors:
            invalid_count += 1
            validation_results.append({
                "row": i + 2,  # +2 for header row and 0-index
                "status": "invalid",
                "errors": row_errors,
                "data": row
            })
        else:
            valid_count += 1
            validation_results.append({
                "row": i + 2,
                "status": "valid",
                "data": row
            })
    
    # Check duplicates
    unique_field = template.get("unique_field")
    duplicates = []
    if unique_field:
        seen_values = {}
        col = get_db()[template["collection"]]
        
        for result in validation_results:
            if result["status"] == "valid":
                value = result["data"].get(unique_field)
                if value:
                    # Check in file
                    if value in seen_values:
                        result["status"] = "duplicate_in_file"
                        result["errors"] = [f"Duplikat dengan baris {seen_values[value]}"]
                        duplicates.append(result["row"])
                    else:
                        seen_values[value] = result["row"]
                        # Check in database
                        existing = await col.find_one({unique_field: value}, {"_id": 0})
                        if existing:
                            result["status"] = "duplicate_in_db"
                            result["warnings"] = [f"Data sudah ada di database (akan di-update)"]
    
    return {
        "valid": invalid_count == 0,
        "template": template["name"],
        "total_rows": len(data),
        "valid_rows": valid_count - len(duplicates),
        "invalid_rows": invalid_count,
        "duplicate_rows": len(duplicates),
        "preview": validation_results[:100],  # First 100 rows
        "file_columns": file_columns
    }

# ==================== EXECUTE IMPORT ====================

@router.post("/execute/{template_key}")
async def execute_import(
    template_key: str,
    file: UploadFile = File(...),
    update_existing: bool = Form(True),
    skip_errors: bool = Form(True)
):
    """Execute import with rollback support"""
    if template_key not in IMPORT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template tidak ditemukan")
    
    template = IMPORT_TEMPLATES[template_key]
    
    try:
        data = await parse_file(file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file: {str(e)}")
    
    if not data:
        raise HTTPException(status_code=400, detail="File kosong")
    
    # Create import log
    import_id = gen_id()
    import_log = {
        "id": import_id,
        "template": template_key,
        "filename": file.filename,
        "total_rows": len(data),
        "status": "processing",
        "started_at": now_iso(),
        "results": {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0
        },
        "errors": [],
        "inserted_ids": []
    }
    await import_logs_col().insert_one(import_log)
    
    # Process data
    col = get_db()[template["collection"]]
    unique_field = template.get("unique_field")
    
    inserted = 0
    updated = 0
    skipped = 0
    failed = 0
    errors = []
    inserted_ids = []
    
    for i, row in enumerate(data):
        row_num = i + 2
        
        try:
            # Validate required fields
            missing = [c for c in template["required_columns"] if not row.get(c)]
            if missing:
                if skip_errors:
                    skipped += 1
                    errors.append({"row": row_num, "error": f"Kolom kosong: {', '.join(missing)}"})
                    continue
                else:
                    failed += 1
                    errors.append({"row": row_num, "error": f"Kolom kosong: {', '.join(missing)}"})
                    break
            
            # Prepare document
            doc = {
                "id": gen_id(),
                **{k: v for k, v in row.items() if v != '' and v is not None},
                "created_at": now_iso(),
                "import_id": import_id
            }
            
            # Check for existing
            if unique_field and row.get(unique_field):
                existing = await col.find_one({unique_field: row[unique_field]})
                if existing:
                    if update_existing:
                        await col.update_one(
                            {unique_field: row[unique_field]},
                            {"$set": {
                                **{k: v for k, v in row.items() if v != '' and v is not None},
                                "updated_at": now_iso(),
                                "last_import_id": import_id
                            }}
                        )
                        updated += 1
                    else:
                        skipped += 1
                    continue
            
            # Insert new
            await col.insert_one(doc)
            inserted += 1
            inserted_ids.append(doc["id"])
            
        except Exception as e:
            failed += 1
            errors.append({"row": row_num, "error": str(e)})
            if not skip_errors:
                break
    
    # Update import log
    status = "completed" if failed == 0 else ("partial" if inserted > 0 or updated > 0 else "failed")
    await import_logs_col().update_one(
        {"id": import_id},
        {"$set": {
            "status": status,
            "completed_at": now_iso(),
            "results": {
                "inserted": inserted,
                "updated": updated,
                "skipped": skipped,
                "failed": failed
            },
            "errors": errors[:100],  # Limit errors stored
            "inserted_ids": inserted_ids
        }}
    )
    
    return {
        "import_id": import_id,
        "status": status,
        "results": {
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "failed": failed
        },
        "errors": errors[:20]  # Return first 20 errors
    }

# ==================== ROLLBACK IMPORT ====================

@router.post("/rollback/{import_id}")
async def rollback_import(import_id: str):
    """Rollback a previous import"""
    log = await import_logs_col().find_one({"id": import_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Import log tidak ditemukan")
    
    if log.get("status") == "rolled_back":
        raise HTTPException(status_code=400, detail="Import sudah di-rollback")
    
    template_key = log.get("template")
    if template_key not in IMPORT_TEMPLATES:
        raise HTTPException(status_code=400, detail="Template tidak valid")
    
    template = IMPORT_TEMPLATES[template_key]
    col = get_db()[template["collection"]]
    
    # Delete inserted records
    inserted_ids = log.get("inserted_ids", [])
    if inserted_ids:
        result = await col.delete_many({"id": {"$in": inserted_ids}})
        deleted_count = result.deleted_count
    else:
        deleted_count = 0
    
    # Update import log
    await import_logs_col().update_one(
        {"id": import_id},
        {"$set": {
            "status": "rolled_back",
            "rolled_back_at": now_iso(),
            "deleted_count": deleted_count
        }}
    )
    
    return {
        "message": f"Rollback berhasil. {deleted_count} record dihapus.",
        "import_id": import_id,
        "deleted_count": deleted_count
    }

# ==================== IMPORT HISTORY ====================

@router.get("/history")
async def get_import_history(limit: int = 50):
    """Get import history"""
    logs = await import_logs_col().find({}, {"_id": 0}).sort("started_at", -1).to_list(length=limit)
    return {"imports": logs}

@router.get("/history/{import_id}")
async def get_import_detail(import_id: str):
    """Get import detail"""
    log = await import_logs_col().find_one({"id": import_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Import tidak ditemukan")
    return log
