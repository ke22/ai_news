## ADDED Requirements

### Requirement: Health checker validates the expected daily page

`health_check.py` SHALL derive the expected report date in `Asia/Taipei` unless an explicit date is provided. It SHALL request `{SITE_BASE_URL}/{YYYY-MM-DD}/` and SHALL exit successfully only when the response is HTTP 200 and contains the same date together with the English report heading marker.

#### Scenario: Current report is healthy

- **WHEN** the expected page returns HTTP 200 and contains `YYYY-MM-DD` with `AI News Summary`
- **THEN** the checker exits with status 0 and prints a healthy result

#### Scenario: Report is missing or stale

- **WHEN** the page request fails, returns a non-success response, or lacks the expected date marker
- **THEN** the checker exits non-zero and prints the reason to standard error

### Requirement: Health checker retries transient publication delays

The checker SHALL support a configurable positive attempt count and delay. It SHALL stop immediately after the first successful validation and SHALL fail only after all configured attempts are exhausted.

#### Scenario: Later attempt succeeds

- **WHEN** the first request fails and a later configured attempt validates the expected page
- **THEN** the checker exits with status 0 without performing remaining attempts

### Requirement: Scheduled health workflow alerts through GitHub

`.github/workflows/health.yml` SHALL run daily after the normal publication window. On an unhealthy result it SHALL open or update one issue for the expected date and SHALL finish with a failed workflow conclusion. On a healthy result it SHALL close an existing open health issue for that date.

#### Scenario: Daily report is unhealthy

- **WHEN** the scheduled health job exhausts checker retries without validating the report
- **THEN** one GitHub issue identifies the missing date and workflow run, and the workflow is marked failed

#### Scenario: Daily report recovers

- **WHEN** a later health run validates the date and an open issue exists for that date
- **THEN** the workflow closes that issue and completes successfully
