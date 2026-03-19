# iPOS 5 Ultimate Adapter Service
# MAIN ORCHESTRATOR untuk Data Rescue Mission
# READ-ONLY - No write operations to source iPOS

import asyncio
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from .parser import IPOSBackupParser
from .staging import StagingService
from .mapping import MappingService
from .reconciliation import ReconciliationEngine

logger = logging.getLogger(__name__)


class IPOSAdapter:
    """
    Main orchestrator for iPOS 5 Ultimate data migration
    
    PIPELINE:
    1. Parse backup file (READ-ONLY)
    2. Stage data to MongoDB staging collections
    3. Map to OCB TITAN schema
    4. Run reconciliation against production data
    5. Generate reports
    
    RULES:
    - READ-ONLY access to source (iPOS backup)
    - All data goes through staging first
    - All operations are audit logged
    - All operations are tenant-aware (default: ocb_titan)
    - All operations are idempotent
    """
    
    DEFAULT_BACKUP_PATH = "/app/ipos_data/extracted/ipos_dump.sql"
    
    def __init__(self, tenant_id: str = "ocb_titan", backup_path: str = None):
        self.tenant_id = tenant_id
        self.backup_path = backup_path or self.DEFAULT_BACKUP_PATH
        
        # Initialize services
        self.parser = IPOSBackupParser(self.backup_path)
        self.staging = StagingService(tenant_id)
        self.mapping = MappingService()
        self.reconciliation = ReconciliationEngine(tenant_id)
        
        # State
        self.current_batch_id = None
        self.extraction_stats = {}
        self.staging_stats = {}
        self.reconciliation_results = {}
    
    # ============================================================
    # MAIN PIPELINE METHODS
    # ============================================================
    
    async def run_full_pipeline(self, user_id: str = "system") -> Dict:
        """
        Run complete data rescue pipeline:
        1. Extract from backup
        2. Stage to MongoDB
        3. Map to OCB TITAN schema
        4. Reconcile against production
        5. Generate report
        
        Returns:
            Complete pipeline result with all stats and findings
        """
        logger.info("=== STARTING FULL DATA RESCUE PIPELINE ===")
        logger.info(f"Tenant: {self.tenant_id}")
        logger.info(f"Backup: {self.backup_path}")
        
        pipeline_start = datetime.now(timezone.utc)
        result = {
            "tenant_id": self.tenant_id,
            "backup_path": self.backup_path,
            "started_at": pipeline_start.isoformat(),
            "status": "running",
            "steps": {}
        }
        
        try:
            # Step 1: Create batch
            batch = await self.staging.create_batch(
                source_file=self.backup_path,
                description="Full Data Rescue Pipeline",
                user_id=user_id
            )
            self.current_batch_id = batch["batch_id"]
            result["batch_id"] = self.current_batch_id
            logger.info(f"Created batch: {self.current_batch_id}")
            
            # Step 2: Extract from backup
            logger.info("Step 1: Extracting data from backup...")
            extraction = await self.extract_all()
            result["steps"]["extraction"] = extraction
            
            if extraction["status"] != "success":
                result["status"] = "failed"
                result["error"] = "Extraction failed"
                return result
            
            # Step 3: Stage data
            logger.info("Step 2: Staging data to MongoDB...")
            staging = await self.stage_all(extraction["data"])
            result["steps"]["staging"] = staging
            
            # Step 4: Reconciliation
            logger.info("Step 3: Running reconciliation...")
            recon = await self.run_reconciliation()
            result["steps"]["reconciliation"] = recon
            
            # Complete
            result["status"] = "completed"
            result["completed_at"] = datetime.now(timezone.utc).isoformat()
            result["duration_seconds"] = (datetime.now(timezone.utc) - pipeline_start).total_seconds()
            
            # Update batch status
            await self.staging.update_batch_status(
                self.current_batch_id,
                "completed",
                stats=result["steps"]
            )
            
            logger.info(f"=== PIPELINE COMPLETED in {result['duration_seconds']:.2f}s ===")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            
            if self.current_batch_id:
                await self.staging.update_batch_status(
                    self.current_batch_id,
                    "failed",
                    errors=[{"error": str(e)}]
                )
        
        return result
    
    async def extract_all(self) -> Dict:
        """Extract all data from iPOS backup"""
        try:
            # Load and parse backup
            if not self.parser.load():
                return {"status": "failed", "error": "Failed to load backup file"}
            
            # Extract all data
            data = self.parser.extract_all()
            
            # Calculate stats
            stats = {
                "file_info": data.get("file_info", {}),
                "counts": {}
            }
            
            for key, value in data.items():
                if key != "file_info" and isinstance(value, list):
                    stats["counts"][key] = len(value)
            
            self.extraction_stats = stats
            
            return {
                "status": "success",
                "data": data,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def stage_all(self, parsed_data: Dict) -> Dict:
        """Stage all parsed data to MongoDB staging collections"""
        try:
            stats = await self.staging.stage_all_from_parser(
                parsed_data,
                self.current_batch_id
            )
            
            self.staging_stats = stats
            
            return {
                "status": "success",
                "batch_id": self.current_batch_id,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Staging failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def run_reconciliation(self) -> Dict:
        """Run reconciliation against OCB TITAN production data"""
        try:
            # Run all reconciliation checks
            results = await self.reconciliation.run_full_reconciliation(
                self.current_batch_id
            )
            
            self.reconciliation_results = results
            
            return {
                "status": "success",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    # ============================================================
    # INDIVIDUAL EXTRACTION METHODS
    # ============================================================
    
    async def extract_items(self) -> Dict:
        """Extract only items from backup"""
        if not self.parser.content:
            self.parser.load()
        
        items = self.parser.extract_items()
        return {
            "status": "success",
            "count": len(items),
            "data": items
        }
    
    async def extract_stock(self) -> Dict:
        """Extract stock positions from backup"""
        if not self.parser.content:
            self.parser.load()
        
        stock = self.parser.extract_stock_positions()
        return {
            "status": "success",
            "count": len(stock),
            "data": stock
        }
    
    async def extract_sales(self) -> Dict:
        """Extract sales transactions from backup"""
        if not self.parser.content:
            self.parser.load()
        
        sales = self.parser.extract_sales()
        return {
            "status": "success",
            "headers_count": len(sales["headers"]),
            "details_count": len(sales["details"]),
            "data": sales
        }
    
    async def extract_purchases(self) -> Dict:
        """Extract purchase transactions from backup"""
        if not self.parser.content:
            self.parser.load()
        
        purchases = self.parser.extract_purchases()
        return {
            "status": "success",
            "headers_count": len(purchases["headers"]),
            "details_count": len(purchases["details"]),
            "data": purchases
        }
    
    async def extract_journals(self) -> Dict:
        """Extract journal entries from backup"""
        if not self.parser.content:
            self.parser.load()
        
        journals = self.parser.extract_journals()
        return {
            "status": "success",
            "count": len(journals),
            "data": journals
        }
    
    async def extract_accounts(self) -> Dict:
        """Extract chart of accounts from backup"""
        if not self.parser.content:
            self.parser.load()
        
        accounts = self.parser.extract_chart_of_accounts()
        return {
            "status": "success",
            "count": len(accounts),
            "data": accounts
        }
    
    # ============================================================
    # REPORTING METHODS
    # ============================================================
    
    async def get_summary(self) -> Dict:
        """Get complete summary of data rescue status"""
        staging_summary = await self.staging.get_staging_summary(self.current_batch_id)
        
        return {
            "tenant_id": self.tenant_id,
            "batch_id": self.current_batch_id,
            "backup_path": self.backup_path,
            "extraction_stats": self.extraction_stats,
            "staging_stats": self.staging_stats,
            "staging_summary": staging_summary,
            "reconciliation_results": self.reconciliation_results
        }
    
    async def generate_report(self, output_path: str = None) -> str:
        """Generate detailed report file"""
        report = {
            "report_type": "DATA_RESCUE_REPORT",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": await self.get_summary(),
            "reconciliation_details": self.reconciliation_results
        }
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report saved to: {output_path}")
        
        return json.dumps(report, indent=2, default=str)
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    def get_table_list(self) -> List[str]:
        """Get list of tables in backup"""
        if not self.parser.content:
            self.parser.load()
        return self.parser.get_available_tables()
    
    async def clear_staging(self, collection: str = None):
        """Clear staging data"""
        await self.staging.clear_staging(collection, self.current_batch_id)
    
    async def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        """Get audit logs"""
        return await self.staging.get_audit_logs(self.current_batch_id, limit)


# ============================================================
# CLI INTERFACE for direct execution
# ============================================================

async def main():
    """CLI entry point for data rescue"""
    import argparse
    
    parser_cli = argparse.ArgumentParser(description="iPOS 5 Data Rescue Tool")
    parser_cli.add_argument("--tenant", default="ocb_titan", help="Tenant ID")
    parser_cli.add_argument("--backup", default="/app/ipos_data/extracted/ipos_dump.sql", help="Backup file path")
    parser_cli.add_argument("--action", default="full", choices=["full", "extract", "stage", "reconcile", "report"])
    parser_cli.add_argument("--output", default="/app/reports/data_rescue_report.json", help="Report output path")
    
    args = parser_cli.parse_args()
    
    adapter = IPOSAdapter(tenant_id=args.tenant, backup_path=args.backup)
    
    if args.action == "full":
        result = await adapter.run_full_pipeline()
        print(json.dumps(result, indent=2, default=str))
    elif args.action == "extract":
        result = await adapter.extract_all()
        print(f"Extracted: {result['stats']['counts']}")
    elif args.action == "report":
        await adapter.generate_report(args.output)
        print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
