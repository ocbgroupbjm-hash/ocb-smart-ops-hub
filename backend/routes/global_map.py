# OCB TITAN AI - Global Map Monitoring System
# Real-time map monitoring for all branches, sales, SPV

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid

from database import get_db

router = APIRouter(prefix="/api/global-map", tags=["Global Map"])

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# Collections
def branches_col():
    return get_db()['branches']

def employees_col():
    return get_db()['employees']

def setoran_col():
    return get_db()['setoran_harian']

def transactions_col():
    return get_db()['transactions']

def products_col():
    return get_db()['products']

def gps_tracking_col():
    return get_db()['gps_tracking']

def alerts_col():
    return get_db()['system_alerts']

def stock_alerts_col():
    return get_db()['stock_alerts']

# ==================== BRANCH LOCATIONS ====================

# Indonesia branch coordinates (sample)
BRANCH_COORDINATES = {
    "OC1": {"lat": -3.3167, "lng": 114.5900, "city": "Banjarmasin"},
    "OC3": {"lat": -3.3200, "lng": 114.5850, "city": "Banjarmasin"},
    "OC8": {"lat": -3.3100, "lng": 114.6000, "city": "Banjarmasin"},
    "OC30": {"lat": -3.2950, "lng": 114.5750, "city": "Banjarmasin"},
    "OC36": {"lat": -3.3300, "lng": 114.5950, "city": "Banjarmasin"},
    "OC37": {"lat": -3.3050, "lng": 114.5800, "city": "Banjarmasin"},
    "OC40": {"lat": -3.3250, "lng": 114.6050, "city": "Banjarmasin"},
}

@router.get("/branches")
async def get_all_branch_locations():
    """Get all branches with their locations and status for map display"""
    today = get_wib_now().strftime("%Y-%m-%d")
    month_start = get_wib_now().strftime("%Y-%m-01")
    
    branches = await branches_col().find({}, {"_id": 0}).to_list(length=500)
    
    # Get today's setoran
    setoran_today = await setoran_col().find({"tanggal": today}, {"_id": 0}).to_list(length=500)
    setoran_today_map = {s["branch_id"]: s for s in setoran_today}
    
    # Get month setoran
    setoran_month = await setoran_col().find({
        "tanggal": {"$gte": month_start, "$lte": today}
    }, {"_id": 0}).to_list(length=5000)
    
    # Group by branch
    branch_month_sales = {}
    for s in setoran_month:
        bid = s.get("branch_id")
        if bid not in branch_month_sales:
            branch_month_sales[bid] = {"total": 0, "count": 0}
        branch_month_sales[bid]["total"] += s.get("total_penjualan", 0)
        branch_month_sales[bid]["count"] += s.get("total_transaksi", 0)
    
    # Get employees per branch
    employees = await employees_col().find({"status": "active"}, {"_id": 0}).to_list(length=1000)
    branch_employees = {}
    for e in employees:
        bid = e.get("branch_id")
        if bid not in branch_employees:
            branch_employees[bid] = 0
        branch_employees[bid] += 1
    
    # Get stock status per branch
    products = await products_col().find({}, {"_id": 0}).to_list(length=10000)
    branch_stock_status = {}
    for p in products:
        bid = p.get("branch_id", "main")
        if bid not in branch_stock_status:
            branch_stock_status[bid] = {"total": 0, "low": 0, "empty": 0}
        branch_stock_status[bid]["total"] += 1
        stock = p.get("stock", 0)
        if stock == 0:
            branch_stock_status[bid]["empty"] += 1
        elif stock < p.get("min_stock", 5):
            branch_stock_status[bid]["low"] += 1
    
    result = []
    for idx, b in enumerate(branches):
        bid = b.get("id", "")
        code = b.get("code", f"OC{idx+1}")
        
        # Get coordinates
        coords = BRANCH_COORDINATES.get(code, {
            "lat": -3.3167 + (idx * 0.005),
            "lng": 114.5900 + (idx * 0.005),
            "city": "Banjarmasin"
        })
        
        # Get today's data
        today_data = setoran_today_map.get(bid, {})
        month_data = branch_month_sales.get(bid, {"total": 0, "count": 0})
        stock_data = branch_stock_status.get(bid, {"total": 0, "low": 0, "empty": 0})
        
        # Determine status
        status = "green"  # normal
        status_text = "Normal"
        
        if stock_data["empty"] > 5:
            status = "red"
            status_text = "Stok Kosong"
        elif stock_data["low"] > 10 or not today_data:
            status = "yellow"
            status_text = "Perlu Perhatian"
        
        # Check for minus kas
        if today_data.get("selisih", 0) < -50000:
            status = "red"
            status_text = "Minus Kas"
        
        result.append({
            "id": bid,
            "code": code,
            "name": b.get("name", f"Cabang {code}"),
            "address": b.get("address", coords["city"]),
            "latitude": coords["lat"],
            "longitude": coords["lng"],
            "city": coords["city"],
            "status": status,
            "status_text": status_text,
            "sales_today": today_data.get("total_penjualan", 0),
            "sales_month": month_data["total"],
            "transactions_today": today_data.get("total_transaksi", 0),
            "transactions_month": month_data["count"],
            "employee_count": branch_employees.get(bid, 0),
            "stock_empty": stock_data["empty"],
            "stock_low": stock_data["low"],
            "stock_total": stock_data["total"],
            "has_setoran_today": bool(today_data),
            "selisih_today": today_data.get("selisih", 0)
        })
    
    return {
        "total_branches": len(result),
        "status_summary": {
            "green": len([r for r in result if r["status"] == "green"]),
            "yellow": len([r for r in result if r["status"] == "yellow"]),
            "red": len([r for r in result if r["status"] == "red"])
        },
        "branches": result
    }

@router.get("/branches/{branch_id}")
async def get_branch_detail(branch_id: str):
    """Get detailed info for a specific branch"""
    branch = await branches_col().find_one({"id": branch_id}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Cabang tidak ditemukan")
    
    today = get_wib_now().strftime("%Y-%m-%d")
    
    # Get employees
    employees = await employees_col().find({
        "branch_id": branch_id, "status": "active"
    }, {"_id": 0}).to_list(length=100)
    
    # Get setoran
    setoran = await setoran_col().find_one({"branch_id": branch_id, "tanggal": today}, {"_id": 0})
    
    # Get stock status
    products = await products_col().find({"branch_id": branch_id}, {"_id": 0}).to_list(length=1000)
    empty_stock = [p for p in products if p.get("stock", 0) == 0]
    low_stock = [p for p in products if 0 < p.get("stock", 0) < p.get("min_stock", 5)]
    
    return {
        "branch": branch,
        "employees": employees,
        "employee_count": len(employees),
        "setoran_today": setoran,
        "stock_summary": {
            "total_products": len(products),
            "empty_count": len(empty_stock),
            "low_count": len(low_stock)
        },
        "empty_stock_items": empty_stock[:20],
        "low_stock_items": low_stock[:20]
    }

# ==================== SALES & SPV TRACKING ====================

class GPSUpdate(BaseModel):
    employee_id: str
    employee_name: str
    jabatan: str
    branch_id: str
    branch_name: str
    latitude: float
    longitude: float
    address: str = ""
    activity: str = ""  # di_toko, perjalanan, kunjungan

@router.post("/gps/update")
async def update_gps_location(data: GPSUpdate):
    """Update GPS location for sales/SPV"""
    tracking = {
        "id": gen_id(),
        "employee_id": data.employee_id,
        "employee_name": data.employee_name,
        "jabatan": data.jabatan,
        "branch_id": data.branch_id,
        "branch_name": data.branch_name,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "address": data.address,
        "activity": data.activity,
        "timestamp": now_iso(),
        "tanggal": get_wib_now().strftime("%Y-%m-%d"),
        "waktu": get_wib_now().strftime("%H:%M:%S")
    }
    
    # Upsert - update existing or insert new
    await gps_tracking_col().update_one(
        {"employee_id": data.employee_id, "tanggal": tracking["tanggal"]},
        {"$set": tracking},
        upsert=True
    )
    
    # Check if SPV leaving store - create alert
    if data.jabatan.lower() in ["spv", "supervisor"] and data.activity == "perjalanan":
        alert = {
            "id": gen_id(),
            "alert_type": "spv_movement",
            "severity": "warning",
            "title": f"SPV Meninggalkan Toko: {data.employee_name}",
            "message": f"SPV {data.employee_name} meninggalkan {data.branch_name} pada {tracking['waktu']}",
            "branch_id": data.branch_id,
            "branch_name": data.branch_name,
            "employee_id": data.employee_id,
            "employee_name": data.employee_name,
            "reference_type": "gps_tracking",
            "reference_id": tracking["id"],
            "data": {
                "latitude": data.latitude,
                "longitude": data.longitude,
                "activity": data.activity
            },
            "is_read": False,
            "is_resolved": False,
            "created_at": now_iso()
        }
        await alerts_col().insert_one(alert)
    
    return {"message": "Lokasi berhasil diupdate", "tracking": tracking}

@router.get("/gps/realtime")
async def get_realtime_gps():
    """Get realtime GPS locations for all sales and SPV"""
    today = get_wib_now().strftime("%Y-%m-%d")
    
    # Get today's tracking
    tracking = await gps_tracking_col().find({"tanggal": today}, {"_id": 0}).to_list(length=500)
    
    # Filter by role (sales, SPV)
    sales_spv_roles = ["sales", "spv", "supervisor", "marketing"]
    
    result = []
    for t in tracking:
        if any(role in t.get("jabatan", "").lower() for role in sales_spv_roles):
            # Check if active (within last 30 minutes)
            try:
                last_update = datetime.fromisoformat(t.get("timestamp", "").replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                minutes_ago = (now - last_update).total_seconds() / 60
                is_active = minutes_ago < 30
            except:
                is_active = False
            
            result.append({
                **t,
                "is_active": is_active,
                "minutes_since_update": int(minutes_ago) if 'minutes_ago' in dir() else 999
            })
    
    return {
        "tanggal": today,
        "total_tracked": len(result),
        "active_count": len([r for r in result if r.get("is_active")]),
        "locations": result
    }

@router.get("/gps/history/{employee_id}")
async def get_gps_history(employee_id: str, tanggal: Optional[str] = None):
    """Get GPS history for an employee"""
    if not tanggal:
        tanggal = get_wib_now().strftime("%Y-%m-%d")
    
    history = await gps_tracking_col().find({
        "employee_id": employee_id,
        "tanggal": tanggal
    }, {"_id": 0}).sort("timestamp", 1).to_list(length=100)
    
    return {"employee_id": employee_id, "tanggal": tanggal, "history": history}

# ==================== STOCK MAP MONITORING ====================

@router.get("/stock/map")
async def get_stock_map():
    """Get stock status for all branches for map display"""
    branches = await branches_col().find({}, {"_id": 0}).to_list(length=500)
    products = await products_col().find({}, {"_id": 0}).to_list(length=50000)
    
    # Group products by branch
    branch_stock = {}
    for p in products:
        bid = p.get("branch_id", "main")
        if bid not in branch_stock:
            branch_stock[bid] = {"total": 0, "low": 0, "empty": 0, "empty_items": [], "low_items": []}
        
        branch_stock[bid]["total"] += 1
        stock = p.get("stock", 0)
        min_stock = p.get("min_stock", 5)
        
        if stock == 0:
            branch_stock[bid]["empty"] += 1
            if len(branch_stock[bid]["empty_items"]) < 10:
                branch_stock[bid]["empty_items"].append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "sku": p.get("sku", "")
                })
        elif stock < min_stock:
            branch_stock[bid]["low"] += 1
            if len(branch_stock[bid]["low_items"]) < 10:
                branch_stock[bid]["low_items"].append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "sku": p.get("sku", ""),
                    "stock": stock,
                    "min_stock": min_stock
                })
    
    result = []
    for idx, b in enumerate(branches):
        bid = b.get("id", "")
        code = b.get("code", f"OC{idx+1}")
        stock_data = branch_stock.get(bid, {"total": 0, "low": 0, "empty": 0, "empty_items": [], "low_items": []})
        
        # Determine status
        if stock_data["empty"] > 5:
            status = "red"
        elif stock_data["low"] > 10:
            status = "yellow"
        else:
            status = "green"
        
        coords = BRANCH_COORDINATES.get(code, {"lat": -3.3167 + (idx * 0.005), "lng": 114.5900 + (idx * 0.005)})
        
        result.append({
            "branch_id": bid,
            "branch_code": code,
            "branch_name": b.get("name", f"Cabang {code}"),
            "latitude": coords["lat"],
            "longitude": coords["lng"],
            "status": status,
            "total_products": stock_data["total"],
            "empty_count": stock_data["empty"],
            "low_count": stock_data["low"],
            "empty_items": stock_data["empty_items"],
            "low_items": stock_data["low_items"]
        })
    
    return {
        "total_branches": len(result),
        "status_summary": {
            "green": len([r for r in result if r["status"] == "green"]),
            "yellow": len([r for r in result if r["status"] == "yellow"]),
            "red": len([r for r in result if r["status"] == "red"])
        },
        "branches": result
    }

# ==================== STOCK ALERTS ====================

@router.post("/stock/alert")
async def create_stock_alert(branch_id: str, branch_name: str, product_id: str, product_name: str):
    """Create stock alert when item is empty"""
    alert = {
        "id": gen_id(),
        "alert_type": "stock_empty",
        "severity": "urgent",
        "title": f"Stok Kosong: {product_name}",
        "message": f"Produk {product_name} habis di {branch_name}",
        "branch_id": branch_id,
        "branch_name": branch_name,
        "product_id": product_id,
        "product_name": product_name,
        "notify_targets": ["gudang", "spv", "hrd", "admin", "owner"],
        "is_read": False,
        "is_resolved": False,
        "created_at": now_iso()
    }
    
    await stock_alerts_col().insert_one(alert)
    return {"message": "Stock alert created", "alert": alert}

@router.get("/stock/alerts")
async def get_stock_alerts(is_resolved: bool = False):
    """Get all stock alerts"""
    alerts = await stock_alerts_col().find(
        {"is_resolved": is_resolved}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=200)
    
    return {
        "total": len(alerts),
        "alerts": alerts
    }

@router.put("/stock/alerts/{alert_id}/resolve")
async def resolve_stock_alert(alert_id: str, resolved_by: str, note: str = ""):
    """Resolve a stock alert"""
    await stock_alerts_col().update_one(
        {"id": alert_id},
        {"$set": {
            "is_resolved": True,
            "resolved_by": resolved_by,
            "resolved_note": note,
            "resolved_at": now_iso()
        }}
    )
    return {"message": "Alert resolved"}

# ==================== SPV MOVEMENT ALERTS ====================

@router.get("/spv/alerts")
async def get_spv_movement_alerts():
    """Get all SPV movement alerts"""
    today = get_wib_now().strftime("%Y-%m-%d")
    
    alerts = await alerts_col().find({
        "alert_type": "spv_movement",
        "created_at": {"$gte": f"{today}T00:00:00"}
    }, {"_id": 0}).sort("created_at", -1).to_list(length=100)
    
    return {
        "tanggal": today,
        "total": len(alerts),
        "alerts": alerts
    }
