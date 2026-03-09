# OCB GROUP - 40 Branch Seeder
# Generate dummy data for 40 branches across Indonesia

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone
import random

load_dotenv()

# Branch data for OCB GROUP across Indonesia
BRANCHES_DATA = [
    # Kalimantan Selatan
    {"code": "BJM-01", "name": "OCB Banjarmasin Pusat", "city": "Banjarmasin", "province": "Kalimantan Selatan", "is_warehouse": True},
    {"code": "BJM-02", "name": "OCB Banjarmasin Duta Mall", "city": "Banjarmasin", "province": "Kalimantan Selatan"},
    {"code": "BJM-03", "name": "OCB Banjarmasin Q Mall", "city": "Banjarmasin", "province": "Kalimantan Selatan"},
    {"code": "BJB-01", "name": "OCB Banjarbaru", "city": "Banjarbaru", "province": "Kalimantan Selatan"},
    {"code": "MTR-01", "name": "OCB Martapura", "city": "Martapura", "province": "Kalimantan Selatan"},
    {"code": "PLH-01", "name": "OCB Pelaihari", "city": "Pelaihari", "province": "Kalimantan Selatan"},
    {"code": "RTB-01", "name": "OCB Rantau", "city": "Rantau", "province": "Kalimantan Selatan"},
    {"code": "KDG-01", "name": "OCB Kandangan", "city": "Kandangan", "province": "Kalimantan Selatan"},
    {"code": "AMT-01", "name": "OCB Amuntai", "city": "Amuntai", "province": "Kalimantan Selatan"},
    {"code": "BTL-01", "name": "OCB Batulicin", "city": "Batulicin", "province": "Kalimantan Selatan"},
    
    # Kalimantan Timur
    {"code": "SMD-01", "name": "OCB Samarinda Pusat", "city": "Samarinda", "province": "Kalimantan Timur", "is_warehouse": True},
    {"code": "SMD-02", "name": "OCB Samarinda Big Mall", "city": "Samarinda", "province": "Kalimantan Timur"},
    {"code": "BPP-01", "name": "OCB Balikpapan Pusat", "city": "Balikpapan", "province": "Kalimantan Timur", "is_warehouse": True},
    {"code": "BPP-02", "name": "OCB Balikpapan E-Walk", "city": "Balikpapan", "province": "Kalimantan Timur"},
    {"code": "BPP-03", "name": "OCB Balikpapan Plaza", "city": "Balikpapan", "province": "Kalimantan Timur"},
    {"code": "BNT-01", "name": "OCB Bontang", "city": "Bontang", "province": "Kalimantan Timur"},
    {"code": "TRK-01", "name": "OCB Tenggarong", "city": "Tenggarong", "province": "Kalimantan Timur"},
    
    # Kalimantan Tengah
    {"code": "PKY-01", "name": "OCB Palangkaraya Pusat", "city": "Palangkaraya", "province": "Kalimantan Tengah", "is_warehouse": True},
    {"code": "PKY-02", "name": "OCB Palangkaraya Mega Mall", "city": "Palangkaraya", "province": "Kalimantan Tengah"},
    {"code": "SPT-01", "name": "OCB Sampit", "city": "Sampit", "province": "Kalimantan Tengah"},
    {"code": "PBN-01", "name": "OCB Pangkalan Bun", "city": "Pangkalan Bun", "province": "Kalimantan Tengah"},
    
    # Kalimantan Barat
    {"code": "PTK-01", "name": "OCB Pontianak Pusat", "city": "Pontianak", "province": "Kalimantan Barat", "is_warehouse": True},
    {"code": "PTK-02", "name": "OCB Pontianak Gajah Mada", "city": "Pontianak", "province": "Kalimantan Barat"},
    {"code": "SGW-01", "name": "OCB Singkawang", "city": "Singkawang", "province": "Kalimantan Barat"},
    {"code": "KTP-01", "name": "OCB Ketapang", "city": "Ketapang", "province": "Kalimantan Barat"},
    
    # Kalimantan Utara
    {"code": "TRK-01", "name": "OCB Tarakan", "city": "Tarakan", "province": "Kalimantan Utara"},
    
    # Sulawesi
    {"code": "MKS-01", "name": "OCB Makassar Pusat", "city": "Makassar", "province": "Sulawesi Selatan", "is_warehouse": True},
    {"code": "MKS-02", "name": "OCB Makassar Mall Panakkukang", "city": "Makassar", "province": "Sulawesi Selatan"},
    {"code": "MDO-01", "name": "OCB Manado", "city": "Manado", "province": "Sulawesi Utara"},
    {"code": "PLU-01", "name": "OCB Palu", "city": "Palu", "province": "Sulawesi Tengah"},
    {"code": "KDR-01", "name": "OCB Kendari", "city": "Kendari", "province": "Sulawesi Tenggara"},
    
    # Jawa
    {"code": "JKT-01", "name": "OCB Jakarta Pusat", "city": "Jakarta", "province": "DKI Jakarta", "is_warehouse": True},
    {"code": "JKT-02", "name": "OCB Jakarta Mangga Dua", "city": "Jakarta", "province": "DKI Jakarta"},
    {"code": "SBY-01", "name": "OCB Surabaya Pusat", "city": "Surabaya", "province": "Jawa Timur", "is_warehouse": True},
    {"code": "SBY-02", "name": "OCB Surabaya Tunjungan", "city": "Surabaya", "province": "Jawa Timur"},
    {"code": "BDG-01", "name": "OCB Bandung Pusat", "city": "Bandung", "province": "Jawa Barat"},
    {"code": "SMG-01", "name": "OCB Semarang Pusat", "city": "Semarang", "province": "Jawa Tengah"},
    {"code": "YGY-01", "name": "OCB Yogyakarta", "city": "Yogyakarta", "province": "DI Yogyakarta"},
    
    # Sumatera
    {"code": "MDN-01", "name": "OCB Medan Pusat", "city": "Medan", "province": "Sumatera Utara", "is_warehouse": True},
    {"code": "PLB-01", "name": "OCB Palembang", "city": "Palembang", "province": "Sumatera Selatan"},
]

async def seed_branches():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'ocb_titan')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print(f"Seeding {len(BRANCHES_DATA)} branches to {db_name}...")
    
    # Check existing branches
    existing_count = await db['branches'].count_documents({})
    if existing_count >= 40:
        print(f"Already have {existing_count} branches. Skipping seed.")
        return
    
    # Clear existing and seed new
    # await db['branches'].delete_many({})  # TIDAK HAPUS - sesuai aturan
    
    branches = []
    for idx, branch_data in enumerate(BRANCHES_DATA):
        branch = {
            "id": str(uuid.uuid4()),
            "code": branch_data["code"],
            "name": branch_data["name"],
            "address": f"Jl. Raya {branch_data['city']} No. {random.randint(1, 100)}",
            "city": branch_data["city"],
            "province": branch_data.get("province", ""),
            "phone": f"0{random.randint(811, 899)}{random.randint(1000000, 9999999)}",
            "email": f"{branch_data['code'].lower().replace('-', '')}@ocbgroup.co.id",
            "is_warehouse": branch_data.get("is_warehouse", False),
            "is_active": True,
            "manager_id": None,
            "cash_balance": random.randint(5000000, 50000000),
            "target_monthly": random.randint(100000000, 500000000),
            "settings": {
                "opening_hour": "09:00",
                "closing_hour": "21:00",
                "enable_delivery": True,
                "enable_pickup": True
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        branches.append(branch)
    
    # Insert branches
    result = await db['branches'].insert_many(branches)
    print(f"Successfully seeded {len(result.inserted_ids)} branches")
    
    # Create index
    await db['branches'].create_index("code", unique=True)
    await db['branches'].create_index("city")
    await db['branches'].create_index("province")
    
    return branches

async def seed_sample_products():
    """Seed sample products for all branches"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'ocb_titan')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Sample products
    products = [
        {"code": "HP-SAM-A54", "name": "Samsung Galaxy A54 5G", "category": "Smartphone", "cost_price": 4500000, "selling_price": 5200000},
        {"code": "HP-SAM-S24", "name": "Samsung Galaxy S24 Ultra", "category": "Smartphone", "cost_price": 18000000, "selling_price": 21000000},
        {"code": "HP-IPH-15", "name": "iPhone 15 Pro Max", "category": "Smartphone", "cost_price": 22000000, "selling_price": 25000000},
        {"code": "HP-XIA-14", "name": "Xiaomi 14 Ultra", "category": "Smartphone", "cost_price": 12000000, "selling_price": 14000000},
        {"code": "HP-OPP-R12", "name": "OPPO Reno 12 Pro", "category": "Smartphone", "cost_price": 5500000, "selling_price": 6500000},
        {"code": "ACC-CASE-01", "name": "Soft Case Universal", "category": "Aksesoris", "cost_price": 15000, "selling_price": 35000},
        {"code": "ACC-TG-01", "name": "Tempered Glass Premium", "category": "Aksesoris", "cost_price": 10000, "selling_price": 50000},
        {"code": "ACC-CHG-20W", "name": "Charger Fast 20W", "category": "Aksesoris", "cost_price": 45000, "selling_price": 85000},
        {"code": "ACC-CABL-TC", "name": "Kabel Type-C 1M", "category": "Aksesoris", "cost_price": 12000, "selling_price": 35000},
        {"code": "ACC-TWS-01", "name": "TWS Bluetooth Earbuds", "category": "Aksesoris", "cost_price": 80000, "selling_price": 150000},
        {"code": "TAB-SAM-A9", "name": "Samsung Tab A9+", "category": "Tablet", "cost_price": 3200000, "selling_price": 3800000},
        {"code": "TAB-IPD-10", "name": "iPad 10th Gen", "category": "Tablet", "cost_price": 6500000, "selling_price": 7500000},
        {"code": "PLN-TEL-10K", "name": "Pulsa Telkomsel 10K", "category": "Pulsa", "cost_price": 10000, "selling_price": 11000},
        {"code": "PLN-TEL-50K", "name": "Pulsa Telkomsel 50K", "category": "Pulsa", "cost_price": 50000, "selling_price": 51500},
        {"code": "PLN-IND-10K", "name": "Pulsa Indosat 10K", "category": "Pulsa", "cost_price": 10000, "selling_price": 11000},
    ]
    
    existing = await db['products'].count_documents({})
    if existing >= 10:
        print(f"Already have {existing} products. Skipping.")
        return
    
    for prod in products:
        product = {
            "id": str(uuid.uuid4()),
            "code": prod["code"],
            "barcode": f"899{random.randint(10000000, 99999999)}",
            "name": prod["name"],
            "description": f"Produk {prod['name']} original garansi resmi",
            "category_id": None,
            "brand": prod["name"].split()[0],
            "unit": "pcs",
            "cost_price": prod["cost_price"],
            "selling_price": prod["selling_price"],
            "wholesale_price": prod["selling_price"] * 0.95,
            "member_price": prod["selling_price"] * 0.97,
            "track_stock": True,
            "min_stock": 5,
            "is_active": True,
            "tax_rate": 11,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await db['products'].insert_one(product)
            print(f"Added product: {prod['name']}")
        except:
            pass  # Skip if exists
    
    # Seed stock for all branches
    branches = await db['branches'].find({}, {"id": 1}).to_list(None)
    products_list = await db['products'].find({}, {"id": 1}).to_list(None)
    
    for branch in branches:
        for product in products_list:
            stock = {
                "id": str(uuid.uuid4()),
                "product_id": product["id"],
                "branch_id": branch["id"],
                "quantity": random.randint(0, 50),
                "reserved": 0,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            try:
                await db['product_stocks'].update_one(
                    {"product_id": product["id"], "branch_id": branch["id"]},
                    {"$setOnInsert": stock},
                    upsert=True
                )
            except:
                pass

async def seed_sample_customers():
    """Seed sample customers"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'ocb_titan')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    existing = await db['customers'].count_documents({})
    if existing >= 20:
        print(f"Already have {existing} customers. Skipping.")
        return
    
    names = [
        "Budi Santoso", "Siti Rahayu", "Ahmad Wijaya", "Dewi Lestari", "Rudi Hartono",
        "Ani Susanti", "Joko Prasetyo", "Maya Sari", "Eko Nugroho", "Rina Wati",
        "Hendra Gunawan", "Lisa Permata", "Agus Setiawan", "Yuni Astuti", "Dedi Kurniawan",
        "Putri Handayani", "Bambang Sugiarto", "Mega Puspita", "Fajar Hidayat", "Sari Indah"
    ]
    
    segments = ["regular", "member", "vip", "reseller"]
    cities = ["Banjarmasin", "Banjarbaru", "Martapura", "Samarinda", "Balikpapan"]
    
    for name in names:
        customer = {
            "id": str(uuid.uuid4()),
            "code": f"CUST{random.randint(10000, 99999)}",
            "name": name,
            "phone": f"08{random.randint(11, 99)}{random.randint(10000000, 99999999)}",
            "whatsapp": f"628{random.randint(11, 99)}{random.randint(10000000, 99999999)}",
            "email": f"{name.lower().replace(' ', '.')}@email.com",
            "address": f"Jl. {name.split()[1]} No. {random.randint(1, 100)}",
            "city": random.choice(cities),
            "segment": random.choice(segments),
            "activity_status": random.choice(["active", "passive", "new"]),
            "lifetime_value": random.randint(500000, 50000000),
            "total_orders": random.randint(1, 50),
            "total_spent": random.randint(500000, 50000000),
            "loyalty_points": random.randint(0, 10000),
            "opt_in_marketing": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await db['customers'].insert_one(customer)
            print(f"Added customer: {name}")
        except:
            pass

async def main():
    print("=" * 50)
    print("OCB GROUP - Data Seeder")
    print("=" * 50)
    
    await seed_branches()
    await seed_sample_products()
    await seed_sample_customers()
    
    print("\nSeeding complete!")

if __name__ == "__main__":
    asyncio.run(main())
