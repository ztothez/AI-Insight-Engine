# Page Override: Agent Mode

> Overrides `MASTER.md` for `/agent` — conversational analysis with LangGraph tools.

---

## Layout

- **Desktop:** 40% code panel | 60% chat panel
- **Mobile:** Code in collapsible drawer above chat; default chat visible

---

## Chat UX (Reiss + Galitz)

| Rule | Implementation |
|------|----------------|
| Predictable process | Show "Agent is thinking…" with animated dots after send |
| Transitional feedback | Typing indicator within 100ms of submit |
| Don't block input | User can edit code while agent responds (read-only context sent on submit) |
| Error recovery | Failed agent call: "Retry" + preserved message in input |

---

## Message Types

1. **User message** — right-aligned, `--color-muted` background
2. **Agent message** — left-aligned, markdown rendered, `--color-primary` border-left
3. **Tool call** (collapsible) — "Used: complexity analyzer" with chevron; default collapsed
4. **System** — centered, muted, for rate limits / errors only

---

## Input Area

- Multi-line textarea, min-height 44px (touch target)
- Send button: icon + "Send" label (not icon-only — a11y)
- Disabled + spinner during in-flight request
- Character limit indicator if API adds one later

---

## Differences from Analyze page

- No score bullet charts — agent returns prose; optional future: parse structured blocks
- Primary CTA is Send, not Analyze
- Breadcrumb: Analyze > Agent (user knows which mode they're in — Reiss Ch. 10)
