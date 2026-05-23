# AI-Insight-Engine

A production-oriented **Code Quality & Security Auditor** built on RAG, LLM agents, and vector search. Analyzes Python code for OWASP Top 10 vulnerabilities, clean code violations, and security risks, grounded in real security literature.

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