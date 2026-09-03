# The inbox — what the desks read

A newspaper's desks are fed, not let loose on the internet. Put material here
(staged by an upstream script or your own cron) and the desks read only this
folder. The whole point of the inbox is that a modest model is asked to *pick
and write*, never to *read four hundred items*.

## Layout

```
inbox/
  feeds.md          the day's news, already summarised to a paragraph each, with URLs
  notes.md          for the desk that surfaces something you wrote a year ago
  calendar.json     the week ahead, for the data desk / lead desk
  ledger.json       household spending, for the ledger data desk
  steps.csv         date,steps, for the steps data desk
  portfolio.json    holdings at the close, for a Money desk
  photos/           a photo library the household desk may draw on, by filename

**Weather and markets are not files here.** They are live feeds: the weather
desk (`scripts/weather-desk.py`) fetches an Open-Meteo forecast, and the
finance desk (`scripts/finance-desk.py`) fetches Yahoo Finance quotes — both
at run time, neither needing an inbox entry. They do need their sections in
`editions/paper.json` (`weather`, `financial` — already added in this example)
and, for weather, coordinates (`WEATHER_LAT` / `WEATHER_LON` / `WEATHER_PLACE`,
or `--lat/--lon/--place`). Finance takes tickers as arguments and defaults to
NVDA AMZN MU.
```

Anything a desk references must be in here. Do not invent sources.

## feeds.md — the shape

One item per block, already cut to a paragraph and carrying its URL. The prose
desk's job is to pick three to five and write, not to summarise the firehose.

```markdown
## Line single-tracked past Eastern Market

Metro is single-tracking the Orange Line between Stadium–Armory and Eastern
Market until the seventeenth for track and platform work. Trains every
fifteen minutes; a shuttle fills the gap.

https://wmata.example/advisories/orange
```

Keep each to a paragraph. Include the URL on its own line — the desk reads the
block and, if it uses the item, must carry a `sources:` entry for it.

## notes.md — the shape

A line per item, from the desk that surfaces last year's writing or a reminder
you set and forgot. Keep entries short; the model's value is in *choosing* what
to resurface, not in reading long passages.

## Staged by code, on schedule

Best to fill the inbox with a small script (or a Hermes cron `script=` step)
before the edition job runs, so the generator itself only ever writes the
edition folder. A line in the README:

```
inbox-collect.sh   →  fetches the feeds, cuts to paragraphs, writes feeds.md
                     (plus calendar/ledger/steps exports from their sources)
```

Do not automate the paper's identity (paper.json) — only the material.