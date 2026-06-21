## 1. Report Integration

- [x] 1.1 Implement **Report pages expose one global research launcher** by adding the report marker and template-level content assertions; verify regenerated homepage and dated pages opt in while Archive and About do not.

## 2. Floating Assistant

- [x] 2.1 Implement **Assistant window preserves active research** and **Assistant follows page language securely** in the shared script and stylesheet; verify one iframe is created, close/minimize retain it, and EN/ZH messages target only the production console origin.
- [x] 2.2 Implement **Assistant is accessible and resilient** with labelled controls, Escape/focus behavior, mobile full-screen layout, iframe sandbox, and timeout fallback; verify automated content/state assertions and browser interaction.

## 3. Verification

- [ ] 3.1 Regenerate the static site, run the Python test suite and Spectra validation, then perform desktop and mobile browser checks against local AI News with the deployed or local embed.
