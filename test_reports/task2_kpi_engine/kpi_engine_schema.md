# Task 2: KPI Engine Schema Design

## Version: 1.0.0
## Date: 2026-03-14
## Blueprint: SUPER DUPER DEWA

---

## Collections

### 1. kpi_targets
Definition of KPI metrics and targets.

```json
{
  "id": "uuid",
  "code": "SALES-MTH",
  "name": "Target Penjualan Bulanan",
  "description": "Target penjualan per bulan",
  "category": "sales | performance | quality | attendance",
  "metric_type": "number | percentage | currency",
  "target_value": 100000000,
  "weight": 0.4,
  "period_type": "monthly | quarterly | yearly",
  "department_id": null,
  "is_active": true,
  "created_at": "ISO datetime"
}
```

### 2. kpi_results
Individual employee KPI tracking.

```json
{
  "id": "uuid",
  "employee_id": "uuid",
  "employee_name": "SAHRI",
  "kpi_target_id": "uuid",
  "kpi_code": "SALES-MTH",
  "kpi_name": "Target Penjualan Bulanan",
  
  "period": "2026-03",
  "target_value": 100000000,
  "actual_value": 85000000,
  "weight": 0.4,
  
  "achievement": 0.85,
  "weighted_score": 0.34,
  "rating": "below",
  
  "status": "in_progress | completed | reviewed"
}
```

### 3. kpi_reviews
Manager reviews and score adjustments.

```json
{
  "id": "uuid",
  "kpi_result_id": "uuid",
  "original_achievement": 0.85,
  "original_score": 0.34,
  "score_adjustment": 0.05,
  "final_score": 0.39,
  "rating": "meets",
  "review_notes": "Good progress despite challenges",
  "reviewer_name": "Manager Name"
}
```

---

## Calculation Formulas

### Achievement
```
achievement = actual_value / target_value
```

Example:
- actual = 85,000,000
- target = 100,000,000
- achievement = 85,000,000 / 100,000,000 = 0.85 (85%)

### Weighted Score
```
weighted_score = achievement × weight
```

Example:
- achievement = 0.85
- weight = 0.4
- weighted_score = 0.85 × 0.4 = 0.34

### Rating Determination
```
if achievement >= 1.2: rating = "exceeds"
elif achievement >= 0.9: rating = "meets"
elif achievement >= 0.7: rating = "below"
else: rating = "unsatisfactory"
```

### Normalized Score (Per Employee)
```
normalized_score = (total_weighted_score / total_weight) × 100
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/hr/kpi/targets | GET, POST | KPI target management |
| /api/hr/kpi/targets/{id} | GET | Get single target |
| /api/hr/kpi/assign | POST | Assign KPI to employee |
| /api/hr/kpi/results | GET | Get KPI results |
| /api/hr/kpi/results/{id} | GET, PUT | Get/Update result |
| /api/hr/kpi/reviews | POST | Submit manager review |
| /api/hr/kpi/dashboard/employee/{id} | GET | Employee KPI dashboard |
| /api/hr/kpi/dashboard/department/{id} | GET | Department ranking |

---

## Test Results

### KPI Target Creation
- Created 3 KPI targets (Sales, Attendance, Quality)
- Total weight = 1.0 (0.4 + 0.3 + 0.3)

### KPI Assignment & Calculation
- Employee: SAHRI
- KPI: Target Penjualan Bulanan
- Target: Rp 100,000,000
- Actual: Rp 85,000,000
- **Achievement: 85%**
- **Weighted Score: 0.34**
- **Rating: below**

### Score Calculation Verified ✅
```
achievement = 85,000,000 / 100,000,000 = 0.85
weighted_score = 0.85 × 0.4 = 0.34
rating = "below" (because 0.7 <= 0.85 < 0.9)
```

---

*Evidence file for Task 2 - KPI Engine Implementation*
