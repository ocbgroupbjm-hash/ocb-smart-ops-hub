"""
OCB TITAN ERP - ERP HARDENING MODULE
Enterprise Features: Fiscal Period System & Multi-Currency System
Following OCB TITAN AI MASTER LAW - NON-DESTRUCTIVE Development
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, date
from database import get_db as get_database
from routes.auth import get_current_user
import uuid

router = APIRouter(prefix="/api/erp-hardening", tags=["ERP Hardening"])

# ==================== FISCAL PERIOD CONSTANTS ====================

FISCAL_STATUS = {
    "open": {
        "name": "Terbuka",
        "color": "green",
        "can_create": True,
        "can_edit": True,
        "can_delete": True,
        "can_post": True
    },
    "closed": {
        "name": "Ditutup",
        "color": "yellow",
        "can_create": False,
        "can_edit": False,
        "can_delete": False,
        "can_post": False
    },
    "locked": {
        "name": "Terkunci",
        "color": "red",
        "can_create": False,
        "can_edit": False,
        "can_delete": False,
        "can_post": False
    }
}

# ==================== MULTI-CURRENCY CONSTANTS ====================

DEFAULT_CURRENCIES = [
    {"code": "IDR", "name": "Rupiah Indonesia", "symbol": "Rp", "decimal_places": 0, "is_base": True},
    {"code": "USD", "name": "US Dollar", "symbol": "$", "decimal_places": 2, "is_base": False},
    {"code": "EUR", "name": "Euro", "symbol": "€", "decimal_places": 2, "is_base": False},
    {"code": "SGD", "name": "Singapore Dollar", "symbol": "S$", "decimal_places": 2, "is_base": False},
    {"code": "MYR", "name": "Malaysian Ringgit", "symbol": "RM", "decimal_places": 2, "is_base": False},
    {"code": "CNY", "name": "Chinese Yuan", "symbol": "¥", "decimal_places": 2, "is_base": False},
    {"code": "JPY", "name": "Japanese Yen", "symbol": "¥", "decimal_places": 0, "is_base": False},
]

# Default exchange rates (to IDR)
DEFAULT_EXCHANGE_RATES = {
    "IDR": 1.0,
    "USD": 15500.0,
    "EUR": 17000.0,
    "SGD": 11500.0,
    "MYR": 3500.0,
    "CNY": 2200.0,
    "JPY": 105.0
}

# ==================== PYDANTIC MODELS ====================

class FiscalPeriodCreate(BaseModel):
    period_name: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    status: str = "open"
    notes: str = ""

class FiscalPeriodUpdate(BaseModel):
    period_name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class CurrencyCreate(BaseModel):
    code: str
    name: str
    symbol: str = ""
    decimal_places: int = 2
    is_active: bool = True

class ExchangeRateCreate(BaseModel):
    currency_code: str
    rate_to_base: float
    effective_date: str  # YYYY-MM-DD
    notes: str = ""

class MultiCurrencyTransaction(BaseModel):
    """Model for multi-currency amount"""
    currency_code: str = "IDR"
    amount_original: float = 0
    exchange_rate: float = 1.0
    amount_base: float = 0  # In base currency (IDR)

# ==================== FISCAL PERIOD HELPER FUNCTIONS ====================

async def get_fiscal_period_for_date(transaction_date: str) -> Optional[Dict]:
    """Get fiscal period containing the given date"""
    db = get_database()
    
    # Parse date string to handle various formats
    if isinstance(transaction_date, str):
        if "T" in transaction_date:
            transaction_date = transaction_date.split("T")[0]
    
    period = await db.fiscal_periods.find_one({
        "start_date": {"$lte": transaction_date},
        "end_date": {"$gte": transaction_date}
    }, {"_id": 0})
    
    return period

async def validate_fiscal_period(transaction_date: str, action: str = "create") -> Dict[str, Any]:
    """
    Validate if action is allowed based on fiscal period status
    
    Args:
        transaction_date: Date of the transaction (YYYY-MM-DD or ISO format)
        action: One of 'create', 'edit', 'delete', 'post'
    
    Returns:
        Dict with 'allowed', 'period', 'message'
    """
    period = await get_fiscal_period_for_date(transaction_date)
    
    # If no period defined, allow by default (graceful degradation)
    if not period:
        return {
            "allowed": True,
            "period": None,
            "message": "Tidak ada periode fiscal yang didefinisikan untuk tanggal ini"
        }
    
    status = period.get("status", "open")
    status_config = FISCAL_STATUS.get(status, FISCAL_STATUS["open"])
    
    action_key = f"can_{action}"
    is_allowed = status_config.get(action_key, True)
    
    if not is_allowed:
        return {
            "allowed": False,
            "period": period,
            "message": f"Tidak dapat {action} transaksi. Periode '{period.get('period_name')}' status: {status_config['name']}"
        }
    
    return {
        "allowed": True,
        "period": period,
        "message": "OK"
    }

async def enforce_fiscal_period(transaction_date: str, action: str = "create"):
    """
    Enforce fiscal period validation - raises HTTPException if not allowed
    Use this in transaction endpoints
    """
    result = await validate_fiscal_period(transaction_date, action)
    
    if not result["allowed"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "FISCAL_PERIOD_LOCKED",
                "message": result["message"],
                "period_id": result["period"].get("id") if result["period"] else None,
                "period_name": result["period"].get("period_name") if result["period"] else None,
                "period_status": result["period"].get("status") if result["period"] else None
            }
        )
    
    return result

# ==================== MULTI-CURRENCY HELPER FUNCTIONS ====================

async def get_exchange_rate(currency_code: str, transaction_date: str = None) -> float:
    """Get exchange rate for currency on specific date (or latest)"""
    db = get_database()
    
    if currency_code == "IDR":
        return 1.0
    
    query = {"currency_code": currency_code, "is_active": True}
    
    if transaction_date:
        # Get rate effective on or before transaction date
        query["effective_date"] = {"$lte": transaction_date}
        rate = await db.exchange_rates.find_one(
            query, {"_id": 0},
            sort=[("effective_date", -1)]
        )
    else:
        # Get latest rate
        rate = await db.exchange_rates.find_one(
            query, {"_id": 0},
            sort=[("effective_date", -1)]
        )
    
    if rate:
        return rate.get("rate_to_base", DEFAULT_EXCHANGE_RATES.get(currency_code, 1.0))
    
    # Return default rate if not found
    return DEFAULT_EXCHANGE_RATES.get(currency_code, 1.0)

async def convert_to_base_currency(amount: float, currency_code: str, transaction_date: str = None) -> Dict[str, float]:
    """Convert amount to base currency (IDR)"""
    rate = await get_exchange_rate(currency_code, transaction_date)
    amount_base = amount * rate
    
    return {
        "amount_original": amount,
        "currency_code": currency_code,
        "exchange_rate": rate,
        "amount_base": amount_base
    }

async def calculate_exchange_gain_loss(
    original_amount: float,
    original_rate: float,
    current_rate: float,
    currency_code: str
) -> Dict[str, Any]:
    """
    Calculate gain/loss from exchange rate difference
    
    Returns:
        Dict with 'gain_loss', 'is_gain', 'original_base', 'current_base'
    """
    original_base = original_amount * original_rate
    current_base = original_amount * current_rate
    
    gain_loss = current_base - original_base
    is_gain = gain_loss > 0
    
    return {
        "currency_code": currency_code,
        "original_amount": original_amount,
        "original_rate": original_rate,
        "current_rate": current_rate,
        "original_base": original_base,
        "current_base": current_base,
        "gain_loss": abs(gain_loss),
        "is_gain": is_gain,
        "account_key": "laba_selisih_kurs" if is_gain else "rugi_selisih_kurs"
    }

# ==================== FISCAL PERIOD ENDPOINTS ====================

@router.get("/fiscal-periods")
async def list_fiscal_periods(user: dict = Depends(get_current_user)):
    """Get all fiscal periods with status info"""
    db = get_database()
    
    periods = await db.fiscal_periods.find({}, {"_id": 0}).sort("start_date", -1).to_list(100)
    
    # Add status info
    for period in periods:
        status = period.get("status", "open")
        period["status_info"] = FISCAL_STATUS.get(status, FISCAL_STATUS["open"])
    
    return {"items": periods, "total": len(periods)}

@router.post("/fiscal-periods")
async def create_fiscal_period(data: FiscalPeriodCreate, user: dict = Depends(get_current_user)):
    """Create a new fiscal period"""
    db = get_database()
    
    # Validate status
    if data.status not in FISCAL_STATUS:
        raise HTTPException(status_code=400, detail=f"Status tidak valid. Pilih: {', '.join(FISCAL_STATUS.keys())}")
    
    # Check overlap
    existing = await db.fiscal_periods.find_one({
        "$or": [
            {"start_date": {"$lte": data.end_date}, "end_date": {"$gte": data.start_date}},
        ]
    })
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Periode overlap dengan '{existing.get('period_name')}' ({existing.get('start_date')} - {existing.get('end_date')})"
        )
    
    period = {
        "id": str(uuid.uuid4()),
        "period_name": data.period_name,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "status": data.status,
        "notes": data.notes,
        "created_by": user.get("id") or user.get("user_id"),
        "created_by_name": user.get("name", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.fiscal_periods.insert_one(period)
    period.pop("_id", None)
    period["status_info"] = FISCAL_STATUS.get(data.status)
    
    return period

@router.put("/fiscal-periods/{period_id}")
async def update_fiscal_period(period_id: str, data: FiscalPeriodUpdate, user: dict = Depends(get_current_user)):
    """Update fiscal period (name, notes, or status)"""
    db = get_database()
    
    period = await db.fiscal_periods.find_one({"id": period_id})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.period_name:
        update_data["period_name"] = data.period_name
    if data.notes is not None:
        update_data["notes"] = data.notes
    if data.status:
        if data.status not in FISCAL_STATUS:
            raise HTTPException(status_code=400, detail=f"Status tidak valid. Pilih: {', '.join(FISCAL_STATUS.keys())}")
        
        # Prevent changing from locked to open (security measure)
        current_status = period.get("status", "open")
        if current_status == "locked" and data.status == "open":
            raise HTTPException(
                status_code=403, 
                detail="Periode LOCKED tidak dapat dibuka kembali ke OPEN. Hubungi administrator sistem."
            )
        
        update_data["status"] = data.status
        update_data["status_changed_at"] = datetime.now(timezone.utc).isoformat()
        update_data["status_changed_by"] = user.get("id") or user.get("user_id")
    
    await db.fiscal_periods.update_one({"id": period_id}, {"$set": update_data})
    
    return {"success": True, "message": "Periode berhasil diperbarui"}

@router.post("/fiscal-periods/{period_id}/close")
async def close_fiscal_period(period_id: str, user: dict = Depends(get_current_user)):
    """Close a fiscal period"""
    db = get_database()
    
    period = await db.fiscal_periods.find_one({"id": period_id})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    if period.get("status") == "locked":
        raise HTTPException(status_code=400, detail="Periode sudah terkunci")
    
    await db.fiscal_periods.update_one(
        {"id": period_id},
        {"$set": {
            "status": "closed",
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "closed_by": user.get("id") or user.get("user_id"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True, "message": "Periode berhasil ditutup", "new_status": "closed"}

@router.post("/fiscal-periods/{period_id}/lock")
async def lock_fiscal_period(period_id: str, user: dict = Depends(get_current_user)):
    """Lock a fiscal period permanently"""
    db = get_database()
    
    period = await db.fiscal_periods.find_one({"id": period_id})
    if not period:
        raise HTTPException(status_code=404, detail="Periode tidak ditemukan")
    
    if period.get("status") == "open":
        raise HTTPException(status_code=400, detail="Periode harus ditutup (CLOSED) terlebih dahulu sebelum dikunci")
    
    await db.fiscal_periods.update_one(
        {"id": period_id},
        {"$set": {
            "status": "locked",
            "locked_at": datetime.now(timezone.utc).isoformat(),
            "locked_by": user.get("id") or user.get("user_id"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True, "message": "Periode berhasil dikunci secara permanen", "new_status": "locked"}

@router.get("/fiscal-periods/validate")
async def validate_date_fiscal_period(
    transaction_date: str,
    action: str = "create",
    user: dict = Depends(get_current_user)
):
    """Check if a transaction date is in an open fiscal period"""
    result = await validate_fiscal_period(transaction_date, action)
    return result

# ==================== MULTI-CURRENCY ENDPOINTS ====================

@router.get("/currencies")
async def list_currencies(user: dict = Depends(get_current_user)):
    """Get all currencies"""
    db = get_database()
    
    currencies = await db.currencies.find({"is_active": True}, {"_id": 0}).to_list(100)
    
    # If no currencies, initialize defaults
    if not currencies:
        currencies = DEFAULT_CURRENCIES.copy()
    
    return {"items": currencies, "base_currency": "IDR"}

@router.post("/currencies")
async def create_currency(data: CurrencyCreate, user: dict = Depends(get_current_user)):
    """Create a new currency"""
    db = get_database()
    
    # Check if exists
    existing = await db.currencies.find_one({"code": data.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail=f"Mata uang {data.code} sudah ada")
    
    currency = {
        "id": str(uuid.uuid4()),
        "code": data.code.upper(),
        "name": data.name,
        "symbol": data.symbol or data.code.upper(),
        "decimal_places": data.decimal_places,
        "is_base": False,
        "is_active": data.is_active,
        "created_by": user.get("id") or user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.currencies.insert_one(currency)
    currency.pop("_id", None)
    
    return currency

@router.post("/currencies/initialize-defaults")
async def initialize_default_currencies(user: dict = Depends(get_current_user)):
    """Initialize default currencies"""
    db = get_database()
    
    count = 0
    for curr in DEFAULT_CURRENCIES:
        existing = await db.currencies.find_one({"code": curr["code"]})
        if not existing:
            currency = {
                "id": str(uuid.uuid4()),
                **curr,
                "created_by": user.get("id") or user.get("user_id"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.currencies.insert_one(currency)
            count += 1
    
    return {"success": True, "initialized": count}

@router.get("/exchange-rates")
async def list_exchange_rates(
    currency_code: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get exchange rates"""
    db = get_database()
    
    query = {"is_active": True}
    if currency_code:
        query["currency_code"] = currency_code.upper()
    
    rates = await db.exchange_rates.find(query, {"_id": 0}).sort("effective_date", -1).to_list(100)
    
    # If no rates, return defaults
    if not rates:
        rates = [
            {"currency_code": code, "rate_to_base": rate, "effective_date": datetime.now().strftime("%Y-%m-%d"), "is_default": True}
            for code, rate in DEFAULT_EXCHANGE_RATES.items()
            if code != "IDR"
        ]
    
    return {"items": rates, "base_currency": "IDR"}

@router.post("/exchange-rates")
async def create_exchange_rate(data: ExchangeRateCreate, user: dict = Depends(get_current_user)):
    """Create or update exchange rate"""
    db = get_database()
    
    if data.currency_code.upper() == "IDR":
        raise HTTPException(status_code=400, detail="Tidak dapat mengatur kurs untuk mata uang dasar (IDR)")
    
    # Deactivate previous rates for same currency on same date
    await db.exchange_rates.update_many(
        {"currency_code": data.currency_code.upper(), "effective_date": data.effective_date},
        {"$set": {"is_active": False}}
    )
    
    rate = {
        "id": str(uuid.uuid4()),
        "currency_code": data.currency_code.upper(),
        "rate_to_base": data.rate_to_base,
        "effective_date": data.effective_date,
        "notes": data.notes,
        "is_active": True,
        "created_by": user.get("id") or user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.exchange_rates.insert_one(rate)
    rate.pop("_id", None)
    
    return rate

@router.get("/exchange-rates/current")
async def get_current_exchange_rates(user: dict = Depends(get_current_user)):
    """Get current exchange rates for all currencies"""
    db = get_database()
    
    # Get all active currencies
    currencies = await db.currencies.find({"is_active": True, "is_base": False}, {"_id": 0}).to_list(100)
    
    if not currencies:
        currencies = [c for c in DEFAULT_CURRENCIES if not c.get("is_base")]
    
    rates = {}
    today = datetime.now().strftime("%Y-%m-%d")
    
    for curr in currencies:
        code = curr.get("code")
        rate = await get_exchange_rate(code, today)
        rates[code] = {
            "code": code,
            "name": curr.get("name", code),
            "symbol": curr.get("symbol", code),
            "rate_to_base": rate
        }
    
    return {"rates": rates, "base_currency": "IDR", "date": today}

@router.post("/exchange-rates/convert")
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str = "IDR",
    transaction_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Convert amount between currencies"""
    from_rate = await get_exchange_rate(from_currency.upper(), transaction_date)
    to_rate = await get_exchange_rate(to_currency.upper(), transaction_date)
    
    # Convert to base (IDR) then to target
    amount_base = amount * from_rate
    converted_amount = amount_base / to_rate if to_rate > 0 else 0
    
    return {
        "original_amount": amount,
        "original_currency": from_currency.upper(),
        "converted_amount": converted_amount,
        "target_currency": to_currency.upper(),
        "from_rate": from_rate,
        "to_rate": to_rate,
        "amount_in_base": amount_base
    }

# ==================== EXCHANGE GAIN/LOSS CALCULATION ====================

@router.post("/exchange-rates/calculate-gain-loss")
async def calculate_gain_loss_endpoint(
    original_amount: float,
    original_rate: float,
    currency_code: str,
    current_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Calculate exchange gain/loss for AR/AP settlement"""
    current_rate = await get_exchange_rate(currency_code.upper(), current_date)
    
    result = await calculate_exchange_gain_loss(
        original_amount, original_rate, current_rate, currency_code.upper()
    )
    
    return result

# ==================== COMBINED VALIDATION ENDPOINT ====================

@router.post("/validate-transaction")
async def validate_transaction(
    transaction_date: str,
    action: str = "create",
    currency_code: str = "IDR",
    amount: float = 0,
    user: dict = Depends(get_current_user)
):
    """
    Combined validation for transaction:
    - Check fiscal period status
    - Get exchange rate for currency
    """
    # Fiscal period validation
    fiscal_result = await validate_fiscal_period(transaction_date, action)
    
    # Currency conversion
    currency_result = await convert_to_base_currency(amount, currency_code, transaction_date)
    
    return {
        "fiscal_period": fiscal_result,
        "currency": currency_result,
        "can_proceed": fiscal_result["allowed"]
    }
