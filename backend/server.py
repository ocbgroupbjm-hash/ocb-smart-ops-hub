# OCB GROUP SUPER AI OPERATING SYSTEM
# Enterprise AI System untuk OCB GROUP
# Sales, CRM, ERP, Marketing, CFO, Warroom

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create app
app = FastAPI(
    title="OCB GROUP SUPER AI OPERATING SYSTEM",
    description="Enterprise AI System - Sales, CRM, ERP, Marketing, CFO, Warroom",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers - Core ERP
from routes.auth import router as auth_router
from routes.products import router as products_router
from routes.pos import router as pos_router
from routes.inventory import router as inventory_router
from routes.master_data import router as master_data_router
from routes.purchase import router as purchase_router
from routes.finance import router as finance_router
from routes.dashboard import router as dashboard_router
from routes.users import router as users_router
from routes.reports import router as reports_router
from routes.roles import router as roles_router
from routes.ai_business import router as ai_business_router
from routes.hallo_ai import router as hallo_ai_router
from routes.master_erp import router as master_erp_router
from routes.settings import router as settings_router
from routes.accounting import router as accounting_router
from routes.backup import router as backup_router
from routes.print_settings import router as print_router
from routes.serial_number import router as serial_router
from routes.assembly import router as assembly_router
from routes.business import router as business_router

# Import Account Settings router
from routes.account_settings import router as account_settings_router

# Import SUPER AI routers
from routes.ai_sales import router as ai_sales_router
from routes.warroom import router as warroom_router
from routes.stock_monitor import router as stock_monitor_router
from routes.ai_cfo import router as ai_cfo_router
from routes.ai_marketing import router as ai_marketing_router
from routes.whatsapp_webhook import router as whatsapp_webhook_router

# Import SUPER ERP routers
from routes.erp_operations import router as erp_operations_router
from routes.attendance import router as attendance_router
from routes.payroll import router as payroll_router
from routes.war_room_v2 import router as war_room_v2_router
from routes.erp_reports import router as erp_reports_router

# Import OCB TITAN AI routers
from routes.global_map import router as global_map_router
from routes.data_export import router as data_export_router
from routes.kpi_performance import router as kpi_router
from routes.ai_command_center import router as ai_command_router
from routes.crm_ai import router as crm_ai_router
from routes.attendance_advanced import router as attendance_v2_router

# Import OCB TITAN AI Phase 2 routers
from routes.export_advanced import router as export_advanced_router
from routes.import_system import router as import_system_router
from routes.file_upload import router as file_upload_router
from routes.whatsapp_alerts import router as whatsapp_alerts_router
from routes.warroom_alerts import router as warroom_alerts_router
from routes.hr_advanced import router as hr_advanced_router

# Import OCB TITAN AI Phase 3 routers - AI Super War Room
from routes.ai_store_prediction import router as ai_store_router
from routes.ai_fraud_detection import router as ai_fraud_router
from routes.payroll_files import router as payroll_files_router
from routes.ai_warroom import router as ai_warroom_router

# Import OCB TITAN AI Phase 4 routers - Payroll & Performance
from routes.payroll_auto import router as payroll_auto_router
from routes.ai_employee_performance import router as ai_employee_router
from routes.seed_data import router as seed_data_router
from routes.audit_data import router as audit_data_router
from routes.branch_stock import router as branch_stock_router
from routes.ai_photo_studio import router as ai_photo_router
from routes.stock_card import router as stock_card_router
from routes.ssot_service import router as ssot_router
from routes.rbac_system import router as rbac_router
from routes.pricing_system import router as pricing_router
from routes.deposit_system import router as deposit_router

# Import AR/AP and Accounting Engine routers
from routes.ar_system import router as ar_router
from routes.ap_system import router as ap_router
from routes.approval_engine import router as approval_router
from routes.accounting_engine import router as accounting_engine_router

# Import Sales Module - iPOS Style (Enterprise Sales)
from routes.sales_module import router as sales_module_router

# Import Number Settings Module - Central Engine for Auto Numbering
from routes.number_settings import router as number_settings_router

# Mount all routers under /api - Core ERP
app.include_router(auth_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(pos_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(master_data_router, prefix="/api")
app.include_router(purchase_router, prefix="/api")
app.include_router(finance_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(roles_router, prefix="/api")
app.include_router(ai_business_router, prefix="/api")
app.include_router(hallo_ai_router, prefix="/api")
app.include_router(master_erp_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(accounting_router)
app.include_router(backup_router)
app.include_router(print_router)
app.include_router(serial_router)
app.include_router(assembly_router)
app.include_router(business_router)

# Mount SUPER AI routers
app.include_router(ai_sales_router)
app.include_router(warroom_router)
app.include_router(stock_monitor_router)
app.include_router(ai_cfo_router)
app.include_router(ai_marketing_router)
app.include_router(whatsapp_webhook_router)

# Mount SUPER ERP routers
app.include_router(erp_operations_router)
app.include_router(attendance_router)
app.include_router(payroll_router)
app.include_router(war_room_v2_router)
app.include_router(erp_reports_router)

# Mount OCB TITAN AI routers
app.include_router(global_map_router)
app.include_router(data_export_router)
app.include_router(kpi_router)
app.include_router(ai_command_router)
app.include_router(crm_ai_router)
app.include_router(attendance_v2_router)

# Mount OCB TITAN AI Phase 2 routers
app.include_router(export_advanced_router)
app.include_router(import_system_router)
app.include_router(file_upload_router)
app.include_router(whatsapp_alerts_router)
app.include_router(warroom_alerts_router)
app.include_router(hr_advanced_router)

# Mount OCB TITAN AI Phase 3 routers
app.include_router(ai_store_router)
app.include_router(ai_fraud_router)
app.include_router(payroll_files_router)
app.include_router(ai_warroom_router)

# Mount OCB TITAN AI Phase 4 routers
app.include_router(payroll_auto_router)
app.include_router(ai_employee_router)
app.include_router(seed_data_router)
app.include_router(audit_data_router)
app.include_router(branch_stock_router, prefix="/api")
app.include_router(ai_photo_router)
app.include_router(stock_card_router)
app.include_router(ssot_router)
app.include_router(rbac_router)
app.include_router(pricing_router)
app.include_router(deposit_router)

# Mount AR/AP and Accounting Engine routers
app.include_router(ar_router)
app.include_router(ap_router)
app.include_router(approval_router)
app.include_router(accounting_engine_router)

# Mount Sales Module - iPOS Style (Enterprise Sales)
app.include_router(sales_module_router)

# Mount Number Settings Module
app.include_router(number_settings_router)

# Mount Account Settings Module - iPOS Style
app.include_router(account_settings_router)

# Mount ERP Hardening Module - Fiscal Period & Multi-Currency
from routes.erp_hardening import router as erp_hardening_router
app.include_router(erp_hardening_router)

# Mount Phase 2 Financial Control Modules
from routes.tax_engine import router as tax_engine_router
from routes.consistency_checker import router as consistency_checker_router
from routes.auto_journal_engine import router as auto_journal_engine_router
from routes.reconciliation_engine import router as reconciliation_router
app.include_router(tax_engine_router)
app.include_router(consistency_checker_router)
app.include_router(auto_journal_engine_router)
app.include_router(reconciliation_router)

# Mount Phase 3 Operational Control Modules
from routes.approval_workflow import router as approval_workflow_router
app.include_router(approval_workflow_router)

from routes.credit_control import router as credit_control_router
app.include_router(credit_control_router)

from routes.stock_reorder import router as stock_reorder_router
app.include_router(stock_reorder_router)

from routes.warehouse_control import router as warehouse_control_router
app.include_router(warehouse_control_router)

from routes.purchase_planning import router as purchase_planning_router
app.include_router(purchase_planning_router)

from routes.sales_target import router as sales_target_router
app.include_router(sales_target_router)

# Phase 3 Module 6: Commission Engine
from routes.commission_engine import router as commission_router
app.include_router(commission_router)

# Phase 3 Module 7: Deposit & Cash Control Enhancement
from routes.cash_control import router as cash_control_router
app.include_router(cash_control_router)

# Phase 4: Report Center
from routes.report_center import router as report_center_router
app.include_router(report_center_router)

# Phase 5: KPI System
from routes.kpi_system import router as kpi_system_router
app.include_router(kpi_system_router)

# Phase 5: Master Advanced (Customer, Discount, Promotion, Barcode)
from routes.master_advanced import router as master_advanced_router
app.include_router(master_advanced_router)

# Health check
@app.get("/api/health")
async def health_check():
    from database import get_active_db_name
    return {
        "status": "healthy", 
        "system": "OCB GROUP SUPER AI OPERATING SYSTEM",
        "active_database": get_active_db_name(),
        "modules": [
            "AI Sales", "AI CFO", "AI Marketing", 
            "Warroom", "Stock Monitor", "ERP"
        ]
    }

@app.get("/api")
async def root():
    return {
        "system": "OCB AI TITAN",
        "description": "Enterprise Retail AI System",
        "version": "2.0.0",
        "company": "OCB GROUP",
        "status": "operational",
        "ai_capabilities": [
            "CEO AI - Strategic Analysis",
            "CFO AI - Financial Analysis",
            "COO AI - Operations Monitoring",
            "CMO AI - Marketing Intelligence",
            "Sales AI - Upselling & Cross-selling",
            "Customer Service AI - Customer Support",
            "Business Analyst AI - Data Analytics"
        ]
    }

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup():
    logger.info("OCB AI TITAN - Enterprise Retail AI System starting...")
    
    # Initialize database indexes
    from database import init_indexes
    await init_indexes()
    
    logger.info("OCB AI TITAN ready - All AI capabilities online")

@app.on_event("shutdown")
async def shutdown():
    from database import client
    client.close()
    logger.info("OCB AI TITAN shutdown")
