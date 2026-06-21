import unittest

from health_check import HealthCheckError, check_report, report_url, validate_report


REPORT_DATE = "2026-06-21"
HEALTHY_HTML = f"<html><h2>{REPORT_DATE} — AI News Summary</h2></html>"


class HealthCheckTests(unittest.TestCase):
    def test_report_url_normalizes_trailing_slash(self):
        self.assertEqual(
            report_url("https://example.test/news/", REPORT_DATE),
            "https://example.test/news/2026-06-21/",
        )

    def test_validate_report_accepts_expected_heading(self):
        validate_report(HEALTHY_HTML, REPORT_DATE)

    def test_validate_report_rejects_stale_page(self):
        with self.assertRaisesRegex(HealthCheckError, "expected heading"):
            validate_report(
                "<html><h2>2026-06-20 — AI News Summary</h2></html>",
                REPORT_DATE,
            )

    def test_check_report_stops_after_retry_success(self):
        responses = iter(
            [
                "<html><h2>2026-06-20 — AI News Summary</h2></html>",
                HEALTHY_HTML,
            ]
        )
        sleeps = []

        url, attempt = check_report(
            "https://example.test/news",
            REPORT_DATE,
            attempts=3,
            delay_seconds=5,
            fetch=lambda _url, _timeout: next(responses),
            sleep=sleeps.append,
        )

        self.assertEqual(url, "https://example.test/news/2026-06-21/")
        self.assertEqual(attempt, 2)
        self.assertEqual(sleeps, [5])

    def test_check_report_fails_after_all_attempts(self):
        calls = []
        sleeps = []

        def stale_fetch(_url, _timeout):
            calls.append(True)
            return "<html><h2>2026-06-20 — AI News Summary</h2></html>"

        with self.assertRaisesRegex(HealthCheckError, "after 3 attempt"):
            check_report(
                "https://example.test/news",
                REPORT_DATE,
                attempts=3,
                delay_seconds=5,
                fetch=stale_fetch,
                sleep=sleeps.append,
            )

        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, [5, 5])

    def test_check_report_rejects_invalid_attempt_count(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            check_report(
                "https://example.test/news",
                REPORT_DATE,
                attempts=0,
            )


if __name__ == "__main__":
    unittest.main()
