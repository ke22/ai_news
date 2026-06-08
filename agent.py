import json
import os
import sys
from datetime import date

import anthropic
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
    sys.exit(1)
if not TAVILY_API_KEY:
    print("Error: TAVILY_API_KEY not set", file=sys.stderr)
    sys.exit(1)

MAX_SEARCH_CALLS = 10

SYSTEM_PROMPT = """You are an AI news analyst. Your job is to research today's most important AI news and produce a structured bilingual (English and Chinese) daily summary.

Use the `search` tool to find AI news. You decide which queries to run — be strategic and cover different angles: model releases, investments, regulations, products, research. Make 3 to 10 searches total.

When you have gathered enough information, call `submit_report` with:
- 7 headlines in English (bold title concept + one-sentence summary)
- A ~280-word analysis in English covering 2 key themes
- 12-14 source citations with labels and URLs
- The same three sections in Traditional Chinese (zh-TW)

The Chinese sections should be independently written in Chinese — not translated word-for-word.

Today's date: {date}"""

SEARCH_TOOL = {
    "name": "search",
    "description": "Search for AI news using the Tavily search API. Returns a list of relevant articles.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find AI news articles",
            }
        },
        "required": ["query"],
    },
}

SUBMIT_REPORT_TOOL = {
    "name": "submit_report",
    "description": "Submit the final structured bilingual daily AI news report. Call this once when you have gathered enough information.",
    "input_schema": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Report date in YYYY-MM-DD format",
            },
            "headlines_en": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 7,
                "maxItems": 7,
                "description": "Exactly 7 English headlines, each as 'Bold Title: one-sentence summary'",
            },
            "analysis_en": {
                "type": "string",
                "description": "~280-word English analysis covering 2 key themes from today's news",
            },
            "sources_en": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["label", "url"],
                },
                "minItems": 12,
                "maxItems": 14,
                "description": "12-14 source citations with publication name and URL",
            },
            "headlines_zh": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 7,
                "maxItems": 7,
                "description": "Exactly 7 Traditional Chinese headlines",
            },
            "analysis_zh": {
                "type": "string",
                "description": "~280-word Traditional Chinese analysis covering 2 key themes",
            },
            "sources_zh": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["label", "url"],
                },
                "minItems": 12,
                "maxItems": 14,
                "description": "12-14 source citations in Chinese labels with URLs",
            },
        },
        "required": [
            "date",
            "headlines_en",
            "analysis_en",
            "sources_en",
            "headlines_zh",
            "analysis_zh",
            "sources_zh",
        ],
    },
}


def search(query: str) -> list[dict]:
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
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = date.today().isoformat()

    messages = []
    search_call_count = 0
    report = None

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            system=SYSTEM_PROMPT.format(date=today),
            tools=[SEARCH_TOOL, SUBMIT_REPORT_TOOL],
            messages=messages,
        )

        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        for block in assistant_content:
            if block.type != "tool_use":
                continue

            if block.name == "search":
                if search_call_count >= MAX_SEARCH_CALLS:
                    raise RuntimeError(
                        f"Exceeded maximum search calls ({MAX_SEARCH_CALLS})"
                    )
                search_call_count += 1
                try:
                    results = search(block.input["query"])
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(results),
                        }
                    )
                except Exception as e:
                    raise RuntimeError(f"Tavily search failed: {e}") from e

            elif block.name == "submit_report":
                report = block.input
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Report submitted successfully.",
                    }
                )

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        if report is not None and response.stop_reason == "tool_use":
            # After submit_report, let the model end naturally
            continue

    if report is None:
        raise RuntimeError("Agent completed without calling submit_report")

    return report


def append_to_summaries(report: dict) -> None:
    summaries_path = os.path.join(os.path.dirname(__file__), "summaries.md")
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
