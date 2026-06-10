## ADDED Requirements

### Requirement: submit_report enforces three quality rules on first submission

On the first call to `submit_report` in any run, Python SHALL evaluate the submitted report against three rules before accepting it:
1. **No homepage URLs**: every URL in `sources_en` and `sources_zh` must have a URL path that is not empty and not `/`
2. **Chinese outlet count**: `sources_zh` must contain at least 2 URLs whose hostname is in the known Chinese outlet list: `ithome.com.tw`, `technews.tw`, `bnext.com.tw`, `36kr.com`, `jiqizhixin.com`, `qbitai.com`, `technews.com.tw`
3. **Source count**: `sources_en` and `sources_zh` must each have between 12 and 14 entries (inclusive)

If all rules pass, the response SHALL be `{"status": "success"}` and the report is accepted.
If any rule fails, the response SHALL be `{"status": "quality_check_failed", "gaps": ["<description>", ...]}` and the loop SHALL continue.

#### Scenario: All rules pass on first submission

- **WHEN** all source URLs have paths, sources_zh has ≥ 2 Chinese outlet URLs, and both source lists have 12–14 entries
- **THEN** `submit_report` responds `{"status": "success"}` and the agent run completes

#### Scenario: Homepage URL detected on first submission

- **WHEN** any source URL has path `/` or empty path (e.g. `https://reuters.com`)
- **THEN** `submit_report` responds `{"status": "quality_check_failed", "gaps": ["Homepage URL detected in sources_en: https://reuters.com"]}` and the loop continues

##### Example: homepage detection

| URL | Path component | Verdict |
|-----|----------------|---------|
| `https://reuters.com` | `` (empty) | FAIL |
| `https://reuters.com/` | `/` | FAIL |
| `https://reuters.com/article/ai-news` | `/article/ai-news` | PASS |

#### Scenario: Insufficient Chinese outlet sources

- **WHEN** `sources_zh` contains fewer than 2 URLs from the known Chinese outlet hostname list
- **THEN** `submit_report` responds `{"status": "quality_check_failed", "gaps": ["Chinese outlet count in sources_zh: 0 (required ≥ 2)"]}` and the loop continues

### Requirement: Second submit_report call is accepted unconditionally

On the second call to `submit_report` in any run, the report SHALL be accepted regardless of quality rule outcomes. The response SHALL be `{"status": "accepted_on_retry"}`.

#### Scenario: Retry accepted unconditionally

- **WHEN** the agent calls `submit_report` a second time (after a prior `quality_check_failed` response)
- **THEN** the report is accepted immediately with `{"status": "accepted_on_retry"}` regardless of URL quality

### Requirement: Quality gaps are recorded in the report JSON

When a run required a retry (second `submit_report` was used), the final report dict SHALL include an `"evaluation_gaps"` key containing the list of gap strings from the first submission's quality check.

#### Scenario: evaluation_gaps present after retry

- **WHEN** the first `submit_report` failed quality checks and the second was accepted
- **THEN** the entry written to `summaries.md` contains `"evaluation_gaps": ["<gap description>", ...]`

#### Scenario: evaluation_gaps absent when first submission passed

- **WHEN** the first `submit_report` passes all quality rules
- **THEN** the entry written to `summaries.md` has no `"evaluation_gaps"` key
