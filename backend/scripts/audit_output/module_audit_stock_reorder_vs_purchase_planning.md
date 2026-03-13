# OCB TITAN AI - Module Audit: Stock Reorder vs Purchase Planning
**Date:** 2026-03-13
**Auditor:** E1 Agent

## Executive Summary

Setelah analisis mendalam kedua modul, ditemukan bahwa kedua modul memiliki **tujuan berbeda** dan **TIDAK DUPLICATE**:

- **Stock Reorder Engine**: Fokus pada **pengelolaan level stok** dan **reorder point**
- **Purchase Planning Engine**: Fokus pada **forecast dan planning pembelian**

Keduanya saling melengkapi, bukan duplicate.

---

## Comparison Table

| Aspek | Stock Reorder | Purchase Planning | Duplicate? |
|-------|---------------|-------------------|------------|
| **Tujuan Utama** | Monitoring stok dan trigger reorder | Forecast & planning pembelian | ❌ NO |
| **Input** | Min/Max stock, reorder point | Sales history, forecast | ❌ NO |
| **Output** | Reorder alerts, suggestions | Purchase plan documents | ❌ NO |
| **Rule Engine** | Safety stock, lead time calc | Sales velocity, seasonal adj | ❌ NO |
| **Inventory Dep** | ✓ SSOT stock_movements | ✓ SSOT stock_movements | Same SSOT |
| **Purchasing Dep** | ✓ Generate PO draft | ✓ Convert plan to PO | Workflow diff |
| **Dashboard** | Low stock alerts | Planning summary | Different |
| **Status Flow** | N/A (reactive) | draft→reviewed→approved→po | Different |

---

## Detailed Analysis

### Stock Reorder Engine (`/api/stock-reorder`)

**Purpose:** Real-time stock monitoring dan automatic reorder trigger

**Endpoints:**
- `GET /policy` - Get reorder policy settings
- `PUT /policy` - Update policy (safety_stock_days, lead_time, etc)
- `GET /settings/{product_id}` - Per-product min/max settings
- `PUT /settings` - Update product stock settings
- `GET /suggestions` - Get items needing reorder NOW
- `GET /velocity/{product_id}` - Sales velocity calculation
- `POST /generate-po-draft` - Quick PO draft from suggestions
- `GET /dashboard` - Reorder status overview
- `GET /low-stock-alerts` - Critical stock alerts

**Core Logic:**
```python
# Reorder Point Formula:
reorder_point = (velocity * lead_time_days) + safety_stock

# Safety Stock:
safety_stock = velocity * safety_stock_days

# Urgency Classification:
- CRITICAL: stock <= 0
- HIGH: stock < reorder_point
- MEDIUM: stock < (reorder_point * 1.5)
- LOW: stock < minimum_stock
```

**Use Case:** Operational - "Apa yang HARUS dibeli SEKARANG?"

---

### Purchase Planning Engine (`/api/purchase-planning`)

**Purpose:** Strategic purchase forecasting dan budget planning

**Endpoints:**
- `POST /generate` - Generate purchase plan from forecast
- `POST /manual` - Manually create planning item
- `GET /list` - List all planning documents
- `GET /{planning_id}` - Get planning detail
- `PUT /{planning_id}` - Update planning item
- `POST /{planning_id}/status` - Change status (draft→reviewed→approved)
- `POST /create-po` - Convert approved plan to PO
- `DELETE /{planning_id}` - Delete draft planning
- `GET /dashboard/summary` - Planning summary

**Core Logic:**
```python
# Recommended Qty Formula:
recommended_qty = (target_stock - current_stock) + (velocity * lead_time)

# Target Stock:
target_stock = velocity * (lead_time_days + safety_days)

# Planning Status Flow:
DRAFT → REVIEWED → APPROVED → PO_CREATED
```

**Use Case:** Strategic - "Apa yang AKAN dibeli dalam periode X?"

---

## Key Differences

| Feature | Stock Reorder | Purchase Planning |
|---------|---------------|-------------------|
| Timing | Real-time reactive | Planned proactive |
| Approval | No approval needed | Requires approval flow |
| Documents | Suggestions only | Planning documents |
| PO Creation | Direct draft | From approved plan |
| Budget Control | No | Yes (can track planned cost) |
| Audit Trail | Minimal | Full (status history) |

---

## Decision: KEEP BOTH

### Recommendation: **DO NOT MERGE OR REMOVE**

Both modules serve distinct business functions:

1. **Stock Reorder** = **Operational Tool**
   - Used by warehouse staff daily
   - Quick response to low stock
   - Automatic alerts

2. **Purchase Planning** = **Strategic Tool**
   - Used by purchasing managers
   - Budget planning
   - Approval workflow

### Integration Point

Both modules can work together:
1. Stock Reorder generates **urgent suggestions**
2. Purchase Planning can **import** these suggestions into a planning document
3. Planning goes through approval
4. Approved planning creates PO

---

## Action Items

1. ✅ **KEEP** Stock Reorder Engine
2. ✅ **KEEP** Purchase Planning Engine
3. 🔄 **INTEGRATE**: Add option in Purchase Planning to import from Stock Reorder suggestions
4. 📝 **DOCUMENT**: Clear UI labels to differentiate the two modules

---

## Endpoints Summary - Final

### Stock Reorder (Operational)
| Endpoint | Method | Keep? |
|----------|--------|-------|
| `/api/stock-reorder/policy` | GET/PUT | ✅ |
| `/api/stock-reorder/settings` | GET/PUT | ✅ |
| `/api/stock-reorder/suggestions` | GET | ✅ |
| `/api/stock-reorder/generate-po-draft` | POST | ✅ |
| `/api/stock-reorder/dashboard` | GET | ✅ |
| `/api/stock-reorder/low-stock-alerts` | GET | ✅ |

### Purchase Planning (Strategic)
| Endpoint | Method | Keep? |
|----------|--------|-------|
| `/api/purchase-planning/generate` | POST | ✅ |
| `/api/purchase-planning/list` | GET | ✅ |
| `/api/purchase-planning/status` | POST | ✅ |
| `/api/purchase-planning/create-po` | POST | ✅ |
| `/api/purchase-planning/dashboard` | GET | ✅ |

---

## Conclusion

**NO DUPLICATE FUNCTION FOUND.**

Both modules complement each other and should be kept separate with clear UI differentiation.
