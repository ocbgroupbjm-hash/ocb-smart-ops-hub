# OCB TITAN AI - Seed Data untuk Testing
# Membuat data dummy yang realistis

from fastapi import APIRouter
from datetime import datetime, timezone, timedelta
import uuid
import random

router = APIRouter(prefix="/api/seed", tags=["Seed Data"])

def get_db():
    from database import get_db as db_get
    return db_get()

def gen_id():
    return str(uuid.uuid4())

def now_iso():
    return datetime.now(timezone.utc).isoformat()


@router.post("/all")
async def seed_all_data():
    """Seed semua data dummy untuk testing"""
    results = {}
    
    # 1. Seed Branches
    branches_result = await seed_branches()
    results["branches"] = branches_result
    
    # 2. Seed Jabatan
    jabatan_result = await seed_jabatan()
    results["jabatan"] = jabatan_result
    
    # 3. Seed Payroll Rules
    payroll_result = await seed_payroll_rules()
    results["payroll_rules"] = payroll_result
    
    # 4. Seed Employees
    employees_result = await seed_employees()
    results["employees"] = employees_result
    
    # 5. Seed Attendance (1 bulan)
    attendance_result = await seed_attendance()
    results["attendance"] = attendance_result
    
    # 6. Seed Transactions/Sales
    sales_result = await seed_transactions()
    results["transactions"] = sales_result
    
    return {"message": "Seed data berhasil", "results": results}


@router.post("/branches")
async def seed_branches():
    """Seed branches data"""
    db = get_db()
    branches = [
        {"id": "BR001", "name": "OCB Banjarmasin Pusat", "code": "BJM01", "city": "Banjarmasin", "address": "Jl. A. Yani Km 2", "phone": "0511-1234567", "is_active": True, "latitude": -3.3194, "longitude": 114.5907},
        {"id": "BR002", "name": "OCB Martapura", "code": "MTP01", "city": "Martapura", "address": "Jl. Sukaramai No. 10", "phone": "0511-2345678", "is_active": True, "latitude": -3.4167, "longitude": 114.8500},
        {"id": "BR003", "name": "OCB Banjarbaru", "code": "BBR01", "city": "Banjarbaru", "address": "Jl. A. Yani Km 35", "phone": "0511-3456789", "is_active": True, "latitude": -3.4419, "longitude": 114.8311},
        {"id": "BR004", "name": "OCB Balikpapan", "code": "BPP01", "city": "Balikpapan", "address": "Jl. MT Haryono No. 99", "phone": "0542-1234567", "is_active": True, "latitude": -1.2379, "longitude": 116.8529},
        {"id": "BR005", "name": "OCB Samarinda", "code": "SMD01", "city": "Samarinda", "address": "Jl. P. Diponegoro No. 50", "phone": "0541-1234567", "is_active": True, "latitude": -0.4948, "longitude": 117.1436},
    ]
    
    for br in branches:
        br["created_at"] = now_iso()
        await db["branches"].update_one({"id": br["id"]}, {"$set": br}, upsert=True)
    
    return {"count": len(branches), "message": f"{len(branches)} cabang berhasil diseed"}


@router.post("/jabatan")
async def seed_jabatan():
    """Seed jabatan data"""
    db = get_db()
    jabatan_list = [
        {"id": "JAB001", "code": "MGR", "name": "Store Manager", "level": 1, "department": "Management", "description": "Manager toko", "is_active": True},
        {"id": "JAB002", "code": "SPV", "name": "Supervisor", "level": 2, "department": "Operations", "description": "Supervisor operasional", "is_active": True},
        {"id": "JAB003", "code": "KSR", "name": "Kasir", "level": 3, "department": "Sales", "description": "Kasir toko", "is_active": True},
        {"id": "JAB004", "code": "SLS", "name": "Sales", "level": 3, "department": "Sales", "description": "Sales / pramuniaga", "is_active": True},
        {"id": "JAB005", "code": "GDG", "name": "Gudang", "level": 4, "department": "Warehouse", "description": "Staff gudang", "is_active": True},
        {"id": "JAB006", "code": "ADM", "name": "Admin", "level": 3, "department": "Admin", "description": "Staff administrasi", "is_active": True},
        {"id": "JAB007", "code": "DRV", "name": "Driver", "level": 4, "department": "Logistics", "description": "Driver pengiriman", "is_active": True},
        {"id": "JAB008", "code": "SCT", "name": "Security", "level": 4, "department": "Security", "description": "Petugas keamanan", "is_active": True},
    ]
    
    for jab in jabatan_list:
        jab["created_at"] = now_iso()
        await db["jabatan"].update_one({"id": jab["id"]}, {"$set": jab}, upsert=True)
    
    return {"count": len(jabatan_list), "message": f"{len(jabatan_list)} jabatan berhasil diseed"}


@router.post("/payroll-rules")
async def seed_payroll_rules():
    """Seed payroll rules per jabatan"""
    db = get_db()
    rules = [
        {"jabatan_id": "JAB001", "jabatan_name": "Store Manager", "gaji_pokok": 8000000, "tunjangan_jabatan": 1000000, "tunjangan_transport": 500000, "tunjangan_makan": 500000, "bonus_kehadiran_full": 500000, "potongan_telat_per_menit": 2000, "potongan_alpha_per_hari": 100000},
        {"jabatan_id": "JAB002", "jabatan_name": "Supervisor", "gaji_pokok": 5500000, "tunjangan_jabatan": 500000, "tunjangan_transport": 400000, "tunjangan_makan": 400000, "bonus_kehadiran_full": 350000, "potongan_telat_per_menit": 1500, "potongan_alpha_per_hari": 75000},
        {"jabatan_id": "JAB003", "jabatan_name": "Kasir", "gaji_pokok": 3500000, "tunjangan_jabatan": 200000, "tunjangan_transport": 300000, "tunjangan_makan": 300000, "bonus_kehadiran_full": 250000, "potongan_telat_per_menit": 1000, "potongan_alpha_per_hari": 50000},
        {"jabatan_id": "JAB004", "jabatan_name": "Sales", "gaji_pokok": 3500000, "tunjangan_jabatan": 200000, "tunjangan_transport": 300000, "tunjangan_makan": 300000, "bonus_kehadiran_full": 250000, "potongan_telat_per_menit": 1000, "potongan_alpha_per_hari": 50000},
        {"jabatan_id": "JAB005", "jabatan_name": "Gudang", "gaji_pokok": 3200000, "tunjangan_jabatan": 150000, "tunjangan_transport": 300000, "tunjangan_makan": 300000, "bonus_kehadiran_full": 200000, "potongan_telat_per_menit": 1000, "potongan_alpha_per_hari": 50000},
        {"jabatan_id": "JAB006", "jabatan_name": "Admin", "gaji_pokok": 3800000, "tunjangan_jabatan": 300000, "tunjangan_transport": 350000, "tunjangan_makan": 350000, "bonus_kehadiran_full": 300000, "potongan_telat_per_menit": 1000, "potongan_alpha_per_hari": 50000},
        {"jabatan_id": "JAB007", "jabatan_name": "Driver", "gaji_pokok": 3000000, "tunjangan_jabatan": 100000, "tunjangan_transport": 500000, "tunjangan_makan": 300000, "bonus_kehadiran_full": 200000, "potongan_telat_per_menit": 1000, "potongan_alpha_per_hari": 50000},
        {"jabatan_id": "JAB008", "jabatan_name": "Security", "gaji_pokok": 3000000, "tunjangan_jabatan": 100000, "tunjangan_transport": 250000, "tunjangan_makan": 250000, "bonus_kehadiran_full": 200000, "potongan_telat_per_menit": 1000, "potongan_alpha_per_hari": 50000},
    ]
    
    for rule in rules:
        rule["id"] = gen_id()
        rule["is_active"] = True
        rule["created_at"] = now_iso()
        await db["payroll_rules"].update_one({"jabatan_id": rule["jabatan_id"]}, {"$set": rule}, upsert=True)
    
    return {"count": len(rules), "message": f"{len(rules)} payroll rules berhasil diseed"}


@router.post("/employees")
async def seed_employees():
    """Seed employees data"""
    db = get_db()
    
    names = [
        ("Ahmad Ridwan", "L"), ("Siti Aminah", "P"), ("Budi Santoso", "L"),
        ("Dewi Lestari", "P"), ("Eko Prasetyo", "L"), ("Fitri Handayani", "P"),
        ("Gunawan", "L"), ("Hani Susanti", "P"), ("Irfan Maulana", "L"),
        ("Joko Widodo", "L"), ("Kartini", "P"), ("Lukman Hakim", "L"),
        ("Maya Sari", "P"), ("Nur Hidayat", "L"), ("Oki Setiawan", "L"),
        ("Putri Rahayu", "P"), ("Qori Amin", "L"), ("Rina Wati", "P"),
        ("Surya Darma", "L"), ("Tina Marlina", "P"), ("Udin Saputra", "L"),
        ("Vina Oktavia", "P"), ("Wahyu Nugroho", "L"), ("Yanti Permata", "P"),
    ]
    
    branches = ["BR001", "BR002", "BR003", "BR004", "BR005"]
    branch_names = ["OCB Banjarmasin Pusat", "OCB Martapura", "OCB Banjarbaru", "OCB Balikpapan", "OCB Samarinda"]
    jabatan = [
        ("JAB001", "Store Manager"), ("JAB002", "Supervisor"), 
        ("JAB003", "Kasir"), ("JAB004", "Sales"),
        ("JAB005", "Gudang"), ("JAB006", "Admin")
    ]
    
    employees = []
    for idx, (name, gender) in enumerate(names):
        br_idx = idx % len(branches)
        jab_idx = min(idx // 5, len(jabatan) - 1)  # Distribute across jabatan
        
        # Determine salary type
        salary_type = "daily" if jab_idx >= 4 else "monthly"
        
        emp = {
            "id": f"EMP-SEED-{idx+1:03d}",
            "nik": f"NK{2024000 + idx}",
            "name": name,
            "email": f"{name.lower().replace(' ', '.')}@ocb.com",
            "phone": f"08{random.randint(1000000000, 9999999999)}",
            "gender": gender,
            "jabatan_id": jabatan[jab_idx][0],
            "jabatan_name": jabatan[jab_idx][1],
            "branch_id": branches[br_idx],
            "branch_name": branch_names[br_idx],
            "department": "Operations",
            "join_date": f"202{random.randint(0, 3)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "contract_type": "tetap" if idx < 18 else "kontrak",
            "status": "active",
            "salary_type": salary_type,
            "gaji_pokok": [8000000, 5500000, 3500000, 3500000, 3200000, 3800000][jab_idx] if salary_type == "monthly" else 0,
            "upah_harian": 150000 if salary_type == "daily" else 0,
            "tunjangan_jabatan": [1000000, 500000, 200000, 200000, 150000, 300000][jab_idx],
            "tunjangan_transport": 300000,
            "tunjangan_makan": 300000,
            "potongan_bpjs_kes": 50000,
            "potongan_bpjs_tk": 30000,
            "bank_name": random.choice(["BCA", "BRI", "Mandiri", "BNI"]),
            "bank_account": str(random.randint(1000000000, 9999999999)),
            "payment_method": "transfer",
            "created_at": now_iso(),
            "updated_at": now_iso()
        }
        employees.append(emp)
    
    for emp in employees:
        await db["employees"].update_one({"id": emp["id"]}, {"$set": emp}, upsert=True)
    
    return {"count": len(employees), "message": f"{len(employees)} karyawan berhasil diseed"}


@router.post("/attendance")
async def seed_attendance():
    """Seed attendance data untuk 1 bulan terakhir"""
    db = get_db()
    
    # Get all employees
    employees = await db["employees"].find({"status": "active"}, {"_id": 0}).to_list(length=100)
    
    today = datetime.now(timezone.utc).date()
    start_date = today.replace(day=1)  # First day of current month
    
    attendance_records = []
    
    for emp in employees:
        current_date = start_date
        while current_date <= today:
            # Skip weekends (simple version)
            if current_date.weekday() < 6:  # Monday to Saturday
                # Random attendance status
                rand = random.random()
                if rand < 0.85:
                    status = "hadir"
                    # Random late (20% chance if hadir)
                    telat = random.randint(0, 45) if random.random() < 0.2 else 0
                    # Random overtime (15% chance)
                    lembur = random.randint(60, 180) if random.random() < 0.15 else 0
                elif rand < 0.92:
                    status = "izin"
                    telat = 0
                    lembur = 0
                elif rand < 0.96:
                    status = "sakit"
                    telat = 0
                    lembur = 0
                else:
                    status = "alpha"
                    telat = 0
                    lembur = 0
                
                record = {
                    "id": gen_id(),
                    "employee_id": emp["id"],
                    "employee_nik": emp.get("nik"),
                    "employee_name": emp.get("name"),
                    "branch_id": emp.get("branch_id"),
                    "branch_name": emp.get("branch_name"),
                    "tanggal": str(current_date),
                    "status": status,
                    "jam_masuk": f"08:{telat:02d}:00" if status == "hadir" else None,
                    "jam_pulang": "17:00:00" if status == "hadir" else None,
                    "telat_menit": telat,
                    "lembur_menit": lembur,
                    "approval_status": "approved" if status in ["izin", "sakit", "cuti"] else None,
                    "created_at": now_iso()
                }
                attendance_records.append(record)
            
            current_date += timedelta(days=1)
    
    # Insert attendance
    if attendance_records:
        await db["attendance"].delete_many({
            "tanggal": {"$gte": str(start_date)}
        })
        await db["attendance"].insert_many(attendance_records)
    
    return {"count": len(attendance_records), "message": f"{len(attendance_records)} record absensi berhasil diseed"}


@router.post("/transactions")
async def seed_transactions():
    """Seed transactions/sales data untuk 1 bulan"""
    db = get_db()
    
    # Get employees with sales role
    employees = await db["employees"].find({
        "status": "active",
        "jabatan_name": {"$in": ["Kasir", "Sales", "Supervisor"]}
    }, {"_id": 0}).to_list(length=50)
    
    today = datetime.now(timezone.utc)
    start_date = today.replace(day=1)
    
    transactions = []
    invoice_counter = 1
    
    for emp in employees:
        # Random number of transactions per employee per day
        current_date = start_date
        while current_date.date() <= today.date():
            if current_date.weekday() < 6:
                # 5-15 transactions per day
                num_trans = random.randint(5, 15)
                for _ in range(num_trans):
                    total = random.randint(50000, 2000000)
                    trans = {
                        "id": gen_id(),
                        "invoice_number": f"SEED-{current_date.strftime('%Y%m%d')}-{invoice_counter:06d}",
                        "cashier_id": emp["id"],
                        "cashier_name": emp.get("name"),
                        "branch_id": emp.get("branch_id"),
                        "branch_name": emp.get("branch_name"),
                        "total": total,
                        "payment_method": random.choice(["cash", "transfer", "card", "qris"]),
                        "status": "completed",
                        "created_at": current_date.isoformat()
                    }
                    transactions.append(trans)
                    invoice_counter += 1
            
            current_date += timedelta(days=1)
    
    # Delete old seed transactions first
    if transactions:
        await db["transactions"].delete_many({
            "invoice_number": {"$regex": "^SEED-"}
        })
        await db["transactions"].insert_many(transactions)
    
    return {"count": len(transactions), "message": f"{len(transactions)} transaksi berhasil diseed"}


@router.post("/selisih-kas")
async def seed_selisih_kas():
    """Seed selisih kas data"""
    db = get_db()
    
    employees = await db["employees"].find({
        "status": "active",
        "jabatan_name": "Kasir"
    }, {"_id": 0}).to_list(length=20)
    
    today = datetime.now(timezone.utc).date()
    records = []
    
    for emp in employees:
        # Random selisih kas (5% chance per employee)
        if random.random() < 0.3:
            for _ in range(random.randint(1, 3)):
                record = {
                    "id": gen_id(),
                    "penjaga_id": emp["id"],
                    "penjaga_name": emp.get("name"),
                    "branch_id": emp.get("branch_id"),
                    "tanggal": str(today - timedelta(days=random.randint(1, 30))),
                    "jenis": random.choice(["minus", "plus"]),
                    "nominal": random.randint(10000, 500000),
                    "keterangan": "Selisih kas harian",
                    "created_at": now_iso()
                }
                records.append(record)
    
    if records:
        await db["selisih_kas"].insert_many(records)
    
    return {"count": len(records), "message": f"{len(records)} selisih kas berhasil diseed"}
