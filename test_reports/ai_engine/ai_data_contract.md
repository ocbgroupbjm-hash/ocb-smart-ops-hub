# OCB TITAN ERP - AI Data Contract

**Generated:** 2026-03-14
**AI Engine Version:** 1.0.0

---

## PURPOSE

This document defines the data contract between the AI Engine and the Core ERP System.

---

## DATA SOURCES

### Collections AI Can Read

| Collection | Fields Used | Purpose |
|------------|-------------|---------|
| sales_invoices | id, date, items, grand_total, branch_id, customer_name | Sales analysis |
| products | id, name, cost, price, min_stock | Product insights |
| stock_movements | product_id, quantity, movement_type, created_at | Inventory analysis |
| stock | product_id, quantity, warehouse_id | Current stock |
| journal_entries | entries, journal_date, status | Finance analysis |
| chart_of_accounts | code, name, type | Account mapping |
| branches | id, name | Branch performance |
| cash_transactions | amount, date, type | Cash flow |

### Collections AI Cannot Access

| Collection | Reason |
|------------|--------|
| users | Security - contains passwords |
| sessions | Security - authentication data |
| api_keys | Security - credentials |
| _tenant_metadata | System internal |

---

## OUTPUT CONTRACTS

### Sales AI Output
```json
{
  "insight_type": "sales",
  "period_days": 30,
  "summary": {
    "total_transactions": number,
    "total_revenue": number,
    "avg_transaction_value": number,
    "growth_rate_7d": number
  },
  "top_products": [...],
  "slow_products": [...],
  "sales_trend": [...],
  "recommendations": [string]
}
```

### Inventory AI Output
```json
{
  "insight_type": "inventory",
  "summary": {
    "total_products": number,
    "dead_stock_count": number,
    "restock_needed_count": number,
    "inventory_health": "GOOD" | "NEEDS_ATTENTION"
  },
  "dead_stock": [...],
  "restock_recommendation": [...],
  "recommendations": [string]
}
```

### Finance AI Output
```json
{
  "insight_type": "finance",
  "period_days": 30,
  "summary": {
    "total_revenue": number,
    "total_expense": number,
    "net_profit": number,
    "profit_margin_percent": number,
    "total_assets": number,
    "total_liabilities": number
  },
  "cash_trend": [...],
  "profit_analysis": {...},
  "recommendations": [string]
}
```

### CEO Dashboard Output
```json
{
  "insight_type": "ceo_dashboard",
  "date": "YYYY-MM-DD",
  "omzet_hari_ini": {
    "value": number,
    "formatted": string,
    "transaction_count": number
  },
  "cabang_terbaik": [...],
  "cabang_minus": [...],
  "produk_terbaik_hari_ini": {...},
  "executive_summary": [string]
}
```

---

## QUERY LIMITS

| Limit | Value | Purpose |
|-------|-------|---------|
| Default query limit | 1000 | Prevent excessive data load |
| Max query limit | 5000 | Hard cap for aggregations |
| Period max | 365 days | Historical analysis limit |
| Result set max | 20 items | Top/bottom lists |

---

## DATA FRESHNESS

| Data Type | Freshness | Notes |
|-----------|-----------|-------|
| Sales | Real-time | Direct from collection |
| Inventory | Real-time | Direct from collection |
| Finance | Real-time | Posted journals only |
| Aggregations | On-demand | Computed per request |

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-14 | Initial contract |

---

*Data Contract - OCB TITAN AI Engine*
