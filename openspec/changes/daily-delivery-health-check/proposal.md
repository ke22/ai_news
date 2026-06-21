## Why

The daily report can publish successfully without giving the owner a clear delivery signal, and optional delivery failures are currently hidden by `continue-on-error`. A separate post-publication health check is needed so missing or stale reports produce an actionable notification.

## What Changes

- Add a deterministic checker that verifies the expected Taiwan-date report is reachable and contains the matching report marker.
- Add a daily GitHub Actions health workflow that runs after the publication window, retries transient failures, and opens or updates a GitHub issue when unhealthy.
- Mark the health workflow failed after creating the alert so GitHub's native workflow notifications also fire.
- Consolidate Notion delivery on `notion_sync.py` and remove the duplicate optional `notion_publish.py` step from the daily workflow.

## Non-Goals

- Sending success notifications every day.
- Automatically rerunning the news-generation workflow after a failed health check.
- Adding a new external notification provider or secret.

## Capabilities

### New Capabilities

- `delivery-health`: Daily verification and GitHub-native alerting for missing or stale published reports.

### Modified Capabilities

- `daily-pipeline`: Use one authoritative Notion synchronization path without a hidden duplicate publisher failure.

## Impact

- Affected specs: `delivery-health`, `daily-pipeline`
- Affected code:
  - New: `health_check.py`, `tests/test_health_check.py`, `.github/workflows/health.yml`
  - Modified: `.github/workflows/daily.yml`, `.github/workflows/notion.yml`
  - Removed: none
