#!/usr/bin/env python3
"""Sync the latest AI news report from summaries.md into Notion."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib import error, request

from dotenv import load_dotenv

from publish import parse_summaries

load_dotenv()

DEFAULT_NOTION_DATABASE_ID = "38335900ea068066b483ff3b73399962"
NOTION_VERSION = "2022-06-28"
MAX_RICH_TEXT_CHARS = 1900


class NotionError(RuntimeError):
    pass


def _token() -> str | None:
    return os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")


def _database_id() -> str:
    return os.environ.get("NOTION_DATABASE_ID") or DEFAULT_NOTION_DATABASE_ID


def notion_request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    token = _token()
    if not token:
        raise NotionError("NOTION_TOKEN is not set")

    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    req = request.Request(
        f"https://api.notion.com/v1{path}",
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        },
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise NotionError(f"Notion API {e.code}: {detail}") from e
    except error.URLError as e:
        raise NotionError(f"Notion API request failed: {e.reason}") from e

    return json.loads(raw) if raw else {}


def select_entry(date: str | None) -> dict[str, Any]:
    entries = parse_summaries()
    if not entries:
        raise RuntimeError("No entries found in summaries.md")

    if date is None or date == "latest":
        latest_date = entries[0]["date"]
        matches = [entry for entry in entries if entry["date"] == latest_date]
        return matches[-1]

    matches = [entry for entry in entries if entry["date"] == date]
    if not matches:
        raise RuntimeError(f"No report found for date {date}")
    return matches[-1]


def report_title(entry: dict[str, Any]) -> str:
    return f"{entry['date']} AI News"


def existing_page(title: str) -> str | None:
    payload = {
        "filter": {
            "property": "Name",
            "title": {
                "equals": title,
            },
        },
        "page_size": 1,
    }
    result = notion_request("POST", f"/databases/{_database_id()}/query", payload)
    results = result.get("results", [])
    if not results:
        return None
    return results[0].get("url")


def rich_text(content: str, href: str | None = None) -> list[dict[str, Any]]:
    text: dict[str, Any] = {"content": content[:MAX_RICH_TEXT_CHARS]}
    if href:
        text["link"] = {"url": href}
    return [{"type": "text", "text": text}]


def block(block_type: str, text: str, href: str | None = None) -> dict[str, Any]:
    return {
        "object": "block",
        "type": block_type,
        block_type: {"rich_text": rich_text(text, href)},
    }


def paragraph_chunks(text: str) -> list[dict[str, Any]]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()] or [text.strip()]
    return [block("paragraph", p) for p in paragraphs if p]


def source_blocks(sources: list[dict[str, str]]) -> list[dict[str, Any]]:
    items = []
    for source in sources:
        label = source.get("label", "").strip() or source.get("url", "").strip()
        url = source.get("url", "").strip()
        if label and url:
            items.append(block("bulleted_list_item", label, url))
    return items


def build_children(entry: dict[str, Any]) -> list[dict[str, Any]]:
    data = entry["data"]
    children: list[dict[str, Any]] = [
        block("heading_2", "English"),
        block("heading_3", "Headlines"),
    ]

    children.extend(block("bulleted_list_item", h.replace("**", "").strip()) for h in data.get("headlines_en", []))
    children.append(block("heading_3", "Analysis"))
    children.extend(paragraph_chunks(data.get("analysis_en", "")))
    children.append(block("heading_3", "Sources"))
    children.extend(source_blocks(data.get("sources_en", [])))

    children.extend([
        block("heading_2", "繁體中文"),
        block("heading_3", "重點新聞"),
    ])
    children.extend(block("bulleted_list_item", h.replace("**", "").strip()) for h in data.get("headlines_zh", []))
    children.append(block("heading_3", "分析"))
    children.extend(paragraph_chunks(data.get("analysis_zh", "")))
    children.append(block("heading_3", "資料來源"))
    children.extend(source_blocks(data.get("sources_zh", [])))

    return children[:100]


def create_page(entry: dict[str, Any]) -> str:
    title = report_title(entry)
    payload = {
        "parent": {"database_id": _database_id()},
        "properties": {
            "Name": {
                "title": rich_text(title),
            },
        },
        "children": build_children(entry),
    }
    result = notion_request("POST", "/pages", payload)
    return result.get("url", "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync an AI news report into Notion.")
    parser.add_argument("--date", default="latest", help="Report date in YYYY-MM-DD format, or latest")
    parser.add_argument("--dry-run", action="store_true", help="Print the target report without calling Notion")
    parser.add_argument("--required", action="store_true", help="Fail instead of skipping when Notion credentials are missing")
    args = parser.parse_args()

    try:
        entry = select_entry(args.date)
        title = report_title(entry)
        if args.dry_run:
            print(f"Would sync {title} to Notion database {_database_id()}")
            return

        if not _token():
            message = "Skipping Notion sync: NOTION_TOKEN is not set"
            if args.required:
                print(message, file=sys.stderr)
                sys.exit(1)
            print(message, file=sys.stderr)
            return

        existing_url = existing_page(title)
        if existing_url:
            print(f"Notion page already exists: {existing_url}", file=sys.stderr)
            return

        url = create_page(entry)
        print(f"Created Notion page: {url}", file=sys.stderr)
    except (RuntimeError, NotionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
