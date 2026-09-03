#!/usr/bin/env python3
"""Render docs/architecture.html to docs/architecture.png.

The diagram is HTML rather than Mermaid because it is set in the paper's own
faces and colours. This script drives headless Chrome over it, then trims the
sheet to its content so the image has no dead margin at the foot.

    python3 docs/render-architecture.py [--scale 2]

Needs Google Chrome and Pillow. Both are development-only: nothing the desks
do requires either.
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
SHEET_WIDTH = 1360          # matches .sheet in architecture.html
SHEET_PAD_BOTTOM = 26       # ditto, so the trim keeps the sheet's own margin
PAPER = (250, 247, 240)     # --paper #faf7f0
CHROME_TIMEOUT = 60         # hard cap; the render normally settles far sooner

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


def trim_to_content(path: Path, scale: int) -> None:
    """Drop the run of pure-paper rows below the sheet.

    Done with a difference image and getbbox() rather than a pixel loop: the
    same answer, but in C and in a moment.
    """
    from PIL import Image, ImageChops

    img = Image.open(path).convert("RGB")
    w, h = img.size
    ground = Image.new("RGB", img.size, PAPER)
    ink = ImageChops.difference(img, ground).convert("L").point(lambda v: 255 if v > 12 else 0)
    box = ink.getbbox()
    if box is None:                       # a blank sheet: nothing to trim
        return
    bottom = min(h, box[3] + SHEET_PAD_BOTTOM * scale)
    img.crop((0, 0, w, bottom)).quantize(colors=64).save(path, optimize=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scale", type=int, default=2, help="device pixel ratio (default 2)")
    args = ap.parse_args()

    src = DOCS / "architecture.html"
    out = DOCS / "architecture.png"
    if not src.exists():
        sys.exit(f"missing {src}")

    # Remove any previous render first, so a failed run cannot quietly pass off
    # a stale image as a fresh one.
    out.unlink(missing_ok=True)

    # Headless Chrome writes the screenshot and then, with --virtual-time-budget
    # set, often declines to exit. So do not wait on the process: wait for the
    # file to appear and stop growing, then stop Chrome ourselves.
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.Popen(
            [
                find_chrome(),
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--no-first-run",
                f"--user-data-dir={tmp}",
                f"--force-device-scale-factor={args.scale}",
                f"--window-size={SHEET_WIDTH},900",
                # the faces come off Google Fonts; give them time to arrive
                "--virtual-time-budget=8000",
                f"--screenshot={out}",
                src.as_uri(),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,          # so the helpers go down with it
        )
        deadline = time.time() + CHROME_TIMEOUT
        settled, last_size = 0, -1
        try:
            while time.time() < deadline:
                if proc.poll() is not None:
                    break                     # exited on its own; nothing to wait for
                size = out.stat().st_size if out.exists() else -1
                settled = settled + 1 if size > 0 and size == last_size else 0
                last_size = size
                if settled >= 3:              # unchanged for ~0.75s: written
                    break
                time.sleep(0.25)
        finally:
            if proc.poll() is None:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)

    if not out.exists() or out.stat().st_size == 0:
        sys.exit("Chrome produced no screenshot; run the command by hand to see why.")

    trim_to_content(out, args.scale)
    from PIL import Image

    w, h = Image.open(out).size
    print(f"wrote {out.relative_to(DOCS.parent)} ({w}x{h}, {out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
