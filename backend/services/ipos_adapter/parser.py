# iPOS 5 Ultimate Backup Parser
# Parses PostgreSQL dump files (.i5bu) from iPOS 5 Ultimate
# READ-ONLY - No write operations to source

import re
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Generator
import logging

logger = logging.getLogger(__name__)


class IPOSBackupParser:
    """
    Parser for iPOS 5 Ultimate backup files (.i5bu)
    
    File format: PostgreSQL pg_dump binary/text format
    
    RULES:
    - READ-ONLY operations only
    - All extracts must be timestamped
    - Batch extracts must be idempotent
    """
    
    # Table mappings - iPOS table name to canonical name
    TABLE_MAP = {
        'tbl_item': 'items',
        'tbl_supel': 'suppliers_customers',  # Combined supplier/customer
        'tbl_itemstok': 'stock_positions',
        'tbl_itemjenis': 'categories',
        'tbl_itemmerek': 'brands',
        'tbl_itemsatuan': 'units',
        'tbl_perkiraan': 'chart_of_accounts',
        'tbl_accjurnal': 'journals',
        'tbl_kantor': 'warehouses',
        'tbl_ikhd': 'sales_headers',
        'tbl_ikdt': 'sales_details',
        'tbl_imhd': 'purchase_headers',
        'tbl_imdt': 'purchase_details',
        'tbl_byrhutanghd': 'ap_payment_headers',
        'tbl_byrhutangdt': 'ap_payment_details',
        'tbl_byrpiutanghd': 'ar_payment_headers',
        'tbl_byrpiutangdt': 'ar_payment_details',
        'tbl_user': 'users',
        'tbl_conf': 'config',
    }
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = None
        self.tables = {}
        self.extract_timestamp = datetime.now(timezone.utc).isoformat()
        self.file_hash = None
        
    def load(self) -> bool:
        """Load and parse the backup file"""
        try:
            with open(self.file_path, 'rb') as f:
                raw_content = f.read()
                self.file_hash = hashlib.sha256(raw_content).hexdigest()
                
            # Decode content
            self.content = raw_content.decode('utf-8', errors='ignore')
            logger.info(f"Loaded iPOS backup: {self.file_path}, hash: {self.file_hash[:16]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to load iPOS backup: {e}")
            return False
    
    def get_file_info(self) -> Dict:
        """Get backup file metadata"""
        return {
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "extract_timestamp": self.extract_timestamp,
            "source_system": "IPOS5_ULTIMATE",
            "format": "PGDUMP"
        }
    
    def extract_table_data(self, table_name: str) -> List[Dict]:
        """
        Extract data from a specific table
        
        Args:
            table_name: iPOS table name (e.g., 'tbl_item')
            
        Returns:
            List of dictionaries containing row data
        """
        if not self.content:
            self.load()
        
        # Find COPY statement for this table
        # Format: COPY table_name (columns) FROM stdin;
        copy_pattern = rf'COPY {table_name}\s*\(([^)]+)\)\s*FROM stdin;'
        match = re.search(copy_pattern, self.content, re.IGNORECASE)
        
        if not match:
            logger.warning(f"Table {table_name} not found in backup")
            return []
        
        # Get column names
        columns_str = match.group(1)
        columns = [c.strip() for c in columns_str.split(',')]
        
        # Find data section (after COPY statement until \.)
        copy_start = match.end()
        end_marker = self.content.find('\\.', copy_start)
        
        if end_marker == -1:
            # Try alternative end marker
            end_marker = self.content.find('\\.\n', copy_start)
        
        if end_marker == -1:
            logger.warning(f"Could not find end of data for table {table_name}")
            return []
        
        data_section = self.content[copy_start:end_marker].strip()
        
        # Parse rows (tab-separated)
        rows = []
        for line_num, line in enumerate(data_section.split('\n')):
            if not line.strip() or line.startswith('--'):
                continue
                
            values = line.split('\t')
            
            if len(values) != len(columns):
                # Skip malformed rows
                continue
            
            row = {}
            for i, col in enumerate(columns):
                val = values[i] if i < len(values) else None
                # Handle PostgreSQL NULL representation
                if val == '\\N':
                    val = None
                row[col] = val
            
            rows.append(row)
        
        logger.info(f"Extracted {len(rows)} rows from {table_name}")
        return rows
    
    def extract_items(self) -> List[Dict]:
        """Extract master items (barang)"""
        raw_data = self.extract_table_data('tbl_item')
        
        items = []
        for row in raw_data:
            item = {
                "source_id": row.get('kodeitem'),
                "code": row.get('kodeitem'),
                "name": row.get('namaitem'),
                "category": row.get('jenis'),
                "brand": row.get('merek'),
                "unit": row.get('satuan'),
                "type": row.get('tipe'),
                "currency": row.get('matauang'),
                "is_serial": row.get('serial') == 'Y',
                "is_consignment": row.get('konsinyasi') == 'Y',
                "min_stock": self._parse_decimal(row.get('stokmin')),
                "cost_price": self._parse_decimal(row.get('hargapokok')),
                "sell_price_1": self._parse_decimal(row.get('hargajual1')),
                "sell_price_2": self._parse_decimal(row.get('hargajual2')),
                "sell_price_3": self._parse_decimal(row.get('hargajual3')),
                "barcode": row.get('barcode'),
                "supplier_code": row.get('kodesupel'),
                "location": row.get('rak'),
                "is_active": row.get('aktif') != 'N',
                "source_system": "IPOS5",
                "raw_data": row
            }
            items.append(item)
        
        return items
    
    def extract_suppliers_customers(self) -> Dict[str, List[Dict]]:
        """Extract suppliers and customers (combined in tbl_supel)"""
        raw_data = self.extract_table_data('tbl_supel')
        
        suppliers = []
        customers = []
        
        for row in raw_data:
            entity = {
                "source_id": row.get('kode'),
                "code": row.get('kode'),
                "type": row.get('tipe'),  # 'S' = Supplier, 'C' = Customer, 'SC' = Both
                "name": row.get('nama'),
                "address": row.get('alamat'),
                "city": row.get('kota'),
                "province": row.get('provinsi'),
                "postal_code": row.get('kodepos'),
                "country": row.get('negara'),
                "phone": row.get('telepon'),
                "fax": row.get('fax'),
                "contact": row.get('kontak'),
                "email": row.get('email'),
                "currency": row.get('matauang'),
                "bank_account": row.get('norek'),
                "account_name": row.get('atasnama'),
                "tax_id": row.get('npwp'),
                "credit_limit": self._parse_decimal(row.get('kreditlimit')),
                "is_active": row.get('aktif') != 'N',
                "source_system": "IPOS5",
                "raw_data": row
            }
            
            if row.get('tipe') in ['S', 'SC']:
                suppliers.append(entity)
            if row.get('tipe') in ['C', 'SC']:
                customers.append(entity)
        
        return {
            "suppliers": suppliers,
            "customers": customers
        }
    
    def extract_stock_positions(self) -> List[Dict]:
        """Extract stock positions per item per warehouse"""
        raw_data = self.extract_table_data('tbl_itemstok')
        
        stocks = []
        for row in raw_data:
            stock = {
                "source_id": f"{row.get('kodeitem')}_{row.get('kantor')}",
                "item_code": row.get('kodeitem'),
                "warehouse_code": row.get('kantor'),
                "quantity": self._parse_decimal(row.get('stok')),
                "hpp_base": self._parse_decimal(row.get('hppdasar')),
                "source_system": "IPOS5",
                "raw_data": row
            }
            stocks.append(stock)
        
        return stocks
    
    def extract_warehouses(self) -> List[Dict]:
        """Extract warehouses/outlets (kantor)"""
        raw_data = self.extract_table_data('tbl_kantor')
        
        warehouses = []
        for row in raw_data:
            wh = {
                "source_id": row.get('kodekantor'),
                "code": row.get('kodekantor'),
                "name": row.get('namakantor'),
                "function": row.get('fungsi'),  # 'GUDANG', 'TOKO', etc
                "address": row.get('alamat'),
                "phone": row.get('notelepon'),
                "fax": row.get('fax'),
                "is_branch": row.get('cabang') == 't',
                "account_code": row.get('kodeacc'),
                "is_active": row.get('stsaktif') == 'Y',
                "source_system": "IPOS5",
                "raw_data": row
            }
            warehouses.append(wh)
        
        return warehouses
    
    def extract_chart_of_accounts(self) -> List[Dict]:
        """Extract chart of accounts (perkiraan)"""
        raw_data = self.extract_table_data('tbl_perkiraan')
        
        accounts = []
        for row in raw_data:
            acc = {
                "source_id": row.get('kodeacc'),
                "code": row.get('kodeacc'),
                "parent_code": row.get('parentacc'),
                "group": row.get('kelompok'),  # '1' = Asset, '2' = Liability, etc
                "type": row.get('tipe'),  # 'H' = Header, 'D' = Detail
                "name": row.get('namaacc'),
                "currency": row.get('matauang'),
                "is_cash_bank": row.get('kasbank') == 't',
                "activity": row.get('aktivitas'),
                "source_system": "IPOS5",
                "raw_data": row
            }
            accounts.append(acc)
        
        return accounts
    
    def extract_journals(self) -> List[Dict]:
        """Extract journal entries"""
        raw_data = self.extract_table_data('tbl_accjurnal')
        
        journals = []
        for row in raw_data:
            journal = {
                "source_id": row.get('iddetail'),
                "line_no": self._parse_int(row.get('nourut')),
                "input_type": row.get('tipeinput'),
                "transaction_no": row.get('notransaksi'),
                "date": row.get('tanggal'),
                "account_code": row.get('kodeacc'),
                "journal_type": row.get('jenis'),
                "description": row.get('keterangan'),
                "currency": row.get('matauang'),
                "rate": self._parse_decimal(row.get('rate')),
                "amount": self._parse_decimal(row.get('jumlah')),
                "position": row.get('posisi'),  # 'D' or 'K'
                "debit": self._parse_decimal(row.get('debet')),
                "credit": self._parse_decimal(row.get('kredit')),
                "warehouse_code": row.get('kantor'),
                "source_system": "IPOS5",
                "raw_data": row
            }
            journals.append(journal)
        
        return journals
    
    def extract_sales(self) -> Dict[str, List[Dict]]:
        """Extract sales transactions (invoice keluar)"""
        headers = self.extract_table_data('tbl_ikhd')
        details = self.extract_table_data('tbl_ikdt')
        
        # Map headers
        sales_headers = []
        for row in headers:
            header = {
                "source_id": row.get('notransaksi'),
                "transaction_no": row.get('notransaksi'),
                "warehouse_code": row.get('kodekantor'),
                "from_warehouse": row.get('kantordari'),
                "date": row.get('tanggal'),
                "type": row.get('tipe'),
                "order_no": row.get('notrsorder'),
                "customer_code": row.get('kodesupel'),
                "sales_code": row.get('kodesales'),
                "currency": row.get('matauang'),
                "rate": self._parse_decimal(row.get('rate')),
                "description": row.get('keterangan'),
                "total_items": self._parse_decimal(row.get('totalitem')),
                "subtotal": self._parse_decimal(row.get('subtotal')),
                "discount": self._parse_decimal(row.get('potfaktur')),
                "tax": self._parse_decimal(row.get('pajak')),
                "total": self._parse_decimal(row.get('total')),
                "paid": self._parse_decimal(row.get('bayar')),
                "change": self._parse_decimal(row.get('kembalian')),
                "remaining": self._parse_decimal(row.get('sisa')),
                "status": row.get('ststransaksi'),
                "payment_status": row.get('statusbyr'),
                "source_system": "IPOS5",
                "raw_data": row
            }
            sales_headers.append(header)
        
        # Map details
        sales_details = []
        for row in details:
            detail = {
                "source_id": row.get('iddetail'),
                "line_no": self._parse_int(row.get('nobaris')),
                "transaction_no": row.get('notransaksi'),
                "item_code": row.get('kodeitem'),
                "quantity": self._parse_decimal(row.get('jumlah')),
                "qty_ordered": self._parse_decimal(row.get('jmlpesan')),
                "unit": row.get('satuan'),
                "price": self._parse_decimal(row.get('harga')),
                "discount1": self._parse_decimal(row.get('potongan')),
                "discount2": self._parse_decimal(row.get('potongan2')),
                "discount3": self._parse_decimal(row.get('potongan3')),
                "total": self._parse_decimal(row.get('total')),
                "tax": self._parse_decimal(row.get('pajak')),
                "cost": self._parse_decimal(row.get('hpp')),
                "source_system": "IPOS5",
                "raw_data": row
            }
            sales_details.append(detail)
        
        return {
            "headers": sales_headers,
            "details": sales_details
        }
    
    def extract_purchases(self) -> Dict[str, List[Dict]]:
        """Extract purchase transactions (invoice masuk)"""
        headers = self.extract_table_data('tbl_imhd')
        details = self.extract_table_data('tbl_imdt')
        
        # Map headers
        purchase_headers = []
        for row in headers:
            header = {
                "source_id": row.get('notransaksi'),
                "transaction_no": row.get('notransaksi'),
                "warehouse_code": row.get('kodekantor'),
                "dest_warehouse": row.get('kantortujuan'),
                "date": row.get('tanggal'),
                "type": row.get('tipe'),
                "order_no": row.get('notrsorder'),
                "supplier_code": row.get('kodesupel'),
                "currency": row.get('matauang'),
                "rate": self._parse_decimal(row.get('rate')),
                "description": row.get('keterangan'),
                "total_items": self._parse_decimal(row.get('totalitem')),
                "subtotal": self._parse_decimal(row.get('subtotal')),
                "discount": self._parse_decimal(row.get('potfaktur')),
                "tax": self._parse_decimal(row.get('pajak')),
                "total": self._parse_decimal(row.get('total')),
                "due_date": row.get('jatuhtempo'),
                "status": row.get('ststransaksi'),
                "payment_status": row.get('statusbyr'),
                "source_system": "IPOS5",
                "raw_data": row
            }
            purchase_headers.append(header)
        
        # Map details
        purchase_details = []
        for row in details:
            detail = {
                "source_id": row.get('iddetail'),
                "line_no": self._parse_int(row.get('nobaris')),
                "transaction_no": row.get('notransaksi'),
                "item_code": row.get('kodeitem'),
                "quantity": self._parse_decimal(row.get('jumlah')),
                "qty_ordered": self._parse_decimal(row.get('jmlpesan')),
                "unit": row.get('satuan'),
                "price": self._parse_decimal(row.get('harga')),
                "discount": self._parse_decimal(row.get('potongan')),
                "total": self._parse_decimal(row.get('total')),
                "tax": self._parse_decimal(row.get('pajak')),
                "base_price": self._parse_decimal(row.get('hargadsr')),
                "source_system": "IPOS5",
                "raw_data": row
            }
            purchase_details.append(detail)
        
        return {
            "headers": purchase_headers,
            "details": purchase_details
        }
    
    def extract_categories(self) -> List[Dict]:
        """Extract item categories (jenis)"""
        raw_data = self.extract_table_data('tbl_itemjenis')
        
        categories = []
        for row in raw_data:
            cat = {
                "source_id": row.get('jenis'),
                "code": row.get('jenis'),
                "name": row.get('ketjenis') or row.get('jenis'),
                "source_system": "IPOS5",
                "raw_data": row
            }
            categories.append(cat)
        
        return categories
    
    def extract_brands(self) -> List[Dict]:
        """Extract item brands (merek)"""
        raw_data = self.extract_table_data('tbl_itemmerek')
        
        brands = []
        for row in raw_data:
            brand = {
                "source_id": row.get('merek'),
                "code": row.get('merek'),
                "name": row.get('ketmerek') or row.get('merek'),
                "source_system": "IPOS5",
                "raw_data": row
            }
            brands.append(brand)
        
        return brands
    
    def extract_units(self) -> List[Dict]:
        """Extract item units (satuan)"""
        raw_data = self.extract_table_data('tbl_itemsatuan')
        
        units = []
        for row in raw_data:
            unit = {
                "source_id": row.get('satuan'),
                "code": row.get('satuan'),
                "name": row.get('ketsatuan') or row.get('satuan'),
                "conversion": self._parse_decimal(row.get('konversi')),
                "conversion_unit": row.get('satuankonversi'),
                "is_primary": row.get('utama') == 't',
                "source_system": "IPOS5",
                "raw_data": row
            }
            units.append(unit)
        
        return units
    
    def extract_all(self) -> Dict[str, Any]:
        """Extract all data from backup"""
        if not self.content:
            self.load()
        
        supel = self.extract_suppliers_customers()
        sales = self.extract_sales()
        purchases = self.extract_purchases()
        
        return {
            "file_info": self.get_file_info(),
            "items": self.extract_items(),
            "categories": self.extract_categories(),
            "brands": self.extract_brands(),
            "units": self.extract_units(),
            "suppliers": supel["suppliers"],
            "customers": supel["customers"],
            "warehouses": self.extract_warehouses(),
            "stock_positions": self.extract_stock_positions(),
            "chart_of_accounts": self.extract_chart_of_accounts(),
            "journals": self.extract_journals(),
            "sales_headers": sales["headers"],
            "sales_details": sales["details"],
            "purchase_headers": purchases["headers"],
            "purchase_details": purchases["details"],
        }
    
    def _parse_decimal(self, value: Any) -> float:
        """Parse decimal value"""
        if value is None or value == '' or value == '\\N':
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_int(self, value: Any) -> int:
        """Parse integer value"""
        if value is None or value == '' or value == '\\N':
            return 0
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
