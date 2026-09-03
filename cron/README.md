# Scheduling the nightly run with Hermes cron

`launchd` and a shell script can start a writer, but they cannot run the
write → check → fix loop — that needs an agent. Hermes cron runs the whole
loop at 04:00 and delivers the result to you.

## Install the skill first

The generator skill lives in this repo at `skills/vael-paper-write/`. Install
it into Hermes so the job can load it by name:

```
hermes skills install skills/vael-paper-write
```

## Create the job

From this repo's root (or at least with the same `workdir`), create the job
with the `cronjob` tool / `hermes cron add`:

```yaml
schedule: every day at 4am
workdir:  /home/you/vael-paper-agent     # must resolve to this directory,
                                         # so AGENTS.md + inbox are in context
skills:   [vael-paper-write]
name:     nightly edition
prompt: >
  Write tomorrow's edition of the Vael Paper. The inbox material is in
  inbox/ (calendar.json, ledger.json, steps.csv, feeds.md, notes.md,
  photos/). Use the vael-paper-write skill: run the data desks — steps,
  ledger, weather (scripts/weather-desk.py, live forecast), and finance
  (scripts/finance-desk.py, quotes for NVDA AMZN MU) — then the prose desks,
  then the lead; check with vael-paper-check and fix until "ok": true.
deliver:  all        # e.g. telegram, or an explicit channel
```

### The two `workdir` gotchas

1. **Resolve the real path.** Cron jobs get a fresh session with no
   conversation context; they must find the paper by path. A relative
   `workdir` or a `~/` that does not expand will silently start in the wrong
   place and produce an empty paper.
2. **Point `workdir` at the agent repo, not the paper repo.** The generator
   lives here. Keep this folder's AGENTS.md in context so every interaction
   behaves like the night editor. The seed `editions/paper.json` can be
   symlinked or copied into the paper repo's `editions/` if you keep the two
   apart.

## The check step is the safety

The job prompt tells the agent to keep checking until `"ok": true` — the same
gate `GENERATING.md` calls "never publish on red." If the agent cannot reach
`"ok"`, its report (delivered to you) says exactly which marks remain. That is
the desired failure: visible at breakfast, not fatal at four in the morning.

## Test it before you trust it

```
hermes cron run <job-id>     # fire once now, in the background
hermes cron list
```

Iterate on the desk prompts, not the model. Run it a few nights watching the
report; only then rely on it silently.