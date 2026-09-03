# My Hermes Personal Paper 📰

Your own nightly newspaper — written overnight from your calendar, budget,
feeds, notes and a couple of live data feeds, and printed the way a real
broadsheet is.

![The opening spread of the sample edition — page one leads with the front-page
story, page two with the Weather and Financial boards, set as a two-page
broadsheet spread.](screenshots/pages-1-2.png)

*The first two pages of a generated edition. Page one is today's lead; page two
carries the Weather and the Markets — written every night from your own
material and live feeds.*

## ✨ Highlights

- **A paper, not a feed** — a front page, sections, charts, quotes, and an
  *end*.
- **Runs on a small model** — every desk is a short prompt over a little
  material, so a modest local model is enough.
- **Numbers come from code** — data desks render tables and charts in Python;
  the model never invents a figure.
- **Self-correcting** — every desk runs a write → check → fix loop and won't
  publish on red.
- **Nightly, unattended** — one cron job and the paper is waiting at breakfast.
- **Yours** — masthead, sections, sources and desks are all files you own.

---

## 📑 Contents

- [Overview](#-overview)
- [How it works](#-how-it-works)
- [Getting started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [1. Install the required software](#1-install-the-required-software)
  - [2. Install Vael Paper (the engine that prints it)](#2-install-vael-paper-the-engine-that-prints-it)
  - [3. Install the agent (this repo)](#3-install-the-agent-this-repo)
  - [4. Print your first edition](#4-print-your-first-edition)
- [Usage — sample prompts](#-usage--sample-prompts)
- [Configuration](#-configuration)
  - [The masthead: editions/paper.json](#the-masthead-editionspaperjson)
  - [The material: inbox/](#the-material-inbox)
  - [The live desks](#the-live-desks)
- [Examples — write your own desk](#-examples--write-your-own-desk)
- [Project structure](#-project-structure)
- [The write → check → fix loop](#-the-write--check--fix-loop)
- [Run it every night](#-run-it-every-night)
- [License](#-license)

---

## 📖 Overview

A newspaper is a good shape for a personal daily briefing: it is finite, it is
ordered by what matters, and it ends. This repo is the **generator** for one —
it assembles tomorrow's edition as a folder of markdown articles. The reading
and printing is done by the [Vael Paper](https://github.com/vaelkeep/vael-paper)
engine, which this generator feeds.

The whole thing is an agent. You talk to Hermes once and a scheduled run
writes, checks, fixes and publishes a clean edition every night at 4 a.m.

Three pieces, cleanly separated:

| | |
|---|---|
| **The generator** | This repo. Desks — some code, some model — write markdown into `editions/<date>/articles/`. |
| **The engine** | [Vael Paper](https://github.com/vaelkeep/vael-paper). Scans that folder and prints a paginated broadsheet with charts, drop caps, pull quotes and page turns. It *deliberately* does not generate — anything that writes markdown into the folder can publish. |
| **The agent** | [Hermes Agent](https://hermes-agent.nousresearch.com) runs the desks, checks the result, fixes what's wrong, and schedules the run. Hermes is the "night editor". |

You own everything. `editions/paper.json` sets the masthead and the sections;
`inbox/` is your material; `scripts/` are your data desks. The example ships
with fiction fixtures, so you can run it once unchanged to see a full paper,
then replace the standing parts with your real ones.

## 🏗️ How it works

A newspaper isn't written by one person. It's assembled by **desks**, each with
a beat and a source of material, then put in order by an editor. That is the
shape here, because it is the shape that lets a small model succeed — every
desk is a short prompt over a small amount of material, producing one file.

- **Data desks** turn structured data into correct tables *by code* — no model
  in the loop. The repo ships four: steps, ledger (from files in `inbox/`),
  weather and finance (from live APIs).
- **Prose desks** are the model (Hermes). They take a handful of
  already-summarised feed items, notes or photos and write one story each.
- **The lead desk** runs last, sees everything, and writes the front page: the
  reader's own day in the order it will happen, tying the data to the stories.

Every desk — and the edition as a whole — runs the same loop: **write** the
file, **check** it with `vael-paper-check`, **fix** what the report names,
repeat until `"ok": true`. A story that summarises someone else's reporting
carries a `sources:` list; data that belongs in a chart goes in a `chart:`
block and the engine draws the plate in the paper's style.

---

## 🚀 Getting started

### Prerequisites

| Software | Version | Why |
|---|---|---|
| [Python](https://www.python.org/) | 3.11+ | the data desks and the engine |
| [uv](https://docs.astral.sh/uv/) | latest | runs the Vael Paper server and check |
| [Node.js](https://nodejs.org/) + npm | 20+ | builds the reader |
| [Hermes Agent](https://hermes-agent.nousresearch.com) | latest | the agent that writes and schedules |

Everything else is zero-dependency: the data desks use only Python's standard
library (no `pip install` needed for them), and the example pulls from free,
keyless APIs (Open-Meteo, Yahoo Finance). Tested on macOS and Linux.

### 1. Install the required software

**Python + uv:**

```bash
# Python 3.11+ — your system package manager, pyenv, or homebrew
brew install python                       # macOS
sudo apt install python3 python3-venv     # Debian / Ubuntu

# uv — the fast Python package manager the engine uses
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Node.js 20+ and npm:**

```bash
# macOS
brew install node
# Debian / Ubuntu
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs
```

**Hermes Agent** — the framework this example runs on:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

hermes setup      # one-time setup wizard
hermes model      # pick your provider + model (local or hosted)
```

A modest model you can run locally is enough — the design keeps every prompt
small on purpose. Where to put a model and which to pick is in Hermes's own
docs; you can switch any time with `hermes model`.

### 2. Install Vael Paper (the engine that prints it)

The reader/engine is a separate project. Clone it and build the reader once:

```bash
git clone https://github.com/vaelkeep/vael-paper.git ~/vael-paper
cd ~/vael-paper

npm --prefix reader install
npm --prefix reader run build
```

### 3. Install the agent (this repo)

Clone this repo wherever you keep it — it is the agent's working directory:

```bash
git clone <your-fork-or-path> vael-paper-agent
cd vael-paper-agent
```

Install the `write-edition` procedure as a Hermes **skill**, so a session or a
scheduled job can load it by name:

```bash
hermes skills install skills/vael-paper-write
```

That's the whole install. The data desks just run (standard library only), and
the skill already knows the format contract and the fix-for-every-check-code
table. There is nothing else to build.

### 4. Print your first edition

Editions are *output* — the repo ships the fixtures, not a finished paper. Ask
Hermes for one, from this repo's directory so `AGENTS.md` loads:

```bash
cd vael-paper-agent
hermes
```

> Write tomorrow's edition. Use the vael-paper-write skill. The material is in
> inbox/.

That writes `editions/<date>/articles/`. Now point the server at **this repo's**
`editions/` so it prints *your* paper, not the engine's demo:

```bash
cd ~/vael-paper/server
VAEL_PAPER_EDITIONS=/absolute/path/to/vael-paper-agent/editions \
VAEL_PAPER_READER=/absolute/path/to/vael-paper/reader/dist \
  uv run vael-paper          # serves on http://localhost:8791
```

Open <http://localhost:8791>. Turn pages with the arrow keys; press **Source**
to see the markdown behind any page. The first run is the fiction sample —
next, make it yours.

---

## 💡 Usage — sample prompts

The whole generator is driven by plain prompts to Hermes, run from this repo's
directory. Here are the ones you'll use, in order.

**The sample paper, no real data needed:**

> Write tomorrow's edition. Use the vael-paper-write skill. The material is in
> inbox/.

**Make it yours — run the live desks only:**

> Run the data desks into `editions/<date>/articles/`: steps, ledger, weather for
> my town (use --place), and finance. Then check with vael-paper-check and fix
> until "ok" is true.

**One desk at a time, to tune it:**

> Run the finance desk for AFLAC (AFL) and UnitedHealth (UNH) into today's
> edition folder, then tell me what the check reports.

**Add your new desk to the mix:**

> I added scripts/coin-desk.py. Run it with the other data desks into
> `editions/<date>/`, then check and fix.

**A prose story over your notes:**

> Write a "this week last year" story from inbox/notes.md in the house voice.

**The edition as a whole, done properly:**

> Write tomorrow's edition. Use the vael-paper-write skill: data desks (steps,
> ledger, weather, finance), then prose over feeds.md and notes.md, then the
> lead. Check with vael-paper-check and fix until it's clean, marks first.

---

## ⚙️ Configuration

### The masthead: `editions/paper.json`

The paper's identity lives in one file — the masthead, the motto, the date you
started, and the section order. A generator never writes it: you do, once, by
hand.

```json
{
  "masthead": "my own Daily",
  "motto": "Printed nightly, for one reader",
  "founded": "2026-09-01",
  "sections": [
    { "id": "today", "name": "Today" },
    { "id": "weather", "name": "Weather" },
    { "id": "financial", "name": "Financial" },
    { "id": "local", "name": "Local" },
    { "id": "world", "name": "World" }
  ]
}
```

- `founded` is the date your paper began; every issue number and volume is
  worked out from it, so it survives old editions being pruned.
- Sections in this list are the *only* ids the desks may use. Add or remove
  them freely — a story whose section the catalogue doesn't know still prints,
  at the back, with a note.

### The material: `inbox/`

Replace the standing fixtures with your real material. The shape of each file
is in [`inbox/README.md`](inbox/README.md); in short:

```text
inbox/
  feeds.md          the day's news, already cut to a paragraph each, with URLs
  notes.md          lines to resurface ("this week last year", reminders)
  calendar.json     the week ahead
  ledger.json       household spending
  steps.csv         date,steps
  photos/           optional — a photo library, by filename
  portfolio.json    optional — holdings at the close, for a Money desk
```

**Feed the desks, not the model.** The point of the inbox is that the model
picks and writes from a handful of items — it never reads four hundred. So a
small upstream script (or a Hermes cron `script=` step) is what should fill
`inbox/feeds.md` each day, cut to paragraphs with URLs. That script is yours;
model-writing raw feeds is exactly what this design avoids.

### The live desks

| Desk | Source | Default data | Config |
|---|---|---|---|
| `weather-desk.py` | Open-Meteo (free, no key) | Washington DC forecast | `--lat` / `--lon` / `--place`, or `WEATHER_LAT` / `WEATHER_LON` / `WEATHER_PLACE`; `--c` for Celsius |
| `finance-desk.py` | Yahoo Finance (free, no key) | NVDA, AMZN, MU | tickers as arguments: `finance-desk.py <dir> AAPL MSFT` |
| `steps-desk.py` | `inbox/steps.csv` | the shipped fixture | `steps-desk.py <dir> [date] [csv]` |
| `ledger-desk.py` | `inbox/ledger.json` | the shipped fixture | `ledger-desk.py <dir> [date] [json]` |

---

## 🎬 Examples — write your own desk

Everything beyond the stock desks is a **data desk**: a small Python script
that reads a source and writes one markdown article. It is code, not a model,
so it is right every night. `weather-desk.py` and `finance-desk.py` are working
templates for exactly this pattern:

1. **Fetch** a source — a file in `inbox/` or a live API (both use only the
   standard library).
2. **Render** frontmatter + markdown into `editions/<date>/articles/<nn>.md`,
   using the fields the engine expects (`headline`, `deck`, `section`,
   `priority`, `chart:`, `sources:`).
3. **Check** with `vael-paper-check`; the skill has a fix for every code.
4. Never **invent** a number — if the fetch fails, exit nonzero and drop the
   story rather than guess.

A minimal desk, as a template:

```python
#!/usr/bin/env python3
"""Desk: a "coin desk" — today's small random fact of the day."""
import json, sys, urllib.request
from pathlib import Path

def build_article(edition_dir: Path):
    # 1. fetch (or read inbox/) — example: a tiny public API, keyless
    with urllib.request.urlopen("https://api.fact.example/today", timeout=15) as r:
        fact = json.load(r)["fact"]

    # 2. render the article
    (edition_dir / "articles").mkdir(parents=True, exist_ok=True)
    (edition_dir / "articles" / "05-fact-of-the-day.md").write_text(f"""---
headline: Fact of the Day
deck: One small thing, before the world
section: today
priority: 4
sources:
  - name: Fact API
    url: https://api.fact.example
---

{fact}
""")
    print("wrote fact-of-the-day")

if __name__ == "__main__":
    build_article(Path(sys.argv[1]))
```

Then tell Hermes to run it — the agent calls the script inside the write →
check → fix loop (see [Usage](#-usage--sample-prompts)).

---

## 📁 Project structure

```
AGENTS.md                     the paper's standing orders (the "editor").
                              Hermes auto-loads it whenever a session or cron
                              job runs here, so any interaction already
                              behaves like the night editor.
skills/vael-paper-write/      the reusable procedure: the desks, the format
                              contract, and the write → check → fix loop.
scripts/                      the data desks — code, deliberately.
  steps-desk.py               steps.csv      → a "Week in Steps" chart story
  ledger-desk.py              ledger.json    → a household table
  weather-desk.py             Open-Meteo API → a Weather chart + board
  finance-desk.py             Yahoo Finance  → a Financial quote table
samples/lead-desk/            an exemplar front-page story — what the model
                              writes, kept as a house voice and a check target.
inbox/                        what the desks read: feeds, notes, calendar,
                              ledger, steps, photos. See inbox/README.md.
cron/                         how to schedule the nightly run with Hermes cron,
                              and the two workdir gotchas.
editions/                     the paper's identity (paper.json) and its output.
screenshots/                  the images in this README.
```

Generated edition folders (`editions/2026-*/`) are output, not source — they
are gitignored on purpose.

## ✅ The write → check → fix loop

The check is the safety rail. From the Vael Paper checkout:

```bash
cd ~/vael-paper/server
uv run vael-paper-check /path/to/vael-paper-agent/editions/<date> --json
```

The report has two lists, each entry with a `code`, a `message` and a
`file:line` where it knows one:

- **marks** — something is wrong; the edition prints without the broken piece.
  The paper won't be `"ok"` while any remain.
- **lint** — it will print, but badly; a table too wide, a story too short.

`vael-paper-check` exits 1 when there are marks, so the fix loop can gate
publishing. Never publish on red — an edition with marks is an empty edition
waiting to happen. Fix every mark, then the lint you can, at the named
`file:line`; the `vael-paper-write` skill has the fix for every code. Repeat
until `"ok": true`; stop at `"clean": true` when you can.

## 🌙 Run it every night

Scheduling is one `cronjob`. The full setup — including the two `workdir`
gotchas and the reason cron needs a real path — is in
[`cron/README.md`](cron/README.md). In short:

```bash
hermes skills install skills/vael-paper-write   # once
```

then create the job with `workdir` pointed at this repo, `skills =
[vael-paper-write]`, schedule `every day at 4am`, and the prompt:

> Write tomorrow's edition. The inbox material is in inbox/. Use the write
> skill: run the data desks (steps, ledger, weather, finance), then the prose
> desks over feeds.md and notes.md, then the lead; check with vael-paper-check
> and fix until "ok": true.

Your paper is on the front porch (well: at <http://localhost:8791>) at
breakfast — and if a desk gave up it shows as a printer's mark in the reader,
not a blank page and not a fatal failure at 4 a.m.

---

## 📜 License

Licensed under the [MIT License](LICENSE) — do what you like, keep the
notice. The paper you generate is yours.

The `inbox/` fixtures and the lead-desk sample are fiction, written to match
the Vael Paper demo's shapes, and keep its fiction note. The Vael Paper engine
has its own MIT license — see its `LICENSE` and `NOTICE`.

© 2026 Rodney Moore
