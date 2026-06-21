from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def test_health_workflow_has_daily_alert_and_recovery_paths(self):
        workflow = (ROOT / ".github/workflows/health.yml").read_text()

        self.assertIn('cron: "30 2 * * *"', workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("python3 health_check.py", workflow)
        self.assertIn("--attempts 3", workflow)
        self.assertIn("github.rest.issues.create", workflow)
        self.assertIn('state: "closed"', workflow)
        self.assertIn("if: steps.health.outcome == 'failure'", workflow)
        self.assertIn("run: exit 1", workflow)

    def test_notion_workflows_use_only_authoritative_sync(self):
        daily = (ROOT / ".github/workflows/daily.yml").read_text()
        manual = (ROOT / ".github/workflows/notion.yml").read_text()

        self.assertEqual(daily.count("python3 notion_sync.py"), 1)
        self.assertEqual(manual.count("python3 notion_sync.py"), 1)
        self.assertNotIn("notion_publish.py", daily)
        self.assertNotIn("notion_publish.py", manual)


if __name__ == "__main__":
    unittest.main()
