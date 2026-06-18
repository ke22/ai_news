import json
import os
import sys
from urllib import error, request

from dotenv import load_dotenv

load_dotenv()

ROOT = os.path.dirname(os.path.abspath(__file__))
SUMMARIES_PATH = os.path.join(ROOT, "summaries.md")
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://ke22.github.io/ai_news").rstrip("/")
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def parse_summaries() -> list[dict]:
    if not os.path.exists(SUMMARIES_PATH):
        raise RuntimeError("summaries.md not found")

    with open(SUMMARIES_PATH, encoding="utf-8") as f:
        content = f.read()

    entries = []
    for block in content.split("---\ndate:"):
        block = block.strip()
        if not block:
            continue
        first_nl = block.find("\n")
        if first_nl == -1:
            continue
        date_str = block[:first_nl].strip()
        rest = block[first_nl:].strip()
        if rest.startswith("---"):
            rest = rest[3:].strip()
        if not rest:
            continue
        try:
            data = json.loads(rest)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"malformed JSON for date {date_str}: {e}") from e
        entries.append({"date": date_str, "data": data})

    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def rich_text(text: str, href: str | None = None) -> list[dict]:
    text = text[:2000]
    item = {"type": "text", "text": {"content": text}}
    if href:
        item["text"]["link"] = {"url": href}
    return [item]


def paragraph(text: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_text(text)}}


def heading(text: str, level: int = 2) -> dict:
    block_type = f"heading_{level}"
    return {"object": "block", "type": block_type, block_type: {"rich_text": rich_text(text)}}


def bulleted_item(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rich_text(text)},
    }


def source_item(source: dict) -> dict:
    label = str(source.get("label", "")).strip() or "Source"
    url = str(source.get("url", "")).strip()
    text = f"{label}: {url}" if url else label
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rich_text(text, url or None)},
    }


def chunk_blocks(blocks: list[dict], size: int = 90) -> list[list[dict]]:
    return [blocks[i : i + size] for i in range(0, len(blocks), size)]


def latest_report() -> dict:
    entries = parse_summaries()
    if not entries:
        raise RuntimeError("summaries.md contains no valid entries")
    return entries[0]


def notion_request(method: str, path: str, payload: dict, token: str) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{NOTION_API_BASE}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        },
    )

    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion API {method} {path} failed: HTTP {e.code}: {body}") from e
    except error.URLError as e:
        raise RuntimeError(f"Notion API {method} {path} failed: {e}") from e


def build_page_payload(entry: dict, database_id: str) -> tuple[dict, list[dict]]:
    date_str = entry["date"]
    data = entry["data"]
    page_url = f"{SITE_BASE_URL}/{date_str}/"
    title = f"AI News {date_str}"

    children = [
        paragraph(f"Published report: {page_url}"),
        heading("English Headlines"),
        *[bulleted_item(h.replace("**", "")) for h in data.get("headlines_en", [])],
        heading("English Analysis"),
        *[paragraph(p.strip()) for p in data.get("analysis_en", "").split("\n\n") if p.strip()],
        heading("Traditional Chinese Headlines"),
        *[bulleted_item(h.replace("**", "")) for h in data.get("headlines_zh", [])],
        heading("Traditional Chinese Analysis"),
        *[paragraph(p.strip()) for p in data.get("analysis_zh", "").split("\n\n") if p.strip()],
        heading("Sources"),
        heading("English Sources", 3),
        *[source_item(s) for s in data.get("sources_en", [])],
        heading("Traditional Chinese Sources", 3),
        *[source_item(s) for s in data.get("sources_zh", [])],
    ]

    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": rich_text(title)},
            "Date": {"date": {"start": date_str}},
            "URL": {"url": page_url},
        },
        "children": children[:90],
    }
    return payload, children[90:]


def append_children(page_id: str, blocks: list[dict], token: str) -> None:
    for chunk in chunk_blocks(blocks):
        notion_request("PATCH", f"/blocks/{page_id}/children", {"children": chunk}, token)


def main() -> None:
    token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    if not token or not database_id:
        print("Notion publishing skipped: NOTION_TOKEN or NOTION_DATABASE_ID not set", file=sys.stderr)
        return

    entry = latest_report()
    payload, remaining_children = build_page_payload(entry, database_id)
    page = notion_request("POST", "/pages", payload, token)
    if remaining_children:
        append_children(page["id"], remaining_children, token)

    print(f"Published {entry['date']} report to Notion page {page['id']}", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
