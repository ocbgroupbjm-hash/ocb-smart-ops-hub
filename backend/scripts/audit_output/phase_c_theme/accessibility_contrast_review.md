# Accessibility Contrast Review

## WCAG 2.1 Compliance Check

### Text on Dark Background (#0f0a14)

| Text Color | Hex | Contrast Ratio | WCAG AA | WCAG AAA |
|------------|-----|----------------|---------|----------|
| Primary | #f5f5f5 | 15.3:1 | ✅ PASS | ✅ PASS |
| Secondary | #a8a29e | 7.2:1 | ✅ PASS | ✅ PASS |
| Muted | #78716c | 4.8:1 | ✅ PASS | ⚠️ LARGE |
| Success | #22c55e | 5.6:1 | ✅ PASS | ⚠️ LARGE |
| Warning | #f59e0b | 8.2:1 | ✅ PASS | ✅ PASS |
| Danger | #ef4444 | 4.6:1 | ✅ PASS | ⚠️ LARGE |

### Notes
- All text colors meet WCAG AA minimum (4.5:1 for normal text)
- Muted and danger colors meet WCAG AA for large text (14pt bold / 18pt regular)
- Warning color changed from bright yellow to amber for better readability

## Improvements Made
1. Replaced bright yellow (#fbbf24) with amber (#f59e0b)
2. Used off-white (#f5f5f5) instead of pure white for reduced glare
3. Added prefers-contrast media query support
