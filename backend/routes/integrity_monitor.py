"""
OCB TITAN ERP - INTEGRITY MONITORING DASHBOARD
MASTER BLUEPRINT: Enterprise Hardening Phase - Guard System 6

Dashboard untuk monitoring:
- Journal balance (trial_balance_mismatch)
- Stock drift (inventory vs GL)
- Cash variance alerts
- System health & backup status
- Event queue status
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, List
from datetime import datetime, timezone, timedelta
from database import get_db
from utils.auth import get_current_user
import os
import json

router = APIRouter(prefix="/integrity", tags=["Integrity Monitoring Dashboard"])

# Configuration
BACKUP_DIR = "/app/backend/backups"
REPORTS_DIR = "/app/backend/scripts/audit_output"


class IntegrityMonitor:
    """System integrity monitoring engine"""
    
    def __init__(self, db):
        self.db = db
    
    async def check_journal_balance(self) -> Dict:
        """
        Check if all journals are balanced (SUM debit = SUM credit)
        Returns: status, details
        """
        pipeline = [
            {"$match": {"status": "posted"}},
            {"$project": {
                "journal_number": 1,
                "total_debit": 1,
                "total_credit": 1,
                "is_balanced": {
                    "$lte": [{"$abs": {"$subtract": ["$total_debit", "$total_credit"]}}, 0.01]
                }
            }},
            {"$match": {"is_balanced": False}}
        ]
        
        unbalanced = await self.db["journal_entries"].aggregate(pipeline).to_list(100)
        
        # Get totals
        total_pipeline = [
            {"$match": {"status": "posted"}},
            {"$unwind": "$entries"},
            {"$group": {
                "_id": None,
                "total_debit": {"$sum": "$entries.debit"},
                "total_credit": {"$sum": "$entries.credit"},
                "journal_count": {"$addToSet": "$journal_number"}
            }}
        ]
        
        totals_result = await self.db["journal_entries"].aggregate(total_pipeline).to_list(1)
        totals = totals_result[0] if totals_result else {"total_debit": 0, "total_credit": 0, "journal_count": []}
        
        diff = abs((totals.get("total_debit", 0) or 0) - (totals.get("total_credit", 0) or 0))
        
        return {
            "check": "journal_balance",
            "status": "PASS" if len(unbalanced) == 0 and diff < 1 else "FAIL",
            "total_debit": totals.get("total_debit", 0),
            "total_credit": totals.get("total_credit", 0),
            "difference": diff,
            "journal_count": len(totals.get("journal_count", [])),
            "unbalanced_count": len(unbalanced),
            "unbalanced_journals": [u["journal_number"] for u in unbalanced[:10]],
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_stock_drift(self) -> Dict:
        """
        Check if stock matches movement history (SSOT validation)
        Returns: status, discrepancies
        """
        # Get products with stock
        products = await self.db["products"].find(
            {"stock": {"$exists": True}},
            {"_id": 0, "id": 1, "name": 1, "sku": 1, "stock": 1}
        ).to_list(1000)
        
        discrepancies = []
        
        for product in products:
            product_id = product.get("id")
            stored_stock = product.get("stock", 0) or 0
            
            # Calculate from movements
            movement_pipeline = [
                {"$match": {"product_id": product_id}},
                {"$group": {
                    "_id": None,
                    "total_in": {"$sum": {"$cond": [{"$eq": ["$direction", "IN"]}, "$qty", 0]}},
                    "total_out": {"$sum": {"$cond": [{"$eq": ["$direction", "OUT"]}, "$qty", 0]}}
                }}
            ]
            
            movement_result = await self.db["stock_movements"].aggregate(movement_pipeline).to_list(1)
            
            if movement_result:
                calculated_stock = (movement_result[0].get("total_in", 0) or 0) - (movement_result[0].get("total_out", 0) or 0)
            else:
                calculated_stock = 0
            
            diff = stored_stock - calculated_stock
            if abs(diff) > 0:
                discrepancies.append({
                    "product_id": product_id,
                    "name": product.get("name"),
                    "sku": product.get("sku"),
                    "stored_stock": stored_stock,
                    "calculated_stock": calculated_stock,
                    "difference": diff
                })
        
        return {
            "check": "stock_drift",
            "status": "PASS" if len(discrepancies) == 0 else "FAIL",
            "products_checked": len(products),
            "discrepancies_found": len(discrepancies),
            "discrepancies": discrepancies[:20],  # Limit to 20
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_inventory_vs_gl(self) -> Dict:
        """
        Compare inventory valuation with GL account 1104
        """
        # Calculate inventory valuation
        inv_pipeline = [
            {"$match": {"stock": {"$gt": 0}}},
            {"$project": {
                "value": {"$multiply": [
                    {"$ifNull": ["$stock", 0]},
                    {"$ifNull": ["$cost_price", 0]}
                ]}
            }},
            {"$group": {
                "_id": None,
                "total_value": {"$sum": "$value"},
                "product_count": {"$sum": 1}
            }}
        ]
        
        inv_result = await self.db["products"].aggregate(inv_pipeline).to_list(1)
        inventory_value = inv_result[0].get("total_value", 0) if inv_result else 0
        
        # Get GL balance for inventory account
        gl_pipeline = [
            {"$match": {"status": "posted"}},
            {"$unwind": "$entries"},
            {"$match": {"entries.account_code": {"$regex": "^1104|^1-1400", "$options": "i"}}},
            {"$group": {
                "_id": None,
                "total_debit": {"$sum": "$entries.debit"},
                "total_credit": {"$sum": "$entries.credit"}
            }}
        ]
        
        gl_result = await self.db["journal_entries"].aggregate(gl_pipeline).to_list(1)
        if gl_result:
            gl_balance = (gl_result[0].get("total_debit", 0) or 0) - (gl_result[0].get("total_credit", 0) or 0)
        else:
            gl_balance = 0
        
        diff = inventory_value - gl_balance
        percentage = (diff / gl_balance * 100) if gl_balance != 0 else 0
        
        return {
            "check": "inventory_vs_gl",
            "status": "PASS" if abs(percentage) < 5 else "WARNING" if abs(percentage) < 10 else "FAIL",
            "inventory_value": inventory_value,
            "gl_balance": gl_balance,
            "difference": diff,
            "percentage_diff": round(percentage, 2),
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_cash_variance(self) -> Dict:
        """
        Check for recent cash variances
        """
        # Last 7 days
        date_from = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        
        variances = await self.db["cash_variances"].find(
            {"created_at": {"$gte": date_from}},
            {"_id": 0}
        ).sort("created_at", -1).limit(50).to_list(50)
        
        total_shortage = sum(v.get("variance", 0) for v in variances if v.get("variance", 0) < 0)
        total_overage = sum(v.get("variance", 0) for v in variances if v.get("variance", 0) > 0)
        
        # Pending discrepancies
        pending = await self.db["cash_discrepancies"].count_documents({"status": "pending"})
        
        return {
            "check": "cash_variance",
            "status": "PASS" if pending == 0 else "WARNING",
            "period_days": 7,
            "variance_count": len(variances),
            "total_shortage": total_shortage,
            "total_overage": total_overage,
            "net_variance": total_shortage + total_overage,
            "pending_discrepancies": pending,
            "recent_variances": variances[:10],
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_backup_status(self) -> Dict:
        """
        Check backup status and history
        """
        backups = []
        
        if os.path.exists(BACKUP_DIR):
            for f in os.listdir(BACKUP_DIR):
                if f.endswith(('.gz', '.dump', '.ocb', '.json')):
                    path = os.path.join(BACKUP_DIR, f)
                    stat = os.stat(path)
                    backups.append({
                        "filename": f,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / 1024 / 1024, 2),
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Check if recent backup exists (within 24 hours)
        has_recent = False
        if backups:
            latest_time = datetime.fromisoformat(backups[0]["created_at"])
            has_recent = (datetime.now() - latest_time).days < 1
        
        return {
            "check": "backup_status",
            "status": "PASS" if has_recent else "WARNING",
            "backup_count": len(backups),
            "latest_backup": backups[0] if backups else None,
            "has_recent_backup": has_recent,
            "backup_directory": BACKUP_DIR,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_event_queue(self) -> Dict:
        """
        Check event bus status
        """
        # Last hour
        date_from = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        
        # Count events by status
        pipeline = [
            {"$match": {"created_at": {"$gte": date_from}}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]
        
        results = await self.db["event_log"].aggregate(pipeline).to_list(10)
        status_counts = {r["_id"]: r["count"] for r in results}
        
        failed_count = status_counts.get("failed", 0)
        total_count = sum(status_counts.values())
        
        return {
            "check": "event_queue",
            "status": "PASS" if failed_count == 0 else "WARNING" if failed_count < 5 else "FAIL",
            "period_hours": 1,
            "total_events": total_count,
            "by_status": status_counts,
            "failed_count": failed_count,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_system_health(self) -> Dict:
        """
        Overall system health check
        """
        # Count key collections
        user_count = await self.db["users"].count_documents({"is_active": {"$ne": False}})
        product_count = await self.db["products"].count_documents({})
        journal_count = await self.db["journal_entries"].count_documents({"status": "posted"})
        sales_count = await self.db["sales"].count_documents({})
        
        return {
            "check": "system_health",
            "status": "PASS",
            "counts": {
                "active_users": user_count,
                "products": product_count,
                "posted_journals": journal_count,
                "sales": sales_count
            },
            "database": self.db.name,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def run_all_checks(self) -> Dict:
        """Run all integrity checks"""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant": self.db.name,
            "checks": []
        }
        
        # Run all checks
        results["checks"].append(await self.check_journal_balance())
        results["checks"].append(await self.check_stock_drift())
        results["checks"].append(await self.check_inventory_vs_gl())
        results["checks"].append(await self.check_cash_variance())
        results["checks"].append(await self.check_backup_status())
        results["checks"].append(await self.check_event_queue())
        results["checks"].append(await self.check_system_health())
        
        # Calculate overall status
        statuses = [c["status"] for c in results["checks"]]
        if "FAIL" in statuses:
            results["overall_status"] = "CRITICAL"
        elif "WARNING" in statuses:
            results["overall_status"] = "WARNING"
        else:
            results["overall_status"] = "HEALTHY"
        
        results["summary"] = {
            "total_checks": len(results["checks"]),
            "passed": sum(1 for s in statuses if s == "PASS"),
            "warnings": sum(1 for s in statuses if s == "WARNING"),
            "failed": sum(1 for s in statuses if s == "FAIL")
        }
        
        return results


# ==================== API ENDPOINTS ====================

@router.get("/dashboard")
async def get_integrity_dashboard(
    user: dict = Depends(get_current_user)
):
    """
    Get full integrity monitoring dashboard
    
    Returns all system integrity checks in one call
    """
    db = get_db()
    monitor = IntegrityMonitor(db)
    
    return await monitor.run_all_checks()


@router.get("/check/journal-balance")
async def check_journal_balance(
    user: dict = Depends(get_current_user)
):
    """Check if all journals are balanced"""
    db = get_db()
    monitor = IntegrityMonitor(db)
    return await monitor.check_journal_balance()


@router.get("/check/stock-drift")
async def check_stock_drift(
    user: dict = Depends(get_current_user)
):
    """Check for stock discrepancies (SSOT validation)"""
    db = get_db()
    monitor = IntegrityMonitor(db)
    return await monitor.check_stock_drift()


@router.get("/check/inventory-vs-gl")
async def check_inventory_vs_gl(
    user: dict = Depends(get_current_user)
):
    """Compare inventory valuation with GL"""
    db = get_db()
    monitor = IntegrityMonitor(db)
    return await monitor.check_inventory_vs_gl()


@router.get("/check/cash-variance")
async def check_cash_variance(
    user: dict = Depends(get_current_user)
):
    """Check for cash variances"""
    db = get_db()
    monitor = IntegrityMonitor(db)
    return await monitor.check_cash_variance()


@router.get("/check/backup-status")
async def check_backup_status(
    user: dict = Depends(get_current_user)
):
    """Check backup status"""
    db = get_db()
    monitor = IntegrityMonitor(db)
    return await monitor.check_backup_status()


@router.get("/check/event-queue")
async def check_event_queue(
    user: dict = Depends(get_current_user)
):
    """Check event bus status"""
    db = get_db()
    monitor = IntegrityMonitor(db)
    return await monitor.check_event_queue()


@router.get("/check/system-health")
async def check_system_health(
    user: dict = Depends(get_current_user)
):
    """Check overall system health"""
    db = get_db()
    monitor = IntegrityMonitor(db)
    return await monitor.check_system_health()


@router.post("/generate-report")
async def generate_integrity_report(
    user: dict = Depends(get_current_user)
):
    """Generate full integrity report and save to file"""
    db = get_db()
    monitor = IntegrityMonitor(db)
    
    results = await monitor.run_all_checks()
    
    # Save report
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # JSON
    json_path = f"{REPORTS_DIR}/integrity_monitor_report.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Markdown
    md_path = f"{REPORTS_DIR}/integrity_monitor_report.md"
    with open(md_path, "w") as f:
        f.write("# OCB TITAN - INTEGRITY MONITORING REPORT\n\n")
        f.write(f"**Generated:** {results['timestamp']}\n")
        f.write(f"**Tenant:** {results['tenant']}\n")
        f.write(f"**Overall Status:** {results['overall_status']}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- Total Checks: {results['summary']['total_checks']}\n")
        f.write(f"- Passed: {results['summary']['passed']}\n")
        f.write(f"- Warnings: {results['summary']['warnings']}\n")
        f.write(f"- Failed: {results['summary']['failed']}\n\n")
        
        f.write("## Check Results\n\n")
        for check in results['checks']:
            status_icon = "✅" if check['status'] == "PASS" else "⚠️" if check['status'] == "WARNING" else "❌"
            f.write(f"### {status_icon} {check['check'].replace('_', ' ').title()}\n\n")
            f.write(f"- **Status:** {check['status']}\n")
            for key, value in check.items():
                if key not in ['check', 'status', 'checked_at']:
                    f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
            f.write(f"- **Checked At:** {check['checked_at']}\n\n")
        
        f.write("---\n")
        f.write(f"*Report generated at {results['timestamp']}*\n")
    
    # Create audit log
    await db["audit_logs"].insert_one({
        "id": str(uuid.uuid4()) if 'uuid' in dir() else f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "tenant_id": db.name,
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "action": "INTEGRITY_REPORT_GENERATED",
        "module": "integrity_monitor",
        "entity_type": "report",
        "description": f"Integrity report generated: {results['overall_status']}",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "report": results,
        "files": {
            "json": json_path,
            "markdown": md_path
        }
    }


# Import uuid for audit log
import uuid
