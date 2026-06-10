## Why

The ai_news agent resets to zero on every run — no memory of past sources, no ability to judge its own output quality, and no explicit search plan. These gaps mean it may repeat the same sources week after week, submit low-quality reports without noticing, and search in an unstructured order that misses categories. Addressing all three closes the gap identified by Agent B's critique in the about page debate.

## What Changes

- **Memory**: Before each run, the last 7 days of `summaries.md` are parsed to extract previously-used source domains and recent headline keywords. This context is injected into the system prompt so the agent actively diversifies away from repeated sources.
- **Planning**: A new `submit_plan` tool is added. The agent must call it before its first search, declaring intended queries per category. The plan is stored in the report JSON for auditability.
- **Self-evaluation**: A new `evaluate_report` tool is added. After `submit_report`, Python checks the submitted report against fixed quality rules (category coverage, URL format, Chinese source count). If it fails, the agent is allowed one retry within the same conversation.

## Non-Goals

- No persistent memory store beyond `summaries.md` (no new files or databases)
- No multi-turn conversation memory across separate days (today's context window only)
- No model-judged quality scoring — evaluation is Python-enforced rule checking only
- No changes to `publish.py`, templates, or the static site output
- Planning artifact is logged only; it does not block or gate the search phase

## Capabilities

### New Capabilities

- `agent-memory`: Reads recent run history from `summaries.md` and injects it as context into the system prompt before each run
- `agent-planning`: `submit_plan` tool that captures the agent's intended search strategy per category before searching begins
- `agent-self-evaluation`: `evaluate_report` tool + Python retry logic that enforces quality rules after `submit_report`

### Modified Capabilities

- `news-agent`: Three new behaviours added to the agent loop (memory context, planning tool, evaluation tool)

## Impact

- Affected specs: `agent-memory` (new), `agent-planning` (new), `agent-self-evaluation` (new), `news-agent` (modified)
- Affected code:
  - Modified: `agent.py`
  - New: none
  - Removed: none
