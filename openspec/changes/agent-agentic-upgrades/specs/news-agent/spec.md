## MODIFIED Requirements

### Requirement: Claude searches for AI news autonomously

The agent SHALL use the Google Gemini API with tool definitions backed by Tavily. Gemini SHALL autonomously decide which queries to run and when it has sufficient information. The agent SHALL make between 8 and 15 Tavily calls per run across an English pass (5–10 searches) and a Chinese-language pass (3–5 searches). The agent SHALL call `submit_plan` before making any `search` call. The agent SHALL call `submit_report` to end the loop; Python will respond with a quality check result. If the first `submit_report` fails quality checks, the agent MAY make additional `search` calls before resubmitting once.

#### Scenario: Agent completes within call budget

- **WHEN** `agent.py` is executed
- **THEN** Gemini makes between 8 and 15 calls to the `search` tool before the loop ends

##### Example: typical run

- **GIVEN** Gemini decides to search for AI news in EN and ZH passes
- **WHEN** the agentic loop runs
- **THEN** between 8 and 15 Tavily API calls are made, `submit_plan` is called once before the first search, and `submit_report` is called at least once

## ADDED Requirements

### Requirement: Agent loop accepts two optional new tools

The `run_agent()` function SHALL include `submit_plan` and evaluate-via-`submit_report` in the TOOLS list available to the model. Both are optional in the sense that the pipeline SHALL complete even if the agent does not call `submit_plan`; `submit_report` remains required.

#### Scenario: All three tool types may appear in one run

- **WHEN** `agent.py` runs successfully
- **THEN** the event log (function calls observed in the loop) MAY contain calls to `submit_plan`, one or more `search` calls, and at least one `submit_report` call — in that order
