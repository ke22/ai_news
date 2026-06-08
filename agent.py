import json
import os
import sys
from datetime import date

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

MAX_SEARCH_CALLS = 10

SYSTEM_PROMPT = """You are an AI news analyst. Research today's most important AI news and produce a structured bilingual daily summary.

## Fact-Check Thinking Rules
Before writing any headline, claim, or citation, verify it against your search results:
- Only include headlines and facts that appear in retrieved articles. Do not invent or assume company names, product names, numbers, or events.
- Every source URL must be the exact article URL returned by a search result — never a homepage (e.g. never https://reuters.com, always the full article path).
- If a claim cannot be confirmed from search results, omit it entirely. Do not fill gaps with general knowledge or plausible-sounding content.
- Headlines must reflect actual content found — not extrapolated trends or assumptions.

## Search Scope
Run 5 to 10 searches covering each of these five categories. Use category-targeted queries:
- 當日 (Daily): Today's general AI news — model updates, product launches, company news
- Breaking: Urgent or just-announced AI news today
- High-Impact: AI news with major implications for industry, economy, or society
- Viral: AI stories trending or widely discussed on social media today
- Unusual: Surprising, counterintuitive, or unexpected AI developments

## Report Guideline
When you have enough information, call `submit_report` with:
- Exactly 7 English headlines (format: "Bold Title: one-sentence summary"). The 7 headlines must collectively span the five categories above — aim for at least one headline per category, prioritizing diversity.
- A ~280-word English analysis covering 2 key themes
- 12 to 14 English source citations (label + exact article URL from search results)
- Exactly 7 Traditional Chinese headlines covering the same 7 stories
- A ~280-word Traditional Chinese analysis covering the same themes
- 12 to 14 Traditional Chinese source citations (label + exact article URL from search results)

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
    result = client.search(query, max_results=5)
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
        }
        for r in result.get("results", [])
    ]


def run_agent() -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)
    today = date.today().isoformat()

    config = types.GenerateContentConfig(
        tools=TOOLS,
        system_instruction=SYSTEM_PROMPT.format(date=today),
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

    while True:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config,
        )

        assistant_content = response.candidates[0].content
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

            elif fc.name == "submit_report":
                report = dict(fc.args)
                result_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name="submit_report",
                            response={"status": "success"},
                        )
                    )
                )

        contents.append(types.Content(role="user", parts=result_parts))

        if report is not None:
            break

    if report is None:
        raise RuntimeError("Agent completed without calling submit_report")

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
