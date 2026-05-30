# AI Insight Engine

A portfolio-ready **AI code quality and security auditor** built with FastAPI, RAG, vector search, LLM-based review, a LangGraph agent, evaluation scripts, and CI/CD.

The system accepts Python code snippets and returns structured feedback on security, maintainability, readability, and concrete violations. It is designed as a practical AI engineering project: API-first, testable, evaluable, deployable, and grounded in a searchable security/software-engineering knowledge base.

![CI](https://github.com/ztothez/AI-Insight-Engine/actions/workflows/ci.yml/badge.svg)

## Project status

**Working now**

- FastAPI backend with `/health`, `/analyze`, `/agent`, and `/audit` endpoints
- Static frontend pages served from the API root, `/analyze`, and `/agent`
- RAG pipeline using Together.ai embeddings and PostgreSQL + pgvector
- 20,875 stored embeddings from 8 security and software-engineering references
- LLM-based structured code review using Llama 3.3 70B via Together.ai
- LangGraph ReAct agent using local Ollama/Qwen for tool-assisted review
- Redis response caching for repeated `/analyze` requests
- Pydantic validation for request and response contracts
- Input validation, prompt-injection style blocking, rate limiting, and blocked-input audit logging
- Conversation memory for the agent endpoint (short-term, per session)
- PII and secrets redaction before LLM transmission
- Automated 90-day data retention purge job
- Admin endpoint for blocked-input audit log access
- Structured JSON logging
- Evaluation scripts for repeatable quality checks
- GitHub Actions CI/CD pipeline: run `pytest` on push/PR, trigger Render deployment after green tests, run smoke tests after deploy

**Still intentionally marked as demo / portfolio project**

- Long-term agent memory (persisted per user) not yet implemented
- Live deployment URL should be added here after the first successful Render deploy

## What the project does

Send a code snippet to the API and receive:

- Overall, security, maintainability, and readability scores
- Specific code-quality and security violations
- Actionable remediation suggestions
- Citations from retrieved knowledge-base chunks
- Stored request/response records for traceability
- Cached responses for repeated equivalent analysis requests

The main use case is security-aware code review for Python snippets, especially issues such as SQL injection, XSS, command injection, hardcoded secrets, missing authorization checks, and insecure handling of user-controlled input.

## Architecture

```text
User / Frontend / API Client
        |
        v
FastAPI application
        |
        +--> GET /health
        +--> POST /analyze
        +--> POST /agent
        +--> POST /audit
        +--> GET /admin/blocked-inputs
        |
        +--> Input validation + rate limiting
        |
        +--> /analyze RAG workflow
        |       |
        |       +--> PII redaction
        |       +--> Embed submitted code
        |       +--> Search PostgreSQL + pgvector
        |       +--> Retrieve top-k reference chunks
        |       +--> Build grounded review prompt
        |       +--> Call Together.ai Llama 3.3 70B
        |       +--> Validate structured output with Pydantic
        |       +--> Store request + response in Postgres
        |       +--> Cache response in Redis
        |
        +--> /agent workflow
        |       |
        |       +--> Validate submitted code
        |       +--> Load session memory
        |       +--> Run LangGraph ReAct agent
        |       +--> Use review tools:
        |             - complexity check
        |             - best-practice lookup
        |             - risk scoring
        |       +--> Save turn to session memory
        |       +--> Return final agent recommendation
        |
        +--> /audit workflow
                |
                +--> Route request to RAG or agent path
                +--> Return unified audit response
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Landing page |
| `GET` | `/health` | Lightweight health check |
| `GET` | `/analyze` | Static analyze page |
| `GET` | `/agent` | Static agent page |
| `POST` | `/analyze` | RAG-grounded code quality/security analysis |
| `POST` | `/agent` | LangGraph agent-based code review |
| `POST` | `/audit` | Unified router that chooses RAG or agent workflow |
| `GET` | `/admin/blocked-inputs` | Admin-only blocked-input audit log |

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI, Uvicorn, async Python |
| Data | PostgreSQL, SQLAlchemy async, pgvector |
| Cache | Redis |
| RAG embeddings | Together.ai `intfloat/multilingual-e5-large-instruct` |
| LLM review | Together.ai `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| Agent | LangGraph ReAct agent, LangChain, Ollama, `qwen2.5:3b-instruct` |
| Validation | Pydantic v2 |
| Rate limiting | SlowAPI |
| Testing / evals | pytest, custom eval runner |
| Deployment | Docker, Render deploy hook, GitHub Actions |

## Knowledge base

The RAG layer is built from 20,875 embeddings generated from 8 security and software-engineering references:

- Clean Code in Python
- Secure Coding Principles and Practices
- The Web Application Hacker's Handbook
- Security Engineering by Ross Anderson
- Threat Modeling: Designing for Security
- Web Security
- Hands-On Software Engineering with Python
- Secure Agile SDLC Handbook

The retrieval layer embeds the submitted code, performs vector similarity search with pgvector, retrieves the closest chunks, and injects those chunks into the LLM review prompt.

## Local setup

Clone the repository:

```bash
git clone git@github.com:ztothez/AI-Insight-Engine.git
cd AI-Insight-Engine
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create a local `.env` file from the committed example template:

```bash
cp .env.example .env
```

Then edit `.env` and add your real local values:

```bash
nano .env
```

Required variables:

```bash
TOGETHER_API_KEY=your_together_api_key

DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT_CONTAINER=5432
DB_NAME=ai_insight_engine

REDIS_URL=redis://localhost:6379/0
SQLALCHEMY_ECHO=false
ADMIN_API_KEY=your_admin_api_key
```

Start the required local services:

```bash
# PostgreSQL must have pgvector available.
# Redis is optional for correctness but recommended for caching.
redis-server
```

Start Ollama for the agent route:

```bash
ollama pull qwen2.5:3b-instruct
ollama serve
```

Run the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open locally:

```text
http://localhost:8000
http://localhost:8000/analyze
http://localhost:8000/agent
http://localhost:8000/health
```

## Docker run

The repository includes a Dockerfile for running the FastAPI app:

```bash
docker build -t ai-insight-engine .
docker run --env-file .env -p 8000:8000 ai-insight-engine
```

The container starts Uvicorn on port `8000`.

## Example API request

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code_snippet": "query = f\"SELECT * FROM users WHERE id={user_id}\"",
    "language": "python",
    "strictness_level": 4
  }'
```

Expected response shape:

```json
{
  "scores": {
    "overall": 6.5,
    "security": 4.0,
    "maintainability": 8.0,
    "readability": 9.0
  },
  "violations": [
    "SQL Injection Vulnerability: The query string is formatted using user input without proper sanitization."
  ],
  "suggestion": "Use parameterized queries or an ORM to prevent SQL injection.",
  "sources": [
    {
      "doc_id": "software_engineering_python",
      "chunk_index": 1703,
      "text": "..."
    }
  ]
}
```

## Running tests

```bash
pytest -q
```

The GitHub Actions workflow runs this automatically on:

- every push to `main`
- every pull request targeting `main`

## Running evals

Start the API first:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Build the eval dataset if needed:

```bash
python scripts/build_eval_dataset.py
```

Run the eval suite:

```bash
python scripts/evaluate.py
```

The eval runner sends known code samples to `/analyze`, checks expected violations, score thresholds, and citation presence, then writes structured results to:

```text
scripts/eval_results.json
```

## Running smoke tests

```bash
python scripts/smoke_test.py http://localhost:8000
# or against the live deployment:
python scripts/smoke_test.py https://your-render-url.onrender.com
```

## CI/CD

The repository has a GitHub Actions workflow at:

```text
.github/workflows/ci.yml
```

Pipeline behavior:

```text
Push or pull request to main
        |
        v
Install Python dependencies
        |
        v
Run pytest
        |
        v
If push to main and tests pass: trigger Render deploy hook
        |
        v
Wait 60 seconds for Render to boot
        |
        v
Run smoke tests against live deployment
```

Required GitHub Actions secrets:

```text
RENDER_DEPLOY_HOOK_URL
RENDER_URL
```

Recommended Render setting:

```text
Auto Deploy: Off
```

This avoids deploying before tests pass. GitHub Actions becomes the deployment gate.

## Deployment notes

For Render:

- Runtime: Docker
- Exposed port: `8000`
- Start command is already defined in the Dockerfile
- Add environment variables from `.env.example` as Render environment variables
- Add managed PostgreSQL with pgvector support or connect to an external Postgres instance with pgvector
- Add Redis if response caching should be enabled
- Store the Render deploy hook in GitHub Actions as `RENDER_DEPLOY_HOOK_URL`
- Store the live Render URL in GitHub Actions as `RENDER_URL`

After deployment, add the live URL here:

```text
Live demo: TODO - add Render URL
```

## Design decisions

**RAG instead of fine-tuning**

The project uses retrieval to ground reviews in security and software-engineering material without training a custom model. This keeps the system inspectable and easier to iterate.

**Structured output validation**

LLM output is parsed into Pydantic models before it becomes an API response. This prevents malformed model output from silently leaking into the client contract.

**Separate RAG and agent paths**

The RAG path is optimized for grounded code review with citations. The agent path is optimized for tool-assisted reasoning, complexity analysis, best-practice lookup, and risk scoring.

**Evaluation as an engineering artifact**

The project includes a repeatable eval runner instead of relying only on manual inspection. Known cases are sent through the API and checked against expected violations, score thresholds, and citation requirements.

**CI/CD gated deployment**

Deployment is triggered only after tests pass on `main`, making the project closer to a real production workflow.

**PII redaction before LLM transmission**

Submitted code is scanned for emails, IP addresses, API keys, and hardcoded passwords before being sent to Together.ai. The LLM never sees raw sensitive values.

**Session memory for the agent**

The agent maintains conversation history per `session_id`, allowing follow-up questions within a session. Memory is stored in-process; long-term persistence per user is documented as a future improvement.

## Data handling and GDPR considerations

This is a demonstrator project, not a production deployment. The notes below describe what the running system processes and what would be required for GDPR-compliant production use.

### What data the system processes

When a user submits code via `POST /analyze`:

- The submitted `code_snippet` is stored in the `analysis_requests` table.
- LLM-generated scores and violations are stored in `analysis_responses`.
- The submitted code is transmitted to Together.ai for inference.

When input validation blocks a request:

- The rejected input may be stored in `blocked_inputs`.
- Client IP address and User-Agent may be stored for audit purposes.

Code snippets may contain personal data the user did not intend to share, such as names in test fixtures, email addresses, API keys, production identifiers, or customer-like mock data. The system treats submitted code as potentially sensitive.

### Production hardening checklist

- [x] Add automatic retention policy for stored requests and responses
- [ ] Add deletion/export tooling for stored user data
- [x] Add PII/secrets redaction before LLM transmission
- [x] Add access controls around blocked-input audit logs
- [x] Use EU-hosted inference for EU production deployments, or document transfer safeguards
- [x] Add structured logging and monitoring
- [x] Add deployment smoke tests after Render deploy
- [x] Expand eval coverage beyond the current security cases

### Before production deployment

The following require action outside the codebase:

- **Encryption at rest** — enable Postgres encryption in your hosting provider dashboard
- **DPIA** — complete a Data Protection Impact Assessment if processing personal data at scale

## Portfolio summary

This project demonstrates practical AI engineering skills across the full lifecycle:

- Backend API design
- RAG architecture
- Vector search with pgvector
- LLM integration
- Agent workflows with LangGraph
- Async Python and FastAPI
- Validation and error handling
- Caching
- Evaluation pipelines
- CI/CD with GitHub Actions
- Docker deployment
- Security-aware software design

It is built to show that the system is not just a prompt demo: it has an API contract, persistent storage, retrieval, validation, evals, tests, deployment automation, and documented production risks.