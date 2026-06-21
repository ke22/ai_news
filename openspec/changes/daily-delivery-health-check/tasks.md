## 1. Health Checker

- [x] 1.1 Implement **Health checker validates the expected daily page** and **Health checker retries transient publication delays** in `health_check.py`, with `tests/test_health_check.py` proving healthy, stale, retry-success, and exhausted-attempt behavior via `python3 -m unittest tests.test_health_check`.

## 2. Scheduled Alerting

- [x] 2.1 Implement **Scheduled health workflow alerts through GitHub** in `.github/workflows/health.yml`, including the post-publication schedule, one issue per date, recovery closure, and final failed conclusion; verify the YAML parses and content assertions cover schedule, permissions, checker invocation, issue handling, and failure propagation.

## 3. Delivery Consolidation

- [x] 3.1 Implement **Daily pipeline uses one authoritative Notion synchronization path** by removing the duplicate legacy daily step and routing the manual workflow through `notion_sync.py`; verify both workflow YAML files parse and neither workflow invokes `notion_publish.py`.

## 4. End-to-End Verification

- [x] 4.1 Run the full local unit suite, compile the modified Python files, validate all workflow YAML files, and run `spectra validate daily-delivery-health-check`; all commands must exit 0 before completion.
