# OCB TITAN RETAIL AI SYSTEM
## Enterprise Retail Operating System for OCB GROUP

**Version:** 1.0.0  
**Last Updated:** March 8, 2026

---

## System Overview

OCB TITAN is a comprehensive enterprise retail AI operating system designed to support:
- 40+ branches
- 130+ employees
- Scalable to 500+ branches
- Thousands of daily transactions

---

## Technology Stack

- **Frontend:** React 18 + Tailwind CSS
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Authentication:** JWT (7-day expiration)

---

## Implemented Modules

### ✅ Core Platform
- Multi-branch architecture
- Role-based access control (Owner, Admin, Supervisor, Cashier, Finance, Inventory)
- Audit logging
- Auto-numbering sequences (INV, PO, TRF, OPN, PRD, CUS)

### ✅ MODULE 1: POS System
- Fast checkout interface
- Barcode scanner support
- Product search (code, barcode, name)
- Shopping cart management
- Multiple payment methods (Cash, QRIS, Bank Transfer, E-Wallet)
- Split payment support
- Hold/Recall transactions
- Transaction discount (% or fixed)
- Item-level discount
- Invoice generation

### ✅ MODULE 2: Product Management
- Product catalog with pricing
- Multiple price tiers (Selling, Wholesale, Member, Reseller)
- Category management
- Barcode support
- Stock tracking settings
- Minimum stock alerts

### ✅ MODULE 3: Inventory Management
- Stock per branch
- Low stock alerts
- Stock adjustments
- Stock movement history
- Stock transfers (request, send, receive)
- Stock opname (physical count)

### ✅ MODULE 6: Customer Management
- Customer database
- Segment classification (Regular, Member, VIP, Reseller, Wholesale)
- Loyalty points
- Purchase history tracking
- Auto-pricing by segment

### ✅ MODULE 8: Financial Management
- Cash balance per branch
- Cash in/out tracking
- Expense management
- Daily financial reports

### ✅ MODULE 10: Owner Dashboard
- Real-time sales metrics
- Branch performance comparison
- Best selling products
- Low stock alerts
- Employee count by branch
- 7-day sales trend chart

### ✅ MODULE 11: User Management
- Role-based permissions
- Multi-branch access
- Password management
- Audit logs

### ✅ MODULE 12: Branch Management
- Branch profiles
- Warehouse designation
- Cash balance tracking
- Employee assignment

---

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user

### Products
- `GET /api/products` - List products
- `GET /api/products/search` - Quick search for POS
- `GET /api/products/barcode/{barcode}` - Scan barcode
- `POST /api/products` - Create product
- `PUT /api/products/{id}` - Update product
- `GET /api/products/categories` - List categories
- `POST /api/products/categories` - Create category

### POS
- `POST /api/pos/transaction` - Create sale
- `POST /api/pos/hold` - Hold transaction
- `GET /api/pos/held` - List held transactions
- `POST /api/pos/void/{id}` - Void transaction
- `GET /api/pos/transactions` - Transaction history
- `GET /api/pos/summary/today` - Daily summary

### Inventory
- `GET /api/inventory/stock` - Stock overview
- `GET /api/inventory/stock/low` - Low stock alerts
- `POST /api/inventory/adjust` - Stock adjustment
- `POST /api/inventory/transfer` - Create transfer
- `GET /api/inventory/movements` - Movement history

### Customers
- `GET /api/customers` - List customers
- `GET /api/customers/search` - Quick search
- `POST /api/customers` - Create customer
- `PUT /api/customers/{id}` - Update customer

### Branches
- `GET /api/branches` - List branches
- `POST /api/branches` - Create branch
- `PUT /api/branches/{id}` - Update branch

### Finance
- `GET /api/finance/cash/balance` - Cash balance
- `POST /api/finance/cash/in` - Cash in
- `POST /api/finance/cash/out` - Cash out
- `GET /api/finance/cash/movements` - Cash movements
- `POST /api/finance/expenses` - Record expense
- `GET /api/finance/reports/daily` - Daily report

### Dashboard
- `GET /api/dashboard/owner` - Owner dashboard
- `GET /api/dashboard/branch` - Branch dashboard
- `GET /api/dashboard/sales-trend` - Sales trend
- `GET /api/dashboard/top-products` - Top products
- `GET /api/dashboard/cashier-performance` - Cashier metrics

### Reports
- `GET /api/reports/sales` - Sales report
- `GET /api/reports/inventory` - Inventory valuation
- `GET /api/reports/stock-movements` - Stock movement report
- `GET /api/reports/product-performance` - Product performance
- `GET /api/reports/branch-comparison` - Branch comparison

---

## Test Account

```
Email: owner@ocb.com
Password: owner123
Role: Owner
```

---

## Pending Modules (Future)

- MODULE 4: Purchase Management (UI)
- MODULE 5: Sales Channels (Wholesale, Online)
- MODULE 7: Supplier Management
- MODULE 9: Accounting (Journal, GL, P&L)
- MODULE 13: Business Reports (Advanced)
- MODULE 14: AI Business Automation
- MODULE 15: Marketing Automation
- MODULE 16: Enhanced Security

---

## File Structure

```
/app/backend/
├── models/titan_models.py    # All data models
├── database.py               # MongoDB collections
├── server.py                 # FastAPI main
├── utils/auth.py            # JWT authentication
└── routes/
    ├── auth.py              # Authentication
    ├── products.py          # Product management
    ├── pos.py               # POS transactions
    ├── inventory.py         # Stock management
    ├── master_data.py       # Branches, Customers, Suppliers
    ├── purchase.py          # Purchase orders
    ├── finance.py           # Cash & expenses
    ├── dashboard.py         # Analytics
    ├── users.py             # User management
    └── reports.py           # Business reports

/app/frontend/src/
├── contexts/AuthContext.jsx
├── components/layout/
│   ├── Sidebar.jsx
│   └── DashboardLayout.jsx
└── pages/
    ├── Login.jsx
    ├── Dashboard.jsx
    ├── POS.jsx
    ├── Products.jsx
    ├── Inventory.jsx
    ├── Customers.jsx
    └── Branches.jsx
```
