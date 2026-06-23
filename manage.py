#!/usr/bin/env python3
"""Manage summaries.md: list all runs, pick which to keep for duplicate dates.

Usage:
  python manage.py              # interactive: review dates with multiple runs
  python manage.py --list       # list all runs (date, run #, first headline)
  python manage.py --keep-latest  # non-interactive: keep only the newest run per date
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SUMMARIES_PATH = os.path.join(ROOT, "summaries.md")


# ── Parse / write ────────────────────────────────────────────────────────────

def parse_raw_blocks() -> list[tuple[str, str]]:
    """Return [(date_str, json_str), ...] in summaries.md order."""
    with open(SUMMARIES_PATH, encoding="utf-8") as f:
        content = f.read()
    blocks: list[tuple[str, str]] = []
    for part in content.split("---\ndate:")[1:]:
        first_nl = part.find("\n")
        if first_nl == -1:
            continue
        date_str = part[:first_nl].strip()
        rest = part[first_nl:].strip()
        if rest.startswith("---"):
            rest = rest[3:].strip()
        if rest:
            blocks.append((date_str, rest))
    return blocks


def group_by_date(blocks: list[tuple[str, str]]) -> dict[str, list[tuple[int, str]]]:
    """Return {date: [(original_index, json_str), ...]} preserving summaries.md order."""
    groups: dict[str, list[tuple[int, str]]] = {}
    for i, (date_str, json_str) in enumerate(blocks):
        groups.setdefault(date_str, []).append((i, json_str))
    return groups


def write_blocks(blocks: list[tuple[str, str]]) -> None:
    lines = ["---\ndate: {}\n---\n{}".format(d, j) for d, j in blocks]
    with open(SUMMARIES_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _first_headline(json_str: str) -> str:
    try:
        data = json.loads(json_str)
        hl = data.get("headlines_en", [])
        if hl:
            h = hl[0].replace("**", "").strip()
            if ": " in h:
                h = h.split(": ", 1)[0]
            return (h[:72] + "…") if len(h) > 72 else h
    except (json.JSONDecodeError, ValueError):
        pass
    return "(parse error)"


def _date_order(blocks: list[tuple[str, str]]) -> list[str]:
    seen: set[str] = set()
    order: list[str] = []
    for d, _ in blocks:
        if d not in seen:
            seen.add(d)
            order.append(d)
    return order


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_list(blocks: list[tuple[str, str]], groups: dict) -> None:
    date_order = _date_order(blocks)
    print(f"\n{'DATE':<14} {'RUN':>4}  HEADLINE")
    print("─" * 78)
    for date_str in sorted(date_order, reverse=True):
        runs = groups[date_str]
        n = len(runs)
        for run_num, (_, json_str) in enumerate(runs, 1):
            label = f"{run_num}/{n}"
            tag = " [latest]" if run_num == n else ""
            headline = _first_headline(json_str)
            print(f"{date_str:<14} {label:>5}{tag:<9}  {headline}")
    print(f"\nTotal: {len(date_order)} dates, {len(blocks)} runs\n")


def cmd_keep_latest(blocks: list[tuple[str, str]], groups: dict) -> None:
    multi = {d: runs for d, runs in groups.items() if len(runs) > 1}
    if not multi:
        print("No duplicate dates — nothing to do.")
        return
    to_remove: set[int] = set()
    for date_str in sorted(multi, reverse=True):
        runs = multi[date_str]
        n = len(runs)
        for i, (idx, _) in enumerate(runs[:-1]):  # keep last = newest
            to_remove.add(idx)
        print(f"  {date_str}: keeping run {n}, discarding {n - 1} earlier run(s)")
    new_blocks = [(d, j) for i, (d, j) in enumerate(blocks) if i not in to_remove]
    write_blocks(new_blocks)
    print(f"\nUpdated summaries.md: {len(blocks)} → {len(new_blocks)} entries")
    print("Run 'python publish.py' to regenerate the site.")


def cmd_interactive(blocks: list[tuple[str, str]], groups: dict) -> None:
    multi_dates = sorted([d for d, runs in groups.items() if len(runs) > 1], reverse=True)
    if not multi_dates:
        print("No duplicate dates — all dates have exactly one run.")
        print("Use 'python manage.py --list' to see all runs.")
        return

    to_remove: set[int] = set()

    for date_str in multi_dates:
        runs = groups[date_str]
        n = len(runs)
        print(f"\n{'═' * 60}")
        print(f"  {date_str}  ({n} runs)")
        print()
        for run_num, (_, json_str) in enumerate(runs, 1):
            tag = " ← latest" if run_num == n else ""
            headline = _first_headline(json_str)
            print(f"  [{run_num}] Run {run_num}{tag}")
            print(f"       {headline}")
        print()
        print(f"  Keep: [1–{n}] pick one  [l] keep latest  [a] keep all  [s] skip")

        while True:
            try:
                choice = input("  > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nAborted.")
                sys.exit(0)

            if choice in ("l", ""):
                for idx, _ in runs[:-1]:
                    to_remove.add(idx)
                print(f"  → Keeping run {n}; {n - 1} earlier run(s) will be removed.")
                break
            elif choice == "a":
                print(f"  → Keeping all {n} runs.")
                break
            elif choice == "s":
                print("  → Skipped (no change).")
                break
            else:
                try:
                    pick = int(choice)
                    if 1 <= pick <= n:
                        for j, (idx, _) in enumerate(runs):
                            if j != pick - 1:
                                to_remove.add(idx)
                        print(f"  → Keeping run {pick}; {n - 1} other run(s) will be removed.")
                        break
                    else:
                        print(f"  Enter 1–{n}, l, a, or s.")
                except ValueError:
                    print(f"  Enter 1–{n}, l, a, or s.")

    if not to_remove:
        print("\nNo changes made.")
        return

    new_blocks = [(d, j) for i, (d, j) in enumerate(blocks) if i not in to_remove]
    write_blocks(new_blocks)
    print(f"\nUpdated summaries.md: {len(blocks)} → {len(new_blocks)} entries")
    print("Run 'python publish.py' to regenerate the site.")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage ai-news summaries: view runs, resolve duplicates."
    )
    parser.add_argument("--list", "-l", action="store_true", help="List all runs")
    parser.add_argument(
        "--keep-latest",
        action="store_true",
        help="Non-interactively keep only the latest run per date",
    )
    args = parser.parse_args()

    if not os.path.exists(SUMMARIES_PATH):
        print("Error: summaries.md not found", file=sys.stderr)
        sys.exit(1)

    blocks = parse_raw_blocks()
    groups = group_by_date(blocks)

    if args.list:
        cmd_list(blocks, groups)
    elif args.keep_latest:
        cmd_keep_latest(blocks, groups)
    else:
        cmd_interactive(blocks, groups)


if __name__ == "__main__":
    main()
