# AI-Insight-Engine — Code Reference

**Purpose:** A map of every non-trivial file added during Days 22-24, what it does, why it exists, and how the pieces connect. Use this as a memory refresher before the interview.

---

## Mental model — two independent systems

The work split into two systems that don't depend on each other:

### SYSTEM 1: EVAL FRAMEWORK (Days 22-23)

Purpose: measure if `/analyze` is doing what we think it is.
Lives entirely in `scripts/`. Doesn't change app behavior.
Like a wind tunnel — it tests the plane, isn't part of it.

### SYSTEM 2: PROMPT INJECTION DEFENSE (Day 24)

Purpose: stop hostile input from reaching the LLM.
Lives in `app/`. Runs on every `/analyze` request in production.
Like an airport security checkpoint — runs every time.

Day 24's prompt-injection work has nothing to do with Day 22-23's eval work. They share a project, not a codebase.

---

## System 1: Eval framework

### The pipeline

```
scripts/eval_cases/*.py   →   build_eval_dataset.py   →   eval_dataset.json   →   evaluate.py   →   eval_results.json
       (source)                  (compiler)                  (compiled)            (runner)            (output)
```

Three stages: write cases as Python, compile to JSON, run JSON against the live `/analyze` endpoint.

**Why this shape?** Writing test cases directly in JSON is painful — every newline becomes `\n`, every quote becomes `\"`. Writing them as Python files with triple-quoted strings is comfortable. The build script handles the translation so neither side hurts.

---

### `scripts/eval_cases/*.py` — 15 individual test case files

Each file defines **one test case** as 6 module-level constants.

**File naming convention:** `NN_short_name.py` where `NN` is a zero-padded number for ordering.

**Constants every case file must define:**

| Constant | Type | Purpose |
|----------|------|---------|
| `ID` | str | Unique identifier, e.g. `"sec_sql_injection_01"`. Survives into results so you can find a specific case by ID. |
| `CATEGORY` | str | Failure-mode tag. Lets the runner compute per-category pass rates. |
| `LANGUAGE` | str | The `language` field sent to `/analyze`. |
| `STRICTNESS` | int (1-5) | The `strictness_level` field sent to `/analyze`. |
| `CODE` | str | The actual code snippet to send, as a triple-quoted string. |
| `EXPECTED` | dict | The assertions to run against the response. Keys must match checker function names in `evaluate.py`. |

**Five categories in the dataset:**

| Files | Category | Tests for |
|-------|----------|-----------|
| 01-03 | OWASP A03 Injection | SQL injection, XSS, command injection (positive cases) |
| 04-06 | OWASP A01/A02/A07 | Hardcoded secrets, broken access, weak crypto (positive) |
| 07-09 | Clean code violations | God function, bad naming, no type hints |
| 10-12 | Negative cases | Clean code that should NOT be flagged. False-positive guard. |
| 13-15 | RAG grounding | Citations must come from topically-correct books |

**Why 15 separate files instead of one big list:** Per-case git history, no merge conflicts when editing different cases, search works (`grep -r "SQL injection" eval_cases/` returns one file), adding new cases means dropping a file not editing a central list. Same separation-of-concerns instinct as splitting the validator from the route.

**Example skeleton:**

```python
"""One-line description of the failure mode this case tests."""

ID = "sec_sql_injection_01"
CATEGORY = "security_owasp_a03_injection"
LANGUAGE = "python"
STRICTNESS = 3
CODE = """def login(u, p):
    return db.execute(f"SELECT * FROM users WHERE u={u}")
"""
EXPECTED = {
    "should_contain_violations": ["SQL Injection"],
    "security_score_max": 5.0,
    "should_have_citations": True,
}
```

(Note: in the real file `CODE` uses triple single-quotes `'''...'''` so double quotes inside the snippet don't need escaping. Either works.)

---

### `scripts/build_eval_dataset.py` — the compiler

**Job:** Read every `.py` file in `scripts/eval_cases/`, extract their constants, write a single `eval_dataset.json` array.

**Key function: `load_case(path)`.** Uses Python's `importlib` to dynamically load each `.py` file as a module, then reads `module.ID`, `module.CATEGORY`, etc. This is why the cases are `.py` files rather than `.yaml` or `.json` — Python natively handles multi-line strings, escapes, comments, and we get free syntax checking from the interpreter.

**Run with:**

```bash
python scripts/build_eval_dataset.py
```

**Output:** `scripts/eval_dataset.json` (overwritten every run).

**Never edit `eval_dataset.json` by hand.** It's a build artifact. Edit case files, re-run the build.

---

### `scripts/eval_dataset.json` — the compiled dataset

A JSON array of 15 objects, one per case. Each object matches the FastAPI request shape plus the `expected` block:

```json
[
  {
    "id": "sec_sql_injection_01",
    "category": "security_owasp_a03_injection",
    "input": {
      "code_snippet": "def login(u, p):\n    return db.execute(...)",
      "language": "python",
      "strictness_level": 3
    },
    "expected": {
      "should_contain_violations": ["SQL Injection"],
      "security_score_max": 5.0,
      "should_have_citations": true
    }
  }
]
```

**Why JSON not YAML or Python?** It's the format the runner naturally consumes when POSTing to `/analyze` — saves us a serialization step.

---

### `scripts/evaluate.py` — the runner

**Job:** Load `eval_dataset.json`, POST each case to `/analyze`, check the response against every assertion in `EXPECTED`, print a diagnostic summary, save full results to `eval_results.json`.

**Three logical sections worth knowing:**

**1. Assertion checkers (top of file).** One function per assertion type:

| Function | Checks |
|----------|--------|
| `check_should_contain_violations` | Substring match in violations list. Supports any-of groups via nested lists. |
| `check_score_max` / `check_score_min` | Score is within expected bound. Used for positive (max) and negative (min) cases. |
| `check_should_have_citations` | Sources list is non-empty. Proves RAG retrieval actually happened. |
| `check_citation_sources_any` | At least one citation's `doc_id` matches an expected book. RAG grounding test. |

Each returns `(passed: bool, reason: str)`. Reason explains *why* it passed or failed — that's what gives the eval its diagnostic power.

**2. `ASSERTION_CHECKERS` dict (the dispatch table).** Maps assertion names (the keys in `EXPECTED`) to checker functions. When a case has `"security_score_max": 5.0`, the runner looks up `"security_score_max"` in this dict and calls the corresponding checker. Adding a new assertion type = add a function + add a dict entry. Open/closed principle.

**3. `print_summary()` — three diagnostic views.**

- **Overall pass rate.** "7/15 passed (46.7%)." Headline number.
- **Per-category pass rate.** "rag_grounding: 1/3." Tells you where failures cluster.
- **Per-assertion pass rate.** "should_contain_violations: 7/14." Tells you which *kind* of check fails most.

The third view is the most valuable for diagnosis. If `should_have_citations` is 15/15 but `expected_citation_sources_any` is 2/3, you know retrieval *works* but sometimes pulls from the wrong book.

**Run with:**

```bash
python scripts/evaluate.py
```

**Requires the FastAPI server to be running.** Sleeps 4 seconds between requests to avoid hitting the rate limiter (which has a localhost bypass since Day 24, so this could be removed — kept for production safety).

---

### `scripts/eval_results.json` — the output

Full structured results for every assertion of every case. Read this after a run to see *exactly* what the LLM said for each case. Useful for diagnosing failures.

**Two snapshots saved:**

- `eval_results.json` — most recent run
- `eval_results_day23.json` — locked baseline from Day 23, for before/after comparison

---

## System 2: Prompt injection defense

### The request flow

```
POST /analyze
  ↓
@limiter.limit("5/minute")          ← rate limit (with localhost bypass)
  ↓
Step 0: validate_code_input(code)   ← NEW Day 24
  ↓                                       ↓
  is_safe=True                        is_safe=False
  ↓                                       ↓
Step 1-6 (existing flow)            log_blocked_input() → BlockedInput row
                                        ↓
                                    raise HTTPException(400, generic message)
```

The defense runs *before* the existing DB write and *before* the LLM call. A blocked input never touches `analysis_requests` or the LLM API.

---

### `app/core/input_validator.py` — the brain

**Job:** Given a code snippet, decide if it's safe to send to the LLM. Pure function. No DB, no FastAPI, no side effects.

**Why pure?** Testability. We can unit-test against 32 adversarial payloads in 50ms. If validation were tangled into the FastAPI route, every test would need a running server.

**Five rejection categories** (the `RejectionReason` enum):

| Category | Catches |
|----------|---------|
| `INSTRUCTION_OVERRIDE` | "Ignore previous instructions", "forget your rules", "disregard the above" |
| `ROLE_REASSIGNMENT` | "You are now a...", "Act as a...", "Pretend to be..." |
| `PROMPT_LEAK_ATTEMPT` | "Reveal your system prompt", "Show me your instructions" |
| `SYSTEM_TAG_INJECTION` | Fake `<system>` tags, `### SYSTEM:`, `[INST]`, `<|im_start|>` |
| `NON_CODE_INPUT` | Pure prose with no code indicators (for inputs ≥10 chars) |

Each category is implemented as one or more compiled regex patterns. Regex was chosen for speed (microseconds, no LLM round-trip) and predictability. In production you'd layer an LLM-based classifier on top for novel phrasings — that's the "what I'd improve" answer.

**Public API:** `validate_code_input(code_snippet: str) → ValidationResult`

`ValidationResult` is a frozen dataclass with three fields:

- `is_safe: bool` — the decision
- `reason: RejectionReason | None` — internal category for logging
- `matched_pattern: str | None` — which specific pattern fired

**Critical contract:** `reason` and `matched_pattern` are for **server-side logs only**. The caller must NEVER include them in the user-facing response. This is the "silent rejection" / "deception over deterrence" principle — telling attackers what tripped the detector gives them iteration feedback.

---

### `app/core/block_logger.py` — the audit writer

**Job:** Insert a `BlockedInput` row when an attack is blocked. Async, never raises.

**Why never raise?** Audit logging is *not* the security gate. The validator is the gate. If Postgres is down, the user still gets blocked correctly — they just don't get logged. Conflating the two would mean a DB outage breaks the security layer.

**What it records per attack:**

- `blocked_at` — timestamp
- `client_ip` — for spotting bot patterns
- `reason` — the `RejectionReason.value` string
- `matched_pattern` — human-readable label of which regex caught it
- `input_snippet` — the full rejected input (no truncation — attack payloads can be long)
- `input_length` — denormalized for fast statistics
- `user_agent` — also helps identify bot patterns

**Public API:** `await log_blocked_input(db, result, input_snippet, client_ip, user_agent)`.

Defensive guard at the top: if `result.is_safe is True`, it logs a warning and returns. We never want to log "safe" inputs as if they were attacks.

---

### `app/db/models.py` — `BlockedInput` model (new)

Standard SQLAlchemy ORM model matching your existing pattern (`Column(...)` style, no `relationship()`, no Alembic).

**Key column choices:**

- `input_snippet` is unbounded `String` (Postgres `varchar`) — attack payloads can be huge, truncating defeats the audit
- `reason` is `String(50)`, not a Postgres `ENUM` — keeping it as a string lets us add new categories without migrations
- `blocked_at` and `reason` both have `index=True` — those are the two most-queried columns (recent blocks, blocks by category)

**Created automatically** when the FastAPI server starts up — `init_db()` calls `Base.metadata.create_all()` which is non-destructive (creates missing tables, leaves existing ones alone).

---

### `app/routes/analyze.py` — the wiring (modified)

The original 6-step flow is unchanged. We added a **Step 0** at the top:

```python
validation = validate_code_input(body.code_snippet)
if not validation.is_safe:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await log_blocked_input(
        db=db,
        result=validation,
        input_snippet=body.code_snippet,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    raise HTTPException(status_code=400, detail=_REJECTION_MESSAGE)
```

**Three things worth noticing:**

1. **Runs BEFORE the DB write.** A blocked input never gets a row in `analysis_requests`. The eval table stays clean.
2. **HTTP 400, not 403 or 422.** 400 ("Bad Request") is neutral — it doesn't tell the attacker that we *recognized* the input as an attack. 403 ("Forbidden") would leak that information.
3. **`_REJECTION_MESSAGE` is a module-level constant.** Same exact string for every rejection category, regardless of which pattern matched. The silent-rejection contract enforced in code.

---

### `app/core/limiter.py` — the localhost bypass (modified)

We changed the rate limiter to skip rate-limiting for `127.0.0.1` and `::1`. Production traffic still gets the 5/min limit; internal tooling (eval scripts, health checks) bypasses it.

The mechanism: slowapi treats a `None` return from `key_func` as "skip rate limiting for this request." Our custom `key_func` returns `None` for exempt IPs and the real IP otherwise.

**Interview-relevant point:** This is exactly the kind of production scar tissue Brillian values. *"My eval suite was tripping my own rate limiter. I added a bypass for internal tooling — production protections shouldn't artificially throttle my own diagnostic workflows."*

---

## Tests

### `tests/test_input_validator.py` — 32 unit tests, 6 classes

| Class | Count | Tests |
|-------|-------|-------|
| `TestLegitimateCode` | 6 | Real code doesn't get rejected |
| `TestInstructionOverride` | 6 | "Ignore previous instructions" family |
| `TestRoleReassignment` | 5 | "You are now..." family |
| `TestPromptLeak` | 5 | "Show me your system prompt" family |
| `TestSystemTagInjection` | 6 | Fake `<system>` tags, `[INST]`, chat templates |
| `TestNonCode` | 3 | Empty input, whitespace, pure prose |
| `TestSilentRejectionContract` | 1 | `ValidationResult` has no user-facing fields |

Uses `@pytest.mark.parametrize` heavily — one test method, many payloads. That's how 5 lines of test code becomes 6 test runs.

**Run with:**

```bash
pytest tests/test_input_validator.py -v
```

---

### `tests/test_blocked_input_model.py` — 4 schema tests

Doesn't hit Postgres. Introspects the SQLAlchemy model in-memory to verify:

1. Model is registered under the right `__tablename__`
2. All required columns exist
3. Nullable constraints match design
4. The right columns are indexed

This is the correct level of test for an ORM model. Testing that Postgres accepts the schema would be testing Postgres, not our code.

---

## Quick file lookup

| If you need to... | Open... |
|-------------------|---------|
| Add a new eval case | New file in `scripts/eval_cases/` matching the skeleton |
| Add a new assertion type | `scripts/evaluate.py` → write checker, add to `ASSERTION_CHECKERS` |
| Add a new prompt-injection pattern | `app/core/input_validator.py` → add to `_INJECTION_PATTERNS` list |
| See blocked attacks | `SELECT * FROM blocked_inputs ORDER BY blocked_at DESC` |
| See eval results | `scripts/eval_results.json` |
| Compare today's eval to Day 23 baseline | `eval_results.json` vs `eval_results_day23.json` |

---

## Interview cheat-sheet phrases

If asked about eval:

> "I built a 15-case eval dataset across 5 categories including negative cases that test for false positives. The runner has per-assertion checkers and three diagnostic views — overall, per-category, per-assertion. The third view is what tells me whether failures are about retrieval, scoring, or violation phrasing."

If asked about prompt injection:

> "OWASP LLM01. Regex-based detection across 5 attack categories — instruction override, role reassignment, prompt leak, system tag injection, non-code input. Silent rejection: same generic 'this doesn't look like code' to all attackers, regardless of category. Server-side I get full diagnostic granularity via a separate audit table. 32 unit tests, all green."

If asked about the test files:

> "Pure-function validator with 32 unit tests because security-critical logic deserves fast iteration. The 50ms test run is what let me catch a regex that was too strict — I was missing 'show me your instructions' because my pattern required 'show' followed immediately by 'your'."
