#!/usr/bin/env python3
"""Render docs/nightly-run.gif from docs/nightly-run.html.

The scene is a single page that takes ?n=<lines visible>, so the animation is
made by stepping n and screenshotting each frame. Chrome is asked for one frame
at a time; it writes the file and then, with --virtual-time-budget set, often
declines to exit, so we wait on the file rather than the process.

    python3 docs/render-nightly-gif.py

Needs Google Chrome and Pillow, both development-only.
"""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DOCS = Path(__file__).resolve().parent
SCENE = (1100, 520)          # matches .scene in nightly-run.html
FRAMES = 23                  # transcript lines; see T in the page
HOLD_END = 5                 # frames to sit on the finished paper
HOLD_LINT = 4                # frames to sit on the red check, so it is readable
LINT_AT = 17                 # last line of the lint report
FRAME_MS = 420
END_MS = 1520
CHROME_TIMEOUT = 30

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
]


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    sys.exit("No Chrome or Chromium found; install one or edit CHROME_CANDIDATES.")


def shoot(chrome: str, url: str, out: Path, scale: int) -> None:
    out.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.Popen(
            [
                chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--no-first-run", f"--user-data-dir={tmp}",
                f"--force-device-scale-factor={scale}",
                f"--window-size={SCENE[0]},{SCENE[1]}",
                "--virtual-time-budget=4000",
                f"--screenshot={out}", url,
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
        )
        deadline = time.time() + CHROME_TIMEOUT
        settled, last = 0, -1
        try:
            while time.time() < deadline:
                if proc.poll() is not None:
                    break
                size = out.stat().st_size if out.exists() else -1
                settled = settled + 1 if size > 0 and size == last else 0
                last = size
                if settled >= 3:
                    break
                time.sleep(0.2)
        finally:
            if proc.poll() is None:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    if not out.exists():
        sys.exit(f"Chrome produced no frame for {url}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scale", type=int, default=1, help="device pixel ratio (default 1)")
    args = ap.parse_args()

    from PIL import Image

    src = DOCS / "nightly-run.html"
    out = DOCS / "nightly-run.gif"
    if not src.exists():
        sys.exit(f"missing {src}")

    chrome = find_chrome()
    frames, durations = [], []
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        for n in range(1, FRAMES + 1):
            path = tmpdir / f"f{n:03d}.png"
            shoot(chrome, f"{src.as_uri()}?n={n}", path, args.scale)
            frames.append(Image.open(path).convert("RGB"))
            durations.append(FRAME_MS)
            # linger where the reader needs a moment
            if n == LINT_AT:
                frames += [frames[-1]] * HOLD_LINT
                durations += [FRAME_MS] * HOLD_LINT
            print(f"  frame {n:>2}/{FRAMES}", end="\r", flush=True)

        frames += [frames[-1]] * HOLD_END
        durations += [FRAME_MS] * (HOLD_END - 1) + [END_MS]

        # One shared palette, built from the busiest frame, so the ground does
        # not shimmer between frames the way a per-frame palette makes it.
        palette = frames[-1].quantize(colors=64, method=Image.MEDIANCUT)
        quantised = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
        quantised[0].save(
            out, save_all=True, append_images=quantised[1:],
            duration=durations, loop=0, optimize=True, disposal=1,
        )

    size = out.stat().st_size / 1024
    print(f"wrote {out.relative_to(DOCS.parent)} "
          f"({frames[0].width}x{frames[0].height}, {len(frames)} frames, {size:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
