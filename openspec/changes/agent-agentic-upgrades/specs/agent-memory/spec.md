## ADDED Requirements

### Requirement: Agent receives recent source history before each run

Before each run, the agent SHALL receive a `## Recent History` block in its system prompt listing deduplicated source domain hostnames and headline keyword fragments extracted from the last 7 `summaries.md` entries. The instruction SHALL direct the agent to diversify away from these domains and topics.

#### Scenario: Memory context included when history exists

- **WHEN** `summaries.md` contains at least one parseable entry
- **THEN** the rendered system prompt contains a `## Recent History` section with at least one domain listed

##### Example: single prior entry

- **GIVEN** `summaries.md` has one entry with `sources_en` containing `{"label":"Reuters","url":"https://reuters.com/article/abc"}`
- **WHEN** `build_memory_context()` is called
- **THEN** the returned string contains `reuters.com`

### Requirement: Memory context is absent when no history is available

If `summaries.md` is missing, empty, or contains no parseable JSON entries, `build_memory_context()` SHALL return an empty string and the agent run SHALL proceed without a `## Recent History` section.

#### Scenario: Missing file

- **WHEN** `summaries.md` does not exist at the expected path
- **THEN** `build_memory_context()` returns `""` without raising an exception

#### Scenario: Empty file

- **WHEN** `summaries.md` exists but contains no `---\ndate:` blocks
- **THEN** `build_memory_context()` returns `""`

### Requirement: Memory extraction reads at most the last 7 entries

`build_memory_context()` SHALL process at most the last 7 JSON entries from `summaries.md`, regardless of total file length.

#### Scenario: File with more than 7 entries

- **WHEN** `summaries.md` contains 30 entries
- **THEN** `build_memory_context()` produces output referencing only domains from the 7 most recent entries

##### Example: capped at 7

- **GIVEN** 10 entries where entries 1–3 use `old-source.com` and entries 4–10 use `new-source.com`
- **WHEN** `build_memory_context()` is called
- **THEN** the returned string contains `new-source.com` and does NOT contain `old-source.com`
