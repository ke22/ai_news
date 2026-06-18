# Notion Sync Handoff

## What Changed

- Added `notion_sync.py` to publish the latest report from `summaries.md` into the Notion database `AI News Reports`.
- Added a `Sync Notion` step after `publish.py` in `.github/workflows/daily.yml`.
- Added the same sync step to local `run.sh`.
- Added `NOTION_TOKEN` and `NOTION_DATABASE_ID` to `.env.example`.

## Runtime Flow

1. `agent.py` generates a daily AI news report and appends it to `summaries.md`.
2. `publish.py` regenerates the static site.
3. `notion_sync.py` selects the latest report date and latest run for that date.
4. `notion_sync.py` checks whether a Notion page named `YYYY-MM-DD AI News` already exists.
5. If no page exists, it creates one Notion database entry with English and Traditional Chinese sections.

## Required Setup

- Create a Notion integration and copy its internal integration token.
- Share the target Notion database with that integration.
- Add GitHub repository secret `NOTION_TOKEN`.
- Optional: add repository variable `NOTION_DATABASE_ID` to override the default database ID.

Default database:

```text
38335900ea068066b483ff3b73399962
```

## Local Commands

Dry-run without calling Notion:

```bash
python3 notion_sync.py --dry-run
```

Sync latest report when `NOTION_TOKEN` is available:

```bash
python3 notion_sync.py
```

Sync a specific date:

```bash
python3 notion_sync.py --date 2026-06-17
```

## Learning

The daily report generation still consumes Gemini API tokens through `agent.py`. The Notion sync does not call an LLM; it only reads local JSON from `summaries.md` and calls the Notion REST API, so it does not add AI token cost.

The Notion MCP connector used during development can create pages interactively in this session, but scheduled automation needs a normal Notion integration token because GitHub Actions cannot use the session connector.

## Verification

Run:

```bash
python3 -m py_compile notion_sync.py publish.py agent.py manage.py
python3 notion_sync.py --dry-run
```

Expected dry-run output should name the latest report and target Notion database.
