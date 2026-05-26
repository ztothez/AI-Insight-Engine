# AI Insight Engine — UX Foundations

> Synthesized from *Usable Usability* (Reiss), *Designing Search* (Nudelman), *The Essential Guide to User Interface Design* (Galitz), *Communicating the User Experience* (Caddick & Cable), and UI/UX Pro Max.

---

## Product Definition

**What it is:** A developer-facing code quality & security auditor. Paste Python → get OWASP-grounded scores, violations, suggestions, and book citations.

**What it is not:** A generic chatbot, an IDE replacement, or an e-commerce search product — but search/discovery patterns from *Designing Search* apply to how users find violations, citations, and past analyses.

**Primary user goal:** Understand security risk in code quickly, trust the answer, and act on it.

---

## Personas (Caddick & Cable — Ch. 1)

### Alex — Security-Minded Developer
- **Goal:** Catch OWASP issues before PR merge
- **Behavior:** Pastes snippets from IDE; scans scores first, then violations
- **Must do:** See severity, OWASP mapping, fix suggestion, source citation
- **Must never:** Wait on a frozen UI during 5–15s LLM calls; lose context when rate-limited

### Sam — Engineering Lead
- **Goal:** Review team submissions; compare strictness levels
- **Behavior:** Uses strictness slider; exports or shares results
- **Must do:** Trust citations; distinguish blocked input vs analysis failure
- **Must never:** Misread a 400 validation error as a security finding

### Jordan — Learner / Bootcamp Student
- **Goal:** Learn why code is insecure
- **Behavior:** Reads suggestions and expands citation sources
- **Must do:** Plain-language explanations with book references
- **Must never:** Face jargon-only errors without recovery path

---

## Core UX Framework (Reiss — Two Sides of Usability)

| Side | Principle | Application to AI Insight Engine |
|------|-----------|----------------------------------|
| **Ease of use** (physical) | Functional, Responsive, Ergonomic, Convenient, Foolproof | Working submit flow, skeleton during LLM wait, 44px targets, keyboard shortcuts, helpful errors |
| **Elegance & clarity** (psychological) | Visible, Understandable, Logical, Consistent, Predictable | Scores above fold, shared vocabulary (OWASP), linear analyze flow, one primary CTA |

---

## Design Principles by Book

### From *Usable Usability*

1. **Fine-tune forms, not the homepage** — The code editor + analyze form is the product core; landing page is secondary.
2. **Milliseconds count** — Show feedback within 100ms of click; skeleton after 300ms for LLM.
3. **FUD reduction** — During analysis: progress text ("Retrieving sources…", "Analyzing…"), not a blank panel.
4. **Helpful error messages** — State cause + fix: rate limit → "Try again in 60s"; blocked input → "Submit Python code, not prose."
5. **Don't make people memorize** — Persist last snippet in session; show strictness level in results header.
6. **Predictability** — Always show step count: Input → Analyzing → Results (Reiss Ch. 10).
7. **One button, one function** — "Analyze" runs analysis; "Ask Agent" is separate mode, not overloaded.

### From *Designing Search* (adapted for code/citation discovery)

1. **No empty results state** — Zero violations → celebratory empty state with score summary, not a blank list.
2. **Faceted filters** — Filter violations by category (OWASP, maintainability, readability).
3. **Result layout** — Violations as scannable cards: severity badge + title + line hint + expand for detail.
4. **Query disambiguation** — If input blocked (400), offer examples: "Try a function with SQL, secrets, or XSS patterns."
5. **Breadcrumbs for drill-down** — Analysis → Violation detail → Citation source (Nudelman Ch. 13).
6. **More Like This** — On citations: "Find similar issues in this snippet" links to highlighted code regions.

### From *Galitz — Essential Guide to UI Design*

1. **Consistency** — Same severity colors everywhere: critical `#EF4444`, warning `#F59E0B`, info `#3B82F6`, pass `#22C55E`.
2. **Organize meaningfully** — Scores (summary) → Violations (problems) → Suggestion (action) → Sources (evidence).
3. **Feedback & time delays** — Step 9: progress for operations >1s; never freeze without status.
4. **Prevent errors** — Disable submit on empty editor; warn before navigating away with unsaved code.
5. **Clear text** — Error messages: what happened, why, what to do next.
6. **Focus & emphasis** — Lowest score dimension gets visual emphasis (not color alone — add icon + label).

### From *Communicating the User Experience*

1. **Task model** — Goal: assess code security → Tasks: paste → configure → submit → review → act.
2. **User journey pain points** — Map: waiting (LLM), distrust (hallucination), overload (long violation lists).
3. **Severity indicators** — Use in UI as Caddick recommends for test reports: critical / major / minor.
4. **Audience layers** — Developers want detail; leads want summary scores first (progressive disclosure).

---

## Information Architecture

```text
/                     Landing — hero + live demo + trust (books, OWASP)
/analyze              Primary workspace — editor + results split pane
/agent                Conversational mode — chat + code context
/history              Past analyses (future — API not yet exposed)
```

**Navigation:** Top bar, max 4 items. Primary CTA: "Analyze Code" (accent green).

---

## User Journey — Analyze Flow

| Step | User action | System response | Pain point mitigated |
|------|-------------|-----------------|----------------------|
| 1 | Lands on /analyze | Editor focused, sample snippet optional | Blank page anxiety |
| 2 | Pastes code, sets strictness | Inline validation, char count | Invalid submit |
| 3 | Clicks Analyze | Button → loading; skeleton results panel | FUD / frozen UI |
| 4 | Waits 3–15s | Staged status: embed → retrieve → analyze | Uncertainty |
| 5 | Reviews scores | Bullet charts with numeric values (a11y) | Color-only meaning |
| 6 | Expands violation | OWASP ref + code highlight | Wall of text |
| 7 | Opens citation | Source card with doc_id + excerpt | Untrusted AI |
| 8 | Copies suggestion | Toast confirmation | No feedback |

---

## Key Screens (wireframe intent)

### Analyze (primary — 70% of usage)
```
┌─────────────────────────────────────────────────────────────┐
│ Logo   Analyze   Agent   Docs          [Analyze Code ▶]     │
├──────────────────────────┬──────────────────────────────────┤
│ CODE EDITOR              │ RESULTS                          │
│ [Python ▾] Strictness ●●●○○ │ ┌─ Scores (bullet charts) ─┐  │
│                          │ │ Overall 7.2  Security 4.1  │  │
│ def get_user(id):        │ └────────────────────────────┘  │
│   ...                    │ Violations (3)  [filter ▾]       │
│                          │ ▼ SQL Injection — OWASP A03     │
│                          │ Suggestion + Sources            │
└──────────────────────────┴──────────────────────────────────┘
```

### Agent (secondary)
- Split: code context (read-only or shared editor) + chat thread
- Agent responses support markdown; tool calls shown as collapsible steps

---

## Accessibility & Trust Requirements

- All score values as visible text (WCAG — charts are supplementary)
- Violation severity: icon + label + color
- `aria-live="polite"` on results region during analysis
- Focus management: after results load, focus moves to results summary
- Privacy notice near editor: "Code is sent to Together.ai for analysis"
- Rate limit shown proactively: "5 analyses per minute"

---

## Technical Frontend Recommendation

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | **React + Vite** or Next.js | Matches developer-tool ecosystem; fast dev |
| Styling | Tailwind CSS + CSS variables from MASTER | UI/UX Pro Max Tailwind 10/10 for dark OLED |
| Code editor | Monaco Editor | Familiar VS Code UX for developers |
| Charts | Custom SVG bullet charts | UI/UX Pro Max: bullet charts for KPI grids |
| Icons | Lucide React | No emoji icons; consistent stroke |
| API | Fetch to existing FastAPI `/analyze`, `/agent` | No backend changes required for v1 |

---

## What We Explicitly Avoid (UI/UX Pro Max + books)

- Cyberpunk/neon glitch aesthetic — hurts trust for security product
- Light mode default — developers expect dark IDE-adjacent UI
- Emoji as structural icons
- Pie charts for scores — use bullet charts or labeled bars
- Modal-only primary flow — analyze is a page, not a dialog
- Placeholder-only labels on strictness control — visible label required (Galitz)
