# OCB TITAN ERP - Print Engine
# Generate printable documents: PDF and Thermal receipts
# tenant-aware templates

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from typing import Optional
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm, cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from database import get_db
from utils.auth import get_current_user

router = APIRouter(prefix="/print", tags=["Print"])

# Paper sizes
THERMAL_WIDTH = 80 * mm  # 80mm thermal printer
THERMAL_RECEIPT_WIDTH = 58 * mm  # 58mm thermal printer


async def get_tenant_info(db):
    """Get tenant branding info for printing"""
    tenant = await db["tenants"].find_one({}, {"_id": 0})
    if not tenant:
        return {
            "name": "OCB TITAN",
            "address": "",
            "phone": "",
            "email": "",
            "npwp": "",
            "logo_url": ""
        }
    return tenant


def format_currency(amount: float) -> str:
    """Format number as Indonesian Rupiah"""
    return f"Rp {amount:,.0f}".replace(",", ".")


def draw_header(c, tenant: dict, y_position: float, width: float):
    """Draw company header on PDF"""
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y_position, tenant.get("name", "OCB TITAN"))
    
    y_position -= 15
    c.setFont("Helvetica", 9)
    if tenant.get("address"):
        c.drawCentredString(width / 2, y_position, tenant.get("address", ""))
        y_position -= 12
    
    if tenant.get("phone") or tenant.get("email"):
        contact = []
        if tenant.get("phone"):
            contact.append(f"Telp: {tenant['phone']}")
        if tenant.get("email"):
            contact.append(tenant["email"])
        c.drawCentredString(width / 2, y_position, " | ".join(contact))
        y_position -= 12
    
    if tenant.get("npwp"):
        c.drawCentredString(width / 2, y_position, f"NPWP: {tenant['npwp']}")
        y_position -= 12
    
    # Separator line
    y_position -= 5
    c.setStrokeColor(colors.black)
    c.line(20, y_position, width - 20, y_position)
    
    return y_position - 10


# ==================== SALES INVOICE PDF ====================

@router.get("/invoice/{invoice_id}")
async def print_invoice(
    invoice_id: str,
    format: str = Query("pdf", description="Output format: pdf or thermal"),
    user: dict = Depends(get_current_user)
):
    """Generate printable Sales Invoice"""
    db = get_db()
    
    # Fetch invoice
    invoice = await db["sales_invoices"].find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        # Try by invoice number
        invoice = await db["sales_invoices"].find_one({"invoice_number": invoice_id}, {"_id": 0})
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice tidak ditemukan")
    
    tenant = await get_tenant_info(db)
    
    if format == "thermal":
        return await generate_thermal_receipt(invoice, tenant, "invoice")
    
    # Generate PDF
    buffer = BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # Header
    y = height - 30
    y = draw_header(c, tenant, y, width)
    
    # Document title
    y -= 10
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "FAKTUR PENJUALAN")
    
    # Invoice details
    y -= 30
    c.setFont("Helvetica", 10)
    
    # Left column
    c.drawString(30, y, f"No. Invoice: {invoice.get('invoice_number', '')}")
    c.drawString(30, y - 15, f"Tanggal: {invoice.get('invoice_date', '')[:10]}")
    c.drawString(30, y - 30, f"Customer: {invoice.get('customer_name', 'Walk-in')}")
    
    # Right column
    c.drawRightString(width - 30, y, f"Status: {invoice.get('status', '').upper()}")
    c.drawRightString(width - 30, y - 15, f"Cabang: {invoice.get('branch_name', '-')}")
    c.drawRightString(width - 30, y - 30, f"Kasir: {invoice.get('cashier_name', '-')}")
    
    # Items table
    y -= 60
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, y, "DAFTAR ITEM")
    y -= 5
    c.line(30, y, width - 30, y)
    
    # Table header
    y -= 20
    c.setFont("Helvetica-Bold", 9)
    c.drawString(30, y, "No")
    c.drawString(50, y, "Produk")
    c.drawString(250, y, "Qty")
    c.drawString(300, y, "Harga")
    c.drawString(380, y, "Diskon")
    c.drawRightString(width - 30, y, "Subtotal")
    
    y -= 5
    c.line(30, y, width - 30, y)
    
    # Items
    c.setFont("Helvetica", 9)
    items = invoice.get("items", [])
    for idx, item in enumerate(items, 1):
        y -= 18
        if y < 150:  # New page if needed
            c.showPage()
            y = height - 50
        
        c.drawString(30, y, str(idx))
        
        # Truncate long product names
        product_name = item.get("product_name", "")[:35]
        c.drawString(50, y, product_name)
        
        c.drawString(250, y, str(item.get("quantity", 0)))
        c.drawString(300, y, format_currency(item.get("unit_price", 0)))
        c.drawString(380, y, format_currency(item.get("discount_amount", 0)))
        c.drawRightString(width - 30, y, format_currency(item.get("subtotal", 0)))
    
    # Totals
    y -= 20
    c.line(30, y, width - 30, y)
    
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(350, y, "Subtotal:")
    c.drawRightString(width - 30, y, format_currency(invoice.get("subtotal", 0)))
    
    y -= 15
    c.drawString(350, y, "Diskon:")
    c.drawRightString(width - 30, y, format_currency(invoice.get("discount_amount", 0)))
    
    if invoice.get("tax_amount", 0) > 0:
        y -= 15
        c.drawString(350, y, "PPN (11%):")
        c.drawRightString(width - 30, y, format_currency(invoice.get("tax_amount", 0)))
    
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, y, "TOTAL:")
    c.drawRightString(width - 30, y, format_currency(invoice.get("total", 0)))
    
    # Payment info
    y -= 30
    c.setFont("Helvetica", 10)
    c.drawString(30, y, f"Metode Pembayaran: {invoice.get('payment_method', '-').upper()}")
    
    if invoice.get("payment_method") == "cash":
        y -= 15
        c.drawString(30, y, f"Tunai: {format_currency(invoice.get('cash_received', 0))}")
        c.drawString(200, y, f"Kembalian: {format_currency(invoice.get('change_amount', 0))}")
    
    # Footer
    y -= 50
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, y, "Terima kasih atas kunjungan Anda")
    c.drawCentredString(width / 2, y - 12, f"Dicetak: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    c.save()
    buffer.seek(0)
    
    filename = f"invoice_{invoice.get('invoice_number', invoice_id)}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


# ==================== PURCHASE ORDER PDF ====================

@router.get("/purchase-order/{po_id}")
async def print_purchase_order(
    po_id: str,
    format: str = Query("pdf", description="Output format: pdf"),
    user: dict = Depends(get_current_user)
):
    """Generate printable Purchase Order"""
    db = get_db()
    
    po = await db["purchase_orders"].find_one({"id": po_id}, {"_id": 0})
    if not po:
        po = await db["purchase_orders"].find_one({"po_number": po_id}, {"_id": 0})
    
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order tidak ditemukan")
    
    tenant = await get_tenant_info(db)
    
    buffer = BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # Header
    y = height - 30
    y = draw_header(c, tenant, y, width)
    
    # Document title
    y -= 10
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "PURCHASE ORDER")
    
    # PO details
    y -= 30
    c.setFont("Helvetica", 10)
    
    # Left - PO Info
    c.drawString(30, y, f"No. PO: {po.get('po_number', '')}")
    c.drawString(30, y - 15, f"Tanggal: {po.get('order_date', '')[:10] if po.get('order_date') else ''}")
    c.drawString(30, y - 30, f"Status: {po.get('status', '').upper()}")
    
    # Right - Supplier Info
    c.drawRightString(width - 30, y, "Kepada:")
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 30, y - 15, po.get("supplier_name", "-"))
    c.setFont("Helvetica", 9)
    if po.get("supplier_address"):
        c.drawRightString(width - 30, y - 30, po.get("supplier_address", "")[:50])
    
    # Items table
    y -= 70
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, y, "DAFTAR ITEM")
    y -= 5
    c.line(30, y, width - 30, y)
    
    # Table header
    y -= 20
    c.setFont("Helvetica-Bold", 9)
    c.drawString(30, y, "No")
    c.drawString(50, y, "Kode")
    c.drawString(120, y, "Produk")
    c.drawString(320, y, "Qty")
    c.drawString(370, y, "Harga")
    c.drawRightString(width - 30, y, "Subtotal")
    
    y -= 5
    c.line(30, y, width - 30, y)
    
    # Items
    c.setFont("Helvetica", 9)
    items = po.get("items", [])
    for idx, item in enumerate(items, 1):
        y -= 18
        if y < 150:
            c.showPage()
            y = height - 50
        
        c.drawString(30, y, str(idx))
        c.drawString(50, y, str(item.get("product_code", ""))[:12])
        c.drawString(120, y, str(item.get("product_name", ""))[:30])
        c.drawString(320, y, str(item.get("quantity", 0)))
        c.drawString(370, y, format_currency(item.get("unit_cost", 0)))
        c.drawRightString(width - 30, y, format_currency(item.get("subtotal", 0)))
    
    # Totals
    y -= 20
    c.line(30, y, width - 30, y)
    
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(350, y, "Subtotal:")
    c.drawRightString(width - 30, y, format_currency(po.get("subtotal", 0)))
    
    if po.get("discount_amount", 0) > 0:
        y -= 15
        c.drawString(350, y, "Diskon:")
        c.drawRightString(width - 30, y, format_currency(po.get("discount_amount", 0)))
    
    if po.get("tax_amount", 0) > 0:
        y -= 15
        c.drawString(350, y, "PPN:")
        c.drawRightString(width - 30, y, format_currency(po.get("tax_amount", 0)))
    
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, y, "TOTAL:")
    c.drawRightString(width - 30, y, format_currency(po.get("total", 0)))
    
    # Terms
    y -= 40
    c.setFont("Helvetica", 9)
    if po.get("is_credit"):
        c.drawString(30, y, f"Termin Pembayaran: {po.get('credit_due_days', 0)} hari")
    else:
        c.drawString(30, y, "Termin Pembayaran: COD (Cash on Delivery)")
    
    if po.get("notes"):
        y -= 15
        c.drawString(30, y, f"Catatan: {po.get('notes', '')[:80]}")
    
    # Signatures
    y -= 60
    c.setFont("Helvetica", 9)
    c.drawString(80, y, "Dibuat oleh,")
    c.drawString(width - 150, y, "Disetujui oleh,")
    
    y -= 50
    c.line(50, y, 180, y)
    c.line(width - 180, y, width - 50, y)
    
    y -= 15
    c.drawCentredString(115, y, po.get("created_by_name", "-"))
    c.drawCentredString(width - 115, y, "________________")
    
    # Footer
    y = 30
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, y, f"Dicetak: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    c.save()
    buffer.seek(0)
    
    filename = f"po_{po.get('po_number', po_id)}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


# ==================== THERMAL RECEIPT ====================

async def generate_thermal_receipt(doc: dict, tenant: dict, doc_type: str):
    """Generate thermal printer compatible receipt (58mm or 80mm)"""
    buffer = BytesIO()
    
    # 58mm paper = ~48mm printable width
    page_width = 58 * mm
    page_height = 200 * mm  # Variable height
    
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    
    y = page_height - 10
    center = page_width / 2
    
    # Header
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(center, y, tenant.get("name", "OCB TITAN")[:20])
    
    y -= 12
    c.setFont("Helvetica", 7)
    if tenant.get("address"):
        c.drawCentredString(center, y, tenant.get("address", "")[:35])
        y -= 10
    
    if tenant.get("phone"):
        c.drawCentredString(center, y, tenant.get("phone", ""))
        y -= 10
    
    # Separator
    y -= 3
    c.setDash(1, 2)
    c.line(3, y, page_width - 3, y)
    c.setDash()
    
    # Document info
    y -= 12
    c.setFont("Helvetica-Bold", 8)
    
    if doc_type == "invoice":
        doc_number = doc.get("invoice_number", "")
        doc_date = doc.get("invoice_date", "")[:10]
        c.drawCentredString(center, y, "STRUK PENJUALAN")
    else:
        doc_number = doc.get("po_number", "")
        doc_date = doc.get("order_date", "")[:10] if doc.get("order_date") else ""
        c.drawCentredString(center, y, "PURCHASE ORDER")
    
    y -= 12
    c.setFont("Helvetica", 7)
    c.drawString(3, y, f"No: {doc_number}")
    y -= 10
    c.drawString(3, y, f"Tgl: {doc_date}")
    c.drawRightString(page_width - 3, y, doc.get("cashier_name", "-")[:15])
    
    # Separator
    y -= 8
    c.line(3, y, page_width - 3, y)
    
    # Items
    y -= 10
    c.setFont("Helvetica", 7)
    items = doc.get("items", [])
    
    for item in items:
        if y < 50:
            break
        
        # Product name (may wrap)
        product_name = item.get("product_name", "")[:25]
        c.drawString(3, y, product_name)
        
        y -= 10
        qty = item.get("quantity", 0)
        price = item.get("unit_price", item.get("unit_cost", 0))
        subtotal = item.get("subtotal", 0)
        
        c.drawString(3, y, f"  {qty} x {format_currency(price)}")
        c.drawRightString(page_width - 3, y, format_currency(subtotal))
        y -= 12
    
    # Separator
    c.line(3, y, page_width - 3, y)
    
    # Totals
    y -= 12
    c.drawString(3, y, "Subtotal")
    c.drawRightString(page_width - 3, y, format_currency(doc.get("subtotal", 0)))
    
    if doc.get("discount_amount", 0) > 0:
        y -= 10
        c.drawString(3, y, "Diskon")
        c.drawRightString(page_width - 3, y, f"-{format_currency(doc.get('discount_amount', 0))}")
    
    if doc.get("tax_amount", 0) > 0:
        y -= 10
        c.drawString(3, y, "PPN")
        c.drawRightString(page_width - 3, y, format_currency(doc.get("tax_amount", 0)))
    
    y -= 12
    c.setFont("Helvetica-Bold", 9)
    c.drawString(3, y, "TOTAL")
    c.drawRightString(page_width - 3, y, format_currency(doc.get("total", 0)))
    
    # Payment info for invoice
    if doc_type == "invoice":
        y -= 12
        c.setFont("Helvetica", 7)
        payment = doc.get("payment_method", "cash").upper()
        c.drawString(3, y, f"Bayar: {payment}")
        
        if payment == "CASH":
            y -= 10
            c.drawString(3, y, f"Tunai: {format_currency(doc.get('cash_received', 0))}")
            y -= 10
            c.drawString(3, y, f"Kembali: {format_currency(doc.get('change_amount', 0))}")
    
    # Footer
    y -= 15
    c.setDash(1, 2)
    c.line(3, y, page_width - 3, y)
    c.setDash()
    
    y -= 12
    c.setFont("Helvetica", 6)
    c.drawCentredString(center, y, "Terima kasih")
    y -= 8
    c.drawCentredString(center, y, datetime.now().strftime("%d/%m/%Y %H:%M"))
    
    c.save()
    buffer.seek(0)
    
    filename = f"receipt_{doc_number}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


# ==================== POS RECEIPT ====================

@router.get("/receipt/{invoice_id}")
async def print_receipt(
    invoice_id: str,
    width: int = Query(58, description="Paper width in mm: 58 or 80"),
    user: dict = Depends(get_current_user)
):
    """Generate POS Receipt (thermal printer format)"""
    db = get_db()
    
    invoice = await db["sales_invoices"].find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        invoice = await db["sales_invoices"].find_one({"invoice_number": invoice_id}, {"_id": 0})
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice tidak ditemukan")
    
    tenant = await get_tenant_info(db)
    
    return await generate_thermal_receipt(invoice, tenant, "invoice")
