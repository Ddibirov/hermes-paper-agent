"""The ledger desk: a household table whose total must actually add up."""

import json
import subprocess
import sys

import pytest
from conftest import SCRIPTS, frontmatter

ROWS = [
    {"day": "Fri", "item": "Groceries", "amount": "$184.20"},
    {"day": "Fri", "item": "Furnace service", "amount": "$212.00"},
    {"day": "Sun", "item": "Metro", "amount": "−$8.00"},   # money in
    {"day": "Sun", "item": "Nationals tickets", "amount": "$54.00"},
    {"day": "Wed", "item": "Coffee, the corner", "amount": "$12.50"},
]


@pytest.mark.parametrize("raw,expected", [
    ("$184.20", 184.20),
    ("184.20", 184.20),
    ("$1,184.20", 1184.20),
    ("-$8.00", -8.0),
    ("−$8.00", -8.0),      # typographic minus, as the paper sets it
    ("–$8.00", -8.0),      # en dash, as some exports write it
    ("($8.00)", -8.0),          # accountancy parentheses
])
def test_parse_amount(ledger_desk, raw, expected):
    assert ledger_desk.parse_amount(raw) == pytest.approx(expected)


@pytest.mark.parametrize("raw", ["", "—", "n/a", "about ten"])
def test_parse_amount_rejects_what_it_cannot_read(ledger_desk, raw):
    with pytest.raises(ValueError):
        ledger_desk.parse_amount(raw)


def test_total_subtracts_money_in(ledger_desk):
    """Regression: the typographic minus failed float() and was silently
    skipped, so the printed total was $462.70 instead of $454.70."""
    article = ledger_desk.build_article(ROWS)
    assert "a net of $454.70 across 5 entries" in article
    assert "462.70" not in article


def test_largest_lines_are_derived_from_the_data(ledger_desk):
    """Regression: the sentence named the furnace and the groceries whatever
    the data said."""
    rows = [
        {"day": "Mon", "item": "Rent", "amount": "$1,500.00"},
        {"day": "Tue", "item": "Bicycle", "amount": "$400.00"},
        {"day": "Wed", "item": "Tea", "amount": "$3.00"},
    ]
    article = ledger_desk.build_article(rows)
    assert "the rent and bicycle" in article
    assert "furnace" not in article


def test_single_row_reads_as_singular(ledger_desk):
    article = ledger_desk.build_article([ROWS[0]])
    assert "The largest line is the groceries" in article
    assert "across 1 entry." in article


def test_load_ledger_accepts_both_shapes(ledger_desk, tmp_path):
    bare = tmp_path / "a.json"
    bare.write_text(json.dumps([{"day": "Fri", "item": "X", "amount": "$1.00"}]))
    wrapped = tmp_path / "b.json"
    wrapped.write_text(json.dumps({"rows": [{"day": "Fri", "item": "X", "amount": "$1.00"}]}))
    assert ledger_desk.load_ledger(bare) == ledger_desk.load_ledger(wrapped)


def test_load_ledger_forgives_field_names(ledger_desk, tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps([{"date": "Fri", "what": "Tea", "cost": "$3.00"}]))
    assert ledger_desk.load_ledger(p) == [
        {"day": "Fri", "item": "Tea", "amount": "$3.00"}
    ]


def test_clip_keeps_cells_inside_the_column(ledger_desk):
    assert ledger_desk.clip("short") == "short"
    long = ledger_desk.clip("a very long item name that will not fit the column")
    assert len(long) <= 25 and long.endswith("…")


def test_table_has_at_most_four_columns(ledger_desk):
    """docs/WRITING.md: at most four columns, or the paper lints it wide."""
    article = ledger_desk.build_article(ROWS)
    header = next(ln for ln in article.splitlines() if ln.startswith("| Day"))
    assert header.count("|") - 1 <= 4


def test_section_is_one_the_paper_knows(ledger_desk, paper_sections):
    fm = frontmatter(ledger_desk.build_article(ROWS))
    assert fm["section"] in paper_sections


def test_cli_refuses_an_unreadable_amount(tmp_path):
    """Better a failed run than a total that is quietly short."""
    src = tmp_path / "ledger.json"
    src.write_text(json.dumps([{"day": "Fri", "item": "Mystery", "amount": "about ten"}]))
    out = tmp_path / "edition"
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "ledger-desk.py"), str(out), "2026-09-04", str(src)],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert r.returncode == 1
    assert "unreadable amount" in r.stderr
    assert not (out / "articles").exists()
