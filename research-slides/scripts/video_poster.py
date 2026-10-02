#!/usr/bin/env python3
"""Extract a poster frame (PNG) from a rendered animation.

    python3 video_poster.py clip.mp4 --at last  --out clip_poster.png
    python3 video_poster.py clip.mp4 --at 12.5 --out clip_poster.png

The poster is what the slide shows before the click and in every PDF export. A
Manim scene usually starts on an empty background, so the first frame makes the
slide look blank; prefer `last` (the frozen conclusion) or a representative time.
Reports the frame's brightness spread so a near-blank poster is caught.
"""
import argparse
import subprocess
from pathlib import Path


def duration(mp4):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4", type=Path)
    ap.add_argument("--at", default="last", help="'first', 'last' or a time in seconds")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    if a.at == "first":
        t = 0.0
    elif a.at == "last":
        t = max(duration(a.mp4) - 0.05, 0.0)
    else:
        t = float(a.at)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(a.mp4), "-frames:v", "1", str(a.out)],
                   check=True)
    from PIL import Image, ImageStat

    std = ImageStat.Stat(Image.open(a.out).convert("L")).stddev[0]
    print(f"poster {a.out} at t={t:.2f}s, brightness std {std:.1f}")
    if std < 8:
        print("WARNING: poster is nearly uniform; choose a later --at so the slide is not blank")


if __name__ == "__main__":
    main()
