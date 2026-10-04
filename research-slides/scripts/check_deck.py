#!/usr/bin/env python3
"""Audit a .pptx for problems that are easy to miss before a talk.

    python3 check_deck.py talk.pptx [--minutes 25] [--min-font 14]

Checks, per slide: text smaller than --min-font (footers, page numbers and
figure captions at 10-12 pt are allowed), shapes outside the canvas, missing
speaker notes, slides without a title, dense text, images shown at < 150 dpi,
videos whose poster frame is blank, and the time budget written at the start
of the notes ("1.5 min. ..."). Consecutive build slides sharing identical notes
are counted once. Exit code 1 if any ERROR is found.
"""
import argparse
import io
import re
import sys

from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Emu

# "1.5 min. ..." counts; "~8 min for part one" on a divider or "25 min talk: ..."
# on the title slide is a summary and does not.
TIME = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*min\.", re.I)


def inches(v):
    return Emu(v).inches if v is not None else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--minutes", type=float, help="allotted talk time, excluding questions")
    ap.add_argument("--min-font", type=float, default=14)
    ap.add_argument("--max-words", type=int, default=90)
    a = ap.parse_args()

    prs = Presentation(a.pptx)
    W, H = inches(prs.slide_width), inches(prs.slide_height)
    errors = warnings = 0
    total, prev_notes, in_backup = 0.0, None, False

    def report(level, i, msg):
        nonlocal errors, warnings
        errors += level == "ERROR"
        warnings += level == "WARN"
        print(f"{level:5s} slide {i:3d}: {msg}")

    for i, s in enumerate(prs.slides, 1):
        texts = [sh.text_frame.text for sh in s.shapes if sh.has_text_frame]
        if any(t.strip().lower() in ("backup", "backup slides") for t in texts):
            in_backup = True
        words = 0
        # a title placeholder with text, or any run >= 28 pt (divider / closing slides)
        has_title = any(sh.is_placeholder and sh.placeholder_format.idx == 0 and sh.text_frame.text.strip()
                        for sh in s.shapes if sh.has_text_frame) or any(
            r.font.size and r.font.size.pt >= 28 and r.text.strip()
            for sh in s.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs for r in p.runs)
        is_media = False
        for sh in s.shapes:
            x, y, w, h = inches(sh.left), inches(sh.top), inches(sh.width), inches(sh.height)
            decorative = "alphaModFix" in sh._element.xml  # e.g. a faded watermark image
            if sh.left is not None and not decorative and (x < -0.05 or y < -0.05 or x + w > W + 0.05 or y + h > H + 0.05):
                report("WARN", i, f"'{sh.name}' extends outside the canvas")
            if sh.has_text_frame:
                is_footer = y > H - 0.6
                is_caption = False
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        words += len(r.text.split())
                        sz = r.font.size.pt if r.font.size else None
                        if sz and r.font.italic and sz >= 11:
                            is_caption = True
                        rpr = r._r.rPr
                        if rpr is not None and rpr.get("baseline"):  # super/subscripts
                            continue
                        if sz and sz < a.min_font and not is_footer and not is_caption and r.text.strip():
                            report("WARN", i, f"{sz:.0f} pt text '{r.text.strip()[:40]}'")
                            break
            if sh.shape_type == 13 or sh.shape_type == 16:
                xml = sh._element.xml
                if "videoFile" in xml or "p14:media" in xml:
                    is_media = True
                    try:
                        from PIL import Image, ImageStat

                        blip = sh._element.find(".//" + qn("a:blip"))
                        blob = s.part.related_part(blip.get(qn("r:embed"))).blob
                        img = Image.open(io.BytesIO(blob)).convert("L")
                        if ImageStat.Stat(img).stddev[0] < 8:
                            report("ERROR", i, f"video '{sh.name}' has a blank poster frame (PDF/handout shows nothing)")
                    except Exception:
                        report("WARN", i, f"video '{sh.name}': poster frame not readable")
                elif sh.shape_type == 13 and w > 0 and not decorative:
                    try:
                        px_w, _ = sh.image.size
                        dpi = px_w / w
                        if dpi < 150 and sh.image.ext.lower() in ("png", "jpg", "jpeg"):
                            report("WARN", i, f"image '{sh.name}' shown at {dpi:.0f} dpi")
                    except Exception:
                        pass
        if not has_title and not is_media and i > 1:
            report("WARN", i, "no title")
        if words > a.max_words:
            report("WARN", i, f"{words} words on the slide")
        notes = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
        closing = any(t.strip().lower().startswith("thank") for t in texts)
        if not notes and i > 1 and not in_backup and not closing:
            report("WARN", i, "no speaker notes")
        m = TIME.match(notes)
        if m and not in_backup and notes != prev_notes:
            total += float(m.group(1))
        prev_notes = notes

    print(f"\n{len(prs.slides)} slides, {W:.2f} x {H:.2f} in; planned main-talk time from notes: {total:.1f} min")
    if a.minutes and total:
        if total > a.minutes:
            report("ERROR", 0, f"planned {total:.1f} min exceeds the {a.minutes:.0f} min slot")
        elif total < 0.8 * a.minutes:
            report("WARN", 0, f"planned {total:.1f} min leaves more than 20 % of the {a.minutes:.0f} min slot unused")
    print(f"{errors} error(s), {warnings} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
