#!/bin/bash
# OCB TITAN AI Pilot Monitoring Script
# Run this periodically to collect metrics

API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
TOKEN=$(curl -s -X POST "$API_URL/api/auth/login" -H "Content-Type: application/json" -d '{"email":"ocbgroupbjm@gmail.com","password":"admin123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

TIMESTAMP=$(date -Iseconds)
LOG_FILE="/app/test_reports/ai_pilot/monitoring_log.json"

# Initialize log file if not exists
if [ ! -f "$LOG_FILE" ]; then
    echo '{"checks": []}' > "$LOG_FILE"
fi

# Test endpoints and measure latency
test_endpoint() {
    local endpoint=$1
    local start=$(python3 -c "import time; print(time.time())")
    local response=$(curl -s -X GET "$API_URL$endpoint" -H "Authorization: Bearer $TOKEN")
    local end=$(python3 -c "import time; print(time.time())")
    local latency=$(python3 -c "print(f'{float($end) - float($start):.3f}')")
    local status=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print('ok' if d.get('insight_type') or d.get('status') else 'error')" 2>/dev/null || echo "error")
    echo "{\"endpoint\": \"$endpoint\", \"latency\": $latency, \"status\": \"$status\"}"
}

# Run tests
echo "=== AI Pilot Check: $TIMESTAMP ==="
echo ""

SALES=$(test_endpoint "/api/ai/sales/insights")
echo "Sales: $SALES"

INVENTORY=$(test_endpoint "/api/ai/inventory/insights")
echo "Inventory: $INVENTORY"

FINANCE=$(test_endpoint "/api/ai/finance/insights")
echo "Finance: $FINANCE"

CEO=$(test_endpoint "/api/ai/ceo/dashboard")
echo "CEO: $CEO"

# Calculate summary
TOTAL_LATENCY=$(echo "$SALES $INVENTORY $FINANCE $CEO" | python3 -c "
import sys, json, re
data = sys.stdin.read()
latencies = re.findall(r'\"latency\": (\d+\.?\d*)', data)
if latencies:
    avg = sum(float(l) for l in latencies) / len(latencies)
    print(f'{avg:.3f}')
else:
    print('0')
")

ERROR_COUNT=$(echo "$SALES $INVENTORY $FINANCE $CEO" | grep -c '"status": "error"')
TOTAL_TESTS=4
ERROR_RATE=$(python3 -c "print(f'{int($ERROR_COUNT) / $TOTAL_TESTS * 100:.2f}')")

echo ""
echo "=== Summary ==="
echo "Avg Latency: ${TOTAL_LATENCY}s (target: <2s)"
echo "Error Rate: ${ERROR_RATE}% (target: <1%)"
echo "Timestamp: $TIMESTAMP"

# Append to log
python3 << PYEOF
import json
import os

log_file = "$LOG_FILE"
check = {
    "timestamp": "$TIMESTAMP",
    "avg_latency": float("$TOTAL_LATENCY"),
    "error_rate": float("$ERROR_RATE"),
    "endpoints": {
        "sales": $SALES,
        "inventory": $INVENTORY,
        "finance": $FINANCE,
        "ceo": $CEO
    }
}

if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        data = json.load(f)
else:
    data = {"checks": []}

data["checks"].append(check)

# Keep last 100 checks
data["checks"] = data["checks"][-100:]

with open(log_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Logged to {log_file}")
PYEOF
