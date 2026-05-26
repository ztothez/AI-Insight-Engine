# AI-Insight-Engine

A production-oriented **Code Quality & Security Auditor** built on RAG, LLM agents, and vector search. Analyzes Python code for OWASP Top 10 vulnerabilities, clean code violations, and security risks, grounded in real security literature.

## Project Status

**Working now:** RAG pipeline with 20,875 embeddings, FastAPI endpoints (/analyze, /agent), 
LangGraph ReAct agent, Pydantic validation, eval pipeline with 15 test cases, input validation 
and blocking with audit trail.

**In progress:** Conversation memory for agent, expanded eval coverage, production hardening 
(see GDPR checklist below).

## What it does

Send a code snippet → get back:
- Security scores (overall, security, maintainability, readability)
- Specific violations with OWASP references
- Actionable suggestions
- Citations from security books used to ground the analysis

## Architecture

```text
POST /analyze
     ↓
FastAPI (async) + Rate Limiting + Input Validation
     ↓
RAG Pipeline
  → Embed query (Together.ai intfloat/multilingual-e5-large-instruct)
  → Semantic search (pgvector cosine similarity, 20,875 embeddings)
  → Retrieve top-5 chunks from 8 security/coding books
     ↓
LLM Analysis (Llama 3.3 70B via Together.ai)
  → System prompt: OWASP Top 10 + clean code principles
  → Context-grounded response
     ↓
Pydantic validation of LLM output
     ↓
Structured JSON response + citations
```

## Knowledge Base (RAG)

20,875 embeddings from 8 books ingested into pgvector:
- Clean Code in Python
- Secure Coding Principles and Practices
- Web Application Hacker's Handbook
- Security Engineering (Ross Anderson)
- Threat Modeling: Designing for Security
- Web Security
- Hands-On Software Engineering with Python
- Secure Agile SDLC Handbook

## Tech Stack

- **Backend:** FastAPI, async Python, SQLAlchemy
- **LLM:** Llama 3.3 70B Instruct Turbo (Together.ai)
- **Embeddings:** intfloat/multilingual-e5-large-instruct (Together.ai, 1024-dim)
- **Vector DB:** PostgreSQL + pgvector
- **Agent:** LangGraph ReAct agent with 3 tools
- **Validation:** Pydantic v2
- **Infra:** Docker, docker-compose

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /analyze | RAG + LLM code analysis with citations |
| POST | /agent | LangGraph agent with complexity/risk tools |

## Getting Started

```bash
git clone git@github.com:ztothez/AI-Insight-Engine.git
cd AI-Insight-Engine
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in TOGETHER_API_KEY, DB credentials
docker compose up -d
fastapi dev app/main.py
```

## Example

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"code_snippet": "query = f\"SELECT * FROM users WHERE id={user_id}\"", "language": "python", "strictness_level": 4}'
```

## Design Decisions

- **RAG over fine-tuning:** grounding in real security books gives traceable, up-to-date results without training costs
- **top_k=5:** balances context richness vs prompt size vs latency
- **Pydantic validation of LLM output:** catches hallucinated or malformed scores before they reach the client
- **Separate schemas for API vs LLM output:** `AnalyzeResponse` vs `LLMAnalysisResult`, different contracts, different validation rules

## Data Handling and GDPR Considerations

This is a demonstrator project, not a production deployment. The notes below describe what data the running system processes and what would be required for GDPR-compliant production use.

### What data the system processes

When a user submits code via `POST /analyze`:
- The full `code_snippet` is stored in the `analysis_requests` table (Postgres).
- LLM-generated scores and violations are stored in `analysis_responses`.
- Submitted code is transmitted to Together.ai (US-hosted) for inference.

When the input validator blocks a request:
- The full rejected input is stored in `blocked_inputs`.
- The client IP address and User-Agent header are stored alongside it.

Code snippets may contain personal data the user did not intend to share — names in mock data, email addresses in test fixtures, API keys, or production identifiers. The system treats all `code_snippet` content as potentially containing personal data.

### Lawful basis (GDPR Art. 6)

For this demonstrator, no lawful basis is established. A production deployment would likely rely on legitimate interest (Art. 6(1)(f)) for security analysis, or explicit consent (Art. 6(1)(a)) if the service is end-user-facing.

### Retention

The current implementation has no automatic retention policy — data is kept indefinitely in Postgres. Production deployment would require:
- 30-90 day retention for `analysis_requests` and `analysis_responses`
- Separate, longer retention for `blocked_inputs` (audit trail), with access controls
- Automated purge job (e.g. nightly cron) and documented retention schedule

### User rights (GDPR Art. 15-17)

- **Art. 15 (right of access):** Not implemented. Production would need a mechanism to export a user's stored data.
- **Art. 16 (rectification):** Largely not applicable — submitted code is a point-in-time artifact, not a profile.
- **Art. 17 (right to erasure):** Not implemented. Production would need a deletion endpoint or admin tool that removes all rows tied to a user identifier.

### Cross-border transfer (Schrems II)

Together.ai is US-hosted. Sending EU user data to a US service raises Schrems II concerns. Production options:
- Switch to an EU-region LLM provider (e.g. Mistral via EU-hosted endpoint).
- Sign a Data Processing Agreement (DPA) with Together.ai that addresses Standard Contractual Clauses and supplementary measures.
- Add a PII redaction layer before transmission, so identifiable content never leaves EU infrastructure.

### Production hardening checklist

- [ ] Encryption at rest (RDS-level encryption, or Postgres TDE)
- [ ] PII redaction pipeline before storage and before LLM transmission
- [ ] Access controls on the `blocked_inputs` audit table
- [ ] Automated retention purge job
- [ ] Data Protection Impact Assessment (DPIA) if the deployment context warrants it
- [ ] Documented Data Processing Agreement with all third-party processors