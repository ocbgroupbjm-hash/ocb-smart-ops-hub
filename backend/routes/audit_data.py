# OCB TITAN AI - Comprehensive Audit Data Generator
# Creates all necessary test data for full system audit

from fastapi import APIRouter
from datetime import datetime, timezone, timedelta
import uuid
import random

router = APIRouter(prefix="/api/audit-data", tags=["Audit Data Generator"])

def get_db():
    from database import get_db as db_get
    return db_get()

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()

# ==================== MASTER DATA ====================

@router.post("/all")
async def generate_all_audit_data():
    """Generate comprehensive audit data for all modules"""
    results = {}
    
    # 1. Categories
    results["categories"] = await seed_categories()
    
    # 2. Units
    results["units"] = await seed_units()
    
    # 3. Brands
    results["brands"] = await seed_brands()
    
    # 4. Warehouses
    results["warehouses"] = await seed_warehouses()
    
    # 5. Suppliers
    results["suppliers"] = await seed_suppliers()
    
    # 6. Customers
    results["customers"] = await seed_customers()
    
    # 7. Sales persons
    results["sales_persons"] = await seed_sales_persons()
    
    # 8. Customer groups
    results["customer_groups"] = await seed_customer_groups()
    
    # 9. Regions
    results["regions"] = await seed_regions()
    
    # 10. E-Money
    results["emoney"] = await seed_emoney()
    
    # 11. Banks
    results["banks"] = await seed_banks()
    
    # 12. Shipping costs
    results["shipping"] = await seed_shipping()
    
    # 13. Products/Items
    results["products"] = await seed_products()
    
    # 14. Chart of Accounts
    results["coa"] = await seed_coa()
    
    # 15. Transactions
    results["transactions"] = await seed_transactions_audit()
    
    # 16. Purchase Orders
    results["purchases"] = await seed_purchases()
    
    # 17. Inventory movements
    results["inventory"] = await seed_inventory_movements()
    
    # 18. Cash transactions
    results["cash"] = await seed_cash_transactions()
    
    # 19. Setoran & Selisih
    results["setoran"] = await seed_setoran()
    
    # 20. CRM Data
    results["crm"] = await seed_crm_data()
    
    # 21. KPI Targets
    results["kpi"] = await seed_kpi_targets()
    
    # 22. Alerts
    results["alerts"] = await seed_alerts()
    
    return {"message": "Audit data generated successfully", "results": results}


@router.post("/categories")
async def seed_categories():
    db = get_db()
    categories = [
        {"id": "CAT-AUDIT-001", "code": "CHG", "name": "Charger & Adapter", "description": "Charger HP dan Adapter", "is_active": True},
        {"id": "CAT-AUDIT-002", "code": "CBL", "name": "Kabel & Konverter", "description": "Kabel data dan konverter", "is_active": True},
        {"id": "CAT-AUDIT-003", "code": "ACC", "name": "Aksesoris HP", "description": "Case, tempered glass, dll", "is_active": True},
        {"id": "CAT-AUDIT-004", "code": "AUD", "name": "Audio & Earphone", "description": "Headset, TWS, Speaker", "is_active": True},
        {"id": "CAT-AUDIT-005", "code": "PWB", "name": "Powerbank", "description": "Powerbank dan baterai", "is_active": True},
    ]
    for c in categories:
        c["created_at"] = now_iso()
        await db["categories"].update_one({"id": c["id"]}, {"$set": c}, upsert=True)
    return {"count": len(categories)}


@router.post("/units")
async def seed_units():
    db = get_db()
    units = [
        {"id": "UNIT-AUDIT-001", "code": "PCS", "name": "Pieces", "is_active": True},
        {"id": "UNIT-AUDIT-002", "code": "BOX", "name": "Box", "is_active": True},
        {"id": "UNIT-AUDIT-003", "code": "SET", "name": "Set", "is_active": True},
        {"id": "UNIT-AUDIT-004", "code": "PAK", "name": "Pak/Pack", "is_active": True},
        {"id": "UNIT-AUDIT-005", "code": "LUS", "name": "Lusin", "is_active": True},
    ]
    for u in units:
        u["created_at"] = now_iso()
        await db["units"].update_one({"id": u["id"]}, {"$set": u}, upsert=True)
    return {"count": len(units)}


@router.post("/brands")
async def seed_brands():
    db = get_db()
    brands = [
        {"id": "BRD-AUDIT-001", "code": "OCBT", "name": "OCB Tech", "is_active": True},
        {"id": "BRD-AUDIT-002", "code": "SAMS", "name": "Samsung", "is_active": True},
        {"id": "BRD-AUDIT-003", "code": "ANKE", "name": "Anker", "is_active": True},
        {"id": "BRD-AUDIT-004", "code": "XIAO", "name": "Xiaomi", "is_active": True},
        {"id": "BRD-AUDIT-005", "code": "BASQ", "name": "Baseus", "is_active": True},
    ]
    for b in brands:
        b["created_at"] = now_iso()
        await db["brands"].update_one({"id": b["id"]}, {"$set": b}, upsert=True)
    return {"count": len(brands)}


@router.post("/warehouses")
async def seed_warehouses():
    db = get_db()
    warehouses = [
        {"id": "WH-AUDIT-001", "code": "GD-BJM", "name": "Gudang Banjarmasin", "address": "Jl. A. Yani Km 2", "is_active": True},
        {"id": "WH-AUDIT-002", "code": "GD-MTP", "name": "Gudang Martapura", "address": "Jl. Sukaramai No. 10", "is_active": True},
        {"id": "WH-AUDIT-003", "code": "GD-BBR", "name": "Gudang Banjarbaru", "address": "Jl. A. Yani Km 35", "is_active": True},
    ]
    for w in warehouses:
        w["created_at"] = now_iso()
        await db["warehouses"].update_one({"id": w["id"]}, {"$set": w}, upsert=True)
    return {"count": len(warehouses)}


@router.post("/suppliers")
async def seed_suppliers():
    db = get_db()
    suppliers = [
        {"id": "SUP-AUDIT-001", "code": "SUP001", "name": "PT Elektronik Jaya", "address": "Jakarta", "phone": "021-1234567", "email": "info@elektronikjaya.com", "contact_person": "Budi", "is_active": True},
        {"id": "SUP-AUDIT-002", "code": "SUP002", "name": "CV Mitra Aksesoris", "address": "Surabaya", "phone": "031-7654321", "email": "sales@mitraaksesoris.com", "contact_person": "Siti", "is_active": True},
        {"id": "SUP-AUDIT-003", "code": "SUP003", "name": "UD Berkah Elektronik", "address": "Bandung", "phone": "022-9876543", "email": "berkah@mail.com", "contact_person": "Ahmad", "is_active": True},
        {"id": "SUP-AUDIT-004", "code": "SUP004", "name": "PT Global Tech", "address": "Semarang", "phone": "024-1122334", "email": "global@tech.co.id", "contact_person": "Dewi", "is_active": True},
        {"id": "SUP-AUDIT-005", "code": "SUP005", "name": "CV Sentosa Mandiri", "address": "Medan", "phone": "061-5566778", "email": "sentosa@mandiri.com", "contact_person": "Rudi", "is_active": True},
    ]
    for s in suppliers:
        s["created_at"] = now_iso()
        await db["suppliers"].update_one({"id": s["id"]}, {"$set": s}, upsert=True)
    return {"count": len(suppliers)}


@router.post("/customers")
async def seed_customers():
    db = get_db()
    customers = [
        {"id": "CUS-AUDIT-001", "code": "CUS001", "name": "Toko Maju Jaya", "address": "Banjarmasin", "phone": "0811111001", "email": "majujaya@mail.com", "group_id": "GRP-AUDIT-001", "points": 1500, "is_active": True},
        {"id": "CUS-AUDIT-002", "code": "CUS002", "name": "Toko Sejahtera", "address": "Martapura", "phone": "0811111002", "email": "sejahtera@mail.com", "group_id": "GRP-AUDIT-001", "points": 2500, "is_active": True},
        {"id": "CUS-AUDIT-003", "code": "CUS003", "name": "CV Berkah Abadi", "address": "Banjarbaru", "phone": "0811111003", "email": "berkah@mail.com", "group_id": "GRP-AUDIT-002", "points": 5000, "is_active": True},
        {"id": "CUS-AUDIT-004", "code": "CUS004", "name": "UD Sumber Rejeki", "address": "Balikpapan", "phone": "0811111004", "email": "sumberrejeki@mail.com", "group_id": "GRP-AUDIT-002", "points": 3000, "is_active": True},
        {"id": "CUS-AUDIT-005", "code": "CUS005", "name": "Toko Makmur", "address": "Samarinda", "phone": "0811111005", "email": "makmur@mail.com", "group_id": "GRP-AUDIT-003", "points": 7500, "is_active": True},
        {"id": "CUS-AUDIT-006", "code": "CUS006", "name": "CV Digital Store", "address": "Banjarmasin", "phone": "0811111006", "email": "digital@mail.com", "group_id": "GRP-AUDIT-001", "points": 1000, "is_active": True},
        {"id": "CUS-AUDIT-007", "code": "CUS007", "name": "Toko HP Center", "address": "Martapura", "phone": "0811111007", "email": "hpcenter@mail.com", "group_id": "GRP-AUDIT-002", "points": 4500, "is_active": True},
        {"id": "CUS-AUDIT-008", "code": "CUS008", "name": "UD Elektronik Murah", "address": "Banjarbaru", "phone": "0811111008", "email": "ekmurah@mail.com", "group_id": "GRP-AUDIT-003", "points": 6000, "is_active": True},
        {"id": "CUS-AUDIT-009", "code": "CUS009", "name": "CV Gadget World", "address": "Balikpapan", "phone": "0811111009", "email": "gadgetworld@mail.com", "group_id": "GRP-AUDIT-001", "points": 2000, "is_active": True},
        {"id": "CUS-AUDIT-010", "code": "CUS010", "name": "Toko Tekno", "address": "Samarinda", "phone": "0811111010", "email": "tekno@mail.com", "group_id": "GRP-AUDIT-002", "points": 8000, "is_active": True},
    ]
    for c in customers:
        c["created_at"] = now_iso()
        await db["customers"].update_one({"id": c["id"]}, {"$set": c}, upsert=True)
    return {"count": len(customers)}


@router.post("/sales-persons")
async def seed_sales_persons():
    db = get_db()
    sales_persons = [
        {"id": "SLS-AUDIT-001", "code": "SLS001", "name": "Andi Wijaya", "phone": "0812222001", "email": "andi@ocb.com", "commission_rate": 2.5, "is_active": True},
        {"id": "SLS-AUDIT-002", "code": "SLS002", "name": "Budi Santoso", "phone": "0812222002", "email": "budi@ocb.com", "commission_rate": 2.0, "is_active": True},
        {"id": "SLS-AUDIT-003", "code": "SLS003", "name": "Citra Dewi", "phone": "0812222003", "email": "citra@ocb.com", "commission_rate": 2.5, "is_active": True},
        {"id": "SLS-AUDIT-004", "code": "SLS004", "name": "Deni Pratama", "phone": "0812222004", "email": "deni@ocb.com", "commission_rate": 2.0, "is_active": True},
        {"id": "SLS-AUDIT-005", "code": "SLS005", "name": "Eka Putri", "phone": "0812222005", "email": "eka@ocb.com", "commission_rate": 3.0, "is_active": True},
    ]
    for s in sales_persons:
        s["created_at"] = now_iso()
        await db["sales_persons"].update_one({"id": s["id"]}, {"$set": s}, upsert=True)
    return {"count": len(sales_persons)}


@router.post("/customer-groups")
async def seed_customer_groups():
    db = get_db()
    groups = [
        {"id": "GRP-AUDIT-001", "code": "REG", "name": "Regular", "discount_percent": 0, "min_purchase": 0, "is_active": True},
        {"id": "GRP-AUDIT-002", "code": "SLV", "name": "Silver", "discount_percent": 5, "min_purchase": 1000000, "is_active": True},
        {"id": "GRP-AUDIT-003", "code": "GLD", "name": "Gold", "discount_percent": 10, "min_purchase": 5000000, "is_active": True},
        {"id": "GRP-AUDIT-004", "code": "PLT", "name": "Platinum", "discount_percent": 15, "min_purchase": 10000000, "is_active": True},
    ]
    for g in groups:
        g["created_at"] = now_iso()
        await db["customer_groups"].update_one({"id": g["id"]}, {"$set": g}, upsert=True)
    return {"count": len(groups)}


@router.post("/regions")
async def seed_regions():
    db = get_db()
    regions = [
        {"id": "REG-AUDIT-001", "code": "KALSEL", "name": "Kalimantan Selatan", "is_active": True},
        {"id": "REG-AUDIT-002", "code": "KALTIM", "name": "Kalimantan Timur", "is_active": True},
        {"id": "REG-AUDIT-003", "code": "KALTENG", "name": "Kalimantan Tengah", "is_active": True},
        {"id": "REG-AUDIT-004", "code": "KALBAR", "name": "Kalimantan Barat", "is_active": True},
    ]
    for r in regions:
        r["created_at"] = now_iso()
        await db["regions"].update_one({"id": r["id"]}, {"$set": r}, upsert=True)
    return {"count": len(regions)}


@router.post("/emoney")
async def seed_emoney():
    db = get_db()
    emoney = [
        {"id": "EMN-AUDIT-001", "code": "OVO", "name": "OVO", "fee_percent": 0.7, "is_active": True},
        {"id": "EMN-AUDIT-002", "code": "GOPAY", "name": "GoPay", "fee_percent": 0.7, "is_active": True},
        {"id": "EMN-AUDIT-003", "code": "DANA", "name": "DANA", "fee_percent": 0.7, "is_active": True},
        {"id": "EMN-AUDIT-004", "code": "SPAY", "name": "ShopeePay", "fee_percent": 0.7, "is_active": True},
    ]
    for e in emoney:
        e["created_at"] = now_iso()
        await db["emoney"].update_one({"id": e["id"]}, {"$set": e}, upsert=True)
    return {"count": len(emoney)}


@router.post("/banks")
async def seed_banks():
    db = get_db()
    banks = [
        {"id": "BNK-AUDIT-001", "code": "BCA", "name": "Bank BCA", "account_number": "1234567890", "account_name": "OCB GROUP", "is_active": True},
        {"id": "BNK-AUDIT-002", "code": "BRI", "name": "Bank BRI", "account_number": "0987654321", "account_name": "OCB GROUP", "is_active": True},
        {"id": "BNK-AUDIT-003", "code": "MANDIRI", "name": "Bank Mandiri", "account_number": "1122334455", "account_name": "OCB GROUP", "is_active": True},
        {"id": "BNK-AUDIT-004", "code": "BNI", "name": "Bank BNI", "account_number": "5544332211", "account_name": "OCB GROUP", "is_active": True},
    ]
    for b in banks:
        b["created_at"] = now_iso()
        await db["banks"].update_one({"id": b["id"]}, {"$set": b}, upsert=True)
    return {"count": len(banks)}


@router.post("/shipping")
async def seed_shipping():
    db = get_db()
    shipping = [
        {"id": "SHP-AUDIT-001", "code": "JNE", "name": "JNE Regular", "cost": 15000, "is_active": True},
        {"id": "SHP-AUDIT-002", "code": "JNEYES", "name": "JNE YES", "cost": 25000, "is_active": True},
        {"id": "SHP-AUDIT-003", "code": "SICEPAT", "name": "SiCepat", "cost": 12000, "is_active": True},
        {"id": "SHP-AUDIT-004", "code": "ANTERAJA", "name": "AnterAja", "cost": 10000, "is_active": True},
    ]
    for s in shipping:
        s["created_at"] = now_iso()
        await db["shipping_costs"].update_one({"id": s["id"]}, {"$set": s}, upsert=True)
    return {"count": len(shipping)}


@router.post("/products")
async def seed_products():
    db = get_db()
    products = [
        {"id": "PRD-AUDIT-001", "code": "PRD-AUDIT-001", "sku": "CHG-001", "name": "Charger Fast 20W USB-C", "category_id": "CAT-AUDIT-001", "brand_id": "BRD-AUDIT-001", "unit_id": "UNIT-AUDIT-001", "buy_price": 25000, "sell_price": 45000, "stock": 100, "min_stock": 10, "is_active": True},
        {"id": "PRD-AUDIT-002", "code": "PRD-AUDIT-002", "sku": "CHG-002", "name": "Charger Fast 33W Dual Port", "category_id": "CAT-AUDIT-001", "brand_id": "BRD-AUDIT-003", "unit_id": "UNIT-AUDIT-001", "buy_price": 45000, "sell_price": 85000, "stock": 75, "min_stock": 10, "is_active": True},
        {"id": "PRD-AUDIT-003", "code": "PRD-AUDIT-003", "sku": "CBL-001", "name": "Kabel USB-C to USB-C 1M", "category_id": "CAT-AUDIT-002", "brand_id": "BRD-AUDIT-003", "unit_id": "UNIT-AUDIT-001", "buy_price": 15000, "sell_price": 35000, "stock": 200, "min_stock": 20, "is_active": True},
        {"id": "PRD-AUDIT-004", "code": "PRD-AUDIT-004", "sku": "CBL-002", "name": "Kabel Lightning 2M", "category_id": "CAT-AUDIT-002", "brand_id": "BRD-AUDIT-005", "unit_id": "UNIT-AUDIT-001", "buy_price": 20000, "sell_price": 45000, "stock": 150, "min_stock": 15, "is_active": True},
        {"id": "PRD-AUDIT-005", "code": "PRD-AUDIT-005", "sku": "ACC-001", "name": "Case iPhone 15 Clear", "category_id": "CAT-AUDIT-003", "brand_id": "BRD-AUDIT-001", "unit_id": "UNIT-AUDIT-001", "buy_price": 10000, "sell_price": 25000, "stock": 300, "min_stock": 30, "is_active": True},
        {"id": "PRD-AUDIT-006", "code": "PRD-AUDIT-006", "sku": "ACC-002", "name": "Tempered Glass Samsung S24", "category_id": "CAT-AUDIT-003", "brand_id": "BRD-AUDIT-002", "unit_id": "UNIT-AUDIT-001", "buy_price": 8000, "sell_price": 20000, "stock": 250, "min_stock": 25, "is_active": True},
        {"id": "PRD-AUDIT-007", "code": "PRD-AUDIT-007", "sku": "AUD-001", "name": "TWS Bluetooth 5.3", "category_id": "CAT-AUDIT-004", "brand_id": "BRD-AUDIT-004", "unit_id": "UNIT-AUDIT-001", "buy_price": 50000, "sell_price": 120000, "stock": 80, "min_stock": 10, "is_active": True},
        {"id": "PRD-AUDIT-008", "code": "PRD-AUDIT-008", "sku": "AUD-002", "name": "Headset Gaming RGB", "category_id": "CAT-AUDIT-004", "brand_id": "BRD-AUDIT-001", "unit_id": "UNIT-AUDIT-001", "buy_price": 75000, "sell_price": 150000, "stock": 50, "min_stock": 5, "is_active": True},
        {"id": "PRD-AUDIT-009", "code": "PRD-AUDIT-009", "sku": "PWB-001", "name": "Powerbank 10000mAh", "category_id": "CAT-AUDIT-005", "brand_id": "BRD-AUDIT-003", "unit_id": "UNIT-AUDIT-001", "buy_price": 80000, "sell_price": 150000, "stock": 60, "min_stock": 10, "is_active": True},
        {"id": "PRD-AUDIT-010", "code": "PRD-AUDIT-010", "sku": "PWB-002", "name": "Powerbank 20000mAh Fast Charge", "category_id": "CAT-AUDIT-005", "brand_id": "BRD-AUDIT-003", "unit_id": "UNIT-AUDIT-001", "buy_price": 150000, "sell_price": 280000, "stock": 40, "min_stock": 5, "is_active": True},
    ]
    for p in products:
        p["created_at"] = now_iso()
        p["updated_at"] = now_iso()
        await db["products"].update_one({"id": p["id"]}, {"$set": p}, upsert=True)
    return {"count": len(products)}


@router.post("/coa")
async def seed_coa():
    """Seed Chart of Accounts"""
    db = get_db()
    accounts = [
        {"id": "COA-AUDIT-001", "code": "1-1001", "name": "Kas", "type": "asset", "is_active": True},
        {"id": "COA-AUDIT-002", "code": "1-1002", "name": "Bank BCA", "type": "asset", "is_active": True},
        {"id": "COA-AUDIT-003", "code": "1-1003", "name": "Bank BRI", "type": "asset", "is_active": True},
        {"id": "COA-AUDIT-004", "code": "1-2001", "name": "Piutang Dagang", "type": "asset", "is_active": True},
        {"id": "COA-AUDIT-005", "code": "1-3001", "name": "Persediaan Barang", "type": "asset", "is_active": True},
        {"id": "COA-AUDIT-006", "code": "2-1001", "name": "Hutang Dagang", "type": "liability", "is_active": True},
        {"id": "COA-AUDIT-007", "code": "2-1002", "name": "Hutang Bank", "type": "liability", "is_active": True},
        {"id": "COA-AUDIT-008", "code": "3-1001", "name": "Modal", "type": "equity", "is_active": True},
        {"id": "COA-AUDIT-009", "code": "4-1001", "name": "Penjualan", "type": "revenue", "is_active": True},
        {"id": "COA-AUDIT-010", "code": "5-1001", "name": "Harga Pokok Penjualan", "type": "expense", "is_active": True},
        {"id": "COA-AUDIT-011", "code": "5-2001", "name": "Beban Gaji", "type": "expense", "is_active": True},
        {"id": "COA-AUDIT-012", "code": "5-2002", "name": "Beban Operasional", "type": "expense", "is_active": True},
    ]
    for a in accounts:
        a["created_at"] = now_iso()
        await db["chart_of_accounts"].update_one({"id": a["id"]}, {"$set": a}, upsert=True)
    return {"count": len(accounts)}


@router.post("/transactions-audit")
async def seed_transactions_audit():
    """Seed sales transactions for audit"""
    db = get_db()
    today = datetime.now(timezone.utc)
    transactions = []
    
    customers = ["CUS-AUDIT-001", "CUS-AUDIT-002", "CUS-AUDIT-003", "CUS-AUDIT-004", "CUS-AUDIT-005"]
    products_list = ["PRD-AUDIT-001", "PRD-AUDIT-002", "PRD-AUDIT-003", "PRD-AUDIT-004", "PRD-AUDIT-005"]
    sales_persons = ["SLS-AUDIT-001", "SLS-AUDIT-002", "SLS-AUDIT-003"]
    
    for i in range(10):
        date = today - timedelta(days=random.randint(0, 30))
        trans = {
            "id": f"TRX-AUDIT-{i+1:03d}",
            "invoice_number": f"INV-AUDIT-{date.strftime('%Y%m%d')}-{i+1:03d}",
            "customer_id": random.choice(customers),
            "sales_person_id": random.choice(sales_persons),
            "branch_id": "BR001",
            "items": [
                {
                    "product_id": random.choice(products_list),
                    "qty": random.randint(1, 5),
                    "price": random.randint(20000, 150000),
                    "discount": 0
                }
            ],
            "subtotal": random.randint(50000, 500000),
            "discount": 0,
            "tax": 0,
            "total": random.randint(50000, 500000),
            "payment_method": random.choice(["cash", "transfer", "card"]),
            "status": "completed",
            "created_at": date.isoformat()
        }
        transactions.append(trans)
    
    for t in transactions:
        await db["transactions"].update_one({"id": t["id"]}, {"$set": t}, upsert=True)
    
    return {"count": len(transactions)}


@router.post("/purchases")
async def seed_purchases():
    """Seed purchase orders"""
    db = get_db()
    today = datetime.now(timezone.utc)
    
    purchases = [
        {
            "id": "PO-AUDIT-001",
            "po_number": f"PO-AUDIT-{today.strftime('%Y%m%d')}-001",
            "supplier_id": "SUP-AUDIT-001",
            "supplier_name": "PT Elektronik Jaya",
            "warehouse_id": "WH-AUDIT-001",
            "items": [
                {"product_id": "PRD-AUDIT-001", "product_name": "Charger Fast 20W USB-C", "qty": 50, "price": 25000, "total": 1250000}
            ],
            "subtotal": 1250000,
            "tax": 0,
            "total": 1250000,
            "status": "received",
            "created_at": (today - timedelta(days=5)).isoformat()
        },
        {
            "id": "PO-AUDIT-002",
            "po_number": f"PO-AUDIT-{today.strftime('%Y%m%d')}-002",
            "supplier_id": "SUP-AUDIT-002",
            "supplier_name": "CV Mitra Aksesoris",
            "warehouse_id": "WH-AUDIT-001",
            "items": [
                {"product_id": "PRD-AUDIT-005", "product_name": "Case iPhone 15 Clear", "qty": 100, "price": 10000, "total": 1000000}
            ],
            "subtotal": 1000000,
            "tax": 0,
            "total": 1000000,
            "status": "pending",
            "created_at": (today - timedelta(days=3)).isoformat()
        },
        {
            "id": "PO-AUDIT-003",
            "po_number": f"PO-AUDIT-{today.strftime('%Y%m%d')}-003",
            "supplier_id": "SUP-AUDIT-003",
            "supplier_name": "UD Berkah Elektronik",
            "warehouse_id": "WH-AUDIT-002",
            "items": [
                {"product_id": "PRD-AUDIT-007", "product_name": "TWS Bluetooth 5.3", "qty": 30, "price": 50000, "total": 1500000}
            ],
            "subtotal": 1500000,
            "tax": 0,
            "total": 1500000,
            "status": "ordered",
            "created_at": today.isoformat()
        },
    ]
    
    for p in purchases:
        await db["purchases"].update_one({"id": p["id"]}, {"$set": p}, upsert=True)
    
    return {"count": len(purchases)}


@router.post("/inventory")
async def seed_inventory_movements():
    """Seed inventory movements"""
    db = get_db()
    today = datetime.now(timezone.utc)
    
    movements = [
        {
            "id": "INV-AUDIT-001",
            "type": "in",
            "product_id": "PRD-AUDIT-001",
            "product_name": "Charger Fast 20W USB-C",
            "warehouse_id": "WH-AUDIT-001",
            "qty": 50,
            "reference": "PO-AUDIT-001",
            "notes": "Penerimaan dari supplier",
            "created_at": (today - timedelta(days=5)).isoformat()
        },
        {
            "id": "INV-AUDIT-002",
            "type": "out",
            "product_id": "PRD-AUDIT-001",
            "product_name": "Charger Fast 20W USB-C",
            "warehouse_id": "WH-AUDIT-001",
            "qty": 10,
            "reference": "TRX-AUDIT-001",
            "notes": "Penjualan",
            "created_at": (today - timedelta(days=3)).isoformat()
        },
        {
            "id": "INV-AUDIT-003",
            "type": "transfer",
            "product_id": "PRD-AUDIT-003",
            "product_name": "Kabel USB-C to USB-C 1M",
            "from_warehouse_id": "WH-AUDIT-001",
            "to_warehouse_id": "WH-AUDIT-002",
            "qty": 20,
            "notes": "Transfer ke cabang Martapura",
            "created_at": (today - timedelta(days=2)).isoformat()
        },
    ]
    
    for m in movements:
        await db["inventory_movements"].update_one({"id": m["id"]}, {"$set": m}, upsert=True)
    
    return {"count": len(movements)}


@router.post("/cash")
async def seed_cash_transactions():
    """Seed cash transactions"""
    db = get_db()
    today = datetime.now(timezone.utc)
    
    cash_trans = [
        {
            "id": "CASH-AUDIT-001",
            "type": "in",
            "account_id": "COA-AUDIT-001",
            "amount": 5000000,
            "description": "Setoran modal awal",
            "reference": "Modal",
            "created_at": (today - timedelta(days=10)).isoformat()
        },
        {
            "id": "CASH-AUDIT-002",
            "type": "in",
            "account_id": "COA-AUDIT-001",
            "amount": 2500000,
            "description": "Penerimaan dari penjualan tunai",
            "reference": "TRX-AUDIT-001",
            "created_at": (today - timedelta(days=5)).isoformat()
        },
        {
            "id": "CASH-AUDIT-003",
            "type": "out",
            "account_id": "COA-AUDIT-001",
            "amount": 1000000,
            "description": "Pembayaran supplier",
            "reference": "PO-AUDIT-001",
            "created_at": (today - timedelta(days=3)).isoformat()
        },
        {
            "id": "CASH-AUDIT-004",
            "type": "transfer",
            "from_account_id": "COA-AUDIT-001",
            "to_account_id": "COA-AUDIT-002",
            "amount": 3000000,
            "description": "Setor ke Bank BCA",
            "created_at": (today - timedelta(days=1)).isoformat()
        },
    ]
    
    for c in cash_trans:
        await db["cash_transactions"].update_one({"id": c["id"]}, {"$set": c}, upsert=True)
    
    return {"count": len(cash_trans)}


@router.post("/setoran")
async def seed_setoran():
    """Seed setoran harian dan selisih kas"""
    db = get_db()
    today = datetime.now(timezone.utc)
    
    # Setoran harian
    setoran = [
        {
            "id": "SET-AUDIT-001",
            "tanggal": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
            "branch_id": "BR001",
            "branch_name": "OCB Banjarmasin Pusat",
            "penjaga_id": "EMP-SEED-011",
            "penjaga_name": "Kartini",
            "total_penjualan": 5500000,
            "total_setoran": 5500000,
            "selisih": 0,
            "status": "approved",
            "created_at": (today - timedelta(days=3)).isoformat()
        },
        {
            "id": "SET-AUDIT-002",
            "tanggal": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
            "branch_id": "BR001",
            "branch_name": "OCB Banjarmasin Pusat",
            "penjaga_id": "EMP-SEED-012",
            "penjaga_name": "Lukman Hakim",
            "total_penjualan": 4200000,
            "total_setoran": 4150000,
            "selisih": -50000,
            "status": "pending",
            "created_at": (today - timedelta(days=2)).isoformat()
        },
        {
            "id": "SET-AUDIT-003",
            "tanggal": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "branch_id": "BR002",
            "branch_name": "OCB Martapura",
            "penjaga_id": "EMP-SEED-013",
            "penjaga_name": "Maya Sari",
            "total_penjualan": 3800000,
            "total_setoran": 3800000,
            "selisih": 0,
            "status": "approved",
            "created_at": (today - timedelta(days=1)).isoformat()
        },
    ]
    
    for s in setoran:
        await db["setoran_harian"].update_one({"id": s["id"]}, {"$set": s}, upsert=True)
    
    # Selisih kas
    selisih = [
        {
            "id": "SEL-AUDIT-001",
            "setoran_id": "SET-AUDIT-002",
            "tanggal": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
            "branch_id": "BR001",
            "penjaga_id": "EMP-SEED-012",
            "penjaga_name": "Lukman Hakim",
            "nominal": 50000,
            "jenis": "minus",
            "keterangan": "Selisih kasir",
            "resolution": "pending",
            "created_at": (today - timedelta(days=2)).isoformat()
        },
    ]
    
    for sl in selisih:
        await db["selisih_kas"].update_one({"id": sl["id"]}, {"$set": sl}, upsert=True)
    
    return {"setoran": len(setoran), "selisih": len(selisih)}


@router.post("/crm")
async def seed_crm_data():
    """Seed CRM data"""
    db = get_db()
    today = datetime.now(timezone.utc)
    
    crm_customers = [
        {
            "id": "CRM-AUDIT-001",
            "customer_id": "CUS-AUDIT-001",
            "name": "Toko Maju Jaya",
            "phone": "0811111001",
            "email": "majujaya@mail.com",
            "total_transactions": 15,
            "total_spent": 7500000,
            "last_transaction": (today - timedelta(days=5)).isoformat(),
            "segment": "gold",
            "ai_character": "Pelanggan loyal dengan frekuensi tinggi",
            "recommendations": ["Tawarkan produk premium", "Berikan diskon khusus member"],
            "created_at": now_iso()
        },
        {
            "id": "CRM-AUDIT-002",
            "customer_id": "CUS-AUDIT-005",
            "name": "Toko Makmur",
            "phone": "0811111005",
            "email": "makmur@mail.com",
            "total_transactions": 25,
            "total_spent": 15000000,
            "last_transaction": (today - timedelta(days=2)).isoformat(),
            "segment": "platinum",
            "ai_character": "Pelanggan VIP dengan nilai transaksi tinggi",
            "recommendations": ["Prioritaskan layanan", "Undang ke program loyalty"],
            "created_at": now_iso()
        },
    ]
    
    for c in crm_customers:
        await db["crm_customers"].update_one({"id": c["id"]}, {"$set": c}, upsert=True)
    
    return {"count": len(crm_customers)}


@router.post("/kpi")
async def seed_kpi_targets():
    """Seed KPI targets"""
    db = get_db()
    today = datetime.now(timezone.utc)
    
    kpi_targets = [
        {
            "id": "KPI-AUDIT-001",
            "employee_id": "EMP-SEED-001",
            "employee_name": "Ahmad Ridwan",
            "period_month": today.month,
            "period_year": today.year,
            "target_sales": 50000000,
            "actual_sales": 45000000,
            "target_transactions": 100,
            "actual_transactions": 85,
            "score": 87,
            "status": "on_track",
            "created_at": now_iso()
        },
        {
            "id": "KPI-AUDIT-002",
            "employee_id": "EMP-SEED-003",
            "employee_name": "Budi Santoso",
            "period_month": today.month,
            "period_year": today.year,
            "target_sales": 40000000,
            "actual_sales": 42000000,
            "target_transactions": 80,
            "actual_transactions": 95,
            "score": 105,
            "status": "exceeded",
            "created_at": now_iso()
        },
    ]
    
    for k in kpi_targets:
        await db["kpi_targets"].update_one({"id": k["id"]}, {"$set": k}, upsert=True)
    
    return {"count": len(kpi_targets)}


@router.post("/alerts")
async def seed_alerts():
    """Seed warroom alerts"""
    db = get_db()
    today = datetime.now(timezone.utc)
    
    alerts = [
        {
            "id": "ALT-AUDIT-001",
            "type": "minus_kas",
            "severity": "warning",
            "title": "Selisih Kas Cabang Banjarmasin",
            "message": "Ditemukan selisih kas minus Rp 50.000 pada kasir Lukman Hakim",
            "branch_id": "BR001",
            "employee_id": "EMP-SEED-012",
            "is_read": False,
            "is_resolved": False,
            "created_at": (today - timedelta(hours=5)).isoformat()
        },
        {
            "id": "ALT-AUDIT-002",
            "type": "low_stock",
            "severity": "info",
            "title": "Stok Menipis",
            "message": "Produk Powerbank 20000mAh mendekati batas minimum stok",
            "product_id": "PRD-AUDIT-010",
            "is_read": True,
            "is_resolved": False,
            "created_at": (today - timedelta(days=1)).isoformat()
        },
        {
            "id": "ALT-AUDIT-003",
            "type": "high_sales",
            "severity": "info",
            "title": "Penjualan Tinggi",
            "message": "Cabang Martapura mencapai target penjualan harian",
            "branch_id": "BR002",
            "is_read": False,
            "is_resolved": True,
            "created_at": (today - timedelta(hours=2)).isoformat()
        },
    ]
    
    for a in alerts:
        await db["system_alerts"].update_one({"id": a["id"]}, {"$set": a}, upsert=True)
    
    return {"count": len(alerts)}


# Endpoint to check data counts
@router.get("/check")
async def check_audit_data():
    """Check counts of all audit data"""
    db = get_db()
    
    counts = {}
    collections = [
        "categories", "units", "brands", "warehouses", "suppliers", 
        "customers", "sales_persons", "customer_groups", "regions",
        "emoney", "banks", "shipping_costs", "products", "chart_of_accounts",
        "transactions", "purchases", "inventory_movements", "cash_transactions",
        "setoran_harian", "selisih_kas", "crm_customers", "kpi_targets", "system_alerts"
    ]
    
    for col in collections:
        counts[col] = await db[col].count_documents({})
    
    return counts
