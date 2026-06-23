## Why

AI News readers can discover topics but cannot continue into deeper research without leaving the report and manually finding the separate agent console.

## What Changes

- Add one global Deep Research launcher to the homepage and dated report pages.
- Open the production agent-console `/embed` route in a fixed desktop panel and full-screen mobile sheet.
- Preserve the iframe while hidden or minimized so active SSE research continues.
- Synchronize the current EN/ZH page language and provide an external-console fallback when embedding fails.

## Non-Goals

- Per-headline research actions or automatic page context transfer.
- Assistant access on Archive or About pages.
- Draggable or resizable window behavior.

## Capabilities

### New Capabilities

- `floating-research-assistant`: Accessible floating access from AI News reports to the embeddable deep-research console.

### Modified Capabilities

(none)

## Impact

- Affected specs: `floating-research-assistant`
- Affected code:
  - Modified: `templates/index.html`, `templates/day.html`, `static/main.js`, `static/style.css`, `tests/test_workflows.py`
  - New: `tests/test_assistant.py`
  - Removed: none
