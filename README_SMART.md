# SMART (Self-Managed Autonomous Response Tool)

A practical blueprint for your own ChatGPT-like coding assistant that:

- uses **free APIs** for research (DuckDuckGo, Reddit, GitHub)
- uses a **free LLM endpoint** (for example OpenRouter free-tier models)
- performs **automatic code verification** with pytest before returning output

## What this gives you

This implementation is a **working foundation**, not a guaranteed "better than every model" system. In practice, quality comes from your prompts, eval loops, tools, and model selection.

## Setup

1. Install project dependencies.
2. Export env vars:

```bash
export SMART_API_KEY="<your-api-key>"
# optional overrides
export SMART_API_BASE="https://openrouter.ai/api/v1"
export SMART_MODEL="meta-llama/llama-3.1-8b-instruct:free"
```

3. Run SMART:

```bash
python3 -m smart.cli "write a python function that validates email addresses and include tests"
```

## Architecture

- `smart/research.py` — queries free/public endpoints for context.
- `smart/llm.py` — OpenAI-compatible chat API wrapper.
- `smart/agent.py` — orchestration loop (research → generate → verify → repair).
- `smart/verifier.py` — executes generated code/tests and returns status.
- `smart/cli.py` — simple command-line interface.

## Next upgrades

- Add retrieval cache and ranking for GitHub/Reddit snippets.
- Add containerized sandbox for safer code execution.
- Add benchmark suite (HumanEval/MBPP-like internal tasks).
- Add multi-model voting (free model ensemble).
