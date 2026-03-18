# iPOS 5 to OCB TITAN Mapping Service
# Maps iPOS 5 schema to OCB TITAN canonical schema

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class MappingService:
    """
    Mapping layer for iPOS 5 to OCB TITAN schema conversion
    
    Provides:
    - Field mapping specifications
    - Data transformation
    - Validation rules
    - Mismatch reports
    """
    
    # ============================================================
    # FIELD MAPPING SPECIFICATIONS
    # iPOS field -> OCB TITAN field
    # ============================================================
    
    ITEM_MAPPING = {
        "kodeitem": "code",
        "namaitem": "name",
        "jenis": "category_code",
        "merek": "brand_code",
        "satuan": "unit",
        "tipe": "type",
        "matauang": "currency",
        "serial": "is_serial",
        "konsinyasi": "is_consignment",
        "stokmin": "min_stock",
        "hargapokok": "cost_price",
        "hargajual1": "sell_price",
        "hargajual2": "sell_price_2",
        "hargajual3": "sell_price_3",
        "barcode": "barcode",
        "kodesupel": "supplier_code",
        "rak": "location",
        "aktif": "is_active",
    }
    
    SUPPLIER_MAPPING = {
        "kode": "code",
        "nama": "name",
        "alamat": "address",
        "kota": "city",
        "provinsi": "province",
        "kodepos": "postal_code",
        "negara": "country",
        "telepon": "phone",
        "fax": "fax",
        "kontak": "contact_person",
        "email": "email",
        "norek": "bank_account",
        "atasnama": "account_name",
        "npwp": "tax_id",
        "kreditlimit": "credit_limit",
        "aktif": "is_active",
    }
    
    CUSTOMER_MAPPING = SUPPLIER_MAPPING  # Same structure
    
    WAREHOUSE_MAPPING = {
        "kodekantor": "code",
        "namakantor": "name",
        "fungsi": "type",  # Transform: GUDANG -> warehouse, TOKO -> store
        "alamat": "address",
        "notelepon": "phone",
        "cabang": "is_branch",
        "kodeacc": "account_code",
        "stsaktif": "is_active",
    }
    
    ACCOUNT_MAPPING = {
        "kodeacc": "code",
        "parentacc": "parent_code",
        "kelompok": "group",  # 1=Asset, 2=Liability, 3=Equity, 4=Revenue, 5=Expense
        "tipe": "type",  # H=Header, D=Detail
        "namaacc": "name",
        "matauang": "currency",
        "kasbank": "is_cash_bank",
        "aktivitas": "activity",
    }
    
    JOURNAL_MAPPING = {
        "iddetail": "source_id",
        "nourut": "line_no",
        "notransaksi": "transaction_no",
        "tanggal": "date",
        "kodeacc": "account_code",
        "jenis": "journal_type",
        "keterangan": "description",
        "matauang": "currency",
        "rate": "exchange_rate",
        "jumlah": "amount",
        "posisi": "position",  # D=Debit, K=Credit
        "debet": "debit",
        "kredit": "credit",
        "kantor": "warehouse_code",
    }
    
    SALES_HEADER_MAPPING = {
        "notransaksi": "transaction_no",
        "kodekantor": "warehouse_code",
        "tanggal": "date",
        "tipe": "type",
        "kodesupel": "customer_code",
        "kodesales": "salesperson_code",
        "matauang": "currency",
        "rate": "exchange_rate",
        "keterangan": "notes",
        "subtotal": "subtotal",
        "potfaktur": "discount",
        "pajak": "tax",
        "total": "total",
        "bayar": "paid",
        "sisa": "remaining",
        "ststransaksi": "status",
        "statusbyr": "payment_status",
    }
    
    SALES_DETAIL_MAPPING = {
        "iddetail": "source_id",
        "nobaris": "line_no",
        "notransaksi": "transaction_no",
        "kodeitem": "item_code",
        "jumlah": "quantity",
        "satuan": "unit",
        "harga": "price",
        "potongan": "discount",
        "total": "total",
        "pajak": "tax",
        "hpp": "cost",
    }
    
    PURCHASE_HEADER_MAPPING = {
        "notransaksi": "transaction_no",
        "kodekantor": "warehouse_code",
        "kantortujuan": "dest_warehouse",
        "tanggal": "date",
        "tipe": "type",
        "kodesupel": "supplier_code",
        "matauang": "currency",
        "rate": "exchange_rate",
        "keterangan": "notes",
        "subtotal": "subtotal",
        "potfaktur": "discount",
        "pajak": "tax",
        "total": "total",
        "jatuhtempo": "due_date",
        "ststransaksi": "status",
        "statusbyr": "payment_status",
    }
    
    PURCHASE_DETAIL_MAPPING = {
        "iddetail": "source_id",
        "nobaris": "line_no",
        "notransaksi": "transaction_no",
        "kodeitem": "item_code",
        "jumlah": "quantity",
        "satuan": "unit",
        "harga": "price",
        "potongan": "discount",
        "total": "total",
        "pajak": "tax",
        "hargadsr": "base_price",
    }
    
    # ============================================================
    # ACCOUNT GROUP MAPPING (iPOS kelompok -> OCB TITAN)
    # ============================================================
    ACCOUNT_GROUP_MAP = {
        "1": "ASSET",
        "2": "LIABILITY",
        "3": "EQUITY",
        "4": "REVENUE",
        "5": "EXPENSE",
        "6": "COGS",  # Cost of Goods Sold
    }
    
    # ============================================================
    # MAPPING METHODS
    # ============================================================
    
    def map_item(self, ipos_item: Dict) -> Dict:
        """Map iPOS item to OCB TITAN product schema"""
        mapped = self._apply_mapping(ipos_item, self.ITEM_MAPPING)
        
        # Transform boolean fields
        mapped["is_serial"] = ipos_item.get("serial") == "Y"
        mapped["is_consignment"] = ipos_item.get("konsinyasi") == "Y"
        mapped["is_active"] = ipos_item.get("aktif") != "N"
        
        # Add OCB TITAN specific fields
        mapped["id"] = f"IPOS_{mapped.get('code', '')}"
        mapped["source_system"] = "IPOS5"
        mapped["created_at"] = datetime.now(timezone.utc).isoformat()
        
        return mapped
    
    def map_supplier(self, ipos_supplier: Dict) -> Dict:
        """Map iPOS supplier to OCB TITAN supplier schema"""
        mapped = self._apply_mapping(ipos_supplier, self.SUPPLIER_MAPPING)
        
        mapped["is_active"] = ipos_supplier.get("aktif") != "N"
        mapped["type"] = "supplier"
        mapped["id"] = f"IPOS_SUP_{mapped.get('code', '')}"
        mapped["source_system"] = "IPOS5"
        mapped["created_at"] = datetime.now(timezone.utc).isoformat()
        
        return mapped
    
    def map_customer(self, ipos_customer: Dict) -> Dict:
        """Map iPOS customer to OCB TITAN customer schema"""
        mapped = self._apply_mapping(ipos_customer, self.CUSTOMER_MAPPING)
        
        mapped["is_active"] = ipos_customer.get("aktif") != "N"
        mapped["type"] = "customer"
        mapped["id"] = f"IPOS_CUS_{mapped.get('code', '')}"
        mapped["source_system"] = "IPOS5"
        mapped["created_at"] = datetime.now(timezone.utc).isoformat()
        
        return mapped
    
    def map_warehouse(self, ipos_warehouse: Dict) -> Dict:
        """Map iPOS warehouse/kantor to OCB TITAN warehouse schema"""
        mapped = self._apply_mapping(ipos_warehouse, self.WAREHOUSE_MAPPING)
        
        # Transform warehouse type
        fungsi = ipos_warehouse.get("fungsi", "").upper()
        if "GUDANG" in fungsi:
            mapped["type"] = "warehouse"
        elif "TOKO" in fungsi:
            mapped["type"] = "store"
        else:
            mapped["type"] = "office"
        
        mapped["is_branch"] = ipos_warehouse.get("cabang") == "t"
        mapped["is_active"] = ipos_warehouse.get("stsaktif") == "Y"
        mapped["id"] = f"IPOS_WH_{mapped.get('code', '')}"
        mapped["source_system"] = "IPOS5"
        mapped["created_at"] = datetime.now(timezone.utc).isoformat()
        
        return mapped
    
    def map_account(self, ipos_account: Dict) -> Dict:
        """Map iPOS account to OCB TITAN chart of accounts schema"""
        mapped = self._apply_mapping(ipos_account, self.ACCOUNT_MAPPING)
        
        # Transform account group
        kelompok = ipos_account.get("kelompok", "")
        mapped["group_name"] = self.ACCOUNT_GROUP_MAP.get(kelompok, "UNKNOWN")
        
        # Transform account type
        tipe = ipos_account.get("tipe", "D")
        mapped["is_header"] = tipe == "H"
        
        mapped["is_cash_bank"] = ipos_account.get("kasbank") == "t"
        mapped["id"] = f"IPOS_ACC_{mapped.get('code', '')}"
        mapped["source_system"] = "IPOS5"
        mapped["created_at"] = datetime.now(timezone.utc).isoformat()
        
        return mapped
    
    def map_journal(self, ipos_journal: Dict) -> Dict:
        """Map iPOS journal entry to OCB TITAN journal schema"""
        mapped = self._apply_mapping(ipos_journal, self.JOURNAL_MAPPING)
        
        # Transform position to debit/credit
        posisi = ipos_journal.get("posisi", "")
        mapped["is_debit"] = posisi == "D"
        mapped["is_credit"] = posisi == "K"
        
        mapped["id"] = f"IPOS_JRN_{mapped.get('source_id', '')}"
        mapped["source_system"] = "IPOS5"
        
        return mapped
    
    def map_sales_header(self, ipos_sales: Dict) -> Dict:
        """Map iPOS sales header to OCB TITAN sales schema"""
        mapped = self._apply_mapping(ipos_sales, self.SALES_HEADER_MAPPING)
        
        mapped["id"] = f"IPOS_SLS_{mapped.get('transaction_no', '')}"
        mapped["source_system"] = "IPOS5"
        mapped["transaction_type"] = "sales"
        
        return mapped
    
    def map_sales_detail(self, ipos_detail: Dict) -> Dict:
        """Map iPOS sales detail to OCB TITAN sales detail schema"""
        mapped = self._apply_mapping(ipos_detail, self.SALES_DETAIL_MAPPING)
        
        mapped["id"] = f"IPOS_SLD_{mapped.get('source_id', '')}"
        mapped["source_system"] = "IPOS5"
        
        return mapped
    
    def map_purchase_header(self, ipos_purchase: Dict) -> Dict:
        """Map iPOS purchase header to OCB TITAN purchase schema"""
        mapped = self._apply_mapping(ipos_purchase, self.PURCHASE_HEADER_MAPPING)
        
        mapped["id"] = f"IPOS_PUR_{mapped.get('transaction_no', '')}"
        mapped["source_system"] = "IPOS5"
        mapped["transaction_type"] = "purchase"
        
        return mapped
    
    def map_purchase_detail(self, ipos_detail: Dict) -> Dict:
        """Map iPOS purchase detail to OCB TITAN purchase detail schema"""
        mapped = self._apply_mapping(ipos_detail, self.PURCHASE_DETAIL_MAPPING)
        
        mapped["id"] = f"IPOS_PUD_{mapped.get('source_id', '')}"
        mapped["source_system"] = "IPOS5"
        
        return mapped
    
    def map_stock_position(self, ipos_stock: Dict) -> Dict:
        """Map iPOS stock position to OCB TITAN inventory schema"""
        return {
            "id": f"IPOS_STK_{ipos_stock.get('item_code', '')}_{ipos_stock.get('warehouse_code', '')}",
            "item_code": ipos_stock.get("item_code"),
            "warehouse_code": ipos_stock.get("warehouse_code"),
            "quantity": float(ipos_stock.get("quantity", 0) or 0),
            "unit_cost": float(ipos_stock.get("hpp_base", 0) or 0),
            "total_value": float(ipos_stock.get("quantity", 0) or 0) * float(ipos_stock.get("hpp_base", 0) or 0),
            "source_system": "IPOS5",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    # ============================================================
    # VALIDATION METHODS
    # ============================================================
    
    def validate_mapping(self, collection_name: str, records: List[Dict]) -> Dict:
        """
        Validate mapping for a collection
        
        Returns:
            {
                "valid_count": int,
                "invalid_count": int,
                "missing_fields": {},
                "nullable_fields": {},
                "unknown_enums": {},
                "issues": []
            }
        """
        valid_count = 0
        invalid_count = 0
        missing_fields = {}
        nullable_fields = {}
        unknown_enums = {}
        issues = []
        
        # Define required fields per collection
        required_fields = {
            "items": ["code", "name"],
            "suppliers": ["code", "name"],
            "customers": ["code", "name"],
            "warehouses": ["code", "name"],
            "chart_of_accounts": ["code", "name"],
            "stock_positions": ["item_code", "warehouse_code"],
            "journals": ["transaction_no", "account_code", "date"],
            "sales_headers": ["transaction_no", "date"],
            "sales_details": ["transaction_no", "item_code"],
            "purchase_headers": ["transaction_no", "date"],
            "purchase_details": ["transaction_no", "item_code"],
        }
        
        required = required_fields.get(collection_name, [])
        
        for i, record in enumerate(records):
            is_valid = True
            
            for field in required:
                val = record.get(field)
                if val is None or val == "":
                    is_valid = False
                    missing_fields[field] = missing_fields.get(field, 0) + 1
                    issues.append({
                        "row": i,
                        "issue": "missing_required",
                        "field": field,
                        "source_id": record.get("source_id", record.get("code", i))
                    })
            
            # Check for nullable fields (fields that are often null)
            for field, val in record.items():
                if val is None or val == "":
                    nullable_fields[field] = nullable_fields.get(field, 0) + 1
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        return {
            "collection": collection_name,
            "total_records": len(records),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "missing_fields": missing_fields,
            "nullable_fields": nullable_fields,
            "unknown_enums": unknown_enums,
            "issues": issues[:100]  # Limit issues
        }
    
    def get_mapping_spec(self) -> Dict:
        """Get full mapping specification"""
        return {
            "items": self.ITEM_MAPPING,
            "suppliers": self.SUPPLIER_MAPPING,
            "customers": self.CUSTOMER_MAPPING,
            "warehouses": self.WAREHOUSE_MAPPING,
            "chart_of_accounts": self.ACCOUNT_MAPPING,
            "journals": self.JOURNAL_MAPPING,
            "sales_headers": self.SALES_HEADER_MAPPING,
            "sales_details": self.SALES_DETAIL_MAPPING,
            "purchase_headers": self.PURCHASE_HEADER_MAPPING,
            "purchase_details": self.PURCHASE_DETAIL_MAPPING,
            "account_groups": self.ACCOUNT_GROUP_MAP
        }
    
    def _apply_mapping(self, source: Dict, mapping: Dict) -> Dict:
        """Apply field mapping from source to target"""
        result = {}
        for src_field, tgt_field in mapping.items():
            val = source.get(src_field)
            if val is not None and val != "":
                # Parse numeric values
                if isinstance(val, str) and val.replace('.', '').replace('-', '').isdigit():
                    try:
                        result[tgt_field] = float(val) if '.' in val else int(val)
                    except ValueError:
                        result[tgt_field] = val
                else:
                    result[tgt_field] = val
            else:
                result[tgt_field] = None
        return result
