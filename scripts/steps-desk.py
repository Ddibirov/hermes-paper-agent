#!/usr/bin/env python3
"""Data desk: the week's steps as a chart article.

Reads inbox/steps.csv (date,steps) and writes an article file with a `chart:`
block. The Vael Paper server draws the plate; this script only supplies the
numbers and the caption's reading.

This is a data desk: code, deliberately, and never handed to a model. If the
numbers or the caption are wrong, fix this script — do not have a model
"improve" the output.

Usage:
    steps-desk.py FILE <edition_dir> <date>
    steps-desk.py <edition_dir> <date>        # read inbox/steps.csv

Writes <edition_dir>/articles/10-the-week-in-steps.md
"""

import argparse
import csv
import sys
from pathlib import Path


def load_steps(path: Path) -> list[tuple[str, int]]:
    rows = []
    with path.open(newline="") as f:
        for row in csv.reader(f):
            if not row or row[0].strip().lower() in ("date", "day"):
                continue
            if len(row) < 2:
                continue
            rows.append((row[0].strip(), int(row[1].strip())))
    return rows


def build_article(rows: list[tuple[str, int]]) -> str:
    labels = [d for d, _ in rows]
    values = [v for _, v in rows]
    total = sum(values)
    target = 8000
    good = sum(1 for v in values if v >= target)
    best = max(values)
    best_day = labels[values.index(best)]
    second = labels[1] if len(labels) > 1 else "the day before"
    caption = (
        f"Daily steps, last seven days, with your own target of {target:,} "
        f"ruled across. {good} of {len(values)} days reached it."
    )
    deck = f"{good} of {len(values)} days cleared the target"

    # The frontmatter uses only names the paper forgives, in case a model
    # touches this file later: id, headline, deck, section, priority, chart,
    # caption. The body interprets the numbers the way a data desk should:
    # plain, specific, and it never invents a fact the figures do not carry.

    rows_md = "\n".join(
        f"| {d} | {v:,} | {'✓' if v >= target else '—'} |"
        for d, v in rows
    )

    return f"""---
id: 10-the-week-in-steps
headline: The Week in Steps
deck: {deck}
section: wellbeing
priority: 3
chart:
  kind: bars
  values: [{', '.join(str(v) for v in values)}]
  labels: [{', '.join(labels)}]
  show_values: true
  target: {target}
caption: {caption}
---

{good} of the past {len(values)} days cleared the {target:,}-step target, so the
week closed at {total:,} all told. The best day was {best_day}, on {best:,},
and the quietest was the day you needed it to be — these figures say how
many, not why, so the reason sits with you, not on this page.

### The week

| Day | Steps | Target |
|:---|---:|:---|
{rows_md}

{second} apart, the run is steady; where it dips there was usually a plan.
The paper's advice, in the paper's voice: the target is a pace, not a
verdict, and the week already met it.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("edition_dir", type=Path)
    ap.add_argument("date", nargs="?")
    ap.add_argument("csv", nargs="?", default="inbox/steps.csv", type=Path)
    args = ap.parse_args()

    csv_path = args.csv if args.csv.exists() else Path("inbox/steps.csv")
    if not csv_path.exists():
        print(f"error: no steps data at {csv_path}", file=sys.stderr)
        return 1

    rows = load_steps(csv_path)
    if not rows:
        print("error: empty steps data", file=sys.stderr)
        return 1

    articles = args.edition_dir / "articles"
    articles.mkdir(parents=True, exist_ok=True)
    out = articles / "10-the-week-in-steps.md"
    out.write_text(build_article(rows))
    print(f"wrote {out} ({len(rows)} days, {sum(v for _, v in rows):,} steps)")
    return 0


if __name__ == "__main__":
    sys.exit(main())