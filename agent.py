import json
import os
import sys
from datetime import date
from urllib.parse import urlparse

from dotenv import load_dotenv
from google import genai
from google.genai import types
from tavily import TavilyClient

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not set", file=sys.stderr)
    sys.exit(1)
if not TAVILY_API_KEY:
    print("Error: TAVILY_API_KEY not set", file=sys.stderr)
    sys.exit(1)

MAX_SEARCH_CALLS = 20

# gemini-2.0-flash and earlier were retired 2026-06-01; gemini-2.5-flash has a
# confirmed shutdown no earlier than 2026-10-16 and has already returned early
# 404s for some callers. Candidate list + retry avoids a repeat of the
# openclaw notion-sync incident (see 01_Github/LEARNINGS.md #21).
GEMINI_MODEL_CANDIDATES = [
    m.strip()
    for m in os.environ.get("GEMINI_MODEL", "gemini-3.6-flash,gemini-2.5-flash").split(",")
    if m.strip()
]


def _generate_content_with_fallback(client, contents, config):
    last_err = None
    for model in GEMINI_MODEL_CANDIDATES:
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except Exception as e:
            if "404" in str(e) or "NOT_FOUND" in str(e):
                print(f"[gemini] {model} unavailable, trying next candidate: {e}", file=sys.stderr)
                last_err = e
                continue
            raise
    raise RuntimeError(
        f"All Gemini model candidates unavailable ({', '.join(GEMINI_MODEL_CANDIDATES)}): {last_err}"
    )

SYSTEM_PROMPT = """You are an AI news analyst. Research today's most important AI news and produce a structured bilingual daily summary.

{memory_context}

## Fact-Check Thinking Rules
Before writing any headline, claim, or citation, verify it against your search results:
- Only include headlines and facts that appear in retrieved articles. Do not invent or assume company names, product names, numbers, or events.
- Every source URL must be the exact article URL returned by a search result — never a homepage (e.g. never https://reuters.com, always the full article path).
- If a claim cannot be confirmed from search results, omit it entirely. Do not fill gaps with general knowledge or plausible-sounding content.
- Headlines must reflect actual content found — not extrapolated trends or assumptions.

## Search Scope
Run searches in two passes. Total 8 to 15 searches.

**Before searching**: Call `submit_plan` with your intended queries per category. Example: `{{"category_queries": {{"Breaking": ["breaking AI news today"], "Daily": ["AI news June 2025"]}}}}`. Then begin your `search` calls.

**English pass (5–10 searches)** — cover each of these five categories:
- 當日 (Daily): Today's general AI news — model updates, product launches, company news. Prioritize TechCrunch (techcrunch.com), The Verge (theverge.com), Axios (axios.com)
- Breaking: Urgent or just-announced AI news today. Prioritize the labs' own announcements: OpenAI (openai.com), Anthropic (anthropic.com), Google DeepMind (deepmind.google)
- High-Impact: AI news with major implications for industry, economy, or society. Prioritize McKinsey & Company (mckinsey.com), a16z (a16z.com)
- Viral: AI stories trending or widely discussed on social media today
- Unusual: Surprising, counterintuitive, or unexpected AI developments

**Chinese-language pass (3–5 searches)** — run these queries to surface Asian and Taiwan AI news that English searches miss. Prioritize results from: iThome (ithome.com.tw), 科技新報 (technews.tw), 數位時代 (bnext.com.tw), 36氪 (36kr.com), 机器之心 (jiqizhixin.com), 愛好 AI 工程 Blog (blog.aihao.tw):
- "AI 模型 發布 今日 2025"
- "人工智慧 企業 投資 亞洲 最新"
- "AI 政策 法規 台灣 日本 新加坡"
- "AI 新創 融資 亞洲 本週"
- Add 1 follow-up query based on what you find

## Report Guideline
When you have enough information, call `submit_report` with:
- Exactly 7 English headlines (format: "Bold Title: one-sentence summary"). The 7 headlines must collectively span the five categories above — aim for at least one headline per category, prioritizing diversity.
- A ~280-word English analysis covering 2 key themes
- 12 to 14 English source citations (label + exact article URL from search results)
- Exactly 7 Traditional Chinese headlines covering the same 7 stories
- A ~280-word Traditional Chinese analysis covering the same themes
- 12 to 14 Traditional Chinese source citations (label + exact article URL from search results). Include at least 2 sources from Chinese-language outlets found in the Chinese-language search pass.

Write Chinese sections in Traditional Chinese (zh-TW) independently — not word-for-word translations.

Today's date: {date}"""


def _source_schema() -> types.Schema:
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            "label": types.Schema(type=types.Type.STRING),
            "url": types.Schema(type=types.Type.STRING),
        },
        required=["label", "url"],
    )


TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="search",
                description="Search for AI news using Tavily. Returns articles with title, URL, and content.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "query": types.Schema(
                            type=types.Type.STRING,
                            description="Search query for finding AI news",
                        )
                    },
                    required=["query"],
                ),
            ),
            types.FunctionDeclaration(
                name="submit_plan",
                description="Declare your intended search plan before making any search calls. Provide a map of category names to lists of queries you plan to run.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "category_queries": types.Schema(
                            type=types.Type.OBJECT,
                            description='Map of category names to lists of intended search queries. Example: {"Breaking": ["breaking AI news today"], "Daily": ["AI news June 2025"]}',
                        )
                    },
                    required=["category_queries"],
                ),
            ),
            types.FunctionDeclaration(
                name="submit_report",
                description="Submit the final structured bilingual AI news report. Call once when done searching.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "date": types.Schema(
                            type=types.Type.STRING,
                            description="Report date in YYYY-MM-DD format",
                        ),
                        "headlines_en": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.STRING),
                            description="Exactly 7 English headlines",
                        ),
                        "analysis_en": types.Schema(
                            type=types.Type.STRING,
                            description="~280-word English analysis covering 2 key themes",
                        ),
                        "sources_en": types.Schema(
                            type=types.Type.ARRAY,
                            items=_source_schema(),
                            description="12-14 English source citations. Each URL must be the exact article page URL from search results, not a website homepage.",
                        ),
                        "headlines_zh": types.Schema(
                            type=types.Type.ARRAY,
                            items=types.Schema(type=types.Type.STRING),
                            description="Exactly 7 Traditional Chinese headlines",
                        ),
                        "analysis_zh": types.Schema(
                            type=types.Type.STRING,
                            description="~280-word Traditional Chinese analysis",
                        ),
                        "sources_zh": types.Schema(
                            type=types.Type.ARRAY,
                            items=_source_schema(),
                            description="12-14 Traditional Chinese source citations. Each URL must be the exact article page URL from search results, not a website homepage.",
                        ),
                    },
                    required=[
                        "date",
                        "headlines_en",
                        "analysis_en",
                        "sources_en",
                        "headlines_zh",
                        "analysis_zh",
                        "sources_zh",
                    ],
                ),
            ),
        ]
    )
]


def do_search(query: str) -> list[dict]:
    client = TavilyClient(api_key=TAVILY_API_KEY)
    result = client.search(query, max_results=5, topic="news", days=2)
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
        }
        for r in result.get("results", [])
    ]


def build_memory_context(summaries_path: str) -> str:
    try:
        with open(summaries_path, encoding="utf-8") as f:
            content = f.read()
    except (FileNotFoundError, OSError):
        return ""

    parts = content.split("---\ndate:")
    json_entries = []
    for part in parts[1:]:
        lines = part.split("\n", 3)
        if len(lines) >= 3:
            try:
                json_entries.append(json.loads(lines[2].strip()))
            except (json.JSONDecodeError, ValueError):
                continue

    if not json_entries:
        return ""

    recent = json_entries[-7:]

    domains: set[str] = set()
    for entry in recent:
        for source in entry.get("sources_en", []) + entry.get("sources_zh", []):
            hostname = urlparse(source.get("url", "")).hostname
            if hostname:
                domains.add(hostname)

    topics: list[str] = []
    seen: set[str] = set()
    for entry in recent:
        for headline in entry.get("headlines_en", []):
            fragment = " ".join(headline.split()[:5])
            if fragment and fragment not in seen:
                seen.add(fragment)
                topics.append(fragment)

    if not domains and not topics:
        return ""

    out = ["## Recent History (last 7 days)"]
    if domains:
        out.append(f"Source domains used recently: {', '.join(sorted(domains))}")
    if topics:
        out.append(f"Recent headline topics: {'; '.join(topics[:14])}")
    out.append("Diversify away from these sources and topics today.")
    return "\n".join(out)


_CHINESE_OUTLET_HOSTNAMES = frozenset({
    "ithome.com.tw", "technews.tw", "bnext.com.tw",
    "36kr.com", "jiqizhixin.com", "qbitai.com", "technews.com.tw",
    "blog.aihao.tw",
})


def check_no_homepage_urls(sources: list[dict]) -> list[str]:
    gaps = []
    for s in sources:
        path = urlparse(s.get("url", "")).path
        if path in ("", "/"):
            gaps.append(f"Homepage URL detected: {s.get('url', '')}")
    return gaps


def check_chinese_outlet_count(sources_zh: list[dict]) -> list[str]:
    count = sum(
        1 for s in sources_zh
        if urlparse(s.get("url", "")).hostname in _CHINESE_OUTLET_HOSTNAMES
    )
    if count < 2:
        return [f"Chinese outlet count in sources_zh: {count} (required ≥ 2)"]
    return []


def check_source_counts(sources_en: list[dict], sources_zh: list[dict]) -> list[str]:
    gaps = []
    for label, sources in [("sources_en", sources_en), ("sources_zh", sources_zh)]:
        n = len(sources)
        if n < 12 or n > 14:
            gaps.append(f"{label} count: {n} (required 12–14)")
    return gaps


def run_agent() -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)
    today = date.today().isoformat()
    summaries_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "summaries.md")
    memory_context = build_memory_context(summaries_path)

    config = types.GenerateContentConfig(
        tools=TOOLS,
        system_instruction=SYSTEM_PROMPT.format(date=today, memory_context=memory_context),
    )

    contents: list[types.Content] = [
        types.Content(
            role="user",
            parts=[
                types.Part(
                    text=f"Research today's ({today}) most important AI news and submit the bilingual report."
                )
            ],
        )
    ]

    search_call_count = 0
    report = None
    plan: dict | None = None
    submit_count = 0
    first_submit_gaps: list[str] = []

    while True:
        response = _generate_content_with_fallback(client, contents, config)

        assistant_content = response.candidates[0].content
        if assistant_content is None:
            break
        contents.append(assistant_content)

        function_calls = [
            part.function_call
            for part in assistant_content.parts
            if part.function_call and part.function_call.name
        ]

        if not function_calls:
            break

        result_parts = []
        for fc in function_calls:
            if fc.name == "search":
                if search_call_count >= MAX_SEARCH_CALLS:
                    raise RuntimeError(f"Exceeded maximum search calls ({MAX_SEARCH_CALLS})")
                search_call_count += 1
                try:
                    results = do_search(fc.args["query"])
                    result_parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name="search",
                                response={"content": json.dumps(results, ensure_ascii=False)},
                            )
                        )
                    )
                except Exception as e:
                    raise RuntimeError(f"Tavily search failed: {e}") from e

            elif fc.name == "submit_plan":
                plan = dict(fc.args)
                result_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name="submit_plan",
                            response={"status": "received"},
                        )
                    )
                )

            elif fc.name == "submit_report":
                submit_count += 1
                if submit_count == 1:
                    sources_en = list(fc.args.get("sources_en", []))
                    sources_zh = list(fc.args.get("sources_zh", []))
                    gaps = (
                        check_no_homepage_urls(sources_en)
                        + check_no_homepage_urls(sources_zh)
                        + check_chinese_outlet_count(sources_zh)
                        + check_source_counts(sources_en, sources_zh)
                    )
                    if gaps:
                        first_submit_gaps = gaps
                        result_parts.append(
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name="submit_report",
                                    response={"status": "quality_check_failed", "gaps": gaps},
                                )
                            )
                        )
                    else:
                        report = dict(fc.args)
                        result_parts.append(
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name="submit_report",
                                    response={"status": "success"},
                                )
                            )
                        )
                else:
                    report = dict(fc.args)
                    result_parts.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name="submit_report",
                                response={"status": "accepted_on_retry"},
                            )
                        )
                    )

        contents.append(types.Content(role="user", parts=result_parts))

        if report is not None:
            break

    if report is None:
        raise RuntimeError("Agent completed without calling submit_report")

    if plan is not None:
        report["plan"] = plan
    if first_submit_gaps:
        report["evaluation_gaps"] = first_submit_gaps

    return report


def append_to_summaries(report: dict) -> None:
    summaries_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "summaries.md")
    entry = f"---\ndate: {report['date']}\n---\n{json.dumps(report, ensure_ascii=False)}\n"
    with open(summaries_path, "a", encoding="utf-8") as f:
        f.write(entry)


def main() -> None:
    try:
        print("Starting AI news agent...", file=sys.stderr)
        report = run_agent()
        append_to_summaries(report)
        print(f"Done. Report for {report['date']} appended to summaries.md", file=sys.stderr)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
