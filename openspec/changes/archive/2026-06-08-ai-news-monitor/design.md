## Context

An empty Python project (`ai_news`) needs to be built from scratch. The reference implementation is ainews.ditldesign.com — a live site that has run successfully for 2 days, demonstrating the viability of the approach. There is no existing code to migrate; everything is greenfield.

The system must run unattended every day, producing a bilingual AI-news digest and publishing it to a GitHub Pages static site with zero manual steps.

## Goals / Non-Goals

**Goals:**

- Autonomous daily AI news digest (EN + ZH) published to GitHub Pages
- Claude acts as an agentic decision-maker for search queries (not a fixed prompt)
- Static site with three page types: today, archive, per-day detail
- Fully automated via GitHub Actions — no server needed
- Append-only `summaries.md` as the durable data store

**Non-Goals:**

- Real-time or sub-daily updates
- User accounts, authentication, or personalization
- RSS feeds, email subscriptions, or push notifications
- Scraping HTML — Tavily API is the only search mechanism
- Supporting languages beyond EN and ZH

## Decisions

### Claude as an Agentic Loop (not a single prompt)

Claude receives a `search` tool definition backed by Tavily. The model decides which queries to run, how many (3–10), and when it has enough information to produce the final output. This is `client.messages.create` with `tools=[search_tool]` in a loop until `stop_reason == "end_turn"`.

**Rationale**: Fixed queries would produce repetitive coverage day-to-day. Agentic search lets Claude adapt to what's actually happening in the AI space each day.

**Alternative considered**: Pre-defined query list with Claude only for synthesis. Rejected because it removes the adaptive search behavior that is central to the reference design.

### Structured JSON Output via Tool Use

The agent's final output is produced by Claude calling a `submit_report` tool with a strict JSON schema: `{ date, headlines_en[7], analysis_en, sources_en[12-14], headlines_zh[7], analysis_zh, sources_zh[12-14] }`. This tool call ends the agentic loop.

**Rationale**: Parsing free-text LLM output is brittle. A tool-call response gives a validated, typed structure with no post-processing.

**Alternative considered**: Asking Claude to produce JSON in its text response. Rejected due to formatting inconsistency risk.

### `summaries.md` as Append-Only Log

Each daily run appends a fenced JSON block to `summaries.md`:
```
---
date: YYYY-MM-DD
---
{ ...structured output... }
```
`publish.py` parses this file to regenerate the full site.

**Rationale**: Plain-text append-only log is human-readable, git-diffable, and requires no database. Lost runs leave a visible gap in the log rather than silent corruption.

**Alternative considered**: SQLite database. Rejected because it adds a dependency and binary diffs make git history opaque.

### Static HTML via Python String Templates

`publish.py` uses Python's `string.Template` (or f-strings) over HTML template files in `templates/`. No Jinja2, no Jekyll, no build step.

**Rationale**: Zero extra dependencies beyond the Anthropic and Tavily SDKs. The site is simple enough that a full templating engine is unnecessary overhead.

**Alternative considered**: Jekyll (as used by the reference site). Rejected because it requires Ruby and adds complexity to the GitHub Actions workflow.

### GitHub Actions for Scheduling

`.github/workflows/daily.yml` uses `schedule: cron: '0 0 * * *'` (00:00 UTC = 08:00 TWN). The workflow: checkout → install deps → run agent.py → run publish.py → git commit + push.

**Rationale**: No server required, versioned alongside the code, free for public repos.

**Alternative considered**: Local cron job. Rejected because it requires a persistent machine.

## Implementation Contract

**Behavior observable after this change ships:**

1. On each day at approximately 08:00 TWN (00:00 UTC), GitHub Actions automatically runs the pipeline.
2. `agent.py` exits 0 with a new dated entry appended to `summaries.md`.
3. `publish.py` regenerates `index.html`, `archive.html`, and `YYYY-MM-DD/index.html` from the updated `summaries.md`.
4. GitHub Pages serves the updated site within minutes of the push.
5. The today's report page shows 7 EN headlines, an EN analysis block, 12–14 EN sources, then the same three sections in ZH.
6. The archive page shows all past dates as links in reverse-chronological order.

**Interface / data shape:**

- `summaries.md` entry format:
  ```
  ---
  date: YYYY-MM-DD
  ---
  {"date":"YYYY-MM-DD","headlines_en":[...],"analysis_en":"...","sources_en":[{"label":"...","url":"..."}],"headlines_zh":[...],"analysis_zh":"...","sources_zh":[...]}
  ```
- `submit_report` tool schema (Claude must call this to end the agentic loop):
  ```json
  {
    "date": "string (YYYY-MM-DD)",
    "headlines_en": ["array of 7 strings"],
    "analysis_en": "string (~280 words)",
    "sources_en": [{"label": "string", "url": "string"}],
    "headlines_zh": ["array of 7 strings"],
    "analysis_zh": "string (~280 words)",
    "sources_zh": [{"label": "string", "url": "string"}]
  }
  ```

**Failure modes:**

- Tavily API unavailable: agent.py exits non-zero; GitHub Actions marks run as failed; `summaries.md` is unchanged; site retains previous day's content.
- Claude fails to call `submit_report` within token budget: agent.py raises RuntimeError and exits non-zero.
- Git push fails (e.g., conflict): GitHub Actions marks run as failed; site unchanged; rerun resolves after pull.

**Acceptance criteria:**

- `python agent.py` completes and appends a valid JSON entry to `summaries.md`
- `python publish.py` produces valid HTML at `index.html`, `archive.html`, and `YYYY-MM-DD/index.html`
- GitHub Actions workflow file passes `act` dry-run or equivalent
- The today page renders with all required sections in both languages when opened in a browser

**Scope boundaries:**

- In scope: agent.py, publish.py, run.sh, daily.yml, three HTML templates, style.css, requirements.txt
- Out of scope: RSS feeds, pagination on archive, search functionality, analytics

## Risks / Trade-offs

- [Tavily API cost] → Mitigation: 3–10 calls/day is well within Tavily's free tier limits.
- [Claude token cost] → Mitigation: Daily run with claude-sonnet-4-6 is approximately $0.01–0.05/day at normal usage.
- [GitHub Actions cron jitter] → Mitigation: GH Actions cron can be 15–30 min late under load. Acceptable for a daily digest.
- [summaries.md grows unbounded] → Mitigation: At ~5 KB/entry, 1 year = ~1.8 MB — negligible for git.
- [Claude produces malformed submit_report JSON] → Mitigation: tool-call schema validation catches this; agent retries or exits non-zero.
