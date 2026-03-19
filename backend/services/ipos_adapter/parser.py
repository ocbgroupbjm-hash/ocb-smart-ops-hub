# iPOS 5 Ultimate Backup Parser
# Parses PostgreSQL dump files (.i5bu / .sql) from iPOS 5 Ultimate
# READ-ONLY - No write operations to source
# Supports both custom format (pg_dump -Fc) and plain SQL format

import re
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Generator
import logging
import os

logger = logging.getLogger(__name__)


class IPOSBackupParser:
    """
    Parser for iPOS 5 Ultimate backup files (.i5bu / extracted .sql)
    
    File format: PostgreSQL pg_dump plain SQL format (extracted via pg_restore)
    
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
        'tbl_itrdt': 'sales_return_details',
        'tbl_itrhd': 'sales_return_headers',
        'tbl_user': 'users',
        'tbl_conf': 'config',
        'tbl_hupi_sa': 'ar_ap_balance',
    }
    
    # Critical tables for ERP reconciliation
    CRITICAL_TABLES = [
        'tbl_item', 'tbl_itemstok', 'tbl_supel', 'tbl_perkiraan',
        'tbl_accjurnal', 'tbl_ikhd', 'tbl_ikdt', 'tbl_imhd', 'tbl_imdt',
        'tbl_kantor', 'tbl_itemjenis', 'tbl_itemmerek', 'tbl_itemsatuan',
        'tbl_byrhutanghd', 'tbl_byrhutangdt', 'tbl_byrpiutanghd', 'tbl_byrpiutangdt',
        'tbl_hupi_sa'
    ]
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = None
        self.tables = {}
        self.table_schemas = {}  # Store table column definitions
        self.extract_timestamp = datetime.now(timezone.utc).isoformat()
        self.file_hash = None
        self._cache = {}  # Cache extracted data
        
    def load(self) -> bool:
        """Load and parse the backup file"""
        try:
            file_size = os.path.getsize(self.file_path)
            logger.info(f"Loading iPOS backup: {self.file_path} ({file_size / 1024 / 1024:.2f} MB)")
            
            with open(self.file_path, 'rb') as f:
                raw_content = f.read()
                self.file_hash = hashlib.sha256(raw_content).hexdigest()
                
            # Decode content - handle multiple encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    self.content = raw_content.decode(encoding, errors='replace')
                    break
                except Exception:
                    continue
            
            if not self.content:
                self.content = raw_content.decode('utf-8', errors='ignore')
            
            # Pre-parse table schemas from CREATE TABLE statements
            self._parse_table_schemas()
            
            logger.info(f"Loaded iPOS backup: hash={self.file_hash[:16]}..., tables found: {len(self.table_schemas)}")
            return True
        except Exception as e:
            logger.error(f"Failed to load iPOS backup: {e}")
            return False
    
    def _parse_table_schemas(self):
        """Parse CREATE TABLE statements to get column definitions"""
        if not self.content:
            return
        
        # Pattern to match CREATE TABLE statements
        create_pattern = r'CREATE TABLE\s+(?:public\.)?(\w+)\s*\(([\s\S]*?)\);'
        
        for match in re.finditer(create_pattern, self.content, re.IGNORECASE):
            table_name = match.group(1).lower()
            columns_def = match.group(2)
            
            # Extract column names (first word before type definition)
            columns = []
            for line in columns_def.split('\n'):
                line = line.strip()
                if line and not line.startswith('--') and not line.upper().startswith('CONSTRAINT'):
                    # Get column name (first word)
                    parts = line.split()
                    if parts:
                        col_name = parts[0].strip(',')
                        if col_name and col_name.upper() not in ['PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'CONSTRAINT']:
                            columns.append(col_name)
            
            if columns:
                self.table_schemas[table_name] = columns
    
    def get_available_tables(self) -> List[str]:
        """Get list of tables available in the backup"""
        if not self.content:
            self.load()
        return list(self.table_schemas.keys())
    
    def get_file_info(self) -> Dict:
        """Get backup file metadata"""
        return {
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "extract_timestamp": self.extract_timestamp,
            "source_system": "IPOS5_ULTIMATE",
            "format": "PGDUMP_PLAIN_SQL",
            "tables_found": len(self.table_schemas),
            "critical_tables": [t for t in self.CRITICAL_TABLES if t in self.table_schemas]
        }
    
    def extract_table_data(self, table_name: str) -> List[Dict]:
        """
        Extract data from a specific table
        
        Args:
            table_name: iPOS table name (e.g., 'tbl_item')
            
        Returns:
            List of dictionaries containing row data
        """
        # Check cache first
        if table_name in self._cache:
            return self._cache[table_name]
        
        if not self.content:
            self.load()
        
        # Try multiple patterns for COPY statement
        # Pattern 1: COPY public.table_name (columns) FROM stdin;
        # Pattern 2: COPY table_name (columns) FROM stdin;
        patterns = [
            rf'COPY\s+(?:public\.)?{table_name}\s*\(([^)]+)\)\s*FROM\s+stdin\s*;',
        ]
        
        match = None
        for pattern in patterns:
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                break
        
        if not match:
            logger.warning(f"Table {table_name} not found in backup (COPY statement not found)")
            return []
        
        # Get column names
        columns_str = match.group(1)
        columns = [c.strip().strip('"') for c in columns_str.split(',')]
        
        # Find data section (after COPY statement until \.)
        copy_start = match.end()
        
        end_marker = -1
        search_text = self.content[copy_start:copy_start + 50000000]  # Limit search range
        
        # Simple search for \. at beginning of line
        lines = search_text.split('\n')
        current_pos = 0
        for line in lines:
            if line == '\\.' or line == '\\.':
                end_marker = copy_start + current_pos
                break
            current_pos += len(line) + 1  # +1 for newline
        
        if end_marker == -1:
            # Fallback: search for next COPY or end of reasonable section
            next_copy = re.search(r'\nCOPY\s+', search_text)
            if next_copy:
                end_marker = copy_start + next_copy.start()
            else:
                logger.warning(f"Could not find end of data for table {table_name}")
                return []
        
        data_section = self.content[copy_start:end_marker].strip()
        
        # Parse rows (tab-separated)
        rows = []
        for line in data_section.split('\n'):
            line = line.strip()
            if not line or line.startswith('--') or line == '\\.' or line == '\\.':
                continue
            
            values = line.split('\t')
            
            # Allow some flexibility in column count
            if len(values) < len(columns) - 2:
                continue
            
            row = {}
            for i, col in enumerate(columns):
                if i < len(values):
                    val = values[i]
                    # Handle PostgreSQL NULL representation
                    if val == '\\N' or val == 'NULL':
                        val = None
                    # Handle escaped characters
                    elif isinstance(val, str):
                        val = val.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                else:
                    val = None
                row[col] = val
            
            rows.append(row)
        
        # Cache the result
        self._cache[table_name] = rows
        
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
    
    def extract_ar_ap_balance(self) -> Dict[str, List[Dict]]:
        """Extract AR/AP balances from tbl_hupi_sa"""
        raw_data = self.extract_table_data('tbl_hupi_sa')
        
        ar_records = []
        ap_records = []
        
        for row in raw_data:
            record = {
                "source_id": f"{row.get('kodesupel')}_{row.get('notransaksi')}",
                "entity_code": row.get('kodesupel'),
                "transaction_no": row.get('notransaksi'),
                "transaction_date": row.get('tanggal'),
                "due_date": row.get('jatuhtempo'),
                "type": row.get('tipe'),  # HU = Hutang (AP), PI = Piutang (AR)
                "currency": row.get('matauang'),
                "rate": self._parse_decimal(row.get('rate')),
                "amount": self._parse_decimal(row.get('jumlah')),
                "paid": self._parse_decimal(row.get('bayar')),
                "remaining": self._parse_decimal(row.get('sisa')),
                "status": row.get('status'),
                "warehouse_code": row.get('kantor'),
                "source_system": "IPOS5",
                "raw_data": row
            }
            
            if row.get('tipe') == 'HU':
                ap_records.append(record)
            elif row.get('tipe') == 'PI':
                ar_records.append(record)
        
        return {
            "ar": ar_records,
            "ap": ap_records
        }
    
    def extract_ap_payments(self) -> Dict[str, List[Dict]]:
        """Extract AP payment headers and details"""
        headers = self.extract_table_data('tbl_byrhutanghd')
        details = self.extract_table_data('tbl_byrhutangdt')
        
        payment_headers = []
        for row in headers:
            header = {
                "source_id": row.get('notransaksi'),
                "transaction_no": row.get('notransaksi'),
                "warehouse_code": row.get('kodekantor'),
                "date": row.get('tanggal'),
                "supplier_code": row.get('kodesupel'),
                "currency": row.get('matauang'),
                "rate": self._parse_decimal(row.get('rate')),
                "payment_method": row.get('bayarlewat'),
                "bank_account": row.get('kodeacc'),
                "total": self._parse_decimal(row.get('total')),
                "description": row.get('keterangan'),
                "source_system": "IPOS5",
                "raw_data": row
            }
            payment_headers.append(header)
        
        payment_details = []
        for row in details:
            detail = {
                "source_id": row.get('iddetail'),
                "transaction_no": row.get('notransaksi'),
                "invoice_no": row.get('nofaktur'),
                "amount": self._parse_decimal(row.get('jumlah')),
                "source_system": "IPOS5",
                "raw_data": row
            }
            payment_details.append(detail)
        
        return {
            "headers": payment_headers,
            "details": payment_details
        }
    
    def extract_ar_payments(self) -> Dict[str, List[Dict]]:
        """Extract AR payment headers and details"""
        headers = self.extract_table_data('tbl_byrpiutanghd')
        details = self.extract_table_data('tbl_byrpiutangdt')
        
        payment_headers = []
        for row in headers:
            header = {
                "source_id": row.get('notransaksi'),
                "transaction_no": row.get('notransaksi'),
                "warehouse_code": row.get('kodekantor'),
                "date": row.get('tanggal'),
                "customer_code": row.get('kodesupel'),
                "currency": row.get('matauang'),
                "rate": self._parse_decimal(row.get('rate')),
                "payment_method": row.get('bayarlewat'),
                "bank_account": row.get('kodeacc'),
                "total": self._parse_decimal(row.get('total')),
                "description": row.get('keterangan'),
                "source_system": "IPOS5",
                "raw_data": row
            }
            payment_headers.append(header)
        
        payment_details = []
        for row in details:
            detail = {
                "source_id": row.get('iddetail'),
                "transaction_no": row.get('notransaksi'),
                "invoice_no": row.get('nofaktur'),
                "amount": self._parse_decimal(row.get('jumlah')),
                "source_system": "IPOS5",
                "raw_data": row
            }
            payment_details.append(detail)
        
        return {
            "headers": payment_headers,
            "details": payment_details
        }
    
    def extract_all(self) -> Dict[str, Any]:
        """Extract all data from backup"""
        if not self.content:
            self.load()
        
        logger.info("=== EXTRACTING ALL DATA FROM iPOS BACKUP ===")
        
        supel = self.extract_suppliers_customers()
        sales = self.extract_sales()
        purchases = self.extract_purchases()
        ar_ap = self.extract_ar_ap_balance()
        ap_payments = self.extract_ap_payments()
        ar_payments = self.extract_ar_payments()
        
        result = {
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
            "ar_balances": ar_ap["ar"],
            "ap_balances": ar_ap["ap"],
            "ap_payment_headers": ap_payments["headers"],
            "ap_payment_details": ap_payments["details"],
            "ar_payment_headers": ar_payments["headers"],
            "ar_payment_details": ar_payments["details"],
        }
        
        # Log extraction summary
        logger.info("=== EXTRACTION SUMMARY ===")
        for key, value in result.items():
            if key != "file_info" and isinstance(value, list):
                logger.info(f"  {key}: {len(value)} records")
        
        return result
    
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
