# OCB TITAN AI - AI Fraud Detection System
# Deteksi kecurangan kasir dan stok hilang

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

router = APIRouter(prefix="/api/ai-fraud", tags=["AI Fraud Detection"])

def get_db():
    from database import get_db as db_get
    return db_get()

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# Collections
def sales_col():
    return get_db()['transactions']

def branches_col():
    return get_db()['branches']

def employees_col():
    return get_db()['employees']

def setoran_col():
    return get_db()['setoran_harian']

def selisih_col():
    return get_db()['selisih_kas']

def voids_col():
    return get_db()['void_transactions']

def refunds_col():
    return get_db()['refunds']

def inventory_col():
    return get_db()['inventory']

def stock_movements_col():
    return get_db()['stock_movements']

def opname_col():
    return get_db()['stock_opname']

def fraud_alerts_col():
    return get_db()['fraud_alerts']


# ==================== CASHIER FRAUD DETECTION ====================

@router.get("/cashier-risk")
async def detect_cashier_fraud(branch_id: Optional[str] = None, period: str = "30days"):
    """
    Deteksi potensi kecurangan kasir berdasarkan:
    - Minus kas berulang
    - Void transaksi berulang
    - Refund tidak wajar
    - Transaksi jam abnormal
    - Rasio pembatalan tinggi
    """
    today = datetime.now(timezone.utc).date()
    
    if period == "7days":
        start_date = today - timedelta(days=7)
    elif period == "30days":
        start_date = today - timedelta(days=30)
    elif period == "90days":
        start_date = today - timedelta(days=90)
    else:
        start_date = today - timedelta(days=30)
    
    # Get all cashiers/employees
    emp_query = {"status": "active"}
    if branch_id:
        emp_query["branch_id"] = branch_id
    
    employees = await employees_col().find(emp_query, {"_id": 0}).to_list(length=500)
    
    # Get selisih kas data
    selisih_query = {"tanggal": {"$gte": str(start_date)}}
    if branch_id:
        selisih_query["branch_id"] = branch_id
    
    selisih_data = await selisih_col().find(selisih_query, {"_id": 0}).to_list(length=10000)
    
    # Get void transactions
    void_data = await voids_col().find({
        "created_at": {"$gte": f"{start_date}T00:00:00"}
    }, {"_id": 0}).to_list(length=5000)
    
    # Get refunds
    refund_data = await refunds_col().find({
        "created_at": {"$gte": f"{start_date}T00:00:00"}
    }, {"_id": 0}).to_list(length=5000)
    
    # Get sales for ratio calculation
    sales_data = await sales_col().find({
        "created_at": {"$gte": f"{start_date}T00:00:00"}
    }, {"_id": 0}).to_list(length=50000)
    
    risk_analysis = []
    
    for emp in employees:
        emp_id = emp.get("id")
        emp_name = emp.get("name")
        emp_branch = emp.get("branch_name", "Unknown")
        
        # === MINUS KAS ANALYSIS ===
        emp_selisih = [s for s in selisih_data if s.get("penjaga_id") == emp_id]
        minus_count = len([s for s in emp_selisih if s.get("jenis") == "minus"])
        total_minus = sum(s.get("nominal", 0) for s in emp_selisih if s.get("jenis") == "minus")
        
        # === VOID ANALYSIS ===
        emp_voids = [v for v in void_data if v.get("cashier_id") == emp_id or v.get("created_by") == emp_id]
        void_count = len(emp_voids)
        total_void_amount = sum(v.get("amount", 0) for v in emp_voids)
        
        # === REFUND ANALYSIS ===
        emp_refunds = [r for r in refund_data if r.get("cashier_id") == emp_id or r.get("processed_by") == emp_id]
        refund_count = len(emp_refunds)
        total_refund_amount = sum(r.get("amount", 0) for r in emp_refunds)
        
        # === TRANSACTION ANALYSIS ===
        emp_sales = [s for s in sales_data if s.get("cashier_id") == emp_id or s.get("created_by") == emp_id]
        total_transactions = len(emp_sales)
        total_sales_amount = sum(s.get("total", 0) for s in emp_sales)
        
        # Abnormal hours transactions (before 6am or after 11pm)
        abnormal_hour_trans = 0
        for s in emp_sales:
            try:
                trans_time = s.get("created_at", "")
                if trans_time:
                    hour = int(trans_time[11:13])
                    if hour < 6 or hour > 23:
                        abnormal_hour_trans += 1
            except:
                pass
        
        # === RISK SCORING ===
        risk_score = 0
        indicators = []
        
        # Minus kas scoring
        if minus_count >= 5:
            risk_score += 35
            indicators.append(f"Minus kas {minus_count}x (Rp {total_minus:,.0f})")
        elif minus_count >= 3:
            risk_score += 25
            indicators.append(f"Minus kas {minus_count}x (Rp {total_minus:,.0f})")
        elif minus_count >= 1:
            risk_score += 10
            indicators.append(f"Minus kas {minus_count}x")
        
        # Void ratio scoring
        if total_transactions > 0:
            void_ratio = (void_count / total_transactions) * 100
            if void_ratio > 10:
                risk_score += 30
                indicators.append(f"Void ratio tinggi: {void_ratio:.1f}%")
            elif void_ratio > 5:
                risk_score += 15
                indicators.append(f"Void ratio moderate: {void_ratio:.1f}%")
        
        # Refund scoring
        if total_transactions > 0:
            refund_ratio = (refund_count / total_transactions) * 100
            if refund_ratio > 5:
                risk_score += 20
                indicators.append(f"Refund ratio tinggi: {refund_ratio:.1f}%")
            elif refund_ratio > 2:
                risk_score += 10
                indicators.append(f"Refund ratio: {refund_ratio:.1f}%")
        
        # Abnormal hours
        if abnormal_hour_trans > 5:
            risk_score += 20
            indicators.append(f"Transaksi jam abnormal: {abnormal_hour_trans}x")
        elif abnormal_hour_trans > 0:
            risk_score += 5
            indicators.append(f"Transaksi jam abnormal: {abnormal_hour_trans}x")
        
        # Large void amounts
        if total_void_amount > 1000000:
            risk_score += 15
            indicators.append(f"Total void besar: Rp {total_void_amount:,.0f}")
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "KRITIS"
            risk_color = "red"
            recommendation = "INVESTIGASI SEGERA - Pertimbangkan suspend"
        elif risk_score >= 50:
            risk_level = "TINGGI"
            risk_color = "orange"
            recommendation = "Perlu investigasi mendalam"
        elif risk_score >= 30:
            risk_level = "SEDANG"
            risk_color = "yellow"
            recommendation = "Monitor ketat, verifikasi manual"
        else:
            risk_level = "RENDAH"
            risk_color = "green"
            recommendation = "Dalam batas normal"
        
        # Only include if has transactions or issues
        if total_transactions > 0 or risk_score > 0:
            risk_analysis.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "branch_name": emp_branch,
                "metrics": {
                    "total_transactions": total_transactions,
                    "total_sales": total_sales_amount,
                    "minus_count": minus_count,
                    "total_minus": total_minus,
                    "void_count": void_count,
                    "total_void": total_void_amount,
                    "refund_count": refund_count,
                    "total_refund": total_refund_amount,
                    "abnormal_hour_transactions": abnormal_hour_trans
                },
                "risk_score": min(100, risk_score),
                "risk_level": risk_level,
                "risk_color": risk_color,
                "indicators": indicators,
                "recommendation": recommendation
            })
    
    # Sort by risk (highest first)
    risk_analysis.sort(key=lambda x: x["risk_score"], reverse=True)
    
    # Summary
    summary = {
        "total_analyzed": len(risk_analysis),
        "kritis_count": len([r for r in risk_analysis if r["risk_level"] == "KRITIS"]),
        "tinggi_count": len([r for r in risk_analysis if r["risk_level"] == "TINGGI"]),
        "sedang_count": len([r for r in risk_analysis if r["risk_level"] == "SEDANG"]),
        "rendah_count": len([r for r in risk_analysis if r["risk_level"] == "RENDAH"])
    }
    
    # Aggregate by branch
    branch_summary = {}
    for r in risk_analysis:
        br = r["branch_name"]
        if br not in branch_summary:
            branch_summary[br] = {"high_risk_count": 0, "total_risk_score": 0}
        if r["risk_level"] in ["KRITIS", "TINGGI"]:
            branch_summary[br]["high_risk_count"] += 1
        branch_summary[br]["total_risk_score"] += r["risk_score"]
    
    high_risk_branches = [
        {"branch": k, **v} for k, v in branch_summary.items() if v["high_risk_count"] > 0
    ]
    high_risk_branches.sort(key=lambda x: x["high_risk_count"], reverse=True)
    
    return {
        "period": period,
        "summary": summary,
        "high_risk_branches": high_risk_branches[:5],
        "employees": risk_analysis[:50],  # Top 50
        "generated_at": now_iso()
    }


# ==================== MISSING STOCK DETECTION ====================

@router.get("/missing-stock")
async def detect_missing_stock(branch_id: Optional[str] = None, period: str = "30days"):
    """
    Deteksi potensi stok hilang berdasarkan:
    - Selisih opname
    - Mutasi stok abnormal
    - Stok keluar tanpa penjualan
    - Item hilang berulang
    """
    today = datetime.now(timezone.utc).date()
    
    if period == "7days":
        start_date = today - timedelta(days=7)
    elif period == "30days":
        start_date = today - timedelta(days=30)
    elif period == "90days":
        start_date = today - timedelta(days=90)
    else:
        start_date = today - timedelta(days=30)
    
    # Get opname data
    opname_query = {"opname_date": {"$gte": str(start_date)}}
    if branch_id:
        opname_query["branch_id"] = branch_id
    
    opname_data = await opname_col().find(opname_query, {"_id": 0}).to_list(length=5000)
    
    # Get stock movements
    movement_query = {"created_at": {"$gte": f"{start_date}T00:00:00"}}
    if branch_id:
        movement_query["branch_id"] = branch_id
    
    movements = await stock_movements_col().find(movement_query, {"_id": 0}).to_list(length=10000)
    
    # Get branches
    branches = await branches_col().find({"is_active": True}, {"_id": 0}).to_list(length=100)
    
    # Analyze by product/branch
    item_analysis = {}
    
    # Process opname differences
    for op in opname_data:
        items = op.get("items", [])
        br_id = op.get("branch_id", "")
        br_name = op.get("branch_name", "Unknown")
        
        for item in items:
            prod_id = item.get("product_id")
            prod_name = item.get("product_name", "Unknown")
            system_qty = item.get("system_quantity", 0)
            actual_qty = item.get("actual_quantity", 0)
            difference = actual_qty - system_qty
            
            if difference < 0:  # Stock missing
                key = f"{prod_id}_{br_id}"
                
                if key not in item_analysis:
                    item_analysis[key] = {
                        "product_id": prod_id,
                        "product_name": prod_name,
                        "branch_id": br_id,
                        "branch_name": br_name,
                        "total_missing": 0,
                        "missing_incidents": 0,
                        "estimated_loss": 0,
                        "incidents": []
                    }
                
                item_analysis[key]["total_missing"] += abs(difference)
                item_analysis[key]["missing_incidents"] += 1
                item_analysis[key]["estimated_loss"] += abs(difference) * item.get("cost_price", 0)
                item_analysis[key]["incidents"].append({
                    "date": op.get("opname_date"),
                    "missing_qty": abs(difference),
                    "system": system_qty,
                    "actual": actual_qty
                })
    
    # Convert to list and analyze risk
    stock_risks = []
    
    for key, data in item_analysis.items():
        risk_score = 0
        indicators = []
        
        # Frequency scoring
        if data["missing_incidents"] >= 3:
            risk_score += 40
            indicators.append(f"Hilang {data['missing_incidents']}x dalam periode")
        elif data["missing_incidents"] >= 2:
            risk_score += 25
            indicators.append(f"Hilang {data['missing_incidents']}x")
        else:
            risk_score += 10
        
        # Quantity scoring
        if data["total_missing"] >= 50:
            risk_score += 30
            indicators.append(f"Total {data['total_missing']} unit hilang")
        elif data["total_missing"] >= 20:
            risk_score += 20
            indicators.append(f"Total {data['total_missing']} unit hilang")
        elif data["total_missing"] >= 5:
            risk_score += 10
        
        # Value scoring
        if data["estimated_loss"] >= 5000000:
            risk_score += 30
            indicators.append(f"Kerugian estimasi Rp {data['estimated_loss']:,.0f}")
        elif data["estimated_loss"] >= 1000000:
            risk_score += 20
            indicators.append(f"Kerugian estimasi Rp {data['estimated_loss']:,.0f}")
        
        # Determine status
        if risk_score >= 70:
            status = "KRITIS"
            status_color = "red"
            recommendation = "INVESTIGASI SEGERA - Kemungkinan pencurian"
        elif risk_score >= 50:
            status = "TINGGI"
            status_color = "orange"
            recommendation = "Audit stok dan CCTV"
        elif risk_score >= 30:
            status = "WARNING"
            status_color = "yellow"
            recommendation = "Monitor dan verifikasi prosedur"
        else:
            status = "NORMAL"
            status_color = "green"
            recommendation = "Dalam batas toleransi"
        
        stock_risks.append({
            **data,
            "risk_score": min(100, risk_score),
            "status": status,
            "status_color": status_color,
            "indicators": indicators,
            "recommendation": recommendation
        })
    
    # Sort by risk
    stock_risks.sort(key=lambda x: x["risk_score"], reverse=True)
    
    # Branch summary
    branch_loss = {}
    for sr in stock_risks:
        br = sr["branch_name"]
        if br not in branch_loss:
            branch_loss[br] = {"total_loss": 0, "item_count": 0, "high_risk_count": 0}
        branch_loss[br]["total_loss"] += sr["estimated_loss"]
        branch_loss[br]["item_count"] += 1
        if sr["status"] in ["KRITIS", "TINGGI"]:
            branch_loss[br]["high_risk_count"] += 1
    
    risky_branches = [
        {"branch": k, **v} for k, v in branch_loss.items()
    ]
    risky_branches.sort(key=lambda x: x["total_loss"], reverse=True)
    
    return {
        "period": period,
        "summary": {
            "total_items_analyzed": len(stock_risks),
            "kritis_count": len([s for s in stock_risks if s["status"] == "KRITIS"]),
            "tinggi_count": len([s for s in stock_risks if s["status"] == "TINGGI"]),
            "total_estimated_loss": sum(s["estimated_loss"] for s in stock_risks)
        },
        "risky_branches": risky_branches[:5],
        "items": stock_risks[:30],  # Top 30
        "generated_at": now_iso()
    }


# ==================== FRAUD ALERT MANAGEMENT ====================

@router.post("/alert")
async def create_fraud_alert(
    alert_type: str,  # cashier_fraud, missing_stock
    target_id: str,  # employee_id or product_id
    target_name: str,
    branch_id: str,
    branch_name: str,
    severity: str,  # low, medium, high, critical
    description: str,
    evidence: dict = {}
):
    """Create a fraud alert for investigation"""
    alert = {
        "id": gen_id(),
        "alert_type": alert_type,
        "target_id": target_id,
        "target_name": target_name,
        "branch_id": branch_id,
        "branch_name": branch_name,
        "severity": severity,
        "description": description,
        "evidence": evidence,
        "status": "open",  # open, investigating, resolved, closed
        "assigned_to": "",
        "resolution": "",
        "created_at": now_iso(),
        "updated_at": now_iso()
    }
    
    await fraud_alerts_col().insert_one(alert)
    
    return {"message": "Alert berhasil dibuat", "alert_id": alert["id"]}


@router.get("/alerts")
async def get_fraud_alerts(
    status: Optional[str] = None,
    alert_type: Optional[str] = None,
    branch_id: Optional[str] = None,
    limit: int = 50
):
    """Get fraud alerts"""
    query = {}
    if status:
        query["status"] = status
    if alert_type:
        query["alert_type"] = alert_type
    if branch_id:
        query["branch_id"] = branch_id
    
    alerts = await fraud_alerts_col().find(query, {"_id": 0}).sort("created_at", -1).to_list(length=limit)
    
    return {
        "alerts": alerts,
        "total": len(alerts),
        "summary": {
            "open": len([a for a in alerts if a.get("status") == "open"]),
            "investigating": len([a for a in alerts if a.get("status") == "investigating"]),
            "resolved": len([a for a in alerts if a.get("status") == "resolved"])
        }
    }


@router.put("/alerts/{alert_id}/status")
async def update_alert_status(
    alert_id: str,
    status: str,
    assigned_to: str = "",
    resolution: str = ""
):
    """Update fraud alert status"""
    update_data = {
        "status": status,
        "updated_at": now_iso()
    }
    
    if assigned_to:
        update_data["assigned_to"] = assigned_to
    if resolution:
        update_data["resolution"] = resolution
        update_data["resolved_at"] = now_iso()
    
    await fraud_alerts_col().update_one({"id": alert_id}, {"$set": update_data})
    
    return {"message": "Status alert berhasil diupdate"}


# ==================== DASHBOARD SUMMARY ====================

@router.get("/dashboard")
async def get_fraud_dashboard():
    """Get fraud detection dashboard summary"""
    today = datetime.now(timezone.utc).date()
    month_ago = today - timedelta(days=30)
    
    # Get recent alerts
    recent_alerts = await fraud_alerts_col().find({
        "created_at": {"$gte": f"{month_ago}T00:00:00"},
        "status": {"$in": ["open", "investigating"]}
    }, {"_id": 0}).sort("created_at", -1).to_list(length=10)
    
    # Get cashier risk summary (top 5)
    cashier_risk = await detect_cashier_fraud(period="30days")
    top_risk_cashiers = cashier_risk.get("employees", [])[:5]
    
    # Get stock risk summary (top 5)
    stock_risk = await detect_missing_stock(period="30days")
    top_risk_items = stock_risk.get("items", [])[:5]
    
    return {
        "recent_alerts": recent_alerts,
        "top_risk_cashiers": top_risk_cashiers,
        "top_risk_items": top_risk_items,
        "cashier_summary": cashier_risk.get("summary", {}),
        "stock_summary": stock_risk.get("summary", {}),
        "high_risk_branches": cashier_risk.get("high_risk_branches", [])[:3],
        "generated_at": now_iso()
    }
