# site-publisher Specification

## Purpose

TBD - created by archiving change 'ai-news-monitor'. Update Purpose after archive.

## Requirements

### Requirement: Publisher reads summaries.md and generates three page types

`publish.py` SHALL parse `summaries.md` and produce: `/index.html` (today's report), `/archive.html` (all dates, newest first), and `/{YYYY-MM-DD}/index.html` for each past entry. All pages SHALL be regenerated on every run.

#### Scenario: Full site regenerated from summaries.md

- **WHEN** `python publish.py` is executed with a `summaries.md` containing N entries
- **THEN** `index.html`, `archive.html`, and N `YYYY-MM-DD/index.html` files are written

##### Example: two entries

- **GIVEN** `summaries.md` contains entries for 2026-06-06 and 2026-06-07
- **WHEN** `publish.py` runs on 2026-06-07
- **THEN** the following files are written: `index.html` (2026-06-07 content), `archive.html` (links to both dates newest first), `2026-06-06/index.html`, `2026-06-07/index.html`


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
### Requirement: Today's report page shows all required sections in both languages

The `/index.html` page SHALL display: 7 EN headlines (bold title + summary sentence each), an EN analysis block, 12–14 EN sources as links, then the same three sections in ZH.

#### Scenario: today page renders complete content

- **WHEN** a browser opens `/index.html`
- **THEN** the page contains 7 EN headline items, an EN analysis paragraph, at least 12 EN source links, 7 ZH headline items, a ZH analysis paragraph, and at least 12 ZH source links


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
### Requirement: Archive page lists all dates newest-first as links

`/archive.html` SHALL list every date in `summaries.md` in reverse-chronological order. Each date SHALL be a hyperlink to `/{YYYY-MM-DD}/`.

#### Scenario: Archive ordering

- **GIVEN** entries for 2026-06-06 and 2026-06-07 exist
- **WHEN** `/archive.html` is rendered
- **THEN** 2026-06-07 appears before 2026-06-06 in the list


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
### Requirement: Per-day detail pages use date-based URL paths

Each daily entry SHALL be published at `/{YYYY-MM-DD}/index.html`. The directory SHALL be created by `publish.py` if it does not exist.

#### Scenario: Directory created for new date

- **WHEN** `publish.py` processes an entry for a date with no existing directory
- **THEN** the directory `{YYYY-MM-DD}/` is created and `{YYYY-MM-DD}/index.html` is written


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
### Requirement: Publisher exits non-zero if summaries.md is missing or malformed

If `summaries.md` does not exist or contains an entry that cannot be parsed, `publish.py` SHALL print an error message to stderr and exit with a non-zero status code. Partial output SHALL NOT be committed by the pipeline.

#### Scenario: Missing summaries.md

- **WHEN** `python publish.py` is run and `summaries.md` does not exist
- **THEN** publish.py exits non-zero with an error message on stderr

<!-- @trace
source: ai-news-monitor
updated: 2026-06-08
code:
  - .github/workflows/daily.yml
  - requirements.txt
  - .env.example
  - agent.py
-->