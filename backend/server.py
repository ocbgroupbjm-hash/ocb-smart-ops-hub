from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app
app = FastAPI(title="AI Business OS", version="1.0.0")

# Create API router
api_router = APIRouter(prefix="/api")

# Import routes
from routes import auth, ai_chat, crm, branches, knowledge, analytics

# Import OCB AI routes
try:
    from routes_ocb import pos_products, pos_transactions, attendance, kpi
    OCB_ROUTES_AVAILABLE = True
except ImportError:
    OCB_ROUTES_AVAILABLE = False

# Include routers
api_router.include_router(auth.router)
api_router.include_router(ai_chat.router)
api_router.include_router(crm.router)
api_router.include_router(branches.router)
api_router.include_router(knowledge.router)
api_router.include_router(analytics.router)

# Include OCB AI routers if available
if OCB_ROUTES_AVAILABLE:
    api_router.include_router(pos_products.router)
    api_router.include_router(pos_transactions.router)
    api_router.include_router(attendance.router)
    api_router.include_router(kpi.router)

# Health check
@api_router.get("/")
async def root():
    return {"message": "AI Business OS API", "status": "running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include API router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("AI Business OS API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    from database import client
    client.close()
    logger.info("AI Business OS API shut down")