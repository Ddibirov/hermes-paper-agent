# What wrote what, in the published sample

This edition is what the reader at
<https://vaelkeep.github.io/hermes-paper-agent/> serves, and what the
screenshots in the README show. It is a real edition in the sense that matters
— it was assembled by the desks, it passes `vael-paper-check` at `"ok": true`
and `"clean": true`, and the engine printed it without special handling. But
the stories in it were not written by a small local model, and a demo that
leaves you to assume otherwise is not worth having.

## The data desks: code, run for real

These four ran against live sources when the edition was built. Every figure in
them is real and was fetched at that moment. No model touched them, which is
the whole point of a data desk.

| Article | Desk | Source |
|---|---|---|
| `02-your-week-in-weather.md` | `scripts/weather-desk.py` | Open-Meteo, live |
| `03-the-markets.md` | `scripts/finance-desk.py` | Yahoo Finance, live |
| `07-household-ledger.md` | `scripts/ledger-desk.py` | `inbox/ledger.json` |
| `10-the-week-in-steps.md` | `scripts/steps-desk.py` | `inbox/steps.csv` |

## The prose and the lead: written with Claude

These seven were written with Claude while the desks were being built, working
from `inbox/feeds.md`, `inbox/notes.md` and `inbox/calendar.json` in the house
voice — the same job a prose desk does, done by a much larger model than you
would run at home.

| Article | Section | Written from |
|---|---|---|
| `01-your-friday.md` | the lead | everything the other desks filed, plus the calendar |
| `04-orange-line.md` | local | `inbox/feeds.md` |
| `05-bike-lanes.md` | local | `inbox/feeds.md` |
| `06-power-cap.md` | technology | `inbox/feeds.md` |
| `08-rothko.md` | local | `inbox/feeds.md` |
| `09-this-week-last-year.md` | notes | `inbox/notes.md` |
| `11-the-week-ahead.md` | week | `inbox/calendar.json` |

## What this means for you

A nightly run on a modest local model produces the same *shape* — one story per
desk, the same frontmatter, the same check passing — and noticeably plainer
prose. That is expected and it is the trade the design makes: the figures are
never at risk because they are code, so the model is only ever on the hook for
sentences.

If you want to see what your own model does with it, run the desks over the
same fixtures and compare. The material in `inbox/` is the same material these
were written from.

## Why the fixtures are fiction

The `inbox/` material is invented, written to match the shapes the Vael Paper
demo uses. Nell, the Henley review, the dentist and the fennel are not real,
and neither is anything in `feeds.md`, whose links all point at `example.com`.
The weather and the market figures, by contrast, are real.
