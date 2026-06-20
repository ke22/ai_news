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
            print(f"Error: malformed JSON for date {date_str}: {e}", file=sys.stderr)
            sys.exit(1)
        entries.append({"date": date_str, "data": data})

    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def group_entries(entries: list[dict]) -> tuple[list[str], dict[str, list[dict]]]:
    """Group entries by date preserving newest-date-first order.
    Within each date, entries are in summaries.md order (oldest run first)."""
    groups: dict[str, list[dict]] = {}
    date_order: list[str] = []
    for entry in entries:
        d = entry["date"]
        if d not in groups:
            groups[d] = []
            date_order.append(d)
        groups[d].append(entry)
    return date_order, groups


def render_headlines(headlines: list[str]) -> str:
    items = []
    for h in headlines:
        h = h.replace("**", "").strip()
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
            f'<li>{label}: '
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


def _first_headline(data: dict, lang: str) -> str:
    headlines = data.get(f"headlines_{lang}", [])
    if not headlines:
        return ""
    h = headlines[0].replace("**", "").strip()
    if ": " in h:
        title, _ = h.split(": ", 1)
    else:
        title = h
    return title[:65] + "…" if len(title) > 65 else title


def render_archive_items(date_order: list[str], groups: dict[str, list[dict]], lang: str) -> str:
    items = []
    for date_str in date_order:
        date_entries = groups[date_str]
        n = len(date_entries)
        # Newest run first
        for i, entry in enumerate(reversed(date_entries)):
            orig_idx = n - 1 - i  # position in date_entries (0 = oldest)
            is_canonical = orig_idx == n - 1
            link = f"{date_str}/" if is_canonical else f"{date_str}/run-{orig_idx + 1}.html"
            run_label = "" if is_canonical else f"run {orig_idx + 1}"
            title = _first_headline(entry["data"], lang)
            badge = f'<span class="run-badge">{run_label}</span>' if run_label else ""
            css_class = "archive-item archive-item--prev" if not is_canonical else "archive-item"
            items.append(
                f'<li class="{css_class}">'
                f'<span class="archive-date-col"><a href="{link}">{date_str}</a>{badge}</span>'
                f'<span class="archive-preview">{title}</span>'
                f'</li>'
            )
    return "\n          ".join(items)


def write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    entries = parse_summaries()

    if not entries:
        print("Error: summaries.md contains no valid entries", file=sys.stderr)
        sys.exit(1)

    date_order, groups = group_entries(entries)

    day_template = load_template("day.html")
    index_template = load_template("index.html")
    archive_template = load_template("archive.html")
    about_template = load_template("about.html")

    # Per-date pages: oldest runs → run-N.html, newest run → index.html
    for date_str in date_order:
        date_entries = groups[date_str]
        n = len(date_entries)
        for orig_idx, entry in enumerate(date_entries):
            html = render_day_page(entry, day_template)
            if orig_idx == n - 1:
                out_path = os.path.join(ROOT, date_str, "index.html")
                label = "index.html"
            else:
                fname = f"run-{orig_idx + 1}.html"
                out_path = os.path.join(ROOT, date_str, fname)
                label = fname
            write_file(out_path, html)
            print(f"  wrote {date_str}/{label}", file=sys.stderr)

    # Homepage = most recent date, most recent run
    latest = groups[date_order[0]][-1]
    data = latest["data"]
    index_html = index_template.substitute(
        date=latest["date"],
        headlines_en=render_headlines(data.get("headlines_en", [])),
        analysis_en=render_analysis(data.get("analysis_en", "")),
        sources_en=render_sources(data.get("sources_en", [])),
        headlines_zh=render_headlines(data.get("headlines_zh", [])),
        analysis_zh=render_analysis(data.get("analysis_zh", "")),
        sources_zh=render_sources(data.get("sources_zh", [])),
    )
    write_file(os.path.join(ROOT, "index.html"), index_html)
    print("  wrote index.html", file=sys.stderr)

    # Archive page
    archive_html = archive_template.substitute(
        archive_items_en=render_archive_items(date_order, groups, "en"),
        archive_items_zh=render_archive_items(date_order, groups, "zh"),
    )
    write_file(os.path.join(ROOT, "archive.html"), archive_html)
    print("  wrote archive.html", file=sys.stderr)

    # About page (static)
    write_file(os.path.join(ROOT, "about.html"), about_template.template)
    print("  wrote about.html", file=sys.stderr)

    total_runs = sum(len(v) for v in groups.values())
    print(f"Done. {len(date_order)} dates, {total_runs} total runs.", file=sys.stderr)


if __name__ == "__main__":
    main()
