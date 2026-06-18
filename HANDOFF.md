# Handoff: Daily AI News Operations

## 2026-06-17 missed news incident

### What happened

- The scheduled GitHub Actions workflow ran on 2026-06-17 and failed during `python3 agent.py`.
- GitHub Actions had both required secrets available: `GEMINI_API_KEY` and `TAVILY_API_KEY`.
- The failing log showed `Error: Tavily search failed:` with no useful exception body.
- A local rerun with network access succeeded and appended a 2026-06-17 report.
- Rerunning the failed GitHub Actions workflow also succeeded, published the site, and pushed `132d161 Daily update 2026-06-17`.

### Current production state

- Today's page was published at `https://ke22.github.io/ai_news/2026-06-17/`.
- The published page returned HTTP 200 after the workflow rerun.
- The successful rerun touched:
  - `2026-06-17/index.html`
  - `archive.html`
  - `index.html`
  - `summaries.md`

### Root cause assessment

The immediate failure was an intermittent Tavily/API search failure, not a missing secret or a broken workflow configuration. Evidence:

- The original failed workflow showed secrets were injected.
- The same agent code succeeded on rerun.
- The same workflow succeeded when rerun from GitHub Actions.

### Learning

- A single transient search failure currently aborts the whole daily pipeline.
- Manual workflow rerun is the fastest recovery path when the failure is transient.
- Before pushing from local, fetch remote first. The local checkout can be behind because scheduled workflows commit directly to `main`.
- Avoid committing from a stale dirty checkout; use a clean worktree or update local state first.

### Recommended follow-up

- Add retry/backoff around `do_search()` so Tavily transient failures do not immediately fail the daily run.
- Log the search query and exception type when Tavily fails, while avoiding API keys or sensitive response details.
- Consider continuing after one failed query if enough other searches succeed to produce a valid report.
- Add a lightweight post-run check that confirms the expected `YYYY-MM-DD/` page is reachable after the workflow completes.
