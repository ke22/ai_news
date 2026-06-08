## 1. Project Setup

- [x] 1.1 Create `requirements.txt` listing `anthropic`, `tavily-python`, and `python-dotenv`. Verify: `pip install -r requirements.txt` completes without error.
- [x] 1.2 Create `.env.example` with placeholder keys `ANTHROPIC_API_KEY=` and `TAVILY_API_KEY=` and add `.env` to `.gitignore`. Verify: `.env` is absent from `git status` output after creating a local `.env` file.
- [x] 1.3 Create an empty `summaries.md` committed to the repo. Verify: file exists at repo root and `git ls-files summaries.md` returns it.

## 2. News Agent (agent.py)

- [x] 2.1 Implement the `search` tool definition for Tavily: the function calls `TavilyClient.search(query)` and returns a list of `{title, url, content}` dicts. Verify: calling the tool with query `"OpenAI news"` returns at least one result when `TAVILY_API_KEY` is set.
- [x] 2.2 Implement the `submit_report` tool for structured JSON output via tool use: the tool schema covers `{date, headlines_en[7], analysis_en, sources_en[], headlines_zh[7], analysis_zh, sources_zh[]}`, delivering the requirement "Agent produces structured bilingual output via submit_report tool". Verify: the JSON schema is accepted by the Anthropic SDK tool-definition validator (no SDK exception on instantiation).
- [x] 2.3 Implement Claude as an agentic loop (not a single prompt): send messages to `claude-sonnet-4-6` with both tool definitions, handle `tool_use` blocks by dispatching to the correct tool, and terminate when `stop_reason == "end_turn"`. The loop enforces a maximum of 10 `search` calls; if Claude searches more than 10 times, the loop exits with a RuntimeError. Verify: running `python agent.py` with valid API keys completes and calls `submit_report` exactly once. This satisfies the requirement "Claude searches for AI news autonomously".
- [x] 2.4 Implement `summaries.md` as append-only log: after `submit_report` is called, serialize the tool input as a single-line JSON object and append it with the `---\ndate: YYYY-MM-DD\n---\n{json}` delimiter format. The file is NOT modified if `submit_report` is never called. Verify: after a successful run, `summaries.md` contains a new entry with today's date, and running `python agent.py` a second time on the same day appends a second entry without corrupting the first. This satisfies the requirement "Agent appends output to summaries.md".
- [x] 2.5 Implement failure exit: if Tavily raises an exception or `submit_report` is never called, the agent prints an error to stderr and exits with `sys.exit(1)`. Verify: `python agent.py` with an invalid `TAVILY_API_KEY` exits non-zero and `summaries.md` is unchanged. This satisfies the requirement "Agent exits non-zero on failure".

## 3. Site Publisher (publish.py)

- [x] 3.1 Implement `summaries.md` parser: reads the file, splits on the `---\ndate:` delimiter, and returns a list of `{date, data}` dicts sorted newest-first. Raises a clear error if the file is missing or any entry fails JSON parse. Verify: given a two-entry `summaries.md`, the parser returns two dicts in reverse-chronological order. This satisfies the requirement "Publisher reads summaries.md and generates three page types".
- [x] 3.2 Create `templates/index.html` and `templates/day.html` for static HTML via Python string templates: HTML files with `${}` placeholder slots for date, EN headlines, EN analysis, EN sources, ZH headlines, ZH analysis, ZH sources, and a nav bar linking to `/archive.html`. Verify: the template files contain no hardcoded news content and all required placeholder slots are present.
- [x] 3.3 Create `templates/archive.html`: HTML template with a placeholder for a list of date links. Verify: template contains a placeholder for the date list.
- [x] 3.4 Create `static/style.css`: minimal stylesheet (font, spacing, max-width, headline bold). Verify: page renders readable in a browser with the stylesheet linked.
- [x] 3.5 Implement `index.html` generation: render the latest entry using `templates/index.html` and write to `index.html` at repo root. Verify: `python publish.py` writes `index.html` containing the 7 EN headlines from the most recent `summaries.md` entry. This satisfies the requirement "Today's report page shows all required sections in both languages".
- [x] 3.6 Implement per-day page generation: for each entry, create directory `YYYY-MM-DD/` if absent and write `YYYY-MM-DD/index.html` using `templates/day.html`. Verify: after running `publish.py` with two entries, `2026-06-06/index.html` and `2026-06-07/index.html` both exist. This satisfies the requirement "Per-day detail pages use date-based URL paths".
- [x] 3.7 Implement `archive.html` generation: render all dates newest-first as `<a href="/YYYY-MM-DD/">YYYY-MM-DD</a>` items and write to `archive.html`. Verify: `archive.html` lists dates in reverse-chronological order as clickable links. This satisfies the requirement "Archive page lists all dates newest-first as links".
- [x] 3.8 Implement failure exit: if `summaries.md` is missing or any entry is malformed, print to stderr and exit non-zero before writing any output files. Verify: `python publish.py` with no `summaries.md` exits non-zero with an error message. This satisfies the requirement "Publisher exits non-zero if summaries.md is missing or malformed".

## 4. Pipeline Orchestration (run.sh)

- [x] 4.1 Create `run.sh` with `set -e` and steps: `python agent.py`, `python publish.py`, `git add -A`, `git commit -m "Daily update $(date +%Y-%m-%d)"`, `git push`. Verify: running `bash run.sh` locally with valid API keys and a clean git state completes all five steps, producing a new git commit. This satisfies the requirements "Pipeline steps execute in strict order with failure propagation" and "Pipeline can be run locally for testing".

## 5. GitHub Actions Workflow

- [x] 5.1 Set up GitHub Actions for scheduling: create `.github/workflows/daily.yml` with `schedule: cron: '0 0 * * *'`, job running on `ubuntu-latest` with Python 3.12, steps: checkout (with `persist-credentials: true`), `pip install -r requirements.txt`, `python agent.py`, `python publish.py`, git config + commit + push. Inject `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` from repository secrets as `env:` on the job. Verify: YAML is valid (`python -c "import yaml; yaml.safe_load(open('.github/workflows/daily.yml'))"`) and both secret references are present. This satisfies the requirements "GitHub Actions triggers the pipeline daily at 00:00 UTC" and "Secrets are injected via GitHub Actions environment variables".
- [x] 5.2 Configure GitHub repository: enable GitHub Pages from the `main` branch root, and add `ANTHROPIC_API_KEY` and `TAVILY_API_KEY` as repository secrets. Verify: after a manual workflow trigger, the Actions run completes and the site is accessible at `https://<username>.github.io/<repo>/`.

## 6. End-to-End Validation

- [x] 6.1 Run a full local test: `bash run.sh` with real API keys. Open `index.html` in a browser and confirm 7 EN headlines, EN analysis, EN sources, and the same three sections in ZH are all present and non-empty. This validates the full pipeline end-to-end.
- [x] 6.2 Trigger the GitHub Actions workflow manually (Actions → daily → Run workflow). Confirm the run succeeds and GitHub Pages updates within 5 minutes. This validates the deployment pipeline.
