# OCB TITAN RETAIL AI SYSTEM - Main Server
# Enterprise-grade retail operating system for OCB GROUP

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
    title="OCB TITAN Retail AI System",
    description="Enterprise Retail Operating System for OCB GROUP",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
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

# Mount all routers under /api
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

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "system": "OCB TITAN Retail AI"}

@app.get("/api")
async def root():
    return {
        "system": "OCB TITAN Retail AI System",
        "version": "1.0.0",
        "company": "OCB GROUP",
        "status": "operational"
    }

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup():
    logger.info("OCB TITAN Retail AI System starting...")
    
    # Initialize database indexes
    from database import init_indexes
    await init_indexes()
    
    logger.info("OCB TITAN Retail AI System ready")

@app.on_event("shutdown")
async def shutdown():
    from database import client
    client.close()
    logger.info("OCB TITAN Retail AI System shutdown")
