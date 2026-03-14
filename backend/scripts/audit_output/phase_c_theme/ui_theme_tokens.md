# PHASE C - VISUAL THEME HARDENING
## Design Tokens Documentation

### Created: 2026-03-14
### File: `/app/frontend/src/styles/design-tokens.css`

---

## 1. COLOR TOKENS

### Primary Colors
| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | #7c3aed | Brand/Purple buttons |
| `--color-primary-hover` | #6d28d9 | Button hover |
| `--color-primary-light` | #a78bfa | Light accent |

### Background Colors
| Token | Value | Usage |
|-------|-------|-------|
| `--color-bg-base` | #0f0a14 | Page background |
| `--color-bg-elevated` | #1a1424 | Elevated surfaces |
| `--color-bg-card` | #150f1e | Card background |
| `--color-bg-input` | #0a0608 | Input fields |
| `--color-bg-hover` | #251d32 | Hover states |

### Text Colors
| Token | Value | Usage |
|-------|-------|-------|
| `--color-text-primary` | #f5f5f5 | Main text (off-white) |
| `--color-text-secondary` | #a8a29e | Secondary text |
| `--color-text-muted` | #78716c | Placeholder/muted |
| `--color-text-disabled` | #57534e | Disabled state |

### Status Colors
| Token | Value | Usage |
|-------|-------|-------|
| `--color-success` | #22c55e | Success/green |
| `--color-warning` | #f59e0b | Warning/amber (NOT bright yellow) |
| `--color-danger` | #ef4444 | Error/red |
| `--color-info` | #3b82f6 | Info/blue |

---

## 2. FIXES APPLIED

### Problem: Teks kuning terang di background putih
**Solution:** Override `.text-yellow-*` classes to use amber (#f59e0b) instead of bright yellow

### Problem: Kontras tidak cukup
**Solution:** Text colors use off-white (#f5f5f5) instead of pure white for eye comfort

### Problem: Hirarki visual tidak jelas
**Solution:** Three-tier text color system:
- Primary: Main content (#f5f5f5)
- Secondary: Supporting text (#a8a29e)
- Muted: Placeholder/hints (#78716c)

---

## 3. UTILITY CLASSES

```css
/* Text Colors */
.text-primary   → #f5f5f5
.text-secondary → #a8a29e
.text-muted     → #78716c
.text-success   → #22c55e
.text-warning   → #f59e0b
.text-danger    → #ef4444

/* Background Colors */
.bg-surface     → #150f1e
.bg-elevated    → #1a1424
.bg-success     → rgba(34, 197, 94, 0.1)
.bg-warning     → rgba(245, 158, 11, 0.1)
.bg-danger      → rgba(239, 68, 68, 0.1)
```

---

## 4. ACCESSIBILITY

- Minimum contrast ratio: 4.5:1 for normal text
- `@media (prefers-contrast: more)` support for high contrast mode
- No pure white (#fff) text to reduce eye strain

---

## Status: IMPLEMENTED
Design tokens created and imported into main CSS.
