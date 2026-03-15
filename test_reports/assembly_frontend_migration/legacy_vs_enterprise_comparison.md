# Legacy vs Enterprise Assembly API Comparison

## Key Differences

### 1. Status Management
| Aspect | Legacy | Enterprise |
|--------|--------|------------|
| Transaction Status | Simple (success/fail) | DRAFT/POSTED/REVERSED/CANCELLED |
| Edit Allowed | Always | Only DRAFT |
| Delete Allowed | Always | DRAFT only, POSTED needs REVERSAL |

### 2. Component Structure
| Aspect | Legacy | Enterprise |
|--------|--------|------------|
| Components | Inline array in formula | Separate collection (assembly_components) |
| Sequence | No | Yes (sequence_no) |
| Waste Factor | No | Yes (waste_factor) |

### 3. Audit Trail
| Aspect | Legacy | Enterprise |
|--------|--------|------------|
| Logging | Minimal | Full (assembly_logs) |
| User Tracking | Basic | Complete (created_by, posted_by, reversed_by) |

### 4. Stock Management
| Aspect | Legacy | Enterprise |
|--------|--------|------------|
| Movement Types | assembly_in/out | ASSEMBLY_CONSUME/PRODUCE + REVERSAL |
| Reversal | Not supported | Fully supported |

### 5. Accounting
| Aspect | Legacy | Enterprise |
|--------|--------|------------|
| Journal | Basic | Full with reversal support |
| Immutability | Not enforced | Strictly enforced |

## Recommendation
Migrate fully to Enterprise API for production use.
Legacy API should be deprecated after validation period.
