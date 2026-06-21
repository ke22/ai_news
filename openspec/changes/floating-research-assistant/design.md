## Context

Every public AI News page is regenerated from templates and loads `static/main.js`. The launcher must survive regeneration, avoid appearing on non-report pages, and frame a cross-origin Cloudflare Worker without receiving credentials or research output.

## Goals / Non-Goals

**Goals**
- A fixed, accessible desktop panel and full-screen mobile sheet.
- Iframe remains mounted after first open so minimize/close does not stop SSE.
- Current page language is sent to the embed without reloading it.
- Clear fallback when the embed cannot load.

**Non-Goals**
- Topic suggestions, selected-text actions, or headline transfer.
- Parent access to iframe storage or run state.

## Decisions

### Report Marker

`templates/index.html` and `templates/day.html` add `data-research-assistant` to their main report element. `main.js` initializes the launcher only when this marker exists, keeping Archive and About unchanged.

### Fixed Window

Desktop uses a 440px-wide panel capped to the viewport height, anchored bottom-right above a persistent Deep Research launcher. At 640px and below it becomes a full-viewport sheet with safe-area padding. Close and minimize hide but do not remove the iframe.

### Cross-Origin Contract

The iframe URL is `https://agent-console.ke2211975.workers.dev/embed?lang=<en|zh>`. On iframe load and every page language change, the parent sends `{ type: "ai-news:language", language: "en" | "zh" }` to exactly `https://agent-console.ke2211975.workers.dev`.

## Implementation Contract

- Launcher appears on generated home and dated report pages only.
- The iframe is created at most once per page load and remains mounted after close/minimize.
- Panel controls have accessible labels, Escape closes the visible panel, focus returns to the launcher, and mobile content does not overflow.
- Iframe sandbox permits scripts, forms, same-origin storage, downloads, and popups; no broader permissions are added.
- A delayed load timeout exposes an external-console link without destroying the iframe.
