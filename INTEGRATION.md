# InsightAI stack integration

Cross-repo roles for the local InsightAI products:

| Repo | Role |
|------|------|
| `/home/ztothez/AI/InsightAICode/clean/` | Primary coding agent CLI (clean-room MVP) |
| `/home/ztothez/AI/AI-Insight-Model` | LoRA/GGUF training + Ollama packaging (`insightai-code`) |
| `/home/ztothez/AI/AI-Insight-Engine` | RAG code auditor API; optional shared Ollama agent |

## Shared local model

1. Package the GGUF in Ollama:

```bash
cd /home/ztothez/AI/AI-Insight-Model
ollama create insightai-code -f Modelfile
```

2. Engine agent path:

```bash
export OLLAMA_MODEL=insightai-code
```

Used by `app/services/agent_service.py`. `/analyze` still uses Together.ai for RAG.

3. InsightAI Code CLI:

```bash
cd /home/ztothez/AI/InsightAICode/clean
bun run src/cli.ts -p "…" --model insightai-code
```

## Tool-schema note

The Model SFT dataset and Code MVP share IDE-style tools (`Read`, `Grep`, `Edit`, …).
Engine’s LangGraph agent currently uses review helpers (`check_code_complexity`, …).
Fine-tune gains apply most directly to the Code CLI; Engine benefits mainly from the
same base instruct model tag until Engine tools are aligned.
