"""
OCB TITAN ERP - PRODUCTION SCHEDULER
MASTER BLUEPRINT: Automated Task Scheduler

Runs scheduled tasks based on cron_config.yml:
- Stock Reconciliation (daily 02:00)
- Business Snapshot (daily 03:00)
- Database Backup (daily 01:00)
"""

import asyncio
import os
import yaml
import json
import subprocess
from datetime import datetime, timezone
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scheduler")

CONFIG_PATH = "/app/backend/config/cron_config.yml"
LOG_DIR = "/app/logs"
SCHEDULER_LOG = "/app/logs/scheduler_log.json"


class ProductionScheduler:
    def __init__(self):
        self.config = self.load_config()
        self.run_history = []
        os.makedirs(LOG_DIR, exist_ok=True)
    
    def load_config(self) -> Dict:
        """Load scheduler configuration"""
        if not os.path.exists(CONFIG_PATH):
            logger.warning(f"Config not found: {CONFIG_PATH}")
            return {}
        
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    
    def log_run(self, task_name: str, status: str, output: str = "", duration: float = 0):
        """Log task execution"""
        entry = {
            "task": task_name,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(duration, 2),
            "output": output[:500] if output else ""
        }
        self.run_history.append(entry)
        
        # Append to log file
        try:
            existing = []
            if os.path.exists(SCHEDULER_LOG):
                with open(SCHEDULER_LOG, "r") as f:
                    existing = json.load(f)
            
            existing.append(entry)
            
            # Keep last 1000 entries
            if len(existing) > 1000:
                existing = existing[-1000:]
            
            with open(SCHEDULER_LOG, "w") as f:
                json.dump(existing, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to write scheduler log: {e}")
    
    async def run_task(self, task_name: str, script: str, args: List[str] = None) -> Dict:
        """Run a scheduled task"""
        logger.info(f"Starting task: {task_name}")
        start_time = datetime.now()
        
        cmd_parts = ["python3", script]
        if args:
            cmd_parts.extend(args)
        
        cmd = " ".join(cmd_parts)
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                logger.info(f"Task {task_name} completed successfully in {duration:.2f}s")
                self.log_run(task_name, "SUCCESS", result.stdout, duration)
                return {
                    "task": task_name,
                    "status": "SUCCESS",
                    "duration": duration,
                    "output": result.stdout
                }
            else:
                logger.error(f"Task {task_name} failed: {result.stderr}")
                self.log_run(task_name, "FAILED", result.stderr, duration)
                return {
                    "task": task_name,
                    "status": "FAILED",
                    "duration": duration,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"Task {task_name} timed out")
            self.log_run(task_name, "TIMEOUT", "Task exceeded 1 hour timeout", 3600)
            return {
                "task": task_name,
                "status": "TIMEOUT",
                "error": "Exceeded 1 hour timeout"
            }
        except Exception as e:
            logger.error(f"Task {task_name} error: {e}")
            self.log_run(task_name, "ERROR", str(e), 0)
            return {
                "task": task_name,
                "status": "ERROR",
                "error": str(e)
            }
    
    async def run_stock_reconciliation(self) -> Dict:
        """Run stock reconciliation task"""
        task_config = self.config.get("stock_reconciliation", {})
        return await self.run_task(
            "stock_reconciliation",
            task_config.get("script", "/app/backend/scripts/stock_reconciliation_engine.py"),
            task_config.get("args", ["--all"])
        )
    
    async def run_business_snapshot(self) -> Dict:
        """Run business snapshot task"""
        task_config = self.config.get("business_snapshot", {})
        return await self.run_task(
            "business_snapshot",
            task_config.get("script", "/app/backend/scripts/business_snapshot_generator.py"),
            task_config.get("args", ["--tenant", "ocb_titan"])
        )
    
    async def run_database_backup(self) -> Dict:
        """Run database backup task"""
        task_config = self.config.get("database_backup", {})
        return await self.run_task(
            "database_backup",
            task_config.get("script", "/app/backend/scripts/backup_system.py"),
            task_config.get("args", ["--all-tenants"])
        )
    
    async def run_all_tasks(self) -> Dict:
        """Run all scheduled tasks (manual trigger)"""
        logger.info("Running all scheduled tasks")
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tasks": []
        }
        
        # Run in sequence
        results["tasks"].append(await self.run_database_backup())
        results["tasks"].append(await self.run_stock_reconciliation())
        results["tasks"].append(await self.run_business_snapshot())
        
        return results
    
    def get_schedule_status(self) -> Dict:
        """Get current schedule status"""
        return {
            "config": self.config,
            "last_runs": self.run_history[-10:] if self.run_history else [],
            "next_runs": {
                "database_backup": "01:00 daily",
                "stock_reconciliation": "02:00 daily",
                "business_snapshot": "03:00 daily"
            }
        }


# API Integration
scheduler = ProductionScheduler()


async def trigger_stock_reconciliation():
    """API trigger for stock reconciliation"""
    return await scheduler.run_stock_reconciliation()


async def trigger_business_snapshot():
    """API trigger for business snapshot"""
    return await scheduler.run_business_snapshot()


async def trigger_database_backup():
    """API trigger for database backup"""
    return await scheduler.run_database_backup()


async def get_scheduler_status():
    """Get scheduler status"""
    return scheduler.get_schedule_status()


if __name__ == "__main__":
    # Manual test run
    async def main():
        s = ProductionScheduler()
        result = await s.run_stock_reconciliation()
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())
