## Context

`agent.py` contains the entire news agent: a Gemini agentic loop with two tools (`search`, `submit_report`). Each run starts cold — no knowledge of past searches, no quality gate on the submitted report, no explicit plan before searching. `summaries.md` is an append-only file of past reports as JSON entries, currently used only by `publish.py`. The agent loop in `run_agent()` drives Gemini through tool calls until `submit_report` is received, then immediately returns.

## Goals / Non-Goals

**Goals:**
- Inject a memory context block from the last 7 `summaries.md` entries so the agent diversifies source domains
- Add a `submit_plan` tool so the agent must declare its search strategy before the first `search` call
- Gate `submit_report` with Python-enforced quality rules; allow one retry if rules fail

**Non-Goals:**
- No persistent memory file beyond `summaries.md`
- No multi-day conversation context (today's context window only)
- No model-judged quality scoring — all evaluation is deterministic Python rules
- No changes to `publish.py`, HTML templates, or CSS
- Planning data is logged in the report JSON; it is not displayed on the public site

## Decisions

### Memory context is built from `summaries.md` before `run_agent()` is called

The last 7 JSON entries from `summaries.md` are parsed to extract unique source domains and the first 5 words of each headline. These are formatted into a `## Recent History` block injected into `SYSTEM_PROMPT` at render time.

**Alternative considered**: Import `parse_summaries` from `publish.py`.
**Rejected**: Creates a coupling between agent and publisher; the memory extraction need is narrower than full parse (domains + headline keywords only). A lightweight `build_memory_context()` function in `agent.py` is simpler.

**If `summaries.md` has fewer than 7 entries**: use whatever is available. If the file is empty or missing, memory context is an empty string — the prompt renders without the section.

### Quality evaluation is embedded in `submit_report` response, not a separate tool

When the agent calls `submit_report`, Python immediately runs three deterministic checks against the submitted data. If any check fails, the response is `{"status": "quality_check_failed", "gaps": [...]}` and the loop continues. If all pass, the response is `{"status": "success"}` and the loop exits. Max 1 retry enforced by a `submit_count` counter — on the second `submit_report` call the report is accepted regardless of quality.

**Alternative considered**: Separate `evaluate_report` tool the agent calls after `submit_report`.
**Rejected**: Forces a two-tool sequence the agent might not always follow. Embedding evaluation in `submit_report` response is more reliable — the agent sees the result immediately in the same tool call response.

**Three Python-enforced quality rules:**
1. **No homepage URLs**: every URL in `sources_en` and `sources_zh` must contain a path segment beyond the root (URL parsed; path must not be `/` or empty)
2. **Chinese outlet count**: `sources_zh` must include ≥ 2 URLs whose hostname matches any of: `ithome.com.tw`, `technews.tw`, `bnext.com.tw`, `36kr.com`, `jiqizhixin.com`, `qbitai.com`, `technews.com.tw`
3. **Source count**: `sources_en` and `sources_zh` must each have between 12 and 14 entries

### `submit_plan` tool is required before the first `search` call

A `submit_plan` tool accepts `{category_queries: {category_name: [query_string]}}`. Python stores the plan and responds with `{"status": "received"}`. The system prompt instructs the agent to call `submit_plan` first. The plan dict is stored in the final report JSON as a `plan` field.

**If the agent skips `submit_plan`**: The pipeline continues — planning is not a hard gate. The `plan` field is absent from the report JSON.

## Implementation Contract

### `build_memory_context(summaries_path: str) -> str`

- Reads `summaries_path`, parses last 7 JSON entries
- Returns a string of the form:
  ```
  ## Recent History (last 7 days)
  Source domains used recently: reuters.com, techcrunch.com, ...
  Recent headline topics: OpenAI GPT-5, EU AI Act, ...
  Diversify away from these sources and topics today.
  ```
- Returns `""` (empty string) if the file is missing, empty, or has no parseable entries
- Does not raise; errors are silently ignored and return `""`

### `SYSTEM_PROMPT` change

`SYSTEM_PROMPT` gains a `{memory_context}` placeholder. `run_agent()` calls `build_memory_context()` and passes the result alongside `{date}`. If memory context is empty, the rendered prompt has no `## Recent History` section.

### `submit_plan` tool schema

```json
{
  "name": "submit_plan",
  "parameters": {
    "category_queries": {
      "type": "object",
      "description": "Map of category name to list of intended search queries",
      "additionalProperties": { "type": "array", "items": { "type": "string" } }
    }
  },
  "required": ["category_queries"]
}
```

Python response: `{"status": "received"}`. Plan stored in `run_agent()` local var `plan`, included in returned report dict as `"plan"` key.

### `submit_report` quality gate

`run_agent()` tracks `submit_count: int = 0`. On each `submit_report` call:
1. Increment `submit_count`
2. If `submit_count == 1`: run quality checks; if any fail, return `{"status": "quality_check_failed", "gaps": ["<description>", ...]}` and continue loop without setting `report`
3. If `submit_count >= 2`: accept the report unconditionally (`report = dict(fc.args)`), respond `{"status": "accepted_on_retry"}`, break

Quality check functions are pure: `check_no_homepage_urls(sources) -> list[str]`, `check_chinese_outlet_count(sources_zh) -> list[str]`, `check_source_counts(sources_en, sources_zh) -> list[str]`. Each returns a list of gap description strings (empty = passed).

### Report JSON shape change

The returned `report` dict gains two optional fields:
- `"plan"`: the dict from `submit_plan` (absent if agent skipped planning)
- `"evaluation_gaps"`: list of gap strings from the first quality check (absent if first submission passed; present and non-empty on retry)

`append_to_summaries()` serialises the full dict — these fields are stored in `summaries.md` automatically.

### Acceptance criteria

1. Run `python agent.py` when `summaries.md` has ≥ 1 entry → new entry in `summaries.md` contains no homepage URLs in `sources_en`/`sources_zh` (all URLs have path depth > 1)
2. New entry contains `"plan"` key with at least one category key (agent called `submit_plan`)
3. If `evaluation_gaps` key is present in the entry, it is a non-empty list (confirms retry path was exercised at least once across runs)
4. Run `python publish.py` after step 1 → exits 0, no new fields break HTML rendering

## Risks / Trade-offs

- [Risk] Agent skips `submit_plan` → plan field absent from report; memory and evaluation still work. Mitigation: system prompt instruction is firm; acceptable failure mode since planning is observability-only.
- [Risk] Quality rules force a retry that still fails → second submission is accepted unconditionally to prevent infinite loops. Mitigation: `submit_count >= 2` hard-accepts; worst case is a report with known gaps logged in `evaluation_gaps`.
- [Risk] Memory context adds ~300 tokens per run → negligible cost increase on gemini-2.5-flash. No mitigation needed.
- [Risk] URL homepage detection false-positives a valid short URL → only flags URLs where `urlparse(url).path` is empty or `/`. Legitimate article URLs always have a deeper path.
