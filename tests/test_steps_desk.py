"""The steps desk: a chart article built from date,steps rows."""

import subprocess
import sys

from conftest import REPO, SCRIPTS, frontmatter

WEEK = [("Fri", 9120), ("Sat", 2840), ("Sun", 6400), ("Mon", 8340),
        ("Tue", 10205), ("Wed", 8015), ("Thu", 11240)]


def test_load_steps_skips_header_and_blank_rows(steps_desk, tmp_path):
    csv = tmp_path / "steps.csv"
    csv.write_text("day,steps\nFri,9120\n\nSat,2840\n")
    assert steps_desk.load_steps(csv) == [("Fri", 9120), ("Sat", 2840)]


def test_load_steps_accepts_date_header(steps_desk, tmp_path):
    csv = tmp_path / "steps.csv"
    csv.write_text("date,steps\n2026-09-04,9120\n")
    assert steps_desk.load_steps(csv) == [("2026-09-04", 9120)]


def test_chart_values_match_the_table(steps_desk):
    article = steps_desk.build_article(WEEK)
    # every figure appears in the chart block and again in the pipe table
    assert "values: [9120, 2840, 6400, 8340, 10205, 8015, 11240]" in article
    assert "labels: [Fri, Sat, Sun, Mon, Tue, Wed, Thu]" in article
    for day, steps in WEEK:
        assert f"| {day} | {steps:,} |" in article


def test_target_count_is_derived_not_asserted(steps_desk):
    # five of the seven days clear 8,000
    article = steps_desk.build_article(WEEK)
    assert "5 of 7 days cleared the target" in article
    assert "5 of the past 7 days cleared the 8,000-step target" in article


def test_names_the_quietest_day_not_the_second_row(steps_desk):
    """Regression: the prose used labels[1] and called it the exception, which
    was only right by luck on the shipped fixture."""
    rows = [("Fri", 9000), ("Sat", 9500), ("Sun", 1200), ("Mon", 9100)]
    article = steps_desk.build_article(rows)
    assert article.count("Sun apart, the run is steady") == 1
    assert "Sat apart" not in article


def test_total_is_the_sum(steps_desk):
    article = steps_desk.build_article(WEEK)
    assert f"{sum(v for _, v in WEEK):,}" in article


def test_section_is_one_the_paper_knows(steps_desk, paper_sections):
    fm = frontmatter(steps_desk.build_article(WEEK))
    assert fm["section"] in paper_sections


def test_cli_writes_the_article(tmp_path):
    csv = tmp_path / "steps.csv"
    csv.write_text("day,steps\nFri,9120\nSat,2840\n")
    out = tmp_path / "edition"
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "steps-desk.py"), str(out), "2026-09-04", str(csv)],
        capture_output=True, text=True, cwd=REPO,
    )
    assert r.returncode == 0, r.stderr
    assert (out / "articles" / "10-the-week-in-steps.md").exists()


def test_cli_fails_on_missing_data(tmp_path):
    """A desk that cannot read its source must fail, not invent a week."""
    out = tmp_path / "edition"
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "steps-desk.py"), str(out),
         "2026-09-04", str(tmp_path / "nope.csv")],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert r.returncode == 1
    assert not (out / "articles").exists()
