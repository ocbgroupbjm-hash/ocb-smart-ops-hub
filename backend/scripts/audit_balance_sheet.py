#!/usr/bin/env python3
"""
OCB TITAN ERP - AUDIT BALANCE SHEET
Script untuk audit dan validasi Balance Sheet (Neraca)

TUJUAN:
1. Hitung total assets, liabilities, equity
2. Validasi persamaan akuntansi: Assets = Liabilities + Equity
3. Identifikasi akun penyebab selisih jika ada
4. Telusuri jurnal yang menyebabkan selisih
5. Validasi normal balance semua akun

PENGGUNAAN:
    python3 audit_balance_sheet.py [--database <db_name>] [--output <output_dir>]

DEFAULT:
    Database: ocb_titan
    Output: /app/backend/scripts/audit_output/
"""

import asyncio
import argparse
import json
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Configuration
DEFAULT_DB = "ocb_titan"
DEFAULT_OUTPUT_DIR = "/app/backend/scripts/audit_output"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")


def classify_account(code: str) -> dict:
    """
    Klasifikasi akun berdasarkan kode
    
    Convention:
    - 1xxx: Asset (Normal Balance: Debit)
    - 2xxx: Liability (Normal Balance: Credit)
    - 3xxx: Equity (Normal Balance: Credit)
    - 4xxx: Revenue (Normal Balance: Credit)
    - 5xxx-8xxx: Expense (Normal Balance: Debit)
    - 9xxx: Other/Adjustment
    """
    if not code:
        return {"type": "unknown", "normal_balance": "debit", "category": "unknown"}
    
    # Handle both formats: "1-1000" and "1101"
    prefix = code.split("-")[0] if "-" in code else code[:1]
    
    classifications = {
        "1": {"type": "asset", "normal_balance": "debit", "category": "current_asset"},
        "2": {"type": "liability", "normal_balance": "credit", "category": "current_liability"},
        "3": {"type": "equity", "normal_balance": "credit", "category": "equity"},
        "4": {"type": "revenue", "normal_balance": "credit", "category": "operating_revenue"},
        "5": {"type": "expense", "normal_balance": "debit", "category": "cogs"},
        "6": {"type": "expense", "normal_balance": "debit", "category": "operating_expense"},
        "7": {"type": "expense", "normal_balance": "debit", "category": "other_expense"},
        "8": {"type": "expense", "normal_balance": "debit", "category": "other_expense"},
        "9": {"type": "equity", "normal_balance": "credit", "category": "adjustment"},
    }
    
    return classifications.get(prefix, {"type": "unknown", "normal_balance": "debit", "category": "unknown"})


async def get_all_journal_entries_with_lines(db) -> list:
    """
    Get all posted journal entries with their line items
    Handles both embedded and separate line formats
    """
    je_collection = db["journal_entries"]
    je_lines_collection = db["journal_entry_lines"]
    
    all_je = await je_collection.find({"status": "posted"}, {"_id": 0}).to_list(100000)
    
    result = []
    for je in all_je:
        entries = je.get("entries", [])
        
        # If no embedded entries, load from journal_entry_lines
        if not entries:
            lines = await je_lines_collection.find(
                {"journal_id": je.get("id")}, {"_id": 0}
            ).to_list(100)
            if lines:
                je["entries"] = lines
        
        result.append(je)
    
    return result


async def audit_balance_sheet(database: str, output_dir: str):
    """Main audit function"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[database]
    
    print(f"\n{'='*60}")
    print(f"OCB TITAN ERP - AUDIT BALANCE SHEET")
    print(f"Database: {database}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"{'='*60}\n")
    
    # 1. GET ALL POSTED JOURNALS
    all_journals = await get_all_journal_entries_with_lines(db)
    print(f"Total Posted Journals: {len(all_journals)}")
    
    # 2. AGGREGATE BY ACCOUNT
    account_data = {}
    unbalanced_journals = []
    
    for je in all_journals:
        entries = je.get("entries", [])
        total_debit = sum(e.get("debit", 0) for e in entries)
        total_credit = sum(e.get("credit", 0) for e in entries)
        
        # Check if journal is balanced
        if abs(total_debit - total_credit) > 0.01:
            unbalanced_journals.append({
                "journal_number": je.get("journal_number", ""),
                "journal_date": je.get("journal_date", je.get("created_at", "")),
                "description": je.get("description", ""),
                "total_debit": total_debit,
                "total_credit": total_credit,
                "difference": total_debit - total_credit
            })
        
        # Aggregate by account
        for entry in entries:
            code = entry.get("account_code", "")
            name = entry.get("account_name", "Unknown")
            debit = entry.get("debit", 0)
            credit = entry.get("credit", 0)
            
            if not code:
                continue
            
            if code not in account_data:
                account_data[code] = {
                    "name": name,
                    "debit": 0,
                    "credit": 0,
                    "classification": classify_account(code)
                }
            
            account_data[code]["debit"] += debit
            account_data[code]["credit"] += credit
    
    # 3. CHECK FOR UNBALANCED JOURNALS
    print(f"\n{'='*60}")
    print("STEP 1: VALIDASI JURNAL SEIMBANG (DEBIT = CREDIT)")
    print(f"{'='*60}")
    
    if unbalanced_journals:
        print(f"\n⚠️  DITEMUKAN {len(unbalanced_journals)} JURNAL TIDAK SEIMBANG:\n")
        for uj in unbalanced_journals[:10]:  # Show first 10
            print(f"  - {uj['journal_number']}: D={uj['total_debit']:,.2f} C={uj['total_credit']:,.2f} Diff={uj['difference']:,.2f}")
    else:
        print("\n✅ SEMUA JURNAL SEIMBANG (Debit = Credit)")
    
    # 4. CALCULATE BALANCE SHEET COMPONENTS
    print(f"\n{'='*60}")
    print("STEP 2: KALKULASI SALDO PER AKUN")
    print(f"{'='*60}\n")
    
    assets = []
    liabilities = []
    equity = []
    revenues = []
    expenses = []
    unknowns = []
    
    for code in sorted(account_data.keys()):
        data = account_data[code]
        debit = data["debit"]
        credit = data["credit"]
        classification = data["classification"]
        
        # Calculate balance based on normal balance
        if classification["normal_balance"] == "debit":
            balance = debit - credit
        else:
            balance = credit - debit
        
        if abs(balance) < 0.01:
            continue
        
        account_info = {
            "code": code,
            "name": data["name"],
            "debit": debit,
            "credit": credit,
            "balance": balance,
            "type": classification["type"],
            "normal_balance": classification["normal_balance"]
        }
        
        # Sort into categories
        if classification["type"] == "asset":
            assets.append(account_info)
        elif classification["type"] == "liability":
            liabilities.append(account_info)
        elif classification["type"] == "equity":
            equity.append(account_info)
        elif classification["type"] == "revenue":
            revenues.append(account_info)
        elif classification["type"] == "expense":
            expenses.append(account_info)
        else:
            unknowns.append(account_info)
    
    # Print account details
    def print_accounts(title, accounts, is_credit_normal=False):
        print(f"\n{title}:")
        print("-" * 100)
        total = 0
        for acc in accounts:
            print(f"  {acc['code']:15} | {acc['name'][:35]:35} | Balance: {acc['balance']:>15,.2f}")
            total += acc['balance']
        print("-" * 100)
        print(f"  {'TOTAL':15} | {'':35} | Balance: {total:>15,.2f}")
        return total
    
    total_assets = print_accounts("ASSETS (Aktiva)", assets)
    total_liabilities = print_accounts("LIABILITIES (Kewajiban)", liabilities)
    total_equity = print_accounts("EQUITY (Modal)", equity)
    total_revenue = print_accounts("REVENUE (Pendapatan)", revenues)
    total_expense = print_accounts("EXPENSES (Beban)", expenses)
    
    if unknowns:
        print_accounts("UNKNOWN CLASSIFICATION ⚠️", unknowns)
    
    # 5. CALCULATE NET INCOME AND VALIDATE
    print(f"\n{'='*60}")
    print("STEP 3: PERSAMAAN AKUNTANSI")
    print(f"{'='*60}\n")
    
    net_income = total_revenue - total_expense
    total_equity_with_net = total_equity + net_income
    right_side = total_liabilities + total_equity_with_net
    difference = total_assets - right_side
    is_balanced = abs(difference) < 0.01
    
    print("LABA RUGI (Income Statement):")
    print(f"  Total Revenue:           {total_revenue:>20,.2f}")
    print(f"  Total Expense:           {total_expense:>20,.2f}")
    print(f"  Net Income (Laba/Rugi):  {net_income:>20,.2f}")
    
    print("\nNERACA (Balance Sheet):")
    print(f"  Total Assets:            {total_assets:>20,.2f}")
    print(f"  Total Liabilities:       {total_liabilities:>20,.2f}")
    print(f"  Total Equity (Recorded): {total_equity:>20,.2f}")
    print(f"  Net Income:              {net_income:>20,.2f}")
    print(f"  Total Equity + NI:       {total_equity_with_net:>20,.2f}")
    
    print("\nPERSAMAAN AKUNTANSI:")
    print(f"  Assets                          = {total_assets:>20,.2f}")
    print(f"  Liabilities + Equity + Net Inc  = {right_side:>20,.2f}")
    print(f"  Selisih                         = {difference:>20,.2f}")
    
    print(f"\n{'='*60}")
    if is_balanced:
        print("✅ BALANCE SHEET SEIMBANG - PERSAMAAN AKUNTANSI VALID")
    else:
        print("❌ BALANCE SHEET TIDAK SEIMBANG!")
        print(f"   Selisih: Rp {abs(difference):,.2f}")
    print(f"{'='*60}")
    
    # 6. GENERATE REPORT
    report = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "database": database,
        "total_journals": len(all_journals),
        "unbalanced_journals": {
            "count": len(unbalanced_journals),
            "items": unbalanced_journals[:20]  # First 20
        },
        "balance_sheet": {
            "assets": {
                "items": assets,
                "total": total_assets
            },
            "liabilities": {
                "items": liabilities,
                "total": total_liabilities
            },
            "equity": {
                "items": equity,
                "total_recorded": total_equity,
                "net_income": net_income,
                "total_with_net_income": total_equity_with_net
            },
            "income_statement": {
                "revenue": {
                    "items": revenues,
                    "total": total_revenue
                },
                "expenses": {
                    "items": expenses,
                    "total": total_expense
                },
                "net_income": net_income
            }
        },
        "accounting_equation": {
            "left_side": {
                "description": "Total Assets",
                "value": total_assets
            },
            "right_side": {
                "description": "Liabilities + Equity + Net Income",
                "value": right_side,
                "breakdown": {
                    "liabilities": total_liabilities,
                    "equity_recorded": total_equity,
                    "net_income": net_income
                }
            },
            "difference": difference,
            "is_balanced": is_balanced
        },
        "unknown_accounts": unknowns,
        "validation": {
            "all_journals_balanced": len(unbalanced_journals) == 0,
            "balance_sheet_balanced": is_balanced,
            "no_unknown_accounts": len(unknowns) == 0,
            "overall_status": "PASS" if (len(unbalanced_journals) == 0 and is_balanced and len(unknowns) == 0) else "FAIL"
        }
    }
    
    # Save report
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "balance_sheet_audit_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n📄 Report saved: {report_path}")
    
    # Generate Markdown report
    md_report = generate_markdown_report(report)
    md_path = os.path.join(output_dir, "balance_sheet_audit_report.md")
    with open(md_path, "w") as f:
        f.write(md_report)
    print(f"📄 Markdown report saved: {md_path}")
    
    client.close()
    return report


def generate_markdown_report(report: dict) -> str:
    """Generate Markdown formatted report"""
    md = []
    md.append("# OCB TITAN ERP - BALANCE SHEET AUDIT REPORT")
    md.append(f"\n**Audit Timestamp:** {report['audit_timestamp']}")
    md.append(f"**Database:** {report['database']}")
    md.append(f"**Total Journals:** {report['total_journals']}")
    
    # Validation Status
    status = report["validation"]["overall_status"]
    status_icon = "✅" if status == "PASS" else "❌"
    md.append(f"\n## Status: {status_icon} {status}")
    
    # Balance Sheet Summary
    bs = report["balance_sheet"]
    md.append("\n## Neraca (Balance Sheet)\n")
    md.append("| Komponen | Saldo |")
    md.append("|----------|------:|")
    md.append(f"| **Total Assets** | Rp {bs['assets']['total']:,.2f} |")
    md.append(f"| **Total Liabilities** | Rp {bs['liabilities']['total']:,.2f} |")
    md.append(f"| **Total Equity (Recorded)** | Rp {bs['equity']['total_recorded']:,.2f} |")
    md.append(f"| **Net Income** | Rp {bs['equity']['net_income']:,.2f} |")
    md.append(f"| **Total Equity + NI** | Rp {bs['equity']['total_with_net_income']:,.2f} |")
    
    # Accounting Equation
    eq = report["accounting_equation"]
    md.append("\n## Persamaan Akuntansi\n")
    md.append("```")
    md.append(f"Assets                         = Rp {eq['left_side']['value']:>20,.2f}")
    md.append(f"Liabilities + Equity + NI      = Rp {eq['right_side']['value']:>20,.2f}")
    md.append(f"Selisih                        = Rp {eq['difference']:>20,.2f}")
    md.append("```")
    
    if eq["is_balanced"]:
        md.append("\n✅ **BALANCE SHEET SEIMBANG**")
    else:
        md.append(f"\n❌ **BALANCE SHEET TIDAK SEIMBANG** - Selisih: Rp {abs(eq['difference']):,.2f}")
    
    # Unbalanced Journals
    uj = report["unbalanced_journals"]
    if uj["count"] > 0:
        md.append(f"\n## ⚠️ Jurnal Tidak Seimbang ({uj['count']} total)\n")
        md.append("| Journal # | Debit | Credit | Selisih |")
        md.append("|-----------|------:|-------:|--------:|")
        for j in uj["items"][:10]:
            md.append(f"| {j['journal_number']} | {j['total_debit']:,.2f} | {j['total_credit']:,.2f} | {j['difference']:,.2f} |")
    else:
        md.append("\n## ✅ Semua Jurnal Seimbang")
    
    # Detail per Account Type
    md.append("\n## Detail per Jenis Akun")
    
    for acc_type, title in [("assets", "Assets"), ("liabilities", "Liabilities")]:
        items = bs[acc_type]["items"]
        if items:
            md.append(f"\n### {title}\n")
            md.append("| Kode | Nama Akun | Saldo |")
            md.append("|------|-----------|------:|")
            for item in items:
                md.append(f"| {item['code']} | {item['name'][:40]} | Rp {item['balance']:,.2f} |")
            md.append(f"| **TOTAL** | | **Rp {bs[acc_type]['total']:,.2f}** |")
    
    # Income Statement
    inc = bs["income_statement"]
    md.append("\n### Revenue (Pendapatan)\n")
    md.append("| Kode | Nama Akun | Saldo |")
    md.append("|------|-----------|------:|")
    for item in inc["revenue"]["items"]:
        md.append(f"| {item['code']} | {item['name'][:40]} | Rp {item['balance']:,.2f} |")
    md.append(f"| **TOTAL** | | **Rp {inc['revenue']['total']:,.2f}** |")
    
    md.append("\n### Expenses (Beban)\n")
    md.append("| Kode | Nama Akun | Saldo |")
    md.append("|------|-----------|------:|")
    for item in inc["expenses"]["items"]:
        md.append(f"| {item['code']} | {item['name'][:40]} | Rp {item['balance']:,.2f} |")
    md.append(f"| **TOTAL** | | **Rp {inc['expenses']['total']:,.2f}** |")
    
    md.append(f"\n**Net Income:** Rp {inc['net_income']:,.2f}")
    
    # Unknown Accounts
    unknowns = report.get("unknown_accounts", [])
    if unknowns:
        md.append("\n## ⚠️ Akun Tidak Terklasifikasi\n")
        md.append("| Kode | Nama | Saldo |")
        md.append("|------|------|------:|")
        for item in unknowns:
            md.append(f"| {item['code']} | {item['name']} | Rp {item['balance']:,.2f} |")
    
    md.append(f"\n---\n*Report generated: {report['audit_timestamp']}*")
    
    return "\n".join(md)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit Balance Sheet for OCB TITAN ERP")
    parser.add_argument("--database", "-d", default=DEFAULT_DB, help=f"Database name (default: {DEFAULT_DB})")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT_DIR, help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    
    args = parser.parse_args()
    
    asyncio.run(audit_balance_sheet(args.database, args.output))
