# floating-research-assistant Specification

## Purpose

Let AI News readers launch and continue Deep Research from within a report page via a single floating assistant that embeds the cross-origin agent console, without leaving the report or exposing parent credentials and run state to the embed.

## Requirements

### Requirement: Report pages expose one global research launcher

Generated homepage and dated report pages SHALL display one Deep Research launcher. Archive and About pages SHALL NOT display the launcher.

#### Scenario: Report page initializes assistant
- **WHEN** a page contains the report assistant marker and shared script loads
- **THEN** one accessible launcher is added

#### Scenario: Non-report page remains unchanged
- **WHEN** Archive or About loads without the marker
- **THEN** no launcher or assistant iframe is added


<!-- @trace
source: floating-research-assistant
updated: 2026-06-23
code:
  - 2026-06-18/run-1.html
  - 2026-06-17/index.html
  - 2026-06-08/index.html
  - 2026-06-16/index.html
  - 2026-06-12/index.html
  - 2026-06-14/index.html
  - 2026-06-10/run-1.html
  - 2026-06-09/run-1.html
  - 2026-06-15/index.html
  - 2026-06-09/index.html
  - 2026-06-21/index.html
  - index.html
  - 2026-06-18/index.html
  - 2026-06-19/index.html
  - 2026-06-20/index.html
  - 2026-06-11/index.html
  - 2026-06-10/index.html
  - 2026-06-18/run-2.html
  - 2026-06-08/run-1.html
  - manage.py
  - 2026-06-13/index.html
  - archive.html
-->

---
### Requirement: Assistant window preserves active research

The launcher SHALL open a fixed desktop panel and full-screen mobile sheet containing the production `/embed` iframe. Closing or minimizing SHALL hide the panel without removing or reloading the iframe.

#### Scenario: Reopen preserves iframe
- **WHEN** a user opens, closes, and reopens the assistant
- **THEN** the same iframe element and research session remain mounted


<!-- @trace
source: floating-research-assistant
updated: 2026-06-23
code:
  - 2026-06-18/run-1.html
  - 2026-06-17/index.html
  - 2026-06-08/index.html
  - 2026-06-16/index.html
  - 2026-06-12/index.html
  - 2026-06-14/index.html
  - 2026-06-10/run-1.html
  - 2026-06-09/run-1.html
  - 2026-06-15/index.html
  - 2026-06-09/index.html
  - 2026-06-21/index.html
  - index.html
  - 2026-06-18/index.html
  - 2026-06-19/index.html
  - 2026-06-20/index.html
  - 2026-06-11/index.html
  - 2026-06-10/index.html
  - 2026-06-18/run-2.html
  - 2026-06-08/run-1.html
  - manage.py
  - 2026-06-13/index.html
  - archive.html
-->

---
### Requirement: Assistant follows page language securely

The parent SHALL send only the current `en` or `zh` language message to the exact agent-console origin on iframe load and language changes. It SHALL NOT send topics, credentials, report content, or run output.

#### Scenario: Language toggle updates embed
- **WHEN** the user changes the AI News language
- **THEN** the parent sends the validated language message without changing iframe `src`


<!-- @trace
source: floating-research-assistant
updated: 2026-06-23
code:
  - 2026-06-18/run-1.html
  - 2026-06-17/index.html
  - 2026-06-08/index.html
  - 2026-06-16/index.html
  - 2026-06-12/index.html
  - 2026-06-14/index.html
  - 2026-06-10/run-1.html
  - 2026-06-09/run-1.html
  - 2026-06-15/index.html
  - 2026-06-09/index.html
  - 2026-06-21/index.html
  - index.html
  - 2026-06-18/index.html
  - 2026-06-19/index.html
  - 2026-06-20/index.html
  - 2026-06-11/index.html
  - 2026-06-10/index.html
  - 2026-06-18/run-2.html
  - 2026-06-08/run-1.html
  - manage.py
  - 2026-06-13/index.html
  - archive.html
-->

---
### Requirement: Assistant is accessible and resilient

The panel SHALL provide labelled open, minimize, close, and external-open controls; Escape SHALL close the panel and restore launcher focus. If the iframe does not load within the configured timeout, the panel SHALL display an external-console fallback link.

#### Scenario: Embed load fails
- **WHEN** the iframe load event is not received before timeout
- **THEN** the panel remains usable and presents a link to open the full console in a new tab

<!-- @trace
source: floating-research-assistant
updated: 2026-06-23
code:
  - 2026-06-18/run-1.html
  - 2026-06-17/index.html
  - 2026-06-08/index.html
  - 2026-06-16/index.html
  - 2026-06-12/index.html
  - 2026-06-14/index.html
  - 2026-06-10/run-1.html
  - 2026-06-09/run-1.html
  - 2026-06-15/index.html
  - 2026-06-09/index.html
  - 2026-06-21/index.html
  - index.html
  - 2026-06-18/index.html
  - 2026-06-19/index.html
  - 2026-06-20/index.html
  - 2026-06-11/index.html
  - 2026-06-10/index.html
  - 2026-06-18/run-2.html
  - 2026-06-08/run-1.html
  - manage.py
  - 2026-06-13/index.html
  - archive.html
-->