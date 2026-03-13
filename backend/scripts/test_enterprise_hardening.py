#!/usr/bin/env python3
"""
OCB TITAN ERP - ENTERPRISE HARDENING TEST SUITE
MASTER BLUEPRINT: Phase 1 - 7 Guard Systems Validation

Generates evidence files for all guard systems:
1. period_lock_test_report.md
2. cash_variance_test_report.md
3. inventory_vs_gl_recon_report.md
4. idempotency_test_report.md
5. event_bus_test_report.md
6. integrity_monitor_report.md
7. backup_schedule_config.yml + backup_run_log.json
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone

# Configuration
BASE_URL = os.environ.get("API_URL", "https://smart-ops-hub-6.preview.emergentagent.com")
OUTPUT_DIR = "/app/backend/scripts/audit_output"
TEST_REPORTS_DIR = "/app/test_reports"

# Credentials
EMAIL = "ocbgroupbjm@gmail.com"
PASSWORD = "admin123"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEST_REPORTS_DIR, exist_ok=True)


def login():
    """Login and get token"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )
    if resp.status_code == 200:
        return resp.json().get("token")
    else:
        print(f"Login failed: {resp.text}")
        sys.exit(1)


def test_guard_system_1(token):
    """Test Accounting Period Lock"""
    print("\n" + "="*60)
    print("GUARD SYSTEM 1: ACCOUNTING PERIOD LOCK")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {"test": "accounting_period_lock", "timestamp": datetime.now(timezone.utc).isoformat(), "tests": []}
    
    # Test 1: List periods
    resp = requests.get(f"{BASE_URL}/api/accounting/periods", headers=headers)
    results["tests"].append({
        "name": "List Periods",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [1] List Periods: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Test 2: Lock period March 2026
    resp = requests.post(
        f"{BASE_URL}/api/accounting/periods/lock",
        headers=headers,
        json={"year": 2026, "month": 3, "reason": "Test lock for validation"}
    )
    results["tests"].append({
        "name": "Lock Period 2026-03",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [2] Lock Period 2026-03: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Test 3: Get period status
    resp = requests.get(f"{BASE_URL}/api/accounting/periods/2026/3", headers=headers)
    is_locked = resp.json().get("status") == "locked" if resp.status_code == 200 else False
    results["tests"].append({
        "name": "Verify Period Locked",
        "status": "PASS" if is_locked else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [3] Verify Period Locked: {'PASS' if is_locked else 'FAIL'}")
    
    # Test 4: Validate transaction date (should be blocked)
    resp = requests.post(
        f"{BASE_URL}/api/accounting/periods/validate?transaction_date=2026-03-15",
        headers=headers
    )
    is_blocked = not resp.json().get("allowed", True) if resp.status_code == 200 else False
    results["tests"].append({
        "name": "Validate Blocked Date",
        "status": "PASS" if is_blocked else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [4] Validate Blocked Date: {'PASS' if is_blocked else 'FAIL'}")
    
    # Test 5: Unlock period
    resp = requests.post(
        f"{BASE_URL}/api/accounting/periods/unlock",
        headers=headers,
        json={"year": 2026, "month": 3, "reason": "Unlocking for test cleanup"}
    )
    results["tests"].append({
        "name": "Unlock Period",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [5] Unlock Period: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Calculate overall
    passed = sum(1 for t in results["tests"] if t["status"] == "PASS")
    results["summary"] = {
        "total": len(results["tests"]),
        "passed": passed,
        "failed": len(results["tests"]) - passed,
        "overall": "PASS" if passed == len(results["tests"]) else "FAIL"
    }
    
    # Generate report
    report_path = f"{OUTPUT_DIR}/period_lock_test_report.md"
    with open(report_path, "w") as f:
        f.write("# OCB TITAN - ACCOUNTING PERIOD LOCK TEST REPORT\n\n")
        f.write(f"**Test Date:** {results['timestamp']}\n")
        f.write(f"**Overall Status:** {results['summary']['overall']}\n\n")
        f.write("## Test Results\n\n")
        f.write(f"| Test | Status |\n")
        f.write(f"|------|--------|\n")
        for t in results["tests"]:
            status_icon = "✅" if t["status"] == "PASS" else "❌"
            f.write(f"| {t['name']} | {status_icon} {t['status']} |\n")
        f.write(f"\n**Total:** {results['summary']['passed']}/{results['summary']['total']} PASSED\n")
    
    print(f"\n  Report saved: {report_path}")
    return results


def test_guard_system_2(token):
    """Test Cash Variance Engine"""
    print("\n" + "="*60)
    print("GUARD SYSTEM 2: CASH VARIANCE ENGINE")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {"test": "cash_variance_engine", "timestamp": datetime.now(timezone.utc).isoformat(), "tests": []}
    
    # Test 1: Get variance report
    resp = requests.get(f"{BASE_URL}/api/cash-variance/report", headers=headers)
    results["tests"].append({
        "name": "Get Variance Report",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [1] Get Variance Report: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Test 2: Get cashier ranking
    resp = requests.get(f"{BASE_URL}/api/cash-variance/cashier-ranking?days=30", headers=headers)
    results["tests"].append({
        "name": "Get Cashier Ranking",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [2] Get Cashier Ranking: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Calculate overall
    passed = sum(1 for t in results["tests"] if t["status"] == "PASS")
    results["summary"] = {
        "total": len(results["tests"]),
        "passed": passed,
        "failed": len(results["tests"]) - passed,
        "overall": "PASS" if passed == len(results["tests"]) else "FAIL"
    }
    
    # Save samples
    samples_path = f"{OUTPUT_DIR}/cash_variance_samples.json"
    with open(samples_path, "w") as f:
        json.dump(results["tests"], f, indent=2, default=str)
    
    # Generate report
    report_path = f"{OUTPUT_DIR}/cash_variance_test_report.md"
    with open(report_path, "w") as f:
        f.write("# OCB TITAN - CASH VARIANCE ENGINE TEST REPORT\n\n")
        f.write(f"**Test Date:** {results['timestamp']}\n")
        f.write(f"**Overall Status:** {results['summary']['overall']}\n\n")
        f.write("## Test Results\n\n")
        for t in results["tests"]:
            status_icon = "✅" if t["status"] == "PASS" else "❌"
            f.write(f"### {status_icon} {t['name']}\n\n")
            if isinstance(t.get("response"), dict):
                f.write(f"```json\n{json.dumps(t['response'], indent=2, default=str)[:500]}...\n```\n\n")
    
    print(f"\n  Report saved: {report_path}")
    return results


def test_guard_system_3(token):
    """Test Inventory vs GL Reconciliation"""
    print("\n" + "="*60)
    print("GUARD SYSTEM 3: INVENTORY VS GL RECONCILIATION")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {"test": "inventory_gl_reconciliation", "timestamp": datetime.now(timezone.utc).isoformat(), "tests": []}
    
    # Test 1: Run reconciliation
    resp = requests.get(f"{BASE_URL}/api/reconciliation/inventory-vs-gl", headers=headers)
    results["tests"].append({
        "name": "Run Reconciliation",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [1] Run Reconciliation: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    if resp.status_code == 200:
        recon = resp.json()
        print(f"      Inventory: Rp {recon.get('inventory', {}).get('total_value', 0):,.0f}")
        print(f"      GL Balance: Rp {recon.get('gl', {}).get('balance', 0):,.0f}")
        print(f"      Difference: Rp {recon.get('comparison', {}).get('difference', 0):,.0f}")
        print(f"      Status: {recon.get('comparison', {}).get('status', 'N/A')}")
    
    # Test 2: Generate report
    resp = requests.post(f"{BASE_URL}/api/reconciliation/inventory-vs-gl/generate-report", headers=headers)
    results["tests"].append({
        "name": "Generate Report",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [2] Generate Report: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Calculate overall
    passed = sum(1 for t in results["tests"] if t["status"] == "PASS")
    results["summary"] = {
        "total": len(results["tests"]),
        "passed": passed,
        "failed": len(results["tests"]) - passed,
        "overall": "PASS" if passed == len(results["tests"]) else "FAIL"
    }
    
    print(f"\n  Report saved: {OUTPUT_DIR}/inventory_vs_gl_recon_report.md")
    return results


def test_guard_system_4(token):
    """Test Idempotency Protection"""
    print("\n" + "="*60)
    print("GUARD SYSTEM 4: IDEMPOTENCY PROTECTION")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {"test": "idempotency_protection", "timestamp": datetime.now(timezone.utc).isoformat(), "tests": []}
    
    import uuid
    test_key = f"TEST-{uuid.uuid4().hex[:8]}"
    
    # Test 1: First request with key
    headers_with_key = {**headers, "Idempotency-Key": test_key}
    resp1 = requests.post(
        f"{BASE_URL}/api/idempotency/test",
        headers=headers_with_key,
        json={"test_data": "idempotency test"}
    )
    results["tests"].append({
        "name": "First Request with Key",
        "status": "PASS" if resp1.status_code == 200 else "FAIL",
        "response": resp1.json() if resp1.status_code == 200 else resp1.text
    })
    print(f"  [1] First Request with Key: {'PASS' if resp1.status_code == 200 else 'FAIL'}")
    first_timestamp = resp1.json().get("processed_at") if resp1.status_code == 200 else None
    
    # Test 2: Replay same request
    resp2 = requests.post(
        f"{BASE_URL}/api/idempotency/test",
        headers=headers_with_key,
        json={"test_data": "idempotency test"}
    )
    second_timestamp = resp2.json().get("processed_at") if resp2.status_code == 200 else None
    is_replay = first_timestamp == second_timestamp
    results["tests"].append({
        "name": "Replay Same Request (Should Return Cached)",
        "status": "PASS" if is_replay else "FAIL",
        "response": {"first": first_timestamp, "second": second_timestamp, "cached": is_replay}
    })
    print(f"  [2] Replay Same Request: {'PASS' if is_replay else 'FAIL'} (cached={is_replay})")
    
    # Test 3: Get stats
    resp = requests.get(f"{BASE_URL}/api/idempotency/stats", headers=headers)
    results["tests"].append({
        "name": "Get Idempotency Stats",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [3] Get Idempotency Stats: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Calculate overall
    passed = sum(1 for t in results["tests"] if t["status"] == "PASS")
    results["summary"] = {
        "total": len(results["tests"]),
        "passed": passed,
        "failed": len(results["tests"]) - passed,
        "overall": "PASS" if passed == len(results["tests"]) else "FAIL"
    }
    
    # Generate report
    report_path = f"{OUTPUT_DIR}/idempotency_test_report.md"
    with open(report_path, "w") as f:
        f.write("# OCB TITAN - IDEMPOTENCY PROTECTION TEST REPORT\n\n")
        f.write(f"**Test Date:** {results['timestamp']}\n")
        f.write(f"**Overall Status:** {results['summary']['overall']}\n\n")
        f.write("## Test Results\n\n")
        for t in results["tests"]:
            status_icon = "✅" if t["status"] == "PASS" else "❌"
            f.write(f"### {status_icon} {t['name']}\n\n")
    
    print(f"\n  Report saved: {report_path}")
    return results


def test_guard_system_5(token):
    """Test Event Bus System"""
    print("\n" + "="*60)
    print("GUARD SYSTEM 5: EVENT BUS SYSTEM")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {"test": "event_bus_system", "timestamp": datetime.now(timezone.utc).isoformat(), "tests": []}
    
    # Test 1: Get event types
    resp = requests.get(f"{BASE_URL}/api/events/types", headers=headers)
    results["tests"].append({
        "name": "Get Event Types",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [1] Get Event Types: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    if resp.status_code == 200:
        print(f"      Total event types: {resp.json().get('total', 0)}")
    
    # Test 2: Publish test event
    resp = requests.post(f"{BASE_URL}/api/events/test", headers=headers)
    results["tests"].append({
        "name": "Publish Test Event",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [2] Publish Test Event: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Test 3: Get event log
    resp = requests.get(f"{BASE_URL}/api/events/log?limit=5", headers=headers)
    results["tests"].append({
        "name": "Get Event Log",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [3] Get Event Log: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Test 4: Get event stats
    resp = requests.get(f"{BASE_URL}/api/events/stats?days=7", headers=headers)
    results["tests"].append({
        "name": "Get Event Stats",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [4] Get Event Stats: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Calculate overall
    passed = sum(1 for t in results["tests"] if t["status"] == "PASS")
    results["summary"] = {
        "total": len(results["tests"]),
        "passed": passed,
        "failed": len(results["tests"]) - passed,
        "overall": "PASS" if passed == len(results["tests"]) else "FAIL"
    }
    
    # Save event samples
    samples_path = f"{OUTPUT_DIR}/event_samples.json"
    with open(samples_path, "w") as f:
        json.dump(results["tests"], f, indent=2, default=str)
    
    # Generate report
    report_path = f"{OUTPUT_DIR}/event_bus_test_report.md"
    with open(report_path, "w") as f:
        f.write("# OCB TITAN - EVENT BUS SYSTEM TEST REPORT\n\n")
        f.write(f"**Test Date:** {results['timestamp']}\n")
        f.write(f"**Overall Status:** {results['summary']['overall']}\n\n")
        f.write("## Supported Event Types\n\n")
        if results["tests"][0]["status"] == "PASS":
            types = results["tests"][0]["response"].get("event_types", {})
            for k, v in list(types.items())[:10]:
                f.write(f"- `{k}`: {v}\n")
        f.write("\n## Test Results\n\n")
        for t in results["tests"]:
            status_icon = "✅" if t["status"] == "PASS" else "❌"
            f.write(f"- {status_icon} {t['name']}\n")
    
    print(f"\n  Report saved: {report_path}")
    return results


def test_guard_system_6(token):
    """Test Integrity Monitoring Dashboard"""
    print("\n" + "="*60)
    print("GUARD SYSTEM 6: INTEGRITY MONITORING DASHBOARD")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {"test": "integrity_monitor", "timestamp": datetime.now(timezone.utc).isoformat(), "tests": []}
    
    # Test 1: Get full dashboard
    resp = requests.get(f"{BASE_URL}/api/integrity/dashboard", headers=headers)
    results["tests"].append({
        "name": "Get Full Dashboard",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [1] Get Full Dashboard: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"      Overall Status: {data.get('overall_status', 'N/A')}")
        for check in data.get("checks", []):
            print(f"      - {check['check']}: {check['status']}")
    
    # Test 2: Generate report
    resp = requests.post(f"{BASE_URL}/api/integrity/generate-report", headers=headers)
    results["tests"].append({
        "name": "Generate Report",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [2] Generate Report: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Calculate overall
    passed = sum(1 for t in results["tests"] if t["status"] == "PASS")
    results["summary"] = {
        "total": len(results["tests"]),
        "passed": passed,
        "failed": len(results["tests"]) - passed,
        "overall": "PASS" if passed == len(results["tests"]) else "FAIL"
    }
    
    print(f"\n  Report saved: {OUTPUT_DIR}/integrity_monitor_report.md")
    return results


def test_guard_system_7(token):
    """Test Backup Automation"""
    print("\n" + "="*60)
    print("GUARD SYSTEM 7: BACKUP AUTOMATION")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {"test": "backup_automation", "timestamp": datetime.now(timezone.utc).isoformat(), "tests": []}
    
    # Test 1: Get backup config
    resp = requests.get(f"{BASE_URL}/api/backup-automation/config", headers=headers)
    results["tests"].append({
        "name": "Get Backup Config",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [1] Get Backup Config: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Test 2: Get backup status
    resp = requests.get(f"{BASE_URL}/api/backup-automation/status", headers=headers)
    results["tests"].append({
        "name": "Get Backup Status",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [2] Get Backup Status: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"      Status: {data.get('status', 'N/A')}")
        print(f"      Total Backups: {data.get('total_backups', 0)}")
        print(f"      Total Size: {data.get('total_size_mb', 0)} MB")
    
    # Test 3: List backups
    resp = requests.get(f"{BASE_URL}/api/backup-automation/list", headers=headers)
    results["tests"].append({
        "name": "List Backups",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [3] List Backups: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Test 4: Get backup history
    resp = requests.get(f"{BASE_URL}/api/backup-automation/history", headers=headers)
    results["tests"].append({
        "name": "Get Backup History",
        "status": "PASS" if resp.status_code == 200 else "FAIL",
        "response": resp.json() if resp.status_code == 200 else resp.text
    })
    print(f"  [4] Get Backup History: {'PASS' if resp.status_code == 200 else 'FAIL'}")
    
    # Calculate overall
    passed = sum(1 for t in results["tests"] if t["status"] == "PASS")
    results["summary"] = {
        "total": len(results["tests"]),
        "passed": passed,
        "failed": len(results["tests"]) - passed,
        "overall": "PASS" if passed == len(results["tests"]) else "FAIL"
    }
    
    # Save backup run log
    log_path = f"{OUTPUT_DIR}/backup_run_log.json"
    with open(log_path, "w") as f:
        json.dump(results["tests"], f, indent=2, default=str)
    
    print(f"\n  Config: /app/backend/config/backup_schedule_config.yml")
    print(f"  Run Log: {log_path}")
    return results


def main():
    """Run all guard system tests"""
    print("\n" + "="*70)
    print("OCB TITAN ERP - ENTERPRISE HARDENING TEST SUITE")
    print("PHASE 1: 7 GUARD SYSTEMS VALIDATION")
    print("="*70)
    print(f"\nTimestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"API URL: {BASE_URL}")
    
    # Login
    print("\n[LOGIN]")
    token = login()
    print(f"  Token acquired: {token[:30]}...")
    
    # Run all tests
    all_results = []
    
    all_results.append(test_guard_system_1(token))
    all_results.append(test_guard_system_2(token))
    all_results.append(test_guard_system_3(token))
    all_results.append(test_guard_system_4(token))
    all_results.append(test_guard_system_5(token))
    all_results.append(test_guard_system_6(token))
    all_results.append(test_guard_system_7(token))
    
    # Generate final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    total_tests = sum(r["summary"]["total"] for r in all_results)
    total_passed = sum(r["summary"]["passed"] for r in all_results)
    total_failed = total_tests - total_passed
    
    print(f"\n| Guard System | Tests | Passed | Status |")
    print(f"|--------------|-------|--------|--------|")
    for r in all_results:
        status_icon = "✅" if r["summary"]["overall"] == "PASS" else "❌"
        print(f"| {r['test']} | {r['summary']['total']} | {r['summary']['passed']} | {status_icon} {r['summary']['overall']} |")
    
    print(f"\n**Total: {total_passed}/{total_tests} tests passed**")
    
    overall = "PASS" if total_passed == total_tests else "FAIL"
    print(f"**Overall Status: {overall}**")
    
    # Save final report
    final_report = {
        "test_suite": "enterprise_hardening_phase1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "overall_status": overall,
        "guard_systems": all_results
    }
    
    final_path = f"{TEST_REPORTS_DIR}/enterprise_hardening_test_report.json"
    with open(final_path, "w") as f:
        json.dump(final_report, f, indent=2, default=str)
    
    print(f"\nFinal report saved: {final_path}")
    
    # Generate evidence index
    evidence = {
        "period_lock_test_report.md": f"{OUTPUT_DIR}/period_lock_test_report.md",
        "cash_variance_test_report.md": f"{OUTPUT_DIR}/cash_variance_test_report.md",
        "cash_variance_samples.json": f"{OUTPUT_DIR}/cash_variance_samples.json",
        "inventory_vs_gl_recon.json": f"{OUTPUT_DIR}/inventory_vs_gl_recon.json",
        "inventory_vs_gl_recon_report.md": f"{OUTPUT_DIR}/inventory_vs_gl_recon_report.md",
        "idempotency_test_report.md": f"{OUTPUT_DIR}/idempotency_test_report.md",
        "event_bus_test_report.md": f"{OUTPUT_DIR}/event_bus_test_report.md",
        "event_samples.json": f"{OUTPUT_DIR}/event_samples.json",
        "integrity_monitor_report.md": f"{OUTPUT_DIR}/integrity_monitor_report.md",
        "integrity_monitor_report.json": f"{OUTPUT_DIR}/integrity_monitor_report.json",
        "backup_schedule_config.yml": "/app/backend/config/backup_schedule_config.yml",
        "backup_run_log.json": f"{OUTPUT_DIR}/backup_run_log.json"
    }
    
    evidence_path = f"{OUTPUT_DIR}/enterprise_hardening_evidence_index.json"
    with open(evidence_path, "w") as f:
        json.dump(evidence, f, indent=2)
    
    print(f"Evidence index saved: {evidence_path}")
    
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
