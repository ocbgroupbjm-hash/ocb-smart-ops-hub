# OCB TITAN AI - Data Export System
# Full data export for all modules

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import json
import csv
import io

from database import get_db

router = APIRouter(prefix="/api/export", tags=["Data Export"])

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# ==================== HELPER FUNCTIONS ====================

async def get_collection_data(collection_name: str, query: dict = None, limit: int = 10000):
    """Get data from collection"""
    if query is None:
        query = {}
    cursor = get_db()[collection_name].find(query, {"_id": 0})
    return await cursor.to_list(length=limit)

def generate_csv(data: list, filename: str):
    """Generate CSV file from data"""
    if not data:
        return StreamingResponse(
            io.StringIO("No data"),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

def generate_json(data: list, filename: str):
    """Generate JSON file from data"""
    return StreamingResponse(
        iter([json.dumps(data, indent=2, default=str)]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==================== MASTER DATA EXPORTS ====================

@router.get("/master/products")
async def export_products(format: str = "json"):
    """Export all products"""
    data = await get_collection_data("products")
    filename = f"products_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/master/categories")
async def export_categories(format: str = "json"):
    """Export all categories"""
    data = await get_collection_data("categories")
    filename = f"categories_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/master/brands")
async def export_brands(format: str = "json"):
    """Export all brands"""
    data = await get_collection_data("brands")
    filename = f"brands_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/master/suppliers")
async def export_suppliers(format: str = "json"):
    """Export all suppliers"""
    data = await get_collection_data("suppliers")
    filename = f"suppliers_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/master/customers")
async def export_customers(format: str = "json"):
    """Export all customers"""
    data = await get_collection_data("customers")
    filename = f"customers_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/master/branches")
async def export_branches(format: str = "json"):
    """Export all branches"""
    data = await get_collection_data("branches")
    filename = f"branches_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/master/warehouses")
async def export_warehouses(format: str = "json"):
    """Export all warehouses"""
    data = await get_collection_data("warehouses")
    filename = f"warehouses_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

# ==================== EMPLOYEE EXPORTS ====================

@router.get("/employees/all")
async def export_employees(format: str = "json"):
    """Export all employees"""
    data = await get_collection_data("employees")
    filename = f"employees_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/employees/jabatan")
async def export_jabatan(format: str = "json"):
    """Export all jabatan"""
    data = await get_collection_data("master_jabatan")
    filename = f"jabatan_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/employees/attendance")
async def export_attendance(month: int, year: int, format: str = "json"):
    """Export attendance data"""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    data = await get_collection_data("attendance", {
        "tanggal": {"$gte": start_date, "$lte": end_date}
    })
    filename = f"attendance_{year}{month:02d}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/employees/kpi")
async def export_kpi(format: str = "json"):
    """Export KPI data"""
    data = await get_collection_data("employee_kpi")
    filename = f"kpi_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

# ==================== SALES EXPORTS ====================

@router.get("/sales/transactions")
async def export_transactions(start_date: str, end_date: str, format: str = "json"):
    """Export sales transactions"""
    data = await get_collection_data("transactions", {
        "created_at": {"$gte": start_date, "$lte": end_date}
    })
    filename = f"transactions_{start_date}_{end_date}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/sales/setoran")
async def export_setoran(month: int, year: int, format: str = "json"):
    """Export setoran harian"""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    data = await get_collection_data("setoran_harian", {
        "tanggal": {"$gte": start_date, "$lte": end_date}
    })
    filename = f"setoran_{year}{month:02d}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/sales/selisih")
async def export_selisih(month: int, year: int, format: str = "json"):
    """Export selisih kas"""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    data = await get_collection_data("selisih_kas", {
        "tanggal": {"$gte": start_date, "$lte": end_date}
    })
    filename = f"selisih_kas_{year}{month:02d}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

# ==================== INVENTORY EXPORTS ====================

@router.get("/inventory/stock")
async def export_stock(format: str = "json"):
    """Export current stock"""
    data = await get_collection_data("products")
    # Simplify to stock data
    stock_data = [{
        "id": p.get("id"),
        "sku": p.get("sku"),
        "name": p.get("name"),
        "category": p.get("category"),
        "stock": p.get("stock", 0),
        "min_stock": p.get("min_stock", 0),
        "branch_id": p.get("branch_id", "main"),
        "price": p.get("price", 0),
        "cost": p.get("cost", 0)
    } for p in data]
    
    filename = f"stock_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(stock_data, f"{filename}.csv")
    return generate_json(stock_data, f"{filename}.json")

@router.get("/inventory/mutations")
async def export_stock_mutations(start_date: str, end_date: str, format: str = "json"):
    """Export stock mutations"""
    data = await get_collection_data("stock_mutations", {
        "created_at": {"$gte": start_date, "$lte": end_date}
    })
    filename = f"stock_mutations_{start_date}_{end_date}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

# ==================== ACCOUNTING EXPORTS ====================

@router.get("/accounting/journals")
async def export_journals(month: int, year: int, format: str = "json"):
    """Export journal entries"""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    data = await get_collection_data("journals", {
        "date": {"$gte": start_date, "$lte": end_date}
    })
    filename = f"journals_{year}{month:02d}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/accounting/kas-masuk")
async def export_kas_masuk(month: int, year: int, format: str = "json"):
    """Export cash in"""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    data = await get_collection_data("cash_transactions", {
        "type": "in",
        "date": {"$gte": start_date, "$lte": end_date}
    })
    filename = f"kas_masuk_{year}{month:02d}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/accounting/kas-keluar")
async def export_kas_keluar(month: int, year: int, format: str = "json"):
    """Export cash out"""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    data = await get_collection_data("cash_transactions", {
        "type": "out",
        "date": {"$gte": start_date, "$lte": end_date}
    })
    filename = f"kas_keluar_{year}{month:02d}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

# ==================== PAYROLL EXPORTS ====================

@router.get("/payroll/details")
async def export_payroll(period_id: str, format: str = "json"):
    """Export payroll details"""
    data = await get_collection_data("payroll_details", {"period_id": period_id})
    filename = f"payroll_{period_id}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

# ==================== AUDIT EXPORTS ====================

@router.get("/audit/kas")
async def export_audit_kas(format: str = "json"):
    """Export cash audit data"""
    data = await get_collection_data("audit_kas")
    filename = f"audit_kas_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/audit/stock")
async def export_audit_stock(format: str = "json"):
    """Export stock audit data"""
    data = await get_collection_data("stock_opname")
    filename = f"audit_stock_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

# ==================== CRM EXPORTS ====================

@router.get("/crm/customers")
async def export_crm_customers(format: str = "json"):
    """Export CRM customer data with history"""
    data = await get_collection_data("customers")
    filename = f"crm_customers_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

@router.get("/crm/complaints")
async def export_complaints(format: str = "json"):
    """Export customer complaints"""
    data = await get_collection_data("customer_complaints")
    filename = f"complaints_{get_wib_now().strftime('%Y%m%d')}"
    
    if format == "csv":
        return generate_csv(data, f"{filename}.csv")
    return generate_json(data, f"{filename}.json")

# ==================== BULK EXPORT ====================

@router.get("/bulk/all")
async def export_all_data():
    """Export all data as JSON"""
    all_data = {
        "export_date": get_wib_now().isoformat(),
        "products": await get_collection_data("products", limit=50000),
        "categories": await get_collection_data("categories"),
        "brands": await get_collection_data("brands"),
        "suppliers": await get_collection_data("suppliers"),
        "customers": await get_collection_data("customers"),
        "branches": await get_collection_data("branches"),
        "employees": await get_collection_data("employees"),
        "jabatan": await get_collection_data("master_jabatan"),
        "shifts": await get_collection_data("master_shifts"),
    }
    
    filename = f"ocb_full_export_{get_wib_now().strftime('%Y%m%d')}"
    return generate_json(all_data, f"{filename}.json")
