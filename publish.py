import json
import os
import sys
from string import Template

ROOT = os.path.dirname(os.path.abspath(__file__))
SUMMARIES_PATH = os.path.join(ROOT, "summaries.md")
TEMPLATES_DIR = os.path.join(ROOT, "templates")


def load_template(name: str) -> Template:
    path = os.path.join(TEMPLATES_DIR, name)
    with open(path, encoding="utf-8") as f:
        return Template(f.read())


def parse_summaries() -> list[dict]:
    if not os.path.exists(SUMMARIES_PATH):
        print("Error: summaries.md not found", file=sys.stderr)
        sys.exit(1)

    with open(SUMMARIES_PATH, encoding="utf-8") as f:
        content = f.read()

    entries = []
    blocks = content.split("---\ndate:")
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # block: " 2026-06-06\n---\n{json}"
        first_nl = block.find("\n")
        if first_nl == -1:
            continue
        date_str = block[:first_nl].strip()
        rest = block[first_nl:].strip()
        # skip the closing "---" separator before JSON
        if rest.startswith("---"):
            rest = rest[3:].strip()
        if not rest:
            continue
        try:
            data = json.loads(rest)
        except json.JSONDecodeError as e:
            print(f"Error: malformed JSON for date {date_str}: {e}", file=sys.stderr)
            sys.exit(1)
        entries.append({"date": date_str, "data": data})

    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def render_headlines(headlines: list[str]) -> str:
    items = []
    for h in headlines:
        if ": " in h:
            title, rest = h.split(": ", 1)
            items.append(f"            <li><strong>{title}:</strong> {rest}</li>")
        else:
            items.append(f"            <li>{h}</li>")
    return "\n".join(items)


def render_analysis(text: str) -> str:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]
    return "\n".join(f"          <p>{p}</p>" for p in paragraphs)


def render_sources(sources: list[dict]) -> str:
    items = []
    for s in sources:
        label = s.get("label", "")
        url = s.get("url", "")
        items.append(
            f'            <li><strong>{label}:</strong> '
            f'<a href="{url}" target="_blank" rel="noopener">{url}</a></li>'
        )
    return "\n".join(items)


def render_day_page(entry: dict, template: Template) -> str:
    data = entry["data"]
    return template.substitute(
        date=entry["date"],
        headlines_en=render_headlines(data.get("headlines_en", [])),
        analysis_en=render_analysis(data.get("analysis_en", "")),
        sources_en=render_sources(data.get("sources_en", [])),
        headlines_zh=render_headlines(data.get("headlines_zh", [])),
        analysis_zh=render_analysis(data.get("analysis_zh", "")),
        sources_zh=render_sources(data.get("sources_zh", [])),
    )


def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    entries = parse_summaries()

    if not entries:
        print("Error: summaries.md contains no valid entries", file=sys.stderr)
        sys.exit(1)

    day_template = load_template("day.html")
    index_template = load_template("index.html")
    archive_template = load_template("archive.html")

    # Per-day pages
    for entry in entries:
        html = render_day_page(entry, day_template)
        out_path = os.path.join(ROOT, entry["date"], "index.html")
        write_file(out_path, html)
        print(f"  wrote {entry['date']}/index.html", file=sys.stderr)

    # Today's index page (most recent entry)
    latest = entries[0]
    data = latest["data"]
    index_html = index_template.substitute(
        date=latest["date"],
        headlines_en=render_headlines(data.get("headlines_en", [])),
        analysis_en=data.get("analysis_en", ""),
        sources_en=render_sources(data.get("sources_en", [])),
        headlines_zh=render_headlines(data.get("headlines_zh", [])),
        analysis_zh=data.get("analysis_zh", ""),
        sources_zh=render_sources(data.get("sources_zh", [])),
    )
    write_file(os.path.join(ROOT, "index.html"), index_html)
    print("  wrote index.html", file=sys.stderr)

    # Archive page
    date_links = "\n".join(
        f'        <li><a href="/{e["date"]}/">{e["date"]}</a></li>'
        for e in entries
    )
    archive_html = archive_template.substitute(date_links=date_links)
    write_file(os.path.join(ROOT, "archive.html"), archive_html)
    print("  wrote archive.html", file=sys.stderr)

    print(f"Done. Published {len(entries)} entries.", file=sys.stderr)


if __name__ == "__main__":
    main()
