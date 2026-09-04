"""Cross-cutting rules every desk has to honour, from AGENTS.md and the
Vael Paper format contract. These are the invariants that stop an edition
printing with a mark in it.
"""

import json
import os
import re
import stat

import pytest
from conftest import REPO, SCRIPTS, frontmatter

DESKS = ["ops-desk.py"]


@pytest.fixture
def articles(ops_desk, checks):
    """One article from the data desk, from canned checks — no network."""
    return {"ops": ops_desk.build_article(checks)}


def test_every_article_opens_with_frontmatter(articles):
    for name, article in articles.items():
        assert article.startswith("---\n"), name


def test_every_article_has_a_headline(articles):
    for name, article in articles.items():
        assert frontmatter(article).get("headline"), name


def test_no_headline_carries_a_colon(articles):
    """The scanner forgives it, but the paper sets it badly."""
    for name, article in articles.items():
        assert ":" not in frontmatter(article)["headline"], name


def test_no_headline_asks_a_question(articles):
    """AGENTS.md, the paper's voice: no headlines that ask a question."""
    for name, article in articles.items():
        assert not frontmatter(article)["headline"].endswith("?"), name


def test_every_section_exists_in_paper_json(articles, paper_sections):
    """AGENTS.md hard rule: look up section ids, do not invent them."""
    for name, article in articles.items():
        assert frontmatter(article)["section"] in paper_sections, name


def test_priority_is_an_integer(articles):
    for name, article in articles.items():
        assert re.fullmatch(r"\d+", frontmatter(article)["priority"]), name


def test_no_data_desk_claims_the_front_page(articles):
    """Exactly one story is priority 1, and the lead desk writes it."""
    for name, article in articles.items():
        assert frontmatter(article)["priority"] != "1", name


def test_no_exclamation_marks(articles):
    for name, article in articles.items():
        assert "!" not in article, name


def test_pipe_tables_are_rectangular(articles):
    for name, article in articles.items():
        rows = [ln for ln in article.splitlines() if ln.startswith("|")]
        widths = {ln.count("|") for ln in rows}
        assert len(widths) <= 1, f"{name}: ragged table {widths}"


def test_only_http_urls_are_linked(articles):
    """Anything else degrades to plain text with a printer's mark."""
    for name, article in articles.items():
        for url in re.findall(r"url: (\S+)", article):
            assert url.startswith(("http://", "https://")), f"{name}: {url}"


@pytest.mark.parametrize("desk", DESKS)
def test_desks_are_executable(desk):
    """They carry a shebang and the docs invoke them directly, so the exec bit
    has to be set."""
    path = SCRIPTS / desk
    assert path.read_text().startswith("#!/usr/bin/env python3"), desk
    assert os.stat(path).st_mode & stat.S_IXUSR, f"{desk} is not executable"


@pytest.mark.parametrize("desk", DESKS)
def test_desks_import_only_the_standard_library(desk):
    """The README promises the desks need no pip install. Keep it true."""
    third_party = {"requests", "httpx", "pandas", "numpy", "yaml", "yfinance"}
    source = (SCRIPTS / desk).read_text()
    imported = set(re.findall(r"^(?:from|import) (\w+)", source, re.M))
    assert not (imported & third_party), f"{desk} imports {imported & third_party}"


def test_paper_json_is_well_formed():
    paper = json.loads((REPO / "editions" / "paper.json").read_text())
    assert paper["masthead"] and paper["motto"] and paper["founded"]
    ids = [s["id"] for s in paper["sections"]]
    assert len(ids) == len(set(ids)), "duplicate section ids"
    for section in paper["sections"]:
        assert section["id"] and section["name"]


def test_inbox_has_the_material_the_desks_read():
    """The prose desks read these files every night; they must exist, even
    empty, so a run never trips over a missing path."""
    for name in ("feeds.md", "notes.md", "projects.md"):
        assert (REPO / "inbox" / name).is_file(), f"inbox/{name} missing"