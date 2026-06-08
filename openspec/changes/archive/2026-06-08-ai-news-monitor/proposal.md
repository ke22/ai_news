## Why

This project needs an autonomous AI pipeline that monitors daily AI news, synthesizes it into a structured bilingual report, and publishes it to a static site — with no human intervention required after initial setup.

## What Changes

- New Python agent (`agent.py`) that uses Claude as an agentic loop with Tavily as a tool to search for AI news, then produces a structured bilingual (EN + ZH) daily summary
- New publisher (`publish.py`) that reads an append-only `summaries.md` log and regenerates the full static site (today's index, archive listing, and per-day detail pages)
- New shell orchestrator (`run.sh`) that sequences agent → publish → git push
- New GitHub Actions workflow (`.github/workflows/daily.yml`) that triggers `run.sh` on a daily cron schedule
- New static HTML/CSS site with three page types: today's report, archive listing, per-day detail
- New `summaries.md` as the single source of truth — append-only log of all daily outputs

## Capabilities

### New Capabilities

- `news-agent`: Claude-powered agentic loop that autonomously decides search queries (3–10 Tavily calls/day), collects AI news, and produces a structured bilingual JSON output (7 headlines + analysis block + 12–14 sources, in both EN and ZH)
- `site-publisher`: Static site generator that reads `summaries.md` and writes three page types: `/index.html` (today), `/archive.html` (all dates), `/YYYY-MM-DD/index.html` (per-day detail)
- `daily-pipeline`: End-to-end orchestration — agent → publish → git commit + push — scheduled via GitHub Actions cron at 00:00 UTC (08:00 TWN)

### Modified Capabilities

(none)

## Impact

- Affected specs: news-agent, site-publisher, daily-pipeline (all new)
- Affected code:
  - New: agent.py
  - New: publish.py
  - New: run.sh
  - New: summaries.md
  - New: .github/workflows/daily.yml
  - New: templates/index.html
  - New: templates/archive.html
  - New: templates/day.html
  - New: static/style.css
  - New: requirements.txt
