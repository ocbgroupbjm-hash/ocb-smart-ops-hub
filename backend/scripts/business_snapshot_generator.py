#!/usr/bin/env python3
"""
OCB TITAN ERP - BUSINESS SNAPSHOT GENERATOR
MASTER BLUEPRINT: Production Hardening Phase 20

Layer 2 Backup: Business Snapshot

Generates:
- Trial Balance
- Balance Sheet
- Inventory Snapshot
- GL Summary

Format: PDF + JSON
Folder: /backups/business_snapshot/
"""

import asyncio
import os
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
SNAPSHOT_DIR = "/app/backend/backups/business_snapshot"


class BusinessSnapshotGenerator:
    def __init__(self, mongo_url: str = MONGO_URL):
        self.mongo_url = mongo_url
        self.client = None
        self.timestamp = datetime.now(timezone.utc)
        self.snapshot_id = f"SNAP-{self.timestamp.strftime('%Y%m%d_%H%M%S')}"
        
    async def connect(self):
        self.client = AsyncIOMotorClient(self.mongo_url)
        
    async def disconnect(self):
        if self.client:
            self.client.close()
    
    async def generate_trial_balance(self, db_name: str) -> Dict:
        """Generate Trial Balance from journal entries"""
        db = self.client[db_name]
        
        # Aggregate by account
        pipeline = [
            {"$match": {"status": "posted"}},
            {"$unwind": "$entries"},
            {"$group": {
                "_id": "$entries.account_code",
                "account_name": {"$first": "$entries.account_name"},
                "total_debit": {"$sum": "$entries.debit"},
                "total_credit": {"$sum": "$entries.credit"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = await db["journal_entries"].aggregate(pipeline).to_list(1000)
        
        accounts = []
        for r in results:
            if not r.get("_id"):
                continue
            accounts.append({
                "code": r["_id"],
                "name": r.get("account_name", ""),
                "debit": r.get("total_debit", 0) or 0,
                "credit": r.get("total_credit", 0) or 0
            })
        
        total_debit = sum(a["debit"] for a in accounts)
        total_credit = sum(a["credit"] for a in accounts)
        
        return {
            "report_type": "trial_balance",
            "tenant": db_name,
            "generated_at": self.timestamp.isoformat(),
            "snapshot_id": self.snapshot_id,
            "accounts": accounts,
            "totals": {
                "debit": total_debit,
                "credit": total_credit,
                "difference": abs(total_debit - total_credit),
                "balanced": abs(total_debit - total_credit) < 1
            }
        }
    
    async def generate_balance_sheet(self, db_name: str) -> Dict:
        """Generate Balance Sheet"""
        db = self.client[db_name]
        
        # Get trial balance data first
        tb = await self.generate_trial_balance(db_name)
        
        # Classify accounts by code prefix
        assets = []  # 1xxx
        liabilities = []  # 2xxx
        equity = []  # 3xxx
        revenue = []  # 4xxx
        expenses = []  # 5xxx, 6xxx
        
        for acc in tb["accounts"]:
            code = acc["code"]
            balance = acc["debit"] - acc["credit"]  # Natural balance
            
            if code.startswith("1"):
                assets.append({**acc, "balance": balance})
            elif code.startswith("2"):
                liabilities.append({**acc, "balance": acc["credit"] - acc["debit"]})
            elif code.startswith("3"):
                equity.append({**acc, "balance": acc["credit"] - acc["debit"]})
            elif code.startswith("4"):
                revenue.append({**acc, "balance": acc["credit"] - acc["debit"]})
            elif code.startswith("5") or code.startswith("6"):
                expenses.append({**acc, "balance": balance})
        
        total_assets = sum(a["balance"] for a in assets)
        total_liabilities = sum(l["balance"] for l in liabilities)
        total_equity = sum(e["balance"] for e in equity)
        total_revenue = sum(r["balance"] for r in revenue)
        total_expenses = sum(e["balance"] for e in expenses)
        
        net_income = total_revenue - total_expenses
        
        return {
            "report_type": "balance_sheet",
            "tenant": db_name,
            "generated_at": self.timestamp.isoformat(),
            "snapshot_id": self.snapshot_id,
            "assets": {
                "accounts": assets,
                "total": total_assets
            },
            "liabilities": {
                "accounts": liabilities,
                "total": total_liabilities
            },
            "equity": {
                "accounts": equity,
                "total": total_equity,
                "retained_earnings": net_income
            },
            "income_statement": {
                "revenue": total_revenue,
                "expenses": total_expenses,
                "net_income": net_income
            },
            "equation": {
                "assets": total_assets,
                "liabilities_equity": total_liabilities + total_equity + net_income,
                "balanced": abs(total_assets - (total_liabilities + total_equity + net_income)) < 1
            }
        }
    
    async def generate_inventory_snapshot(self, db_name: str) -> Dict:
        """Generate Inventory Snapshot"""
        db = self.client[db_name]
        
        # Get products with stock
        products = await db["products"].find(
            {},
            {"_id": 0, "id": 1, "name": 1, "sku": 1, "stock": 1, "cost_price": 1, "selling_price": 1, "category": 1}
        ).to_list(10000)
        
        # Calculate totals
        total_qty = 0
        total_cost_value = 0
        total_retail_value = 0
        
        inventory = []
        for p in products:
            qty = p.get("stock", 0) or 0
            cost = p.get("cost_price", 0) or 0
            retail = p.get("selling_price", 0) or 0
            
            cost_value = qty * cost
            retail_value = qty * retail
            
            total_qty += qty
            total_cost_value += cost_value
            total_retail_value += retail_value
            
            inventory.append({
                "product_id": p.get("id", ""),
                "name": p.get("name", ""),
                "sku": p.get("sku", ""),
                "category": p.get("category", ""),
                "quantity": qty,
                "cost_price": cost,
                "selling_price": retail,
                "cost_value": cost_value,
                "retail_value": retail_value
            })
        
        # Sort by value descending
        inventory.sort(key=lambda x: x["cost_value"], reverse=True)
        
        return {
            "report_type": "inventory_snapshot",
            "tenant": db_name,
            "generated_at": self.timestamp.isoformat(),
            "snapshot_id": self.snapshot_id,
            "summary": {
                "total_products": len(inventory),
                "total_quantity": total_qty,
                "total_cost_value": total_cost_value,
                "total_retail_value": total_retail_value,
                "potential_margin": total_retail_value - total_cost_value
            },
            "items": inventory[:500]  # Top 500 by value
        }
    
    async def generate_gl_summary(self, db_name: str) -> Dict:
        """Generate General Ledger Summary"""
        db = self.client[db_name]
        
        # Get recent journal entries
        journals = await db["journal_entries"].find(
            {"status": "posted"},
            {"_id": 0}
        ).sort("posted_at", -1).limit(100).to_list(100)
        
        # Count by type
        type_counts = {}
        for j in journals:
            jtype = j.get("transaction_type", "other")
            type_counts[jtype] = type_counts.get(jtype, 0) + 1
        
        return {
            "report_type": "gl_summary",
            "tenant": db_name,
            "generated_at": self.timestamp.isoformat(),
            "snapshot_id": self.snapshot_id,
            "total_journals": await db["journal_entries"].count_documents({"status": "posted"}),
            "recent_journals": len(journals),
            "by_type": type_counts,
            "journals": journals[:20]  # Last 20 entries
        }
    
    def generate_pdf_report(self, data: Dict, output_path: str, title: str):
        """Generate PDF report from data"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.5*cm,
            bottomMargin=1*cm
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph(f"OCB TITAN ERP - {title}", title_style))
        elements.append(Paragraph(f"Generated: {data.get('generated_at', '')}", styles['Normal']))
        elements.append(Paragraph(f"Snapshot ID: {data.get('snapshot_id', '')}", styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Content based on report type
        report_type = data.get("report_type", "")
        
        if report_type == "trial_balance":
            self._add_trial_balance_pdf(elements, data, styles)
        elif report_type == "balance_sheet":
            self._add_balance_sheet_pdf(elements, data, styles)
        elif report_type == "inventory_snapshot":
            self._add_inventory_pdf(elements, data, styles)
        elif report_type == "gl_summary":
            self._add_gl_summary_pdf(elements, data, styles)
        
        doc.build(elements)
    
    def _add_trial_balance_pdf(self, elements, data, styles):
        """Add trial balance content to PDF"""
        elements.append(Paragraph("TRIAL BALANCE", styles['Heading2']))
        elements.append(Spacer(1, 0.3*cm))
        
        # Table data
        table_data = [["Code", "Account Name", "Debit", "Credit"]]
        
        for acc in data.get("accounts", [])[:50]:
            table_data.append([
                acc.get("code", ""),
                acc.get("name", "")[:40],
                f"Rp {acc.get('debit', 0):,.0f}" if acc.get('debit', 0) > 0 else "",
                f"Rp {acc.get('credit', 0):,.0f}" if acc.get('credit', 0) > 0 else ""
            ])
        
        # Add totals
        totals = data.get("totals", {})
        table_data.append(["", "TOTAL", f"Rp {totals.get('debit', 0):,.0f}", f"Rp {totals.get('credit', 0):,.0f}"])
        
        table = Table(table_data, colWidths=[2*cm, 8*cm, 4*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
        
        status = "BALANCED" if totals.get("balanced") else "IMBALANCED"
        elements.append(Paragraph(f"Status: {status}", styles['Normal']))
    
    def _add_balance_sheet_pdf(self, elements, data, styles):
        """Add balance sheet content to PDF"""
        elements.append(Paragraph("BALANCE SHEET", styles['Heading2']))
        
        # Assets
        elements.append(Paragraph("ASSETS", styles['Heading3']))
        total_assets = data.get("assets", {}).get("total", 0)
        elements.append(Paragraph(f"Total Assets: Rp {total_assets:,.0f}", styles['Normal']))
        
        # Liabilities
        elements.append(Paragraph("LIABILITIES", styles['Heading3']))
        total_liabilities = data.get("liabilities", {}).get("total", 0)
        elements.append(Paragraph(f"Total Liabilities: Rp {total_liabilities:,.0f}", styles['Normal']))
        
        # Equity
        elements.append(Paragraph("EQUITY", styles['Heading3']))
        total_equity = data.get("equity", {}).get("total", 0)
        retained = data.get("equity", {}).get("retained_earnings", 0)
        elements.append(Paragraph(f"Total Equity: Rp {total_equity:,.0f}", styles['Normal']))
        elements.append(Paragraph(f"Retained Earnings: Rp {retained:,.0f}", styles['Normal']))
        
        # Equation
        eq = data.get("equation", {})
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Assets = Rp {eq.get('assets', 0):,.0f}", styles['Normal']))
        elements.append(Paragraph(f"L + E = Rp {eq.get('liabilities_equity', 0):,.0f}", styles['Normal']))
        status = "BALANCED" if eq.get("balanced") else "IMBALANCED"
        elements.append(Paragraph(f"Status: {status}", styles['Normal']))
    
    def _add_inventory_pdf(self, elements, data, styles):
        """Add inventory content to PDF"""
        elements.append(Paragraph("INVENTORY SNAPSHOT", styles['Heading2']))
        
        summary = data.get("summary", {})
        elements.append(Paragraph(f"Total Products: {summary.get('total_products', 0)}", styles['Normal']))
        elements.append(Paragraph(f"Total Quantity: {summary.get('total_quantity', 0):,.0f}", styles['Normal']))
        elements.append(Paragraph(f"Cost Value: Rp {summary.get('total_cost_value', 0):,.0f}", styles['Normal']))
        elements.append(Paragraph(f"Retail Value: Rp {summary.get('total_retail_value', 0):,.0f}", styles['Normal']))
        
        # Top items table
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph("Top Items by Value", styles['Heading3']))
        
        table_data = [["SKU", "Name", "Qty", "Cost Value"]]
        for item in data.get("items", [])[:20]:
            table_data.append([
                item.get("sku", "")[:15],
                item.get("name", "")[:30],
                f"{item.get('quantity', 0):,.0f}",
                f"Rp {item.get('cost_value', 0):,.0f}"
            ])
        
        table = Table(table_data, colWidths=[3*cm, 7*cm, 2*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(table)
    
    def _add_gl_summary_pdf(self, elements, data, styles):
        """Add GL summary content to PDF"""
        elements.append(Paragraph("GENERAL LEDGER SUMMARY", styles['Heading2']))
        elements.append(Paragraph(f"Total Journals: {data.get('total_journals', 0)}", styles['Normal']))
        
        # By type
        elements.append(Paragraph("By Transaction Type:", styles['Heading3']))
        for ttype, count in data.get("by_type", {}).items():
            elements.append(Paragraph(f"  • {ttype}: {count}", styles['Normal']))
    
    async def generate_full_snapshot(self, db_name: str = "ocb_titan") -> Dict:
        """Generate complete business snapshot"""
        await self.connect()
        
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        
        print("="*70)
        print("OCB TITAN - BUSINESS SNAPSHOT GENERATOR")
        print(f"Tenant: {db_name}")
        print(f"Snapshot ID: {self.snapshot_id}")
        print(f"Timestamp: {self.timestamp.isoformat()}")
        print("="*70)
        
        results = {}
        
        # 1. Trial Balance
        print("\n[1/4] Generating Trial Balance...")
        tb = await self.generate_trial_balance(db_name)
        results["trial_balance"] = tb
        
        tb_json = f"{SNAPSHOT_DIR}/trial_balance_{self.timestamp.strftime('%Y%m%d')}.json"
        with open(tb_json, "w") as f:
            json.dump(tb, f, indent=2)
        print(f"  ✅ JSON: {tb_json}")
        
        tb_pdf = f"{SNAPSHOT_DIR}/trial_balance_{self.timestamp.strftime('%Y%m%d')}.pdf"
        self.generate_pdf_report(tb, tb_pdf, "Trial Balance")
        print(f"  ✅ PDF: {tb_pdf}")
        
        # 2. Balance Sheet
        print("\n[2/4] Generating Balance Sheet...")
        bs = await self.generate_balance_sheet(db_name)
        results["balance_sheet"] = bs
        
        bs_json = f"{SNAPSHOT_DIR}/balance_sheet_{self.timestamp.strftime('%Y%m%d')}.json"
        with open(bs_json, "w") as f:
            json.dump(bs, f, indent=2)
        print(f"  ✅ JSON: {bs_json}")
        
        bs_pdf = f"{SNAPSHOT_DIR}/balance_sheet_{self.timestamp.strftime('%Y%m%d')}.pdf"
        self.generate_pdf_report(bs, bs_pdf, "Balance Sheet")
        print(f"  ✅ PDF: {bs_pdf}")
        
        # 3. Inventory Snapshot
        print("\n[3/4] Generating Inventory Snapshot...")
        inv = await self.generate_inventory_snapshot(db_name)
        results["inventory"] = inv
        
        inv_json = f"{SNAPSHOT_DIR}/inventory_snapshot_{self.timestamp.strftime('%Y%m%d')}.json"
        with open(inv_json, "w") as f:
            json.dump(inv, f, indent=2)
        print(f"  ✅ JSON: {inv_json}")
        
        inv_pdf = f"{SNAPSHOT_DIR}/inventory_snapshot_{self.timestamp.strftime('%Y%m%d')}.pdf"
        self.generate_pdf_report(inv, inv_pdf, "Inventory Snapshot")
        print(f"  ✅ PDF: {inv_pdf}")
        
        # 4. GL Summary
        print("\n[4/4] Generating GL Summary...")
        gl = await self.generate_gl_summary(db_name)
        results["gl_summary"] = gl
        
        gl_json = f"{SNAPSHOT_DIR}/gl_summary_{self.timestamp.strftime('%Y%m%d')}.json"
        with open(gl_json, "w") as f:
            json.dump(gl, f, indent=2)
        print(f"  ✅ JSON: {gl_json}")
        
        gl_pdf = f"{SNAPSHOT_DIR}/gl_summary_{self.timestamp.strftime('%Y%m%d')}.pdf"
        self.generate_pdf_report(gl, gl_pdf, "GL Summary")
        print(f"  ✅ PDF: {gl_pdf}")
        
        await self.disconnect()
        
        # Summary
        summary = {
            "snapshot_id": self.snapshot_id,
            "tenant": db_name,
            "generated_at": self.timestamp.isoformat(),
            "output_directory": SNAPSHOT_DIR,
            "files_generated": {
                "trial_balance_json": tb_json,
                "trial_balance_pdf": tb_pdf,
                "balance_sheet_json": bs_json,
                "balance_sheet_pdf": bs_pdf,
                "inventory_json": inv_json,
                "inventory_pdf": inv_pdf,
                "gl_summary_json": gl_json,
                "gl_summary_pdf": gl_pdf
            },
            "status": {
                "trial_balance_balanced": tb["totals"]["balanced"],
                "balance_sheet_balanced": bs["equation"]["balanced"]
            }
        }
        
        # Save summary
        summary_path = f"{SNAPSHOT_DIR}/snapshot_summary_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        print("\n" + "="*70)
        print("BUSINESS SNAPSHOT COMPLETE")
        print("="*70)
        print(f"Snapshot ID: {self.snapshot_id}")
        print(f"Output: {SNAPSHOT_DIR}")
        print(f"Trial Balance: {'✅ BALANCED' if tb['totals']['balanced'] else '❌ IMBALANCED'}")
        print(f"Balance Sheet: {'✅ BALANCED' if bs['equation']['balanced'] else '❌ IMBALANCED'}")
        print("="*70)
        
        return summary


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OCB TITAN Business Snapshot Generator")
    parser.add_argument("--tenant", type=str, default="ocb_titan", help="Tenant database name")
    
    args = parser.parse_args()
    
    generator = BusinessSnapshotGenerator()
    return await generator.generate_full_snapshot(args.tenant)


if __name__ == "__main__":
    asyncio.run(main())
