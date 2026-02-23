# SMART (Self-Managed Autonomous Response Tool)

SMART is a practical foundation for your own ChatGPT-style coding assistant.

## What SMART does now

- uses **free/public web sources** for coding context:
  - Google Programmable Search (free tier, optional)
  - Reddit search
  - GitHub search API
  - DuckDuckGo instant answer fallback
- uses a **free-tier compatible LLM endpoint** via OpenAI-compatible API format
- generates Python + pytest
- verifies code locally before returning results
- retries automatically when verification fails

## Quick start

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install pytest
```

Set required LLM variables:

```bash
export SMART_API_KEY="<your-api-key>"
# optional (defaults shown)
export SMART_API_BASE="https://openrouter.ai/api/v1"
export SMART_MODEL="meta-llama/llama-3.1-8b-instruct:free"
```

Optional Google source (free tier on Google Programmable Search):

```bash
export SMART_GOOGLE_API_KEY="<google-api-key>"
export SMART_GOOGLE_CX="<programmable-search-engine-id>"
```

Run SMART:

```bash
python3 -m smart.cli "build a Python URL shortener module with tests" --rounds 4 --out-dir smart_output
```

Generated artifacts:

- `smart_output/candidate.py`
- `smart_output/test_candidate.py`
- `smart_output/verification.txt`

## Put this into your GitHub repo

If you already created a GitHub repository, run:

```bash
./tools/publish_to_github.sh git@github.com:<your-user>/<your-repo>.git main
```

Or with HTTPS:

```bash
./tools/publish_to_github.sh https://github.com/<your-user>/<your-repo>.git main
```

This script sets (or updates) `origin` and pushes your branch.

## Architecture

- `smart/research.py`: context collector from Google/Reddit/GitHub/DuckDuckGo
- `smart/llm.py`: OpenAI-compatible chat client
- `smart/agent.py`: research → generation → verification → repair loop
- `smart/verifier.py`: executes generated code/tests and captures results
- `smart/cli.py`: CLI that writes code/test/verification outputs
- `tools/publish_to_github.sh`: helper to publish to your GitHub repo

## Important note

No assistant can honestly guarantee it is always "better" than every other model on every task.
What you *can* do is make SMART reliably useful by combining:

- high-quality prompts,
- strong verification,
- eval benchmarks,
- and iterative model/tool improvements.
