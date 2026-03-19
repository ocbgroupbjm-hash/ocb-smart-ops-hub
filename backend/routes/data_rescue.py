# iPOS Data Rescue API Routes
# Endpoints untuk Data Rescue Mission
# READ-ONLY operations from iPOS backup

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import json
import os
import logging

from services.ipos_adapter import IPOSAdapter, IPOSBackupParser, StagingService, ReconciliationEngine, IPOSDataImporter, HistoricalTransactionImporter
from middleware.tenant_isolation import get_current_tenant
from database import get_db

router = APIRouter(prefix="/api/data-rescue", tags=["Data Rescue"])
logger = logging.getLogger(__name__)

# Default backup path
DEFAULT_BACKUP_PATH = "/app/ipos_data/extracted/ipos_dump.sql"


# ============================================================
# EXTRACTION ENDPOINTS
# ============================================================

@router.get("/status")
async def get_rescue_status(tenant_id: str = Depends(get_current_tenant)):
    """Get current status of data rescue operations"""
    try:
        staging = StagingService(tenant_id)
        summary = await staging.get_staging_summary()
        
        # Get latest batch
        batches_coll = staging.db["ipos_import_batches"]
        latest_batch = await batches_coll.find_one(
            {"tenant_id": tenant_id},
            sort=[("created_at", -1)]
        )
        
        # Get latest reconciliation
        recon = ReconciliationEngine(tenant_id)
        latest_recon = await recon.get_latest_results()
        
        return {
            "status": "active",
            "tenant_id": tenant_id,
            "staging_summary": summary,
            "latest_batch": {
                "batch_id": latest_batch["batch_id"] if latest_batch else None,
                "status": latest_batch["status"] if latest_batch else None,
                "created_at": latest_batch["created_at"] if latest_batch else None
            } if latest_batch else None,
            "latest_reconciliation": {
                "timestamp": latest_recon["timestamp"] if latest_recon else None,
                "overall_status": latest_recon["overall_status"] if latest_recon else None
            } if latest_recon else None,
            "backup_path": DEFAULT_BACKUP_PATH,
            "backup_exists": os.path.exists(DEFAULT_BACKUP_PATH)
        }
    except Exception as e:
        logger.error(f"Error getting rescue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract")
async def start_extraction(
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant)
):
    """Start data extraction from iPOS backup (background task)"""
    try:
        adapter = IPOSAdapter(tenant_id=tenant_id, backup_path=DEFAULT_BACKUP_PATH)
        
        # Create batch first
        batch = await adapter.staging.create_batch(
            source_file=DEFAULT_BACKUP_PATH,
            description="Full Data Extraction",
            user_id="system"
        )
        
        # Run extraction in background
        async def run_extraction():
            try:
                result = await adapter.run_full_pipeline(user_id="system")
                logger.info(f"Extraction completed: {result['status']}")
            except Exception as e:
                logger.error(f"Background extraction failed: {e}")
        
        background_tasks.add_task(run_extraction)
        
        return {
            "status": "started",
            "batch_id": batch["batch_id"],
            "message": "Extraction started in background. Check status endpoint for progress."
        }
    except Exception as e:
        logger.error(f"Error starting extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extract/preview")
async def preview_extraction(
    table: str = Query(default="tbl_item", description="Table name to preview"),
    limit: int = Query(default=10, le=100),
    tenant_id: str = Depends(get_current_tenant)
):
    """Preview data from a specific table without staging"""
    try:
        parser = IPOSBackupParser(DEFAULT_BACKUP_PATH)
        parser.load()
        
        raw_data = parser.extract_table_data(table)
        
        return {
            "table": table,
            "total_rows": len(raw_data),
            "preview": raw_data[:limit],
            "available_tables": parser.get_available_tables()
        }
    except Exception as e:
        logger.error(f"Error previewing extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extract/tables")
async def list_available_tables(tenant_id: str = Depends(get_current_tenant)):
    """List all available tables in the backup"""
    try:
        parser = IPOSBackupParser(DEFAULT_BACKUP_PATH)
        parser.load()
        
        tables = parser.get_available_tables()
        critical = [t for t in parser.CRITICAL_TABLES if t in tables]
        
        return {
            "total_tables": len(tables),
            "critical_tables": critical,
            "all_tables": sorted(tables),
            "file_info": parser.get_file_info()
        }
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# STAGING ENDPOINTS
# ============================================================

@router.get("/staging/summary")
async def get_staging_summary(
    batch_id: Optional[str] = None,
    tenant_id: str = Depends(get_current_tenant)
):
    """Get summary of staged data"""
    try:
        staging = StagingService(tenant_id)
        summary = await staging.get_staging_summary(batch_id)
        
        return {
            "tenant_id": tenant_id,
            "batch_id": batch_id,
            "collections": summary
        }
    except Exception as e:
        logger.error(f"Error getting staging summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/staging/{collection}")
async def get_staged_data(
    collection: str,
    batch_id: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=500),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get staged records from a collection"""
    try:
        staging = StagingService(tenant_id)
        records = await staging.get_staged_records(collection, batch_id, skip, limit)
        
        return {
            "collection": collection,
            "skip": skip,
            "limit": limit,
            "count": len(records),
            "records": records
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting staged data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/staging/clear")
async def clear_staging(
    collection: Optional[str] = None,
    batch_id: Optional[str] = None,
    tenant_id: str = Depends(get_current_tenant)
):
    """Clear staging data"""
    try:
        staging = StagingService(tenant_id)
        await staging.clear_staging(collection, batch_id)
        
        return {
            "status": "cleared",
            "collection": collection or "all",
            "batch_id": batch_id
        }
    except Exception as e:
        logger.error(f"Error clearing staging: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# RECONCILIATION ENDPOINTS
# ============================================================

@router.post("/reconcile")
async def run_reconciliation(
    batch_id: Optional[str] = None,
    tenant_id: str = Depends(get_current_tenant)
):
    """Run full reconciliation against OCB TITAN production data"""
    try:
        recon = ReconciliationEngine(tenant_id)
        results = await recon.run_full_reconciliation(batch_id)
        
        return results
    except Exception as e:
        logger.error(f"Error running reconciliation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reconcile/latest")
async def get_latest_reconciliation(tenant_id: str = Depends(get_current_tenant)):
    """Get latest reconciliation results"""
    try:
        recon = ReconciliationEngine(tenant_id)
        results = await recon.get_latest_results()
        
        if not results:
            return {"status": "no_results", "message": "No reconciliation has been run yet"}
        
        return results
    except Exception as e:
        logger.error(f"Error getting reconciliation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reconcile/history")
async def get_reconciliation_history(
    limit: int = Query(default=10, le=50),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get reconciliation history"""
    try:
        recon = ReconciliationEngine(tenant_id)
        results = await recon.get_all_results(limit)
        
        return {
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error getting reconciliation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# BATCH ENDPOINTS
# ============================================================

@router.get("/batches")
async def list_batches(
    limit: int = Query(default=20, le=100),
    tenant_id: str = Depends(get_current_tenant)
):
    """List all import batches"""
    try:
        staging = StagingService(tenant_id)
        batches_coll = staging.db["ipos_import_batches"]
        
        cursor = batches_coll.find(
            {"tenant_id": tenant_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit)
        
        batches = await cursor.to_list(limit)
        
        return {
            "count": len(batches),
            "batches": batches
        }
    except Exception as e:
        logger.error(f"Error listing batches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batches/{batch_id}")
async def get_batch(batch_id: str, tenant_id: str = Depends(get_current_tenant)):
    """Get batch details"""
    try:
        staging = StagingService(tenant_id)
        batches_coll = staging.db["ipos_import_batches"]
        
        batch = await batches_coll.find_one(
            {"batch_id": batch_id, "tenant_id": tenant_id},
            {"_id": 0}
        )
        
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return batch
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# AUDIT LOG ENDPOINTS
# ============================================================

@router.get("/audit")
async def get_audit_logs(
    batch_id: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get audit logs"""
    try:
        staging = StagingService(tenant_id)
        logs = await staging.get_audit_logs(batch_id, limit)
        
        return {
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# REPORT ENDPOINTS
# ============================================================

@router.get("/report")
async def generate_report(tenant_id: str = Depends(get_current_tenant)):
    """Generate comprehensive data rescue report"""
    try:
        adapter = IPOSAdapter(tenant_id=tenant_id, backup_path=DEFAULT_BACKUP_PATH)
        
        # Get all data
        staging_summary = await adapter.staging.get_staging_summary()
        
        # Get latest reconciliation
        recon = ReconciliationEngine(tenant_id)
        latest_recon = await recon.get_latest_results()
        
        report = {
            "report_type": "DATA_RESCUE_REPORT",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "backup_file": DEFAULT_BACKUP_PATH,
            "staging_summary": staging_summary,
            "reconciliation": latest_recon,
            "recommendations": []
        }
        
        # Add recommendations based on reconciliation
        if latest_recon:
            summary = latest_recon.get("summary", {})
            report["recommendations"] = summary.get("recommendations", [])
            report["critical_issues"] = summary.get("critical_issues", [])
        
        return report
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# QUICK STATS ENDPOINTS (for Dashboard)
# ============================================================

@router.get("/stats/ipos")
async def get_ipos_stats(tenant_id: str = Depends(get_current_tenant)):
    """Get quick stats from iPOS backup (from staging)"""
    try:
        staging = StagingService(tenant_id)
        db = staging.db
        
        # Aggregate stock value
        stock_coll = db["ipos_stock_staging"]
        stock_pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": None,
                "total_qty": {"$sum": {"$toDouble": {"$ifNull": ["$data.quantity", 0]}}},
                "total_value": {
                    "$sum": {
                        "$multiply": [
                            {"$toDouble": {"$ifNull": ["$data.quantity", 0]}},
                            {"$toDouble": {"$ifNull": ["$data.hpp_base", 0]}}
                        ]
                    }
                }
            }}
        ]
        stock_result = await stock_coll.aggregate(stock_pipeline).to_list(1)
        
        # Aggregate sales
        sales_coll = db["ipos_sales_hd_staging"]
        sales_pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": None,
                "total_sales": {"$sum": {"$toDouble": {"$ifNull": ["$data.total", 0]}}},
                "count": {"$sum": 1}
            }}
        ]
        sales_result = await sales_coll.aggregate(sales_pipeline).to_list(1)
        
        # Aggregate purchases
        purchase_coll = db["ipos_purchase_hd_staging"]
        purchase_pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": None,
                "total_purchases": {"$sum": {"$toDouble": {"$ifNull": ["$data.total", 0]}}},
                "count": {"$sum": 1}
            }}
        ]
        purchase_result = await purchase_coll.aggregate(purchase_pipeline).to_list(1)
        
        # Aggregate journals
        journal_coll = db["ipos_journal_staging"]
        journal_pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": None,
                "total_debit": {"$sum": {"$toDouble": {"$ifNull": ["$data.debit", 0]}}},
                "total_credit": {"$sum": {"$toDouble": {"$ifNull": ["$data.credit", 0]}}},
                "count": {"$sum": 1}
            }}
        ]
        journal_result = await journal_coll.aggregate(journal_pipeline).to_list(1)
        
        return {
            "source": "IPOS5",
            "inventory": {
                "total_qty": stock_result[0]["total_qty"] if stock_result else 0,
                "total_value": stock_result[0]["total_value"] if stock_result else 0
            },
            "sales": {
                "total": sales_result[0]["total_sales"] if sales_result else 0,
                "count": sales_result[0]["count"] if sales_result else 0
            },
            "purchases": {
                "total": purchase_result[0]["total_purchases"] if purchase_result else 0,
                "count": purchase_result[0]["count"] if purchase_result else 0
            },
            "journals": {
                "total_debit": journal_result[0]["total_debit"] if journal_result else 0,
                "total_credit": journal_result[0]["total_credit"] if journal_result else 0,
                "balance": (journal_result[0]["total_debit"] - journal_result[0]["total_credit"]) if journal_result else 0,
                "count": journal_result[0]["count"] if journal_result else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting iPOS stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/comparison")
async def get_comparison_stats(tenant_id: str = Depends(get_current_tenant)):
    """Get comparison stats between iPOS and OCB TITAN"""
    try:
        # Get iPOS stats
        ipos_stats = await get_ipos_stats(tenant_id)
        
        # Get OCB TITAN stats (simplified)
        staging = StagingService(tenant_id)
        db = staging.db
        
        # TITAN inventory
        titan_inv = db["inventory"]
        titan_inv_pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": None,
                "total_qty": {"$sum": {"$ifNull": ["$quantity", 0]}},
                "total_value": {
                    "$sum": {
                        "$multiply": [
                            {"$ifNull": ["$quantity", 0]},
                            {"$ifNull": ["$unit_cost", {"$ifNull": ["$average_cost", 0]}]}
                        ]
                    }
                }
            }}
        ]
        titan_inv_result = await titan_inv.aggregate(titan_inv_pipeline).to_list(1)
        
        # TITAN sales
        titan_sales = db["sales"]
        titan_sales_count = await titan_sales.count_documents({"tenant_id": tenant_id})
        titan_sales_pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": None,
                "total": {"$sum": {"$ifNull": ["$grand_total", {"$ifNull": ["$total", 0]}]}}
            }}
        ]
        titan_sales_result = await titan_sales.aggregate(titan_sales_pipeline).to_list(1)
        
        comparison = {
            "inventory": {
                "ipos_value": ipos_stats["inventory"]["total_value"],
                "titan_value": titan_inv_result[0]["total_value"] if titan_inv_result else 0,
                "difference": ipos_stats["inventory"]["total_value"] - (titan_inv_result[0]["total_value"] if titan_inv_result else 0),
                "match": abs(ipos_stats["inventory"]["total_value"] - (titan_inv_result[0]["total_value"] if titan_inv_result else 0)) < 1000
            },
            "sales": {
                "ipos_total": ipos_stats["sales"]["total"],
                "titan_total": titan_sales_result[0]["total"] if titan_sales_result else 0,
                "difference": ipos_stats["sales"]["total"] - (titan_sales_result[0]["total"] if titan_sales_result else 0),
                "ipos_count": ipos_stats["sales"]["count"],
                "titan_count": titan_sales_count
            },
            "journals": {
                "ipos_balance": ipos_stats["journals"]["balance"],
                "status": "BALANCED" if abs(ipos_stats["journals"]["balance"]) < 0.01 else "UNBALANCED"
            }
        }
        
        return {
            "ipos": ipos_stats,
            "comparison": comparison,
            "overall_match": comparison["inventory"]["match"] and comparison["journals"]["status"] == "BALANCED"
        }
    except Exception as e:
        logger.error(f"Error getting comparison stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================
# IMPORT ENDPOINTS
# ============================================================

@router.post("/import/master-data")
async def import_master_data(
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant)
):
    """Import master data from staging to OCB TITAN production"""
    try:
        db = get_db()
        
        # Get staged data
        staging = StagingService(tenant_id)
        
        staged_data = {
            "chart_of_accounts": [],
            "categories": [],
            "warehouses": [],
            "items": [],
            "stock_positions": []
        }
        
        # Load from staging collections
        for coll_name in ["chart_of_accounts", "categories", "warehouses", "items", "stock_positions"]:
            coll = staging.COLLECTIONS.get(coll_name)
            if coll:
                cursor = db[coll].find({"tenant_id": tenant_id}, {"_id": 0})
                staged_data[coll_name] = await cursor.to_list(100000)
        
        logger.info(f"Loaded staged data: {[(k, len(v)) for k, v in staged_data.items()]}")
        
        # Run import
        importer = IPOSDataImporter(db, tenant_id)
        results = await importer.run_full_import(staged_data)
        
        return {
            "status": "completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error importing master data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/stock")
async def import_stock_data(tenant_id: str = Depends(get_current_tenant)):
    """Import stock positions with HPP from staging"""
    try:
        db = get_db()
        staging = StagingService(tenant_id)
        
        # Get staged stock
        stock_coll = staging.COLLECTIONS.get("stock_positions")
        cursor = db[stock_coll].find({"tenant_id": tenant_id}, {"_id": 0})
        staged_stocks = await cursor.to_list(100000)
        
        importer = IPOSDataImporter(db, tenant_id)
        results = await importer.import_stock_positions(staged_stocks)
        
        return {
            "status": "completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error importing stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import/validation")
async def validate_import(tenant_id: str = Depends(get_current_tenant)):
    """Validate import by comparing counts and totals"""
    try:
        db = get_db()
        staging = StagingService(tenant_id)
        
        validation = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "checks": {}
        }
        
        # Check products
        staged_items = await db[staging.COLLECTIONS["items"]].count_documents({"tenant_id": tenant_id})
        production_items = await db.products.count_documents({"tenant_id": tenant_id})
        validation["checks"]["products"] = {
            "staged": staged_items,
            "production": production_items,
            "match": staged_items == production_items
        }
        
        # Check accounts
        staged_accs = await db[staging.COLLECTIONS["chart_of_accounts"]].count_documents({"tenant_id": tenant_id})
        production_accs = await db.chart_of_accounts.count_documents({"tenant_id": tenant_id})
        validation["checks"]["accounts"] = {
            "staged": staged_accs,
            "production": production_accs,
            "match": staged_accs <= production_accs  # Production may have more
        }
        
        # Check stock positions
        staged_stock = await db[staging.COLLECTIONS["stock_positions"]].count_documents({"tenant_id": tenant_id})
        production_stock = await db.product_stocks.count_documents({})
        validation["checks"]["stock_positions"] = {
            "staged": staged_stock,
            "production": production_stock,
            "match": staged_stock <= production_stock
        }
        
        # Aggregate stock values
        staged_value_pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": None,
                "total_qty": {"$sum": {"$toDouble": {"$ifNull": ["$data.quantity", 0]}}},
                "total_value": {"$sum": {
                    "$multiply": [
                        {"$toDouble": {"$ifNull": ["$data.quantity", 0]}},
                        {"$toDouble": {"$ifNull": ["$data.hpp_base", 0]}}
                    ]
                }}
            }}
        ]
        staged_result = await db[staging.COLLECTIONS["stock_positions"]].aggregate(staged_value_pipeline).to_list(1)
        
        prod_value_pipeline = [
            {"$group": {
                "_id": None,
                "total_qty": {"$sum": "$quantity"},
                "total_value": {"$sum": "$total_value"}
            }}
        ]
        prod_result = await db.product_stocks.aggregate(prod_value_pipeline).to_list(1)
        
        validation["checks"]["inventory_value"] = {
            "staged": {
                "qty": staged_result[0]["total_qty"] if staged_result else 0,
                "value": staged_result[0]["total_value"] if staged_result else 0
            },
            "production": {
                "qty": prod_result[0]["total_qty"] if prod_result else 0,
                "value": prod_result[0]["total_value"] if prod_result else 0
            }
        }
        
        # Overall validation
        all_pass = all(c.get("match", False) for c in validation["checks"].values() if "match" in c)
        validation["overall_status"] = "PASS" if all_pass else "PENDING"
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# HISTORICAL TRANSACTION IMPORT ENDPOINTS
# ============================================================

@router.post("/import/historical/dry-run/sales")
async def dry_run_sales_import(tenant_id: str = Depends(get_current_tenant)):
    """
    DRY-RUN: Validate sales import without committing
    
    Simulates the import and reports:
    - Which transactions will be imported
    - Which transactions have validation issues
    - Expected effects (stock changes, journal entries, etc.)
    """
    try:
        # Enforce pilot tenant only
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Historical import only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.dry_run_sales_import()
        
        # Save dry-run report
        report_path = f"/app/test_reports/sales_dryrun_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        result["report_saved_to"] = report_path
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in sales dry-run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/historical/dry-run/purchases")
async def dry_run_purchases_import(tenant_id: str = Depends(get_current_tenant)):
    """
    DRY-RUN: Validate purchase import without committing
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Historical import only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.dry_run_purchase_import()
        
        # Save dry-run report
        report_path = f"/app/test_reports/purchase_dryrun_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        result["report_saved_to"] = report_path
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in purchase dry-run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/historical/execute/sales")
async def execute_sales_import(
    skip_stock_update: bool = Query(default=True, description="Skip stock update (already imported from iPOS)"),
    skip_journal: bool = Query(default=True, description="Skip journal creation (already in staging)"),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    COMMIT: Execute historical sales import
    
    WARNING: This will modify production data!
    
    Steps:
    1. Creates sales_invoices from iPOS staging
    2. Each invoice has import_batch_id for rollback tracking
    3. Skips transactions with missing products
    
    Args:
        skip_stock_update: Don't update stock (already imported from iPOS)
        skip_journal: Don't create journals (will import from iPOS journals)
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Historical import only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        # Execute import
        result = await importer.import_sales(
            skip_stock_update=skip_stock_update,
            skip_journal=skip_journal
        )
        
        # Save result report
        report_path = f"/app/test_reports/sales_import_{result['batch_id']}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        result["report_saved_to"] = report_path
        
        logger.info(f"Sales import completed: batch={result['batch_id']}, imported={result['imported']}, skipped={result['skipped']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing sales import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/historical/execute/purchases")
async def execute_purchases_import(
    skip_stock_update: bool = Query(default=True, description="Skip stock update (already imported from iPOS)"),
    skip_journal: bool = Query(default=True, description="Skip journal creation (already in staging)"),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    COMMIT: Execute historical purchase import
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Historical import only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.import_purchases(
            skip_stock_update=skip_stock_update,
            skip_journal=skip_journal
        )
        
        # Save result report
        report_path = f"/app/test_reports/purchase_import_{result['batch_id']}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        result["report_saved_to"] = report_path
        
        logger.info(f"Purchase import completed: batch={result['batch_id']}, imported={result['imported']}, skipped={result['skipped']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing purchase import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/historical/rollback/{batch_id}")
async def rollback_import_batch(
    batch_id: str,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    ROLLBACK: Undo an entire import batch
    
    Deletes all records that were created with the specified import_batch_id
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Rollback only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.rollback_batch(batch_id)
        
        logger.info(f"Rollback completed for batch {batch_id}: {result}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rolling back batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/historical/validate")
async def validate_historical_import(tenant_id: str = Depends(get_current_tenant)):
    """
    Validate historical import by comparing staging vs production
    
    Checks:
    - Sales count and total
    - Purchase count and total
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Validation only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.validate_import()
        
        # Save validation report
        report_path = f"/app/test_reports/historical_import_validation_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        result["report_saved_to"] = report_path
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import/historical/batches")
async def list_import_batches(
    limit: int = Query(default=20, le=100),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    List all historical import batches
    """
    try:
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        batches = await importer.get_import_batches(limit)
        
        return {
            "count": len(batches),
            "batches": batches
        }
        
    except Exception as e:
        logger.error(f"Error listing batches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import/historical/batches/{batch_id}")
async def get_import_batch_details(
    batch_id: str,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Get details of a specific import batch
    """
    try:
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        batch = await importer.get_batch_details(batch_id)
        
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return batch
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch details: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================
# JOURNAL IMPORT ENDPOINTS
# ============================================================

@router.post("/import/historical/dry-run/journals")
async def dry_run_journal_import(tenant_id: str = Depends(get_current_tenant)):
    """
    DRY-RUN: Validate journal import without committing
    
    Checks journal balance and counts
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Historical import only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.dry_run_journal_import()
        
        report_path = f"/app/test_reports/journal_dryrun_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        result["report_saved_to"] = report_path
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in journal dry-run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/historical/execute/journals")
async def execute_journal_import(
    batch_size: int = Query(default=5000, le=10000, description="Batch size for processing"),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    COMMIT: Execute historical journal import
    
    WARNING: This will import all journal entries from iPOS staging
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Historical import only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.import_journals(batch_size=batch_size)
        
        report_path = f"/app/test_reports/journal_import_{result['batch_id']}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        result["report_saved_to"] = report_path
        
        logger.info(f"Journal import completed: batch={result['batch_id']}, imported={result['imported']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing journal import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# AR/AP PAYMENT IMPORT ENDPOINTS
# ============================================================

@router.post("/import/historical/dry-run/ap-payments")
async def dry_run_ap_payment_import(tenant_id: str = Depends(get_current_tenant)):
    """
    DRY-RUN: Validate AP payment import
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Historical import only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.dry_run_ap_payment_import()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AP payment dry-run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/historical/dry-run/ar-payments")
async def dry_run_ar_payment_import(tenant_id: str = Depends(get_current_tenant)):
    """
    DRY-RUN: Validate AR payment import
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Historical import only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.dry_run_ar_payment_import()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AR payment dry-run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/historical/execute/ap-payments")
async def execute_ap_payment_import(tenant_id: str = Depends(get_current_tenant)):
    """
    COMMIT: Execute AP payment import
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Historical import only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.import_ap_payments()
        
        report_path = f"/app/test_reports/ap_payment_import_{result['batch_id']}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        result["report_saved_to"] = report_path
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing AP payment import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/historical/execute/ar-payments")
async def execute_ar_payment_import(tenant_id: str = Depends(get_current_tenant)):
    """
    COMMIT: Execute AR payment import
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Historical import only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.import_ar_payments()
        
        report_path = f"/app/test_reports/ar_payment_import_{result['batch_id']}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        result["report_saved_to"] = report_path
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing AR payment import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# FULL ACCOUNTING CHAIN VALIDATION
# ============================================================

@router.post("/import/historical/validate-full")
async def validate_full_accounting_chain(tenant_id: str = Depends(get_current_tenant)):
    """
    FULL VALIDATION: Verify complete accounting chain
    
    Validates:
    - Sales (count, total)
    - Purchases (count, total)
    - Journals (count, balance)
    - AP Payments (count)
    - AR Payments (count)
    """
    try:
        if tenant_id != "ocb_titan":
            raise HTTPException(
                status_code=403, 
                detail="Validation only allowed on pilot tenant: ocb_titan"
            )
        
        db = get_db()
        importer = HistoricalTransactionImporter(db, tenant_id)
        
        result = await importer.validate_full_accounting_chain()
        
        report_path = f"/app/test_reports/full_accounting_validation_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        result["report_saved_to"] = report_path
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating full accounting chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))
