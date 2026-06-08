## ADDED Requirements

### Requirement: GitHub Actions triggers the pipeline daily at 00:00 UTC

`.github/workflows/daily.yml` SHALL define a `schedule` trigger with cron `'0 0 * * *'` (00:00 UTC = 08:00 TWN). The workflow SHALL run on `ubuntu-latest` with Python 3.12.

#### Scenario: Workflow runs on schedule

- **WHEN** the GitHub Actions cron fires at 00:00 UTC
- **THEN** the workflow job starts, installs dependencies, and executes the pipeline steps in order

### Requirement: Pipeline steps execute in strict order with failure propagation

`run.sh` (or the workflow steps) SHALL execute in the following order: (1) `python agent.py`, (2) `python publish.py`, (3) `git add -A && git commit -m "Daily update YYYY-MM-DD" && git push`. If any step exits non-zero, subsequent steps SHALL NOT execute and the GitHub Actions run SHALL be marked as failed.

#### Scenario: Agent failure halts pipeline

- **WHEN** `agent.py` exits non-zero (e.g., Tavily unavailable)
- **THEN** `publish.py` is not run, no git commit is made, and the GitHub Actions run is marked failed

#### Scenario: Successful run produces a git commit

- **WHEN** all three steps exit 0
- **THEN** a git commit with the message `Daily update YYYY-MM-DD` is pushed to the repository, and GitHub Pages serves the updated site

##### Example: commit message format

- **GIVEN** the pipeline runs on 2026-06-08
- **WHEN** all steps succeed
- **THEN** the commit message is `Daily update 2026-06-08`

### Requirement: Secrets are injected via GitHub Actions environment variables

The workflow SHALL inject `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` as environment variables from GitHub repository secrets. The Python scripts SHALL read these from `os.environ`. Secrets SHALL NOT be hard-coded in any file.

#### Scenario: Secrets are available to agent.py

- **WHEN** the GitHub Actions workflow runs
- **THEN** `os.environ["ANTHROPIC_API_KEY"]` and `os.environ["TAVILY_API_KEY"]` are non-empty strings accessible to `agent.py`

### Requirement: Pipeline can be run locally for testing

`run.sh` SHALL be executable locally when `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` are set in the shell environment. The local run SHALL produce the same output as the CI run.

#### Scenario: Local execution

- **WHEN** `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` are set in the environment and `bash run.sh` is executed locally
- **THEN** `summaries.md` is updated and the static site files are regenerated
