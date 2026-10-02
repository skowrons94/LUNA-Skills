#!/usr/bin/env python3
"""Render a .pptx to PDF, per-slide PNGs and contact sheets for visual inspection.

    python3 render_deck.py talk.pptx --out /path/to/render [--dpi 80] [--engine auto|powerpoint|soffice]

Engines:
  powerpoint  macOS Microsoft PowerPoint via AppleScript. Most faithful (same fonts,
              EMF/equation rendering as on the podium). PowerPoint is sandboxed, so
              the deck is copied into its container and the PDF moved out afterwards.
  soffice     LibreOffice headless. Portable, but fonts and OMML equations may differ.

Video slides show their poster frame; a blank poster means the audience and any
PDF handout see an empty slide. Outputs: deck.pdf, slides/slide-NN.png, sheet-NN.png.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

PP_CONTAINER = Path.home() / "Library/Containers/com.microsoft.Powerpoint/Data/Documents"


def via_powerpoint(pptx: Path, pdf: Path, wait=5):
    work = PP_CONTAINER / f"render-{uuid.uuid4().hex[:8]}"
    work.mkdir(parents=True)
    try:
        src = work / pptx.name
        shutil.copy2(pptx, src)
        out = work / (pptx.stem + ".pdf")
        hfs_out = subprocess.run(["osascript", "-e", f'POSIX file "{out}" as string'],
                                 capture_output=True, text=True, check=True).stdout.strip()
        # The first save can fail with error -50 while embedded videos are still
        # loading, so retry for up to ~2 minutes.
        script = f'''
        tell application "Microsoft PowerPoint"
            open POSIX file "{src}"
            delay {wait}
            set done to false
            repeat 40 times
                try
                    save active presentation in "{hfs_out}" as save as PDF
                    set done to true
                    exit repeat
                on error
                    delay 3
                end try
            end repeat
            close active presentation saving no
            if not done then error "save as PDF kept failing"
        end tell'''
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if r.returncode or not out.exists():
            raise RuntimeError(f"PowerPoint export failed: {r.stderr.strip()}")
        shutil.move(str(out), pdf)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def via_soffice(pptx: Path, pdf: Path):
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        raise RuntimeError("LibreOffice not found")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([exe, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(pptx)],
                       check=True, capture_output=True)
        shutil.move(str(Path(tmp) / (pptx.stem + ".pdf")), pdf)


def contact_sheets(pngs, out_dir: Path, per=12, cols=3):
    from PIL import Image, ImageDraw

    sheets = []
    for k in range(0, len(pngs), per):
        batch = pngs[k:k + per]
        w, h = 640, 360
        rows = (len(batch) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (w + 4) + 4, rows * (h + 4) + 4), "#7f7f7f")
        for i, f in enumerate(batch):
            im = Image.open(f).convert("RGB").resize((w, h))
            x, y = 4 + (i % cols) * (w + 4), 4 + (i // cols) * (h + 4)
            sheet.paste(im, (x, y))
            ImageDraw.Draw(sheet).text((x + 6, y + 4), str(k + i + 1), fill="magenta")
        p = out_dir / f"sheet-{k // per + 1:02d}.png"
        sheet.save(p)
        sheets.append(p)
    return sheets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dpi", type=int, default=80)
    ap.add_argument("--engine", choices=["auto", "powerpoint", "soffice"], default="auto")
    a = ap.parse_args()

    pptx = a.pptx.resolve()
    a.out.mkdir(parents=True, exist_ok=True)
    pdf = a.out / "deck.pdf"
    engines = {"powerpoint": [via_powerpoint], "soffice": [via_soffice]}.get(a.engine)
    if engines is None:
        engines = ([via_powerpoint] if sys.platform == "darwin" and Path("/Applications/Microsoft PowerPoint.app").exists()
                   else []) + [via_soffice]
    err = None
    for fn in engines:
        try:
            fn(pptx, pdf)
            print(f"PDF via {fn.__name__[4:]}: {pdf}")
            break
        except Exception as e:  # try the next engine
            err = e
            print(f"{fn.__name__[4:]} failed: {e}", file=sys.stderr)
    else:
        sys.exit(f"No renderer succeeded: {err}")

    slides = a.out / "slides"
    slides.mkdir(exist_ok=True)
    subprocess.run(["pdftoppm", "-r", str(a.dpi), "-png", str(pdf), str(slides / "slide")], check=True)
    pngs = sorted(slides.glob("slide-*.png"))
    for s in contact_sheets(pngs, a.out):
        print("sheet:", s)
    print(f"{len(pngs)} slides rendered to {slides}")


if __name__ == "__main__":
    main()
