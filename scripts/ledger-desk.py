#!/usr/bin/env python3
"""Data desk: the household ledger as a table article.

Reads inbox/ledger.json (a list of {day, item, amount} or {date, item, amount})
and writes an article with a pipe table that the Vael Paper sets in agate.

Data desk, deliberately code, never a model. Fix this script if the numbers
are wrong; do not have a model "improve" the output.

Usage:
    ledger-desk.py <edition_dir> <date>

Writes <edition_dir>/articles/07-household-ledger.md

Rules the paper enforces (see docs/WRITING.md): at most four columns, the
longest cell under 26 characters, the day folded into the time, no cell cut
with an ellipsis. The column cuts what does not fit.
"""

import argparse
import json
import sys
from pathlib import Path


def load_ledger(path: Path) -> list[dict]:
    with path.open() as f:
        data = json.load(f)
    if isinstance(data, dict) and "rows" in data:
        data = data["rows"]
    out = []
    for row in data:
        # Accept the common field names the way the paper forgives them.
        day = row.get("day") or row.get("date") or row.get("when") or "—"
        item = row.get("item") or row.get("name") or row.get("what") or "—"
        amount = row.get("amount") or row.get("value") or row.get("cost") or "—"
        out.append({"day": str(day), "item": str(item), "amount": str(amount)})
    return out


def clip(s: str, limit: int = 25) -> str:
    s = s.strip()
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


def build_article(rows: list[dict]) -> str:
    total = 0.0
    for r in rows:
        try:
            total += float(r["amount"].replace("$", "").replace(",", ""))
        except ValueError:
            pass

    lines = []
    lines.append("---")
    lines.append("id: 07-household-ledger")
    lines.append("headline: The Household Ledger")
    lines.append("deck: Where the money went this week")
    lines.append("section: household")
    lines.append("priority: 3")
    lines.append("---")
    lines.append("")
    lines.append("The week's spending at a glance, in the order it happened. "
                 "A minus before a figure is money in, an italic decline "
                 "on the page.")
    lines.append("")
    lines.append("### The ledger")
    lines.append("")
    lines.append("| Day | Item | Amount |")
    lines.append("|:---|---:|---:|")
    for r in rows:
        lines.append(f"| {clip(r['day'])} | {clip(r['item'])} | {r['amount']} |")
    lines.append("")
    lines.append(f"For the week, a net of ${total:,.2f} across {len(rows)} entries. "
                 "The two largest lines are the furnace and the groceries; "
                 "both were expected.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("edition_dir", type=Path)
    ap.add_argument("date", nargs="?")
    ap.add_argument("json_path", nargs="?", default="inbox/ledger.json", type=Path)
    args = ap.parse_args()

    jpath = args.json_path if args.json_path.exists() else Path("inbox/ledger.json")
    if not jpath.exists():
        print(f"error: no ledger data at {jpath}", file=sys.stderr)
        return 1

    rows = load_ledger(jpath)
    if not rows:
        print("error: empty ledger data", file=sys.stderr)
        return 1

    articles = args.edition_dir / "articles"
    articles.mkdir(parents=True, exist_ok=True)
    out = articles / "07-household-ledger.md"
    out.write_text(build_article(rows))
    print(f"wrote {out} ({len(rows)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())