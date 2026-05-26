# Page Override: Analyze Workspace

> Overrides `MASTER.md` for `/analyze` — the primary product surface.

---

## Layout

- **Pattern:** Split-pane workspace (editor left, results right)
- **Desktop (≥1024px):** 50/50 or 45/55 split, resizable divider
- **Tablet (768px):** Stacked — editor top, results bottom; sticky "Analyze" bar
- **Mobile (375px):** Tab switcher: Code | Results (not simultaneous scroll regions)

---

## Editor Panel

| Element | Spec |
|---------|------|
| Editor | Monaco, theme `vs-dark`, font Fira Code 14px |
| Language | Fixed badge "Python" (only supported language) |
| Strictness | Labeled slider 1–5 with helper text: "1 = lenient, 5 = strict" |
| Primary CTA | Full-width on mobile; "Analyze Code" accent green, disabled when empty |
| Secondary | "Load sample" ghost button — pre-fills SQL injection example |
| Privacy | Muted line below editor: icon + "Snippet processed by Together.ai" |

**Reiss — Foolproof:** Disable submit until `code_snippet` has ≥10 chars and passes client-side non-empty check.

---

## Results Panel — States

### Empty (initial)
- Illustration-free empty state (Lucide `ShieldSearch` icon)
- Copy: "Paste code and run analysis to see security scores, violations, and citations."

### Loading (>300ms)
- Skeleton: 4 score bars + 3 violation rows
- Status steps (aria-live): "Validating…" → "Searching knowledge base…" → "Analyzing…"
- Do not block editor edits during load (Reiss — Responsive)

### Success
**Section order (Galitz — meaningful organization):**
1. Score summary — bullet charts, numeric values always visible
2. Violations list — filterable chips: All | Security | Maintainability | Readability
3. Primary suggestion — single card, copy button
4. Sources — collapsible accordion, doc_id as badge

### Error states
| HTTP | UI treatment |
|------|--------------|
| 400 | Inline alert below editor; include example snippet link |
| 429 | Toast + countdown timer; disable button until window resets |
| 503 | Error card with Retry button; preserve editor content |

**Reiss — helpful errors:** Every error states cause + recovery action.

---

## Violation Card Anatomy

```
┌─────────────────────────────────────────────┐
│ [Critical]  SQL Injection          OWASP A03 │
│ f-string used in SQL query                   │
│ [Expand] [Jump to line]                      │
└─────────────────────────────────────────────┘
```

- Severity: icon + text label + border-left color (not color alone)
- OWASP reference as link-style badge
- Expand reveals full violation text + related citation excerpt

---

## Charts (UI/UX Pro Max — bullet charts)

- One bullet chart per dimension: overall, security, maintainability, readability
- Scale 0–10; zones: 0–4 red tint, 4–7 amber, 7–10 green
- Target marker at strictness-adjusted threshold (optional v2)
- Table fallback below charts for screen readers

---

## Motion

- Panel reveal: 200ms ease-out opacity + translateY(8px)
- Violation expand: 150ms height via CSS grid `0fr → 1fr` (no width animation)
- `prefers-reduced-motion`: instant state changes

---

## Keyboard

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + Enter` | Run analysis |
| `Ctrl/Cmd + K` | Focus editor |
| `Escape` | Clear results panel focus trap |
