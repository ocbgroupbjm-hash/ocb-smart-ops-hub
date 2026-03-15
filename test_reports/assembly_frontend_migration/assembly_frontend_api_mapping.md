# Assembly Frontend API Migration

## Migration Status: IN PROGRESS

### API Endpoint Mapping

| Function | Legacy API | Enterprise API | Status |
|----------|-----------|----------------|--------|
| List Formulas | GET /api/assembly/formulas | GET /api/assembly-enterprise/formulas/v2 | MIGRATED |
| Get Formula | GET /api/assembly/formulas/{id} | GET /api/assembly-enterprise/formulas/v2/{id} | MIGRATED |
| Create Formula | POST /api/assembly/formulas | POST /api/assembly-enterprise/formulas/v2 | MIGRATED |
| Update Formula | PUT /api/assembly/formulas/{id} | PUT /api/assembly-enterprise/formulas/v2/{id} | MIGRATED |
| Delete Formula | DELETE /api/assembly/formulas/{id} | PATCH /api/assembly-enterprise/formulas/v2/{id}/deactivate | MIGRATED |
| List History | GET /api/assembly/transactions | GET /api/assembly-enterprise/history/v2 | MIGRATED |
| Execute Assembly | POST /api/assembly/assemble | POST /api/assembly-enterprise/execute/v2 | MIGRATED |
| Execute Disassembly | POST /api/assembly/disassemble | (Still uses legacy) | PENDING |
| Reverse Assembly | N/A | POST /api/assembly-enterprise/execute/v2/reverse | NEW |

### Fallback Strategy
- Frontend tries enterprise API first
- Falls back to legacy if enterprise returns error
- This ensures backward compatibility during transition

### Files Modified
- `/app/frontend/src/pages/inventory/ProductAssembly.jsx`

### Next Steps
1. Add Reverse button for POSTED transactions
2. Show DRAFT/POSTED/REVERSED status badges
3. Migrate disassembly to enterprise API
4. Remove legacy fallback after stable
