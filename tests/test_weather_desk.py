"""The weather desk: a chart article built from an Open-Meteo response.

Every test runs against the canned fixture — the desk hits the network only
through fetch(), which no test calls. CI stays hermetic.
"""

import sys

import pytest
from conftest import frontmatter


def test_celsius_to_fahrenheit(weather_desk):
    assert weather_desk.to_f(0) == 32
    assert weather_desk.to_f(100) == 212
    assert weather_desk.to_f(30.0) == 86


@pytest.mark.parametrize("code,word", [
    (0, "Clear"), (1, "Mostly clear"), (2, "Partly cloudy"), (3, "Overcast"),
    (45, "Fog"), (48, "Fog"), (53, "Drizzle"), (61, "Light rain"),
    (63, "Rain"), (65, "Heavy rain"), (71, "Snow"), (80, "Showers"),
    (95, "Storm"), (99, "Storm"),
])
def test_sky_words(weather_desk, code, word):
    assert weather_desk.sky(code) == word


def test_sky_falls_back_for_unknown_codes(weather_desk):
    assert weather_desk.sky(1234) == "—"


def test_labels_are_weekdays(weather_desk, open_meteo):
    article = weather_desk.build_article(open_meteo, "Washington", "f")
    assert "labels: [Fri, Sat, Sun, Mon, Tue, Wed, Thu]" in article


def test_peak_and_wettest_days_are_derived(weather_desk, open_meteo):
    article = weather_desk.build_article(open_meteo, "Washington", "f")
    # 33.3C is the week's high, on the last day (Thu); 80% rain lands on Sun
    assert "The warmest day is Thu" in article
    assert "keep the umbrella for Sun" in article
    assert "a 80% chance of rain" in article


def test_fahrenheit_conversion_reaches_the_table(weather_desk, open_meteo):
    article = weather_desk.build_article(open_meteo, "Washington", "f")
    assert "| Thu | 92°F | 72°F |" in article
    assert "values: [86, 90, 84, 79, 82, 88, 92]" in article


def test_celsius_keeps_the_source_numbers(weather_desk, open_meteo):
    article = weather_desk.build_article(open_meteo, "Washington", "c")
    assert "°C" in article and "°F" not in article
    assert "values: [30.0, 32.2, 28.9, 26.1, 27.8, 31.1, 33.3]" in article


def test_chart_floor_sits_under_the_coolest_high(weather_desk, open_meteo):
    """WRITING.md: start highs of 94-99 at 80, not 0, or the week looks flat."""
    article = weather_desk.build_article(open_meteo, "Washington", "f")
    assert "min: 65" in article        # coolest high is 79F
    assert "min: 0" not in article


def test_body_describes_the_range_rather_than_asserting_warmth(weather_desk, open_meteo):
    """Regression: the body opened "The week trends warm" whatever the data."""
    article = weather_desk.build_article(open_meteo, "Washington", "f")
    assert "Highs in Washington run from 79°F to 92°F" in article
    assert "trends warm" not in article


def test_place_name_is_carried_through(weather_desk, open_meteo):
    article = weather_desk.build_article(open_meteo, "Reykjavík", "c")
    assert "Reykjavík" in article


def test_one_row_per_forecast_day(weather_desk, open_meteo):
    article = weather_desk.build_article(open_meteo, "Washington", "f")
    board = article.split("### The board")[1]
    rows = [ln for ln in board.splitlines() if ln.startswith("|") and "---" not in ln]
    assert len(rows) == 1 + 7          # header + seven days


def test_section_is_one_the_paper_knows(weather_desk, open_meteo, paper_sections):
    fm = frontmatter(weather_desk.build_article(open_meteo, "Washington", "f"))
    assert fm["section"] in paper_sections


def test_main_writes_the_article(weather_desk, open_meteo, tmp_path, monkeypatch):
    out = tmp_path / "edition"
    monkeypatch.setattr(weather_desk, "fetch", lambda lat, lon: open_meteo)
    monkeypatch.setattr(sys, "argv", ["weather-desk.py", str(out), "--place", "Washington"])
    assert weather_desk.main() == 0
    assert (out / "articles" / "02-your-week-in-weather.md").exists()


def test_main_fails_and_writes_nothing_when_the_fetch_fails(weather_desk, tmp_path, monkeypatch):
    """A fetch failure must drop the story, never guess a forecast."""
    def boom(lat, lon):
        raise OSError("network unreachable")

    out = tmp_path / "edition"
    monkeypatch.setattr(weather_desk, "fetch", boom)
    monkeypatch.setattr(sys, "argv", ["weather-desk.py", str(out)])
    assert weather_desk.main() == 1
    assert not (out / "articles" / "02-your-week-in-weather.md").exists()


def test_main_reads_place_from_the_environment(weather_desk, open_meteo, tmp_path, monkeypatch):
    out = tmp_path / "edition"
    monkeypatch.setenv("WEATHER_PLACE", "Reykjavík")
    monkeypatch.setattr(weather_desk, "fetch", lambda lat, lon: open_meteo)
    monkeypatch.setattr(sys, "argv", ["weather-desk.py", str(out)])
    assert weather_desk.main() == 0
    assert "Reykjavík" in (out / "articles" / "02-your-week-in-weather.md").read_text()
