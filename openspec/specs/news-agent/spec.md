# news-agent Specification

## Purpose

TBD - created by archiving change 'ai-news-monitor'. Update Purpose after archive.

## Requirements

### Requirement: Claude searches for AI news autonomously

The agent SHALL use the Google Gemini API with tool definitions backed by Tavily. Gemini SHALL autonomously decide which queries to run and when it has sufficient information. The agent SHALL make between 8 and 15 Tavily calls per run across an English pass (5–10 searches) and a Chinese-language pass (3–5 searches). The agent SHALL call `submit_plan` before making any `search` call. The agent SHALL call `submit_report` to end the loop; Python will respond with a quality check result. If the first `submit_report` fails quality checks, the agent MAY make additional `search` calls before resubmitting once.

#### Scenario: Agent completes within call budget

- **WHEN** `agent.py` is executed
- **THEN** Gemini makes between 8 and 15 calls to the `search` tool before the loop ends

##### Example: typical run

- **GIVEN** Gemini decides to search for AI news in EN and ZH passes
- **WHEN** the agentic loop runs
- **THEN** between 8 and 15 Tavily API calls are made, `submit_plan` is called once before the first search, and `submit_report` is called at least once


<!-- @trace
source: agent-agentic-upgrades
updated: 2026-06-13
code:
  - agent.py
  - archive.html
  - summaries.md
  - 2026-06-09/index.html
  - 2026-06-10/index.html
  - index.html
-->

---
### Requirement: Agent produces structured bilingual output via submit_report tool

The agent SHALL define a `submit_report` tool. Claude SHALL call this tool exactly once to end the agentic loop. The tool input SHALL conform to the schema: `{ date, headlines_en[7], analysis_en, sources_en[], headlines_zh[7], analysis_zh, sources_zh[] }`.

#### Scenario: submit_report is called with all required fields

- **WHEN** Claude has gathered sufficient information
- **THEN** Claude calls `submit_report` with exactly 7 EN headlines, an EN analysis block, at least 12 EN sources, exactly 7 ZH headlines, a ZH analysis block, and at least 12 ZH sources

##### Example: output schema validation

| Field | Type | Constraint |
|---|---|---|
| date | string | YYYY-MM-DD format |
| headlines_en | array | exactly 7 items |
| analysis_en | string | non-empty |
| sources_en | array | 12–14 items, each with label + url |
| headlines_zh | array | exactly 7 items |
| analysis_zh | string | non-empty |
| sources_zh | array | 12–14 items, each with label + url |


<!-- @trace
source: ai-news-monitor
updated: 2026-06-08
code:
  - .github/workflows/daily.yml
  - requirements.txt
  - .env.example
  - agent.py
-->

---
### Requirement: Agent appends output to summaries.md

After a successful `submit_report` call, the agent SHALL append a dated JSON entry to `summaries.md`. The entry SHALL use the format:

```

<!-- @trace
source: ai-news-monitor
updated: 2026-06-08
code:
  - .github/workflows/daily.yml
  - requirements.txt
  - .env.example
  - agent.py
-->

---
date: YYYY-MM-DD
---
{...json...}
```

The append operation SHALL be atomic with respect to the file — existing entries SHALL NOT be modified.

#### Scenario: New entry appended without corrupting existing data

- **WHEN** `agent.py` completes successfully
- **THEN** `summaries.md` contains all previous entries unchanged, plus one new entry for today's date at the end of the file

---
### Requirement: Agent exits non-zero on failure

If Claude does not call `submit_report` within the allowed call budget, or if the Tavily API returns an error that prevents search, the agent SHALL raise a RuntimeError and exit with a non-zero status code. `summaries.md` SHALL NOT be modified on failure.

#### Scenario: Tavily unavailable

- **WHEN** Tavily API returns a non-200 response on all calls
- **THEN** `agent.py` exits non-zero and `summaries.md` is unchanged

<!-- @trace
source: ai-news-monitor
updated: 2026-06-08
code:
  - .github/workflows/daily.yml
  - requirements.txt
  - .env.example
  - agent.py
-->

---
### Requirement: Agent loop accepts two optional new tools

The `run_agent()` function SHALL include `submit_plan` and evaluate-via-`submit_report` in the TOOLS list available to the model. Both are optional in the sense that the pipeline SHALL complete even if the agent does not call `submit_plan`; `submit_report` remains required.

#### Scenario: All three tool types may appear in one run

- **WHEN** `agent.py` runs successfully
- **THEN** the event log (function calls observed in the loop) MAY contain calls to `submit_plan`, one or more `search` calls, and at least one `submit_report` call — in that order

<!-- @trace
source: agent-agentic-upgrades
updated: 2026-06-13
code:
  - agent.py
  - archive.html
  - summaries.md
  - 2026-06-09/index.html
  - 2026-06-10/index.html
  - index.html
-->