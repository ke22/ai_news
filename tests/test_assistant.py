from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EMBED_ORIGIN = "https://agent-console.ke2211975.workers.dev"


class ReportLauncherTests(unittest.TestCase):
    """Requirement: Report pages expose one global research launcher."""

    def test_report_templates_opt_in(self):
        index_tpl = (ROOT / "templates/index.html").read_text()
        day_tpl = (ROOT / "templates/day.html").read_text()
        self.assertIn("<main data-research-assistant>", index_tpl)
        self.assertIn("<main data-research-assistant>", day_tpl)

    def test_non_report_templates_stay_out(self):
        archive_tpl = (ROOT / "templates/archive.html").read_text()
        about_tpl = (ROOT / "templates/about.html").read_text()
        self.assertNotIn("data-research-assistant", archive_tpl)
        self.assertNotIn("data-research-assistant", about_tpl)

    def test_script_gates_on_marker(self):
        script = (ROOT / "static/main.js").read_text()
        self.assertIn("querySelector('[data-research-assistant]')", script)
        self.assertIn("assistant = createAssistant()", script)


class AssistantWindowTests(unittest.TestCase):
    """Requirement: Assistant window preserves active research."""

    def setUp(self):
        self.script = (ROOT / "static/main.js").read_text()

    def test_single_iframe_creation_guard(self):
        # ensureIframe returns early once an iframe exists, so it is created at
        # most once per page load.
        self.assertIn("function ensureIframe()", self.script)
        self.assertIn("if (iframe) {", self.script)
        self.assertEqual(self.script.count("document.createElement('iframe')"), 1)

    def test_close_and_minimize_hide_without_removing_iframe(self):
        self.assertIn("minimize.addEventListener('click', hide)", self.script)
        self.assertIn("close.addEventListener('click', hide)", self.script)
        self.assertIn("panel.hidden = true", self.script)
        # The iframe is never removed from the DOM.
        self.assertNotIn("removeChild", self.script)
        self.assertNotIn("iframe.remove()", self.script)


class AssistantLanguageTests(unittest.TestCase):
    """Requirement: Assistant follows page language securely."""

    def setUp(self):
        self.script = (ROOT / "static/main.js").read_text()

    def test_language_message_targets_exact_origin(self):
        self.assertIn("var PROD_ORIGIN = '%s';" % EMBED_ORIGIN, self.script)
        # EMBED_ORIGIN resolves to exactly one origin per environment.
        self.assertIn("var EMBED_ORIGIN = consoleOrigin();", self.script)
        self.assertIn("{ type: 'ai-news:language', language: currentLang },", self.script)
        self.assertIn("EMBED_ORIGIN\n        );", self.script)
        # The language message must never be broadcast to a wildcard origin.
        self.assertNotIn(", '*')", self.script)

    def test_local_dev_uses_local_console(self):
        # Localhost AI News frames the local console dev server; production uses
        # the deployed Worker.
        self.assertIn("var LOCAL_ORIGIN = 'http://localhost:3100';", self.script)
        self.assertIn("function consoleOrigin()", self.script)
        self.assertIn("location.hostname", self.script)

    def test_language_change_does_not_reload_iframe(self):
        # setLanguage posts a message; it never reassigns iframe.src.
        self.assertIn("setLanguage: function (l) {", self.script)
        self.assertEqual(self.script.count("iframe.src ="), 1)

    def test_no_report_payload_sent(self):
        self.assertNotIn("headlines", self.script)
        self.assertNotIn("sources", self.script)


class AssistantResilienceTests(unittest.TestCase):
    """Requirement: Assistant is accessible and resilient."""

    def setUp(self):
        self.script = (ROOT / "static/main.js").read_text()
        self.styles = (ROOT / "static/style.css").read_text()

    def test_controls_are_labelled(self):
        self.assertIn("'aria-label', 'Open Deep Research assistant'", self.script)
        self.assertIn("'aria-label', 'Minimize Deep Research assistant'", self.script)
        self.assertIn("'aria-label', 'Close Deep Research assistant'", self.script)
        self.assertIn("'aria-label', 'Open Deep Research in a new tab'", self.script)

    def test_escape_closes_and_restores_focus(self):
        self.assertIn("e.key === 'Escape'", self.script)
        self.assertIn("launcher.focus();", self.script)

    def test_iframe_sandbox_scope(self):
        self.assertIn(
            "'allow-scripts allow-forms allow-same-origin allow-downloads allow-popups'",
            self.script,
        )

    def test_load_timeout_reveals_fallback(self):
        self.assertIn("LOAD_TIMEOUT_MS", self.script)
        self.assertIn("loadTimer = setTimeout(", self.script)
        self.assertIn("fallback.hidden = false;", self.script)
        self.assertIn(EMBED_ORIGIN, self.script)

    def test_mobile_full_screen_with_safe_area(self):
        self.assertIn("@media (max-width: 640px)", self.styles)
        self.assertIn("width: 100vw;", self.styles)
        self.assertIn("env(safe-area-inset-top)", self.styles)
        self.assertIn("env(safe-area-inset-bottom)", self.styles)

    def test_desktop_fixed_window(self):
        self.assertIn(".assistant-panel {", self.styles)
        self.assertIn("position: fixed;", self.styles)
        self.assertIn("width: 440px;", self.styles)


if __name__ == "__main__":
    unittest.main()
