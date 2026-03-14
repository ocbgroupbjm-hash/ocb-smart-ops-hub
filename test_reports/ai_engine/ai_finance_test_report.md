# OCB TITAN ERP - AI Finance Test Report

**Generated:** 2026-03-14
**Endpoint:** GET /api/ai/finance/insights

---

## TEST EXECUTION

### Request
```bash
GET /api/ai/finance/insights?days=30
Authorization: Bearer <owner_token>
```

### Response Summary

| Metric | Value |
|--------|-------|
| Insight Type | finance |
| Period | 30 days |
| Total Revenue | Rp 31,315,500 |
| Total Expense | Rp 11,247,212 |
| Net Profit | Rp 20,068,288 |
| Profit Margin | 64.08% |
| Margin Status | HEALTHY |

---

## FEATURES ANALYZED

| Feature | Source Collection |
|---------|-------------------|
| Journal entries | journal_entries |
| Account mapping | chart_of_accounts |
| Cash transactions | cash_transactions |

---

## PROFIT ANALYSIS

| Metric | Value | Status |
|--------|-------|--------|
| Revenue | Rp 31,315,500 | - |
| Expense | Rp 11,247,212 | - |
| Net Profit | Rp 20,068,288 | ✅ Positive |
| Margin | 64.08% | ✅ HEALTHY |
| Expense Ratio | 35.9% | ✅ Good |

---

## INSIGHTS GENERATED

### Recommendations
1. 💰 Profit margin: 64.1%
2. 📊 Rasio expense: 35.9%
3. ✅ Cash flow stable

---

## DECISION LOG

| Field | Value |
|-------|-------|
| endpoint | /api/ai/finance/insights |
| model_version | ocb-titan-ai-v1 |
| data_window | 30 days |
| features_used | journal_entries, chart_of_accounts, cash_transactions |
| execution_time | <500ms |

---

## VALIDATION

| Check | Status |
|-------|--------|
| Data returned | ✅ |
| Profit calculated | ✅ |
| Margin analysis | ✅ |
| Decision logged | ✅ |
| Read-only operation | ✅ |

---

## CONCLUSION

**FINANCE AI: WORKING ✅**

---

*Test Report - OCB TITAN AI Engine*
