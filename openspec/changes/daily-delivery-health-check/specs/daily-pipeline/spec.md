## ADDED Requirements

### Requirement: Daily pipeline uses one authoritative Notion synchronization path

The scheduled daily workflow and the manual Notion workflow SHALL invoke `notion_sync.py`. The daily workflow SHALL NOT invoke the legacy `notion_publish.py` path after synchronization.

#### Scenario: Daily report is synchronized once

- **WHEN** the daily workflow reaches its Notion delivery step
- **THEN** it runs `python3 notion_sync.py` exactly once and does not run `python3 notion_publish.py`

#### Scenario: Manual Notion synchronization

- **WHEN** the manual Notion workflow is dispatched
- **THEN** it runs `python3 notion_sync.py` for the latest report
