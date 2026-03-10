# OCB TITAN AI - Advanced Export System
# Export to Excel, PDF, CSV, JSON for all modules

from fastapi import APIRouter, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import json
import csv
import io
import uuid

# Excel & PDF libraries
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from database import get_db

router = APIRouter(prefix="/api/export-v2", tags=["Advanced Export"])

def get_wib_now():
    return datetime.now(timezone.utc) + timedelta(hours=7)

# ==================== HELPER FUNCTIONS ====================

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, json.dumps(v) if v else ''))
        else:
            items.append((new_key, v))
    return dict(items)

async def get_collection_data(collection_name: str, query: dict = None, limit: int = 10000):
    """Get data from collection"""
    col = get_db()[collection_name]
    q = query or {}
    data = await col.find(q, {"_id": 0}).to_list(length=limit)
    return data

def generate_excel(data: List[dict], sheet_name: str = "Data"):
    """Generate Excel file from data"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet(sheet_name[:31])  # Excel sheet name limit
    
    # Styles
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#8B0000',
        'font_color': 'white',
        'border': 1,
        'align': 'center'
    })
    cell_format = workbook.add_format({'border': 1})
    number_format = workbook.add_format({'border': 1, 'num_format': '#,##0'})
    currency_format = workbook.add_format({'border': 1, 'num_format': 'Rp #,##0'})
    
    if not data:
        worksheet.write(0, 0, "No data available")
        workbook.close()
        output.seek(0)
        return output
    
    # Flatten data
    flat_data = [flatten_dict(d) for d in data]
    
    # Get all headers
    headers = list(flat_data[0].keys()) if flat_data else []
    
    # Write headers
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, header_format)
        worksheet.set_column(col_num, col_num, 15)
    
    # Write data
    for row_num, row_data in enumerate(flat_data, 1):
        for col_num, header in enumerate(headers):
            value = row_data.get(header, '')
            if isinstance(value, (int, float)):
                if 'price' in header.lower() or 'total' in header.lower() or 'gaji' in header.lower():
                    worksheet.write(row_num, col_num, value, currency_format)
                else:
                    worksheet.write(row_num, col_num, value, number_format)
            else:
                worksheet.write(row_num, col_num, str(value) if value else '', cell_format)
    
    workbook.close()
    output.seek(0)
    return output

def generate_pdf(data: List[dict], title: str = "OCB TITAN AI Report"):
    """Generate PDF file from data"""
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.darkred
    )
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f"Generated: {get_wib_now().strftime('%Y-%m-%d %H:%M WIB')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    if not data:
        elements.append(Paragraph("No data available", styles['Normal']))
        doc.build(elements)
        output.seek(0)
        return output
    
    # Flatten data
    flat_data = [flatten_dict(d) for d in data]
    headers = list(flat_data[0].keys()) if flat_data else []
    
    # Limit columns for PDF readability (max 8 columns)
    if len(headers) > 8:
        headers = headers[:8]
    
    # Build table data
    table_data = [headers]
    for row in flat_data:
        row_values = []
        for h in headers:
            val = row.get(h, '')
            if isinstance(val, (int, float)):
                if 'price' in h.lower() or 'total' in h.lower():
                    val = f"Rp {val:,.0f}"
                else:
                    val = f"{val:,.0f}" if isinstance(val, int) else f"{val:.2f}"
            row_values.append(str(val)[:30] if val else '')  # Limit cell content
        table_data.append(row_values)
    
    # Create table
    col_widths = [1.2*inch] * len(headers)
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)])
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Total Records: {len(flat_data)}", styles['Normal']))
    
    doc.build(elements)
    output.seek(0)
    return output

def generate_csv(data: List[dict]):
    """Generate CSV file from data"""
    output = io.StringIO()
    if not data:
        output.write("No data available")
        return output.getvalue()
    
    flat_data = [flatten_dict(d) for d in data]
    headers = list(flat_data[0].keys())
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in flat_data:
        writer.writerow(row)
    
    return output.getvalue()

# ==================== SPECIAL EXPORTS (Must be defined BEFORE generic route) ====================

@router.get("/ranking/employees")
async def export_employee_ranking(
    format: str = "xlsx",
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """Export employee ranking"""
    if not month:
        month = get_wib_now().month
    if not year:
        year = get_wib_now().year
    
    # Get ranking data
    targets = await get_collection_data("kpi_targets", {
        "period_month": month, "period_year": year
    })
    
    # Calculate rankings
    employee_scores = {}
    for t in targets:
        eid = t.get("employee_id")
        if eid not in employee_scores:
            employee_scores[eid] = {
                "employee_id": eid,
                "employee_name": t.get("employee_name"),
                "branch_name": t.get("branch_name"),
                "total_kpis": 0,
                "achieved_kpis": 0,
                "total_score": 0
            }
        employee_scores[eid]["total_kpis"] += 1
        achievement = t.get("achievement_percentage", 0)
        employee_scores[eid]["total_score"] += achievement
        if achievement >= 100:
            employee_scores[eid]["achieved_kpis"] += 1
    
    # Calculate final
    rankings = []
    for eid, data in employee_scores.items():
        avg_score = data["total_score"] / data["total_kpis"] if data["total_kpis"] > 0 else 0
        
        if avg_score >= 120:
            rank_cat = "Elite Performer"
        elif avg_score >= 100:
            rank_cat = "Top Performer"
        elif avg_score >= 80:
            rank_cat = "Good Performer"
        elif avg_score >= 60:
            rank_cat = "Average Performer"
        elif avg_score >= 40:
            rank_cat = "Under Performance"
        else:
            rank_cat = "Needs Improvement"
        
        rankings.append({
            **data,
            "average_score": round(avg_score, 2),
            "rank_category": rank_cat,
            "period": f"{month}/{year}"
        })
    
    rankings.sort(key=lambda x: x["average_score"], reverse=True)
    for i, r in enumerate(rankings):
        r["rank"] = i + 1
    
    filename = f"ocb_employee_ranking_{year}{month:02d}"
    title = f"OCB TITAN AI - Employee Ranking {month}/{year}"
    
    if format == "xlsx":
        output = generate_excel(rankings, "Employee_Ranking")
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    elif format == "pdf":
        output = generate_pdf(rankings, title)
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    elif format == "csv":
        content = generate_csv(rankings)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
    else:
        return {"rankings": rankings}

@router.get("/ranking/branches")
async def export_branch_ranking(
    format: str = "xlsx",
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """Export branch ranking"""
    if not month:
        month = get_wib_now().month
    if not year:
        year = get_wib_now().year
    
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    setoran = await get_collection_data("setoran_harian", {
        "tanggal": {"$gte": start_date, "$lte": end_date}
    })
    
    branch_data = {}
    for s in setoran:
        bid = s.get("branch_id")
        if bid not in branch_data:
            branch_data[bid] = {
                "branch_id": bid,
                "branch_code": s.get("branch_code"),
                "branch_name": s.get("branch_name"),
                "total_sales": 0,
                "total_transactions": 0,
                "total_minus": 0,
                "days_reported": 0
            }
        branch_data[bid]["total_sales"] += s.get("total_penjualan", 0)
        branch_data[bid]["total_transactions"] += s.get("total_transaksi", 0)
        if s.get("selisih", 0) < 0:
            branch_data[bid]["total_minus"] += abs(s.get("selisih", 0))
        branch_data[bid]["days_reported"] += 1
    
    rankings = []
    for bid, data in branch_data.items():
        reporting_rate = (data["days_reported"] / last_day) * 100
        minus_rate = (data["total_minus"] / data["total_sales"] * 100) if data["total_sales"] > 0 else 0
        score = reporting_rate * 0.5 + (100 - minus_rate) * 0.5
        
        if score >= 95:
            rank_cat = "Elite Branch"
        elif score >= 85:
            rank_cat = "Top Branch"
        elif score >= 70:
            rank_cat = "Good Branch"
        elif score >= 50:
            rank_cat = "Average Branch"
        else:
            rank_cat = "Needs Attention"
        
        rankings.append({
            **data,
            "reporting_rate": round(reporting_rate, 2),
            "minus_rate": round(minus_rate, 2),
            "final_score": round(score, 2),
            "rank_category": rank_cat,
            "period": f"{month}/{year}"
        })
    
    rankings.sort(key=lambda x: x["final_score"], reverse=True)
    for i, r in enumerate(rankings):
        r["rank"] = i + 1
    
    filename = f"ocb_branch_ranking_{year}{month:02d}"
    title = f"OCB TITAN AI - Branch Ranking {month}/{year}"
    
    if format == "xlsx":
        output = generate_excel(rankings, "Branch_Ranking")
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    elif format == "pdf":
        output = generate_pdf(rankings, title)
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    elif format == "csv":
        content = generate_csv(rankings)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
    else:
        return {"rankings": rankings}

@router.get("/warroom/alerts")
async def export_warroom_alerts(format: str = "xlsx"):
    """Export war room alerts"""
    alerts = await get_collection_data("alerts", {"resolved": False})
    
    filename = f"ocb_warroom_alerts_{get_wib_now().strftime('%Y%m%d')}"
    title = "OCB TITAN AI - War Room Alerts"
    
    if format == "xlsx":
        output = generate_excel(alerts, "Alerts")
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    elif format == "pdf":
        output = generate_pdf(alerts, title)
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    elif format == "csv":
        content = generate_csv(alerts)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
    else:
        return {"alerts": alerts}

@router.get("/dashboard/summary")
async def export_dashboard_summary(format: str = "pdf"):
    """Export dashboard summary report"""
    today = get_wib_now().strftime("%Y-%m-%d")
    
    # Collect dashboard data
    setoran_today = await get_collection_data("setoran_harian", {"tanggal": today})
    attendance_today = await get_collection_data("attendance", {"tanggal": today})
    alerts = await get_collection_data("alerts", {"resolved": False})
    
    summary = [{
        "report_date": today,
        "total_branches": len(set(s.get("branch_id") for s in setoran_today)),
        "total_sales": sum(s.get("total_penjualan", 0) for s in setoran_today),
        "total_transactions": sum(s.get("total_transaksi", 0) for s in setoran_today),
        "total_minus": sum(s.get("selisih", 0) for s in setoran_today if s.get("selisih", 0) < 0),
        "employees_present": len([a for a in attendance_today if a.get("status") in ["hadir", "telat"]]),
        "employees_late": len([a for a in attendance_today if a.get("status") == "telat"]),
        "active_alerts": len(alerts),
        "generated_at": get_wib_now().isoformat()
    }]
    
    filename = f"ocb_dashboard_summary_{today}"
    title = f"OCB TITAN AI - Dashboard Summary {today}"
    
    if format == "pdf":
        output = generate_pdf(summary, title)
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    elif format == "xlsx":
        output = generate_excel(summary, "Dashboard_Summary")
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    else:
        return {"summary": summary}

# ==================== GENERIC EXPORT ENDPOINT (must be AFTER specific routes) ====================

@router.get("/{module}/{data_type}")
async def export_data(
    module: str,
    data_type: str,
    format: str = Query("json", description="Export format: json, csv, xlsx, pdf"),
    month: Optional[int] = None,
    year: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[str] = None
):
    """Universal export endpoint for all modules"""
    
    # Collection mapping
    collection_map = {
        # Master Data
        "master_products": "products",
        "master_categories": "categories",
        "master_brands": "brands",
        "master_suppliers": "suppliers",
        "master_customers": "customers",
        "master_branches": "branches",
        "master_warehouses": "warehouses",
        
        # HR
        "hr_employees": "employees",
        "hr_jabatan": "master_jabatan",
        "hr_shifts": "master_shift",
        "hr_attendance": "attendance",
        "hr_payroll": "payroll_details",
        "hr_leaves": "leave_requests",
        "hr_overtime": "overtime_requests",
        
        # KPI
        "kpi_templates": "kpi_templates",
        "kpi_targets": "kpi_targets",
        "kpi_submissions": "kpi_submissions",
        "kpi_rankings": "ai_rankings",
        
        # Sales
        "sales_transactions": "transactions",
        "sales_setoran": "setoran_harian",
        "sales_selisih": "selisih_kas",
        
        # Inventory
        "inventory_stock": "stock",
        "inventory_mutations": "stock_mutations",
        "inventory_opname": "stock_opname",
        
        # Accounting
        "accounting_journals": "journals",
        "accounting_kas_masuk": "kas_masuk",
        "accounting_kas_keluar": "kas_keluar",
        
        # Audit
        "audit_logs": "audit_logs",
        "audit_kas": "audit_kas",
        "audit_stock": "audit_stock",
        
        # CRM
        "crm_customers": "crm_customers",
        "crm_complaints": "complaints",
        "crm_prompts": "ai_prompts",
        
        # Alerts
        "alerts_all": "alerts",
        "alerts_warroom": "warroom_alerts",
    }
    
    key = f"{module}_{data_type}"
    collection_name = collection_map.get(key)
    
    if not collection_name:
        raise HTTPException(status_code=404, detail=f"Export tidak tersedia untuk {module}/{data_type}")
    
    # Build query
    query = {}
    if branch_id:
        query["branch_id"] = branch_id
    if start_date and end_date:
        query["$or"] = [
            {"tanggal": {"$gte": start_date, "$lte": end_date}},
            {"date": {"$gte": start_date, "$lte": end_date}},
            {"created_at": {"$gte": start_date, "$lte": end_date}}
        ]
    elif month and year:
        import calendar
        _, last_day = calendar.monthrange(year, month)
        start = f"{year}-{month:02d}-01"
        end = f"{year}-{month:02d}-{last_day}"
        query["$or"] = [
            {"tanggal": {"$gte": start, "$lte": end}},
            {"date": {"$gte": start, "$lte": end}},
            {"period_month": month, "period_year": year}
        ]
    
    # Get data
    data = await get_collection_data(collection_name, query if query else None)
    
    filename = f"ocb_{module}_{data_type}_{get_wib_now().strftime('%Y%m%d_%H%M')}"
    title = f"OCB TITAN AI - {module.upper()} {data_type.upper()} Report"
    
    # Generate export based on format
    if format == "xlsx":
        output = generate_excel(data, f"{module}_{data_type}")
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    elif format == "pdf":
        output = generate_pdf(data, title)
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    elif format == "csv":
        content = generate_csv(data)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
    else:  # JSON
        return Response(
            content=json.dumps(data, default=str, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}.json"}
        )
