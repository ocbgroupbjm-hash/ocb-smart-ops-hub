# AUDIT ROUTE MODUL PERAKITAN VOUCHER
## OCB TITAN ERP × AI - Blueprint v2.4.3
## Date: 2026-03-15

---

## 1. STATUS SEBELUM KONSOLIDASI

### Frontend Routes (App.js)
| Route | Component | Status |
|-------|-----------|--------|
| `/inventory/assemblies` | ProductAssembly | **LEGACY - AKAN DIHAPUS** |
| `/inventory/assembly-voucher` | ProductAssembly | **RESMI - AKTIF** |

### Sidebar Menu
| Menu Item | Path | Status |
|-----------|------|--------|
| Perakitan Voucher | `/inventory/assembly-voucher` | **RESMI - AKTIF** |

### Backend Router Files
| File | Prefix | Status |
|------|--------|--------|
| `assembly.py` | `/api/assembly` | **LEGACY - UNTUK BACKWARD COMPAT** |
| `assembly_enterprise.py` | `/api/assembly-enterprise` | **RESMI - AKTIF** |

### Backend Endpoints Enterprise (RESMI)
| Method | Endpoint | Fungsi |
|--------|----------|--------|
| GET | `/api/assembly-enterprise/formulas/v2` | List formulas |
| GET | `/api/assembly-enterprise/formulas/v2/{id}` | Get formula detail |
| POST | `/api/assembly-enterprise/formulas/v2` | Create formula |
| PUT | `/api/assembly-enterprise/formulas/v2/{id}` | Edit formula |
| PATCH | `/api/assembly-enterprise/formulas/v2/{id}/deactivate` | Soft delete |
| PATCH | `/api/assembly-enterprise/formulas/v2/{id}/activate` | Activate |
| DELETE | `/api/assembly-enterprise/formulas/v2/{id}/hard-delete` | Hard delete (dengan validasi) |
| POST | `/api/assembly-enterprise/execute/v2` | Execute assembly |
| POST | `/api/assembly-enterprise/execute/v2/post` | Post assembly |
| POST | `/api/assembly-enterprise/execute/v2/reverse` | Reverse assembly |

### Backend Endpoints Legacy (DEPRECATED)
| Method | Endpoint | Status |
|--------|----------|--------|
| GET | `/api/assembly/formulas` | Deprecated |
| POST | `/api/assembly/formulas` | Deprecated |
| PUT | `/api/assembly/formulas/{id}` | Deprecated |
| DELETE | `/api/assembly/formulas/{id}` | Deprecated |

---

## 2. KEPUTUSAN KONSOLIDASI

### Route Resmi Final
```
/inventory/assembly-voucher
```

### API Resmi Final
```
/api/assembly-enterprise/*
```

### Aksi Yang Dilakukan
1. **HAPUS** route `/inventory/assemblies` dari App.js
2. **UPDATE** frontend untuk HANYA menggunakan `/api/assembly-enterprise/*`
3. **HAPUS** fallback ke legacy API di frontend
4. **PERTAHANKAN** `assembly.py` di backend untuk backward compatibility external system
5. **UPDATE** semua UI text ke "PERAKITAN VOUCHER"

---

## 3. STATUS SETELAH KONSOLIDASI

### Frontend Routes (Target)
| Route | Component | Status |
|-------|-----------|--------|
| `/inventory/assembly-voucher` | ProductAssembly | **SATU-SATUNYA ROUTE AKTIF** |

### API (Target)
| API | Status |
|-----|--------|
| `/api/assembly-enterprise/*` | **SATU-SATUNYA API AKTIF** |
| `/api/assembly/*` | **TIDAK DIGUNAKAN FRONTEND** |

---

## 4. CHECKLIST KONSOLIDASI

- [ ] Route lama `/inventory/assemblies` dihapus dari App.js
- [ ] Frontend hanya menggunakan API enterprise
- [ ] UI text konsisten "PERAKITAN VOUCHER"
- [ ] Page title = "Perakitan Voucher"
- [ ] Breadcrumb = "Perakitan Voucher"  
- [ ] Tab labels konsisten
- [ ] CRUD berfungsi penuh
- [ ] Hard delete dengan validasi berfungsi

---

## 5. EVIDENCE REQUIRED
- assembly_route_mapping.json
- create_voucher_test.json
- edit_voucher_test.json
- hard_delete_unused_voucher_test.json
- hard_delete_used_voucher_rejected_test.json
- assembly_voucher_ui.png
- audit_log_proof.json
