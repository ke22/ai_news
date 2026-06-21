#!/usr/bin/env python3
"""Verify that the expected daily AI news report is publicly available."""

from __future__ import annotations

import argparse
import html
import os
import sys
import time
from datetime import datetime
from urllib import error, request
from zoneinfo import ZoneInfo

DEFAULT_SITE_BASE_URL = "https://ke22.github.io/ai_news"
DEFAULT_TIMEZONE = "Asia/Taipei"


class HealthCheckError(RuntimeError):
    pass


def taipei_date() -> str:
    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date().isoformat()


def report_url(site_base_url: str, report_date: str) -> str:
    return f"{site_base_url.rstrip('/')}/{report_date}/"


def fetch_page(url: str, timeout: float) -> str:
    req = request.Request(
        url,
        headers={"User-Agent": "ai-news-health-check/1.0"},
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            status = getattr(response, "status", response.getcode())
            if status != 200:
                raise HealthCheckError(f"{url} returned HTTP {status}")
            return response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        raise HealthCheckError(f"{url} returned HTTP {exc.code}") from exc
    except error.URLError as exc:
        raise HealthCheckError(f"{url} request failed: {exc.reason}") from exc


def validate_report(page_html: str, report_date: str) -> None:
    normalized = html.unescape(page_html)
    expected_heading = f"{report_date} — AI News Summary"
    if expected_heading not in normalized:
        raise HealthCheckError(
            f"page does not contain expected heading: {expected_heading}"
        )


def check_report(
    site_base_url: str,
    report_date: str,
    attempts: int = 3,
    delay_seconds: float = 60,
    timeout: float = 20,
    *,
    fetch=fetch_page,
    sleep=time.sleep,
) -> tuple[str, int]:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")

    url = report_url(site_base_url, report_date)
    last_error: HealthCheckError | None = None

    for attempt in range(1, attempts + 1):
        try:
            validate_report(fetch(url, timeout), report_date)
            return url, attempt
        except HealthCheckError as exc:
            last_error = exc
            if attempt < attempts:
                sleep(delay_seconds)

    raise HealthCheckError(
        f"report remained unhealthy after {attempts} attempt(s): {last_error}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that the expected daily AI news report is published."
    )
    parser.add_argument("--date", default=taipei_date(), help="Expected YYYY-MM-DD date")
    parser.add_argument(
        "--site-base-url",
        default=os.environ.get("SITE_BASE_URL", DEFAULT_SITE_BASE_URL),
    )
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--delay-seconds", type=float, default=60)
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args()

    try:
        url, attempt = check_report(
            args.site_base_url,
            args.date,
            attempts=args.attempts,
            delay_seconds=args.delay_seconds,
            timeout=args.timeout,
        )
    except (HealthCheckError, ValueError) as exc:
        print(f"UNHEALTHY: {exc}", file=sys.stderr)
        return 1

    print(f"HEALTHY: {url} validated on attempt {attempt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
