#!/usr/bin/env bash
#
# One command from nothing to reading a paper.
#
#   ./quickstart.sh
#
# Fetches the engine, builds its reader once, runs the four data desks against
# live feeds, assembles an edition and serves it. No agent and no model needed:
# the data desks are code, so the weather and the markets in the paper you get
# are real and current. The prose and the front page are the shipped samples,
# because those are the part that needs a model — see the README for adding one.
#
# Everything lands in .quickstart/, which is gitignored. Delete it to start over.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$REPO/.quickstart"
ENGINE="$WORK/vael-paper"
EDITIONS="$WORK/editions"
ENGINE_URL="https://github.com/vaelkeep/vael-paper.git"
SAMPLE="$REPO/samples/edition"

PORT=8791
PLACE=""; LAT=""; LON=""
TICKERS="NVDA AMZN MU"
OPEN_BROWSER=1
SERVE=1

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
say()  { printf '  %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
die()  { printf '\n\033[31merror:\033[0m %s\n\n' "$*" >&2; exit 1; }

usage() {
  cat <<'USAGE'
Usage: ./quickstart.sh [options]

  --place NAME       label for the weather board (needs --lat and --lon too)
  --lat N --lon N    coordinates for the forecast (default: Washington DC)
  --tickers "A B"    quotes for the markets board (default: NVDA AMZN MU)
  --port N           port to serve on (default: 8791)
  --no-open          do not open a browser
  --build-only       assemble the edition and exit without serving
  -h, --help         this

Examples:
  ./quickstart.sh
  ./quickstart.sh --place Berlin --lat 52.52 --lon 13.40 --tickers "SAP ASML"
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --place)   PLACE="${2:?--place needs a name}"; shift 2 ;;
    --lat)     LAT="${2:?--lat needs a number}"; shift 2 ;;
    --lon)     LON="${2:?--lon needs a number}"; shift 2 ;;
    --tickers) TICKERS="${2:?--tickers needs at least one symbol}"; shift 2 ;;
    --port)    PORT="${2:?--port needs a number}"; shift 2 ;;
    --no-open) OPEN_BROWSER=0; shift ;;
    --build-only) SERVE=0; OPEN_BROWSER=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1  (try --help)" ;;
  esac
done

# A place without coordinates would print one city's weather under another
# city's name, which is exactly the kind of quietly wrong page this project
# exists to avoid.
if [ -n "$PLACE" ] && { [ -z "$LAT" ] || [ -z "$LON" ]; }; then
  die "--place also needs --lat and --lon, or the board would carry the wrong city's forecast."
fi

# ---------------------------------------------------------------- preflight
bold "Checking what you have"
MISSING=""
need() {
  if command -v "$1" >/dev/null 2>&1; then say "found    $1"; else warn "missing  $1"; MISSING="$MISSING $1"; fi
}
need git
need python3
need node
need npm

if [ -n "$MISSING" ]; then
  APT=$(echo "$MISSING" | sed 's/\bnode\b/nodejs/; s/\bpython3\b/python3 python3-venv/')
  echo
  die "missing:$MISSING

  macOS:          brew install$MISSING
  Debian/Ubuntu:  sudo apt install -y$APT

Then run ./quickstart.sh again."
fi

PYV=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
  || die "Python 3.11+ required, found $PYV."
say "python   $PYV"

NODEV=$(node -p 'process.versions.node.split(".")[0]')
[ "$NODEV" -ge 18 ] || die "Node 18+ required, found $(node -v)."
say "node     $(node -v)"

mkdir -p "$WORK"

# ------------------------------------------------------------------- engine
echo
bold "The engine that prints it"
if [ -d "$ENGINE/.git" ]; then
  say "already cloned, pulling"
  git -C "$ENGINE" pull --quiet --ff-only || warn "could not fast-forward; using the checkout as it is"
else
  say "cloning vaelkeep/vael-paper"
  git clone --quiet --depth 1 "$ENGINE_URL" "$ENGINE"
fi

if [ -f "$ENGINE/reader/dist/index.html" ]; then
  say "reader already built"
else
  say "building the reader (once; takes a minute)"
  cd "$ENGINE/reader" || die "no reader directory at $ENGINE/reader"
  # `npm ci` needs the lockfile to match package.json; fall back when it does not
  if ! npm ci --silent >/dev/null 2>&1; then
    npm install --silent >/dev/null 2>&1 || die "npm could not install the reader's dependencies"
  fi
  npm run build --silent >/dev/null 2>&1 \
    || die "the reader failed to build. Run it by hand to see why:
    cd $ENGINE/reader && npm run build"
  cd "$REPO"
  say "reader built"
fi

# ------------------------------------------------------- the engine's python
# uv when it is there because it is much faster and is what the engine uses;
# a plain venv otherwise, so a missing uv is not a wall.
echo
bold "The engine's Python"
# Either way the engine's console scripts end up on PATH, so the rest of this
# script just calls vael-paper-check and vael-paper by name.
if command -v uv >/dev/null 2>&1; then
  say "using uv"
  ( cd "$ENGINE/server" && uv sync --quiet ) || die "uv sync failed in $ENGINE/server"
  BIN="$ENGINE/server/.venv/bin"
else
  say "no uv found, using a plain venv"
  BIN="$WORK/venv/bin"
  [ -x "$BIN/python" ] || python3 -m venv "$WORK/venv"
  "$BIN/python" -m pip install --quiet --upgrade pip
  "$BIN/python" -m pip install --quiet -e "$ENGINE/server" \
    || die "could not install the engine into $WORK/venv"
fi
[ -x "$BIN/vael-paper-check" ] || die "the engine installed but its commands are not in $BIN"
PATH="$BIN:$PATH"
say "engine ready"

# ------------------------------------------------------------ the edition
echo
bold "Writing tomorrow's edition"
DATE=$(python3 -c 'import datetime; print(datetime.date.today() + datetime.timedelta(days=1))')
OUT="$EDITIONS/$DATE"
rm -rf "$EDITIONS"
mkdir -p "$OUT/articles"
cp "$REPO/editions/paper.json" "$EDITIONS/paper.json"

WEATHER_ARGS=()
[ -n "$LAT" ] && WEATHER_ARGS+=(--lat "$LAT")
[ -n "$LON" ] && WEATHER_ARGS+=(--lon "$LON")
[ -n "$PLACE" ] && WEATHER_ARGS+=(--place "$PLACE")

# Data desks are code, so these run right now and the numbers are real.
"$REPO/scripts/steps-desk.py"   "$OUT" "$DATE" >/dev/null && say "steps desk    ok"
"$REPO/scripts/ledger-desk.py"  "$OUT" "$DATE" >/dev/null && say "ledger desk   ok"
if "$REPO/scripts/weather-desk.py" "$OUT" "${WEATHER_ARGS[@]+"${WEATHER_ARGS[@]}"}" >/dev/null 2>&1; then
  say "weather desk  ok (live forecast${PLACE:+ for $PLACE})"
else
  warn "weather desk skipped — no network, or Open-Meteo did not answer"
fi
# shellcheck disable=SC2086
if "$REPO/scripts/finance-desk.py" "$OUT" $TICKERS >/dev/null 2>&1; then
  say "finance desk  ok (live quotes: $TICKERS)"
else
  warn "finance desk skipped — no network, or Yahoo did not answer"
fi

# The prose and the front page need a model, which this script deliberately does
# not set up. Borrow the shipped samples so the edition is a whole paper.
for f in "$SAMPLE"/*/articles/*.md; do
  name=$(basename "$f")
  case "$name" in
    01-*|04-*|05-*|06-*|08-*|09-*|11-*) cp "$f" "$OUT/articles/$name" ;;
  esac
done
say "prose + lead  from samples/ (the part that needs a model; those were"
say "                written with Claude — see samples/edition/PROVENANCE.md)"

# ------------------------------------------------------------------- check
echo
bold "Checking it, the way the nightly run does"
if vael-paper-check "$OUT" >/dev/null 2>&1; then
  vael-paper-check "$OUT" 2>&1 | sed 's/^/  /'
else
  vael-paper-check "$OUT" 2>&1 | sed 's/^/  /' || true
  warn "the check found marks; the edition still prints, without the broken piece"
fi

if [ "$SERVE" -eq 0 ]; then
  echo
  bold "Done"
  say "edition at $OUT"
  exit 0
fi

# ------------------------------------------------------------------- serve
echo
bold "Serving it"
if command -v lsof >/dev/null 2>&1 && lsof -i ":$PORT" >/dev/null 2>&1; then
  die "port $PORT is already in use. Try ./quickstart.sh --port 8792"
fi

VAEL_PAPER_EDITIONS="$EDITIONS" \
VAEL_PAPER_READER="$ENGINE/reader/dist" \
  vael-paper --port "$PORT" >"$WORK/server.log" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM

for _ in $(seq 1 40); do
  if curl -fsS "http://localhost:$PORT/api/editions.json" >/dev/null 2>&1; then break; fi
  kill -0 "$SERVER_PID" 2>/dev/null || die "the server exited. Log: $WORK/server.log"
  sleep 0.25
done

URL="http://localhost:$PORT"
echo
bold "Your paper is ready"
say "$URL"
say ""
say "Arrow keys turn the pages. Press Source to see the markdown behind one."
say "The weather and the markets are live. The stories are samples."
say ""
say "Next: add a model and it writes its own. See the README."
say "Ctrl-C to stop."
echo

if [ "$OPEN_BROWSER" -eq 1 ]; then
  if command -v open >/dev/null 2>&1; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1
  fi
fi

wait "$SERVER_PID"
