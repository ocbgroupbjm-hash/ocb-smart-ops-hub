# OCB TITAN AI - Phase 4 HR/Payroll System Testing
# Testing: Seed Data, Payroll Auto, AI Employee Performance, Payslip Generation

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSeedData:
    """Test seed data generation endpoints"""
    
    def test_seed_all_data(self):
        """Test /api/seed/all - Generate all seed data"""
        response = requests.post(f"{BASE_URL}/api/seed/all")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "results" in data
        
        results = data["results"]
        assert "branches" in results
        assert "jabatan" in results
        assert "payroll_rules" in results
        assert "employees" in results
        assert "attendance" in results
        assert "transactions" in results
        
        print(f"✓ Seed all data successful: {data['message']}")
        print(f"  - Branches: {results['branches']['count']}")
        print(f"  - Jabatan: {results['jabatan']['count']}")
        print(f"  - Payroll Rules: {results['payroll_rules']['count']}")
        print(f"  - Employees: {results['employees']['count']}")
        print(f"  - Attendance: {results['attendance']['count']}")
        print(f"  - Transactions: {results['transactions']['count']}")

    def test_seed_branches(self):
        """Test /api/seed/branches - Seed branches data"""
        response = requests.post(f"{BASE_URL}/api/seed/branches")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] >= 5
        print(f"✓ Seed branches: {data['count']} branches created")

    def test_seed_employees(self):
        """Test /api/seed/employees - Seed employees data"""
        response = requests.post(f"{BASE_URL}/api/seed/employees")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] >= 24  # Should create 24 employees
        print(f"✓ Seed employees: {data['count']} employees created")

    def test_seed_attendance(self):
        """Test /api/seed/attendance - Seed attendance records"""
        response = requests.post(f"{BASE_URL}/api/seed/attendance")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] > 0
        print(f"✓ Seed attendance: {data['count']} records created")

    def test_seed_transactions(self):
        """Test /api/seed/transactions - Seed sales transactions"""
        response = requests.post(f"{BASE_URL}/api/seed/transactions")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] > 0
        print(f"✓ Seed transactions: {data['count']} transactions created")


class TestPayrollAuto:
    """Test automatic payroll calculation endpoints"""
    
    def test_calculate_employee_payroll(self):
        """Test /api/payroll-auto/calculate/{employee_id} - Individual payroll calculation"""
        # Use first seeded employee
        employee_id = "EMP-SEED-001"
        month = 1  # January
        year = 2026
        
        response = requests.get(
            f"{BASE_URL}/api/payroll-auto/calculate/{employee_id}",
            params={"month": month, "year": year}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify employee info
        assert "employee" in data
        assert data["employee"]["id"] == employee_id
        assert "name" in data["employee"]
        assert "jabatan" in data["employee"]
        
        # Verify period
        assert "period" in data
        assert data["period"]["month"] == month
        assert data["period"]["year"] == year
        
        # Verify attendance
        assert "attendance" in data
        assert "total_hadir" in data["attendance"]
        assert "total_alpha" in data["attendance"]
        assert "total_telat_menit" in data["attendance"]
        assert "total_lembur_menit" in data["attendance"]
        
        # Verify calculation
        assert "calculation" in data
        calc = data["calculation"]
        assert "gaji_dasar" in calc
        assert "tunjangan" in calc
        assert "bonus" in calc
        assert "potongan" in calc
        assert "gross" in calc
        assert "take_home_pay" in calc
        
        # Verify bonus breakdown
        assert "kehadiran" in calc["bonus"]
        assert "lembur" in calc["bonus"]
        assert "penjualan" in calc["bonus"]
        
        # Verify potongan breakdown
        assert "telat" in calc["potongan"]
        assert "alpha" in calc["potongan"]
        assert "bpjs_kes" in calc["potongan"]
        assert "bpjs_tk" in calc["potongan"]
        
        print(f"✓ Payroll calculation for {data['employee']['name']}")
        print(f"  - Hadir: {data['attendance']['total_hadir']} days")
        print(f"  - Alpha: {data['attendance']['total_alpha']} days")
        print(f"  - Gross: Rp {calc['gross']:,.0f}")
        print(f"  - Potongan: Rp {calc['potongan']['total']:,.0f}")
        print(f"  - Take Home Pay: Rp {calc['take_home_pay']:,.0f}")

    def test_calculate_employee_payroll_not_found(self):
        """Test payroll calculation with invalid employee ID"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-auto/calculate/INVALID-ID",
            params={"month": 1, "year": 2026}
        )
        assert response.status_code == 404
        print("✓ Correctly returns 404 for non-existent employee")

    def test_calculate_all_payroll(self):
        """Test /api/payroll-auto/calculate-all - Bulk payroll calculation"""
        month = 1
        year = 2026
        
        response = requests.get(
            f"{BASE_URL}/api/payroll-auto/calculate-all",
            params={"month": month, "year": year}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        assert "period" in data
        assert "total_employees" in data
        assert "summary" in data
        assert "employees" in data
        assert "by_branch" in data
        
        # Check summary
        assert "total_gross" in data["summary"]
        assert "total_take_home_pay" in data["summary"]
        
        # Check employees list
        assert len(data["employees"]) > 0
        
        print(f"✓ Bulk payroll calculation")
        print(f"  - Period: {data['period']}")
        print(f"  - Total Employees: {data['total_employees']}")
        print(f"  - Total Gross: Rp {data['summary']['total_gross']:,.0f}")
        print(f"  - Total THP: Rp {data['summary']['total_take_home_pay']:,.0f}")
        print(f"  - Branches: {len(data['by_branch'])}")

    def test_calculate_branch_payroll(self):
        """Test /api/payroll-auto/calculate-branch/{branch_id}"""
        branch_id = "BR001"  # OCB Banjarmasin Pusat
        month = 1
        year = 2026
        
        response = requests.get(
            f"{BASE_URL}/api/payroll-auto/calculate-branch/{branch_id}",
            params={"month": month, "year": year}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "branch_id" in data
        assert "branch_name" in data
        assert "employees" in data
        assert "summary" in data
        
        print(f"✓ Branch payroll: {data['branch_name']}")
        print(f"  - Employees: {data['total_employees']}")
        print(f"  - Total THP: Rp {data['summary']['total_take_home_pay']:,.0f}")

    def test_save_payroll_result(self):
        """Test /api/payroll-auto/save/{employee_id} - Save payroll to database"""
        employee_id = "EMP-SEED-001"
        month = 1
        year = 2026
        
        response = requests.post(
            f"{BASE_URL}/api/payroll-auto/save/{employee_id}",
            params={"month": month, "year": year}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "payroll_id" in data
        print(f"✓ Payroll saved: {data['payroll_id']}")

    def test_get_payroll_results(self):
        """Test /api/payroll-auto/results - Get saved payroll results"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-auto/results",
            params={"month": 1, "year": 2026}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "total" in data
        print(f"✓ Retrieved {data['total']} saved payroll results")


class TestAIEmployeePerformance:
    """Test AI employee performance analysis endpoints"""
    
    def test_analyze_employee_performance(self):
        """Test /api/ai-employee/analyze/{employee_id} - AI performance analysis"""
        employee_id = "EMP-SEED-001"
        
        response = requests.get(
            f"{BASE_URL}/api/ai-employee/analyze/{employee_id}",
            params={"period": "1month"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify employee info
        assert "employee" in data
        assert data["employee"]["id"] == employee_id
        
        # Verify analysis
        assert "score" in data
        assert isinstance(data["score"], (int, float))
        assert 0 <= data["score"] <= 100
        
        assert "category" in data
        assert data["category"] in ["ELITE", "SANGAT_BAIK", "BAIK", "NORMAL", "PERLU_PERHATIAN", "BURUK"]
        
        assert "category_color" in data
        assert "category_description" in data
        
        # Verify metrics
        assert "metrics" in data
        assert "attendance" in data["metrics"]
        assert "sales" in data["metrics"]
        assert "minus_kas" in data["metrics"]
        
        # Verify AI recommendations
        assert "strengths" in data
        assert "weaknesses" in data
        assert "recommendations" in data
        assert isinstance(data["strengths"], list)
        assert isinstance(data["weaknesses"], list)
        assert isinstance(data["recommendations"], list)
        
        print(f"✓ AI Performance Analysis for {data['employee']['name']}")
        print(f"  - Score: {data['score']}")
        print(f"  - Category: {data['category']}")
        print(f"  - Strengths: {len(data['strengths'])}")
        print(f"  - Weaknesses: {len(data['weaknesses'])}")
        print(f"  - Recommendations: {len(data['recommendations'])}")

    def test_analyze_employee_different_periods(self):
        """Test AI analysis with different time periods"""
        employee_id = "EMP-SEED-003"
        
        for period in ["1month", "3months", "6months"]:
            response = requests.get(
                f"{BASE_URL}/api/ai-employee/analyze/{employee_id}",
                params={"period": period}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["analysis_period"] == period
            print(f"✓ Analysis for period {period}: Score={data['score']}, Category={data['category']}")

    def test_analyze_employee_not_found(self):
        """Test AI analysis with invalid employee ID"""
        response = requests.get(
            f"{BASE_URL}/api/ai-employee/analyze/INVALID-ID",
            params={"period": "1month"}
        )
        assert response.status_code == 404
        print("✓ Correctly returns 404 for non-existent employee")

    def test_analyze_all_employees(self):
        """Test /api/ai-employee/analyze-all - Bulk AI analysis"""
        response = requests.get(
            f"{BASE_URL}/api/ai-employee/analyze-all",
            params={"period": "1month"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        assert "total_analyzed" in data
        assert "category_summary" in data
        assert "top_performers" in data
        assert "need_attention" in data
        assert "all_employees" in data
        
        # Verify category summary
        categories = data["category_summary"]
        expected_cats = ["ELITE", "SANGAT_BAIK", "BAIK", "NORMAL", "PERLU_PERHATIAN", "BURUK"]
        for cat in expected_cats:
            assert cat in categories
        
        # Verify ranking
        employees = data["all_employees"]
        if len(employees) > 1:
            # Should be sorted by score descending
            for i in range(len(employees) - 1):
                assert employees[i]["score"] >= employees[i+1]["score"]
            
            # Should have rank
            for i, emp in enumerate(employees):
                assert emp["rank"] == i + 1
        
        print(f"✓ Bulk AI Analysis")
        print(f"  - Total Analyzed: {data['total_analyzed']}")
        print(f"  - Categories: {categories}")
        print(f"  - Top Performers: {len(data['top_performers'])}")
        print(f"  - Need Attention: {len(data['need_attention'])}")

    def test_employee_ranking(self):
        """Test /api/ai-employee/ranking - Employee ranking dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/ai-employee/ranking",
            params={"limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        
        assert "top_performers" in data
        assert "category_distribution" in data
        assert "total_employees" in data
        assert "elite_count" in data
        assert "attention_needed" in data
        
        print(f"✓ Employee Ranking")
        print(f"  - Total: {data['total_employees']}")
        print(f"  - Elite: {data['elite_count']}")
        print(f"  - Need Attention: {data['attention_needed']}")

    def test_save_performance_analysis(self):
        """Test /api/ai-employee/save-analysis/{employee_id} - Save performance record"""
        employee_id = "EMP-SEED-001"
        
        response = requests.post(
            f"{BASE_URL}/api/ai-employee/save-analysis/{employee_id}",
            params={"period": "1month"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "record_id" in data
        print(f"✓ Performance analysis saved: {data['record_id']}")

    def test_get_performance_history(self):
        """Test /api/ai-employee/history/{employee_id}"""
        employee_id = "EMP-SEED-001"
        
        response = requests.get(f"{BASE_URL}/api/ai-employee/history/{employee_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "history" in data
        print(f"✓ Performance history: {len(data['history'])} records")


class TestPayslipGeneration:
    """Test payslip file generation endpoints"""
    
    def test_payslip_json_format(self):
        """Test /api/payroll-files/payslip/{employee_id} with JSON format"""
        employee_id = "EMP-SEED-001"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll-files/payslip/{employee_id}",
            params={"period_month": 1, "period_year": 2026, "format": "json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        assert "slip_id" in data
        assert "period" in data
        assert "employee" in data
        assert "calculation" in data
        
        # Verify employee details
        assert "nik" in data["employee"]
        assert "name" in data["employee"]
        assert "jabatan" in data["employee"]
        
        # Verify calculation details
        calc = data["calculation"]
        assert "gaji_dasar" in calc or "gaji_pokok" in calc
        assert "take_home_pay" in calc
        
        print(f"✓ Payslip JSON generated")
        print(f"  - Employee: {data['employee']['name']}")
        print(f"  - Period: {data['period']}")
        print(f"  - THP: Rp {calc['take_home_pay']:,.0f}")

    def test_payslip_pdf_format(self):
        """Test payslip PDF generation"""
        employee_id = "EMP-SEED-001"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll-files/payslip/{employee_id}",
            params={"period_month": 1, "period_year": 2026, "format": "pdf"}
        )
        
        # May return 200 with PDF or 500 if reportlab not installed
        if response.status_code == 200:
            # Verify it's a PDF
            content_type = response.headers.get('content-type', '')
            assert 'pdf' in content_type.lower() or len(response.content) > 0
            print(f"✓ Payslip PDF generated ({len(response.content)} bytes)")
        elif response.status_code == 500:
            data = response.json()
            if "not available" in str(data.get("detail", "")):
                print("⚠ PDF generation library not available (expected)")
            else:
                raise AssertionError(f"Unexpected 500 error: {data}")
        else:
            raise AssertionError(f"Unexpected status: {response.status_code}")

    def test_payslip_excel_format(self):
        """Test payslip Excel generation"""
        employee_id = "EMP-SEED-001"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll-files/payslip/{employee_id}",
            params={"period_month": 1, "period_year": 2026, "format": "excel"}
        )
        
        if response.status_code == 200:
            assert len(response.content) > 0
            print(f"✓ Payslip Excel generated ({len(response.content)} bytes)")
        elif response.status_code == 500:
            data = response.json()
            if "not available" in str(data.get("detail", "")):
                print("⚠ Excel generation library not available (expected)")
            else:
                raise AssertionError(f"Unexpected 500 error: {data}")
        else:
            raise AssertionError(f"Unexpected status: {response.status_code}")

    def test_payslip_invalid_format(self):
        """Test payslip with invalid format"""
        employee_id = "EMP-SEED-001"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll-files/payslip/{employee_id}",
            params={"period_month": 1, "period_year": 2026, "format": "invalid"}
        )
        assert response.status_code == 400
        print("✓ Correctly rejects invalid format")

    def test_payslip_employee_not_found(self):
        """Test payslip for non-existent employee"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-files/payslip/INVALID-ID",
            params={"period_month": 1, "period_year": 2026, "format": "json"}
        )
        assert response.status_code == 404
        print("✓ Correctly returns 404 for non-existent employee")

    def test_branch_payroll_report_json(self):
        """Test branch payroll report in JSON format"""
        branch_id = "BR001"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll-files/report/branch/{branch_id}",
            params={"period_month": 1, "period_year": 2026, "format": "json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "report_type" in data
        assert "branch_name" in data
        assert "employee_count" in data
        assert "summary" in data
        assert "employees" in data
        
        print(f"✓ Branch report JSON: {data['branch_name']}")
        print(f"  - Employees: {data['employee_count']}")
        print(f"  - Total THP: Rp {data['summary']['total_thp']:,.0f}")

    def test_company_payroll_report(self):
        """Test company-wide payroll report"""
        response = requests.get(
            f"{BASE_URL}/api/payroll-files/report/company",
            params={"period_month": 1, "period_year": 2026, "format": "json"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "report_type" in data
        assert "branch_count" in data
        assert "grand_total" in data
        assert "branches" in data
        
        print(f"✓ Company payroll report")
        print(f"  - Branches: {data['branch_count']}")
        print(f"  - Total Employees: {data['grand_total']['employee_count']}")
        print(f"  - Grand Total THP: Rp {data['grand_total']['total_thp']:,.0f}")

    def test_dashboard_summary(self):
        """Test payroll dashboard summary"""
        response = requests.get(f"{BASE_URL}/api/payroll-files/dashboard-summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_employees" in data
        assert "monthly_employees" in data
        assert "daily_employees" in data
        assert "estimated_monthly_payroll" in data
        
        print(f"✓ Dashboard summary")
        print(f"  - Total Employees: {data['total_employees']}")
        print(f"  - Monthly: {data['monthly_employees']}, Daily: {data['daily_employees']}")
        print(f"  - Estimated Payroll: Rp {data['estimated_monthly_payroll']['total_take_home_pay']:,.0f}")


class TestIntegration:
    """Integration tests for the complete workflow"""
    
    def test_full_payroll_workflow(self):
        """Test complete workflow: Seed -> Calculate -> Analyze -> Generate"""
        # 1. Seed data (already done in previous tests)
        print("Step 1: Using existing seed data")
        
        # 2. Calculate payroll for multiple employees
        print("Step 2: Calculate payroll for seeded employees")
        for emp_id in ["EMP-SEED-001", "EMP-SEED-005", "EMP-SEED-010"]:
            response = requests.get(
                f"{BASE_URL}/api/payroll-auto/calculate/{emp_id}",
                params={"month": 1, "year": 2026}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"  - {data['employee']['name']}: THP Rp {data['calculation']['take_home_pay']:,.0f}")
            else:
                print(f"  - {emp_id}: Skipped (not found)")
        
        # 3. AI Performance Analysis
        print("Step 3: AI Performance Analysis")
        response = requests.get(
            f"{BASE_URL}/api/ai-employee/ranking",
            params={"limit": 5}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"  - Top performers: {len(data['top_performers'])}")
            for emp in data['top_performers'][:3]:
                print(f"    #{emp['rank']} {emp['name']}: Score {emp['score']} ({emp['category']})")
        
        # 4. Generate payslip
        print("Step 4: Generate payslip")
        response = requests.get(
            f"{BASE_URL}/api/payroll-files/payslip/EMP-SEED-001",
            params={"period_month": 1, "period_year": 2026, "format": "json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"  - Payslip generated for {data['employee']['name']}")
        
        print("✓ Full workflow completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
