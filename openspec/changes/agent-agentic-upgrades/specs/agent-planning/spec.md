## ADDED Requirements

### Requirement: Agent declares search plan before first search call

The agent SHALL call the `submit_plan` tool before making any `search` tool call. The `submit_plan` tool SHALL accept a `category_queries` object mapping category names to lists of intended query strings.

#### Scenario: Plan submitted before searching

- **WHEN** the agent calls `submit_plan` with a non-empty `category_queries` map
- **THEN** Python responds with `{"status": "received"}` and the plan is stored for inclusion in the final report

##### Example: valid plan submission

- **GIVEN** agent calls `submit_plan` with `{"category_queries": {"Breaking": ["breaking AI news today"], "Viral": ["trending AI social media"]}}`
- **WHEN** `submit_plan` handler executes
- **THEN** response is `{"status": "received"}` and `plan["category_queries"]` is stored

### Requirement: Plan is stored in the final report JSON

When `submit_report` is accepted, the returned report dict SHALL include a `"plan"` key containing the dict received from `submit_plan`.

#### Scenario: Plan persisted in summaries.md

- **WHEN** the agent completes a run with a prior `submit_plan` call
- **THEN** the new entry written to `summaries.md` contains a `"plan"` key with at least one category entry

### Requirement: Missing plan does not block the pipeline

If the agent does not call `submit_plan` before searching, the run SHALL continue normally. The final report JSON SHALL omit the `"plan"` key.

#### Scenario: Agent skips submit_plan

- **WHEN** the agent calls `search` without first calling `submit_plan`
- **THEN** the run completes successfully and the report entry in `summaries.md` has no `"plan"` key
