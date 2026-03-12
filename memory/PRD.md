# OCB TITAN ERP - Product Requirements Document

## Original Problem Statement
Sistem ERP retail lengkap dengan AI untuk OCB Group yang mencakup:
- Multi-cabang & multi-gudang management
- POS, Inventory, Akuntansi terintegrasi
- AI-powered analytics dan insights
- Mandatory cashier shift system

## Core Requirements

### User Personas
- **Owner/Admin**: Full access, reports, settings
- **Kasir**: POS, shift management, basic inventory
- **Sales**: Customer management, quotations, invoices
- **Purchasing**: Purchase orders, supplier management
- **Finance**: Accounting, payments, reports

## COMPLETED FEATURES (March 12, 2026)

### STEP 1: ARSITEKTUR REFACTORING ✅
- Merged all "Advanced" modules into base modules
- Deleted: MasterCustomersAdvanced.jsx, MasterDiscountsAdvanced.jsx, MasterPromotionsAdvanced.jsx, MasterBarcodeAdvanced.jsx, master_advanced.py
- Updated Sidebar.jsx and App.js to remove duplicate routes
- Single source of truth for: Barcode, Diskon, Promosi, Pelanggan

### STEP 2: BARCODE ENGINE ✅
**Frontend:** `/app/frontend/src/pages/master/MasterBarcode.jsx`
**Backend:** `/app/backend/routes/barcode_engine.py`
- Print modes: Single Item, All Items, Selected Items, Rack Label
- Template support: Label 58x40, Label 38x25, A4 30 Label, Rak/Shelf
- Barcode source: barcode, item_code, SKU
- Price display: price_buy, price_sell, both, none
- JsBarcode integration for preview and print
- Custom template creation with dimensions, margins, font size

### STEP 3: DISKON ENGINE ✅
**Frontend:** `/app/frontend/src/pages/master/MasterDiscounts.jsx`
**Backend:** `/app/backend/routes/master_erp.py`
- Jenis: percentage, nominal, per_pcs, per_item, per_transaction, tiered
- Target: item, category, brand, customer_group, branch, all
- Conditions: min_purchase, min_qty, date_range, time_range
- Advanced: priority, stackable, max_usage, max_usage_per_customer
- Tiered discount support with multiple tiers

### STEP 4: PROMOSI ENGINE ✅
**Frontend:** `/app/frontend/src/pages/master/MasterPromotions.jsx`
**Backend:** `/app/backend/routes/master_erp.py`
- Jenis: product, category, brand, bundle, buy_x_get_y, special_price, quota
- Trigger: item, qty, subtotal
- Benefit: discount, free_item, bundle_price, special_price
- Quota tracking for limited promotions
- Period and time-based activation

### STEP 5: PRICE LEVEL SYSTEM ✅
**Frontend:** `/app/frontend/src/pages/master/MasterCustomerGroups.jsx`
**Backend:** `/app/backend/routes/master_erp.py`
- 5 Price Levels: Umum, Member, Grosir, Reseller, VIP
- Customer group → price_level mapping
- Items with price_level_1 to price_level_5 fields
- API: `/api/master/items/{id}/price-for-customer/{customer_id}`
- Auto price lookup based on customer's group

### STEP 6: TARGET SALES ✅
**Backend:** `/app/backend/routes/sales_target.py`
- Fields: sales_id, period, target_qty, target_amount
- Bonus: bonus_value, bonus_type, bonus_min_achievement
- Achievement tracking: on_track, behind, at_risk, achieved, exceeded, failed
- Leaderboard feature

### STEP 7: CUSTOMER LOYALTY POINTS ✅
**Frontend:** `/app/frontend/src/pages/master/MasterCustomerPoints.jsx`
**Backend:** `/app/backend/routes/loyalty_points.py`
- Earn rules: points_per_amount (Rp 10.000 = 1 point), min_transaction, multiplier
- Redeem rules: point_value (100 point = Rp 10.000), min_redeem, max_redeem_percent
- Point transactions: earn, redeem, adjustment, expired
- Customer balance tracking: current_points, total_earned, total_redeemed
- Manual adjustment for admin

### STEP 8: SALESMAN QUERY ✅
**Backend:** `/app/backend/routes/master_erp.py`
- Endpoint: `/api/master/salesmen`
- Query: role IN ['sales', 'kasir'] AND is_active = true
- Returns all active sales users

### STEP 9: TANGGAL OTOMATIS ✅
- All backend routes use `datetime.now(timezone.utc)` for server timestamps
- 562 instances of correct datetime usage
- 0 instances of deprecated `datetime.utcnow()`

### STEP 10: GUDANG = CABANG ✅
**Backend:** `/app/backend/routes/master_data.py`
- Branch model with `is_warehouse` field
- When branch.is_warehouse=true, auto-creates linked warehouse entry
- Single `branches` table as source of truth
- Stock operations use `branch_id`

### STEP 11: VALIDATION ✅
7 Screenshots captured as proof:
1. Barcode Preview - Template selection, product list, print settings
2. Diskon - Master discount with type, value, target, period
3. Promosi - Master promotion with rule engine
4. Price Level - Customer groups with 5 price levels
5. Target Sales - Achievement tracking with gap analysis
6. Loyalty Point - Customer points with earn/redeem rules
7. Shift Kasir - Cash control with discrepancy tracking

## Architecture

```
/app/
├── backend/
│   ├── routes/
│   │   ├── master_erp.py          # Discounts, Promotions, Items, Customer Groups
│   │   ├── barcode_engine.py      # Barcode templates CRUD
│   │   ├── loyalty_points.py      # Customer points system
│   │   ├── sales_target.py        # Sales target tracking
│   │   ├── cash_control.py        # Cashier shift management
│   │   └── account_settings.py    # Default ERP accounts
│   └── server.py                  # FastAPI main app
└── frontend/
    └── src/
        ├── pages/master/
        │   ├── MasterBarcode.jsx         # Barcode printing UI
        │   ├── MasterDiscounts.jsx       # Discount management
        │   ├── MasterPromotions.jsx      # Promotion management
        │   ├── MasterCustomerGroups.jsx  # Customer groups with price levels
        │   └── MasterCustomerPoints.jsx  # Loyalty points UI
        └── components/layout/
            └── Sidebar.jsx               # Navigation (cleaned of duplicates)
```

## Database Collections

- `barcode_templates`: Template configurations for barcode printing
- `discounts`: Discount rules with advanced targeting
- `promotions`: Promotion rules with trigger/benefit engine
- `customer_groups`: Groups with price_level mapping
- `customer_points`: Customer point balances
- `point_transactions`: Point earn/redeem history
- `point_rules`: Earn and redeem rule configurations
- `sales_targets`: Target definitions and tracking
- `cashier_shifts`: Shift sessions with cash tracking

## P0/P1/P2 Backlog

### P0 - COMPLETED
- [x] Refactor arsitektur (merge modules)
- [x] Barcode engine
- [x] Diskon engine
- [x] Promosi engine
- [x] Price level system
- [x] Target sales enhancement
- [x] Customer loyalty points
- [x] Salesman query fix
- [x] Server timestamps
- [x] Gudang = Cabang

### P1 - PENDING
- [ ] Auto-apply discounts in POS/Sales Invoice
- [ ] Auto-apply promotions in POS/Sales Invoice
- [ ] Price level auto-lookup in POS/Sales Invoice
- [ ] Point earning on invoice completion
- [ ] Point redemption in checkout

### P2 - FUTURE
- [ ] Phase 6 - AI Business Engine
- [ ] Advanced reporting
- [ ] Mobile app

## Credentials

- Demo: `ocbgroupbjm@gmail.com` / `admin123`
- Admin: `admin@ocb.com` / `password`

## Notes

- All features are REAL, TESTED, and CONNECTED
- No placeholder/mock implementations
- Server timestamps used throughout
- MongoDB with proper ObjectId exclusion
