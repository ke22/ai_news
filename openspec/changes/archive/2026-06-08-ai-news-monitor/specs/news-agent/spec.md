## ADDED Requirements

### Requirement: Claude searches for AI news autonomously

The agent SHALL use the Anthropic messages API with a `search` tool definition backed by Tavily. Claude SHALL autonomously decide which queries to run and when it has sufficient information. The agent SHALL make between 3 and 10 Tavily calls per run.

#### Scenario: Agent completes within call budget

- **WHEN** `agent.py` is executed
- **THEN** Claude makes between 3 and 10 calls to the `search` tool before ending the loop

##### Example: typical run

- **GIVEN** Claude decides to search for AI news
- **WHEN** the agentic loop runs
- **THEN** between 3 and 10 Tavily API calls are made, and the loop ends with `stop_reason == "end_turn"` after `submit_report` is called

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

### Requirement: Agent appends output to summaries.md

After a successful `submit_report` call, the agent SHALL append a dated JSON entry to `summaries.md`. The entry SHALL use the format:

```
---
date: YYYY-MM-DD
---
{...json...}
```

The append operation SHALL be atomic with respect to the file — existing entries SHALL NOT be modified.

#### Scenario: New entry appended without corrupting existing data

- **WHEN** `agent.py` completes successfully
- **THEN** `summaries.md` contains all previous entries unchanged, plus one new entry for today's date at the end of the file

### Requirement: Agent exits non-zero on failure

If Claude does not call `submit_report` within the allowed call budget, or if the Tavily API returns an error that prevents search, the agent SHALL raise a RuntimeError and exit with a non-zero status code. `summaries.md` SHALL NOT be modified on failure.

#### Scenario: Tavily unavailable

- **WHEN** Tavily API returns a non-200 response on all calls
- **THEN** `agent.py` exits non-zero and `summaries.md` is unchanged
