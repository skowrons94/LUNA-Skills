"""Build PowerPoint decks in the user's house style with python-pptx.

The default ("house") layout is drawn by this module on python-pptx's blank
presentation: red header bar with a white bold title, grey footer rule, page
number, and full-red title/divider/closing slides. No logos or third-party
templates are bundled; pass your own .pptx as template=, and your own image
files as logos or badges, only where you are entitled to use them.
Every helper places shapes in inches on a 13.33 x 7.50 in canvas.

    import sys; sys.path.insert(0, "SKILL_DIR/scripts")
    from deck import Deck, LEFT_FIG, RIGHT_TEXT

    d = Deck(footer="A. Author  |  Institute  |  Conference 2026")
    d.title_slide("Direct and indirect approaches ...", subtitle="The ^{14}N(p,γ)^{15}O reaction ...",
                  author="A. Author", affiliation="Institute",
                  event="Conference 2026", date="10/09/2026")
    s = d.content("CNO neutrinos: a probe limited by nuclear physics")
    s.figure("plots/cno_flux.png", LEFT_FIG, caption="Source: journal, volume (year)")
    s.bullets(["Flux ∝ **C+N abundance in the core**", "S_{114} is the **2nd largest term**"], RIGHT_TEXT)
    s.notes("1.5 min. ...")
    d.save("talk.pptx")

Inline markup in every text helper: **bold**, ==accent red==, ^{superscript},
_{subscript}. Use Unicode for Greek letters and symbols (γ, β, τ, ∝, →, ±).
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

SKILL_DIR = Path(__file__).resolve().parents[1]
HOUSE = "house"  # built-in layout drawn by this module; no template file needed

# House palette.
RED = RGBColor(0xAA, 0x00, 0x04)      # header bar, callouts, key numbers
TEXT = RGBColor(0x39, 0x3D, 0x3F)     # body text
GREY = RGBColor(0x6E, 0x73, 0x76)     # captions, page number, secondary KPI box
LIGHT = RGBColor(0xF2, 0xF2, 0xF2)    # card bodies
ORANGE = RGBColor(0xFF, 0x7D, 0x0D)   # secondary highlight inside figures/equations
BLUE = RGBColor(0x1F, 0x4E, 0x79)     # card header (first column)
GREEN = RGBColor(0x2E, 0x7D, 0x32)    # card header (second column)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NAVY = RGBColor(0x0B, 0x12, 0x20)     # Manim background, for video slides

W, H = 13.333, 7.5


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float


# Standard regions of the content slide (inches).
BODY = Box(0.5, 0.95, 12.33, 5.95)
LEFT_FIG = Box(0.5, 0.95, 6.9, 4.3)        # main figure, left
RIGHT_TEXT = Box(7.7, 1.5, 5.1, 3.6)       # bullets beside the figure
BOTTOM_BAND = Box(0.5, 5.55, 12.33, 1.3)   # callout / KPI row
LEFT_HALF = Box(0.5, 0.95, 6.0, 5.9)
RIGHT_HALF = Box(6.83, 0.95, 6.0, 5.9)


def _rgb(c):
    return c if isinstance(c, RGBColor) else RGBColor.from_string(c.lstrip("#"))


_TOKEN = re.compile(r"(\*\*|==|\^\{[^}]*\}|_\{[^}]*\})")


def add_rich_text(paragraph, text, size=18, color=TEXT, bold=False, font=None, accent=RED):
    """Append runs to a paragraph, honouring **bold**, ==accent==, ^{sup}, _{sub}."""
    state = {"bold": bold, "accent": False}
    for tok in _TOKEN.split(text):
        if not tok:
            continue
        if tok == "**":
            state["bold"] = not state["bold"]
            continue
        if tok == "==":
            state["accent"] = not state["accent"]
            continue
        baseline = 0
        if tok.startswith("^{"):
            tok, baseline = tok[2:-1], 30000
        elif tok.startswith("_{"):
            tok, baseline = tok[2:-1], -25000
        run = paragraph.add_run()
        run.text = tok
        f = run.font
        f.size = Pt(size)
        f.bold = state["bold"]
        f.color.rgb = accent if state["accent"] else _rgb(color)
        if font:
            f.name = font
        if baseline:
            run._r.get_or_add_rPr().set("baseline", str(baseline))
    return paragraph


def _set_bullet(paragraph, char="•", indent_in=0.25, level=0):
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set("marL", str(int(Inches(indent_in * (level + 1)))))
    pPr.set("indent", str(int(-Inches(indent_in))))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", char)


def _no_bullet(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    if pPr.find(qn("a:buNone")) is None:
        etree.SubElement(pPr, qn("a:buNone"))


class Slide:
    """Thin wrapper around a python-pptx slide with house-style components."""

    def __init__(self, deck: "Deck", slide):
        self.deck = deck
        self.slide = slide
        self.shapes = slide.shapes

    # -- text ---------------------------------------------------------------
    def text(self, text, box: Box, size=18, color=TEXT, bold=False, align="left",
             anchor="top", font=None, line_spacing=1.1):
        tb = self.shapes.add_textbox(Inches(box.x), Inches(box.y), Inches(box.w), Inches(box.h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE,
                              "bottom": MSO_ANCHOR.BOTTOM}[anchor]
        for i, line in enumerate(text.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
            p.line_spacing = line_spacing
            add_rich_text(p, line, size=size, color=color, bold=bold, font=font)
        return tb

    def bullets(self, items, box: Box = RIGHT_TEXT, size=18, color=TEXT, gap_pt=8, numbered=False):
        """Bulleted list. An item may be a (text, [sub-items]) tuple for one sub-level."""
        tb = self.shapes.add_textbox(Inches(box.x), Inches(box.y), Inches(box.w), Inches(box.h))
        tf = tb.text_frame
        tf.word_wrap = True
        first = True
        n = 0
        for item in items:
            subs = []
            if isinstance(item, tuple):
                item, subs = item
            n += 1
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.space_after = Pt(gap_pt)
            _set_bullet(p, char=f"{n}." if numbered else "•")
            add_rich_text(p, item, size=size, color=color)
            for sub in subs:
                q = tf.add_paragraph()
                q.space_after = Pt(gap_pt / 2)
                _set_bullet(q, char="–", level=1)
                add_rich_text(q, sub, size=size - 2, color=color)
        return tb

    def caption(self, text, box: Box | None = None, below: Box | None = None, size=12):
        """Small grey italic source line, e.g. under a borrowed figure."""
        if box is None:
            ref = below or LEFT_FIG
            box = Box(ref.x, ref.y + ref.h + 0.05, ref.w, 0.3)
        tb = self.text(text, box, size=size, color=GREY, align="center")
        for p in tb.text_frame.paragraphs:
            for r in p.runs:
                r.font.italic = True
        return tb

    # -- figures ------------------------------------------------------------
    def figure(self, path, box: Box = LEFT_FIG, caption=None, align="center"):
        """Place an image inside box, preserving its aspect ratio."""
        from PIL import Image

        path = str(path)
        try:
            with Image.open(path) as im:
                iw, ih = im.size
        except Exception:  # vector formats: fill the box width
            pic = self.shapes.add_picture(path, Inches(box.x), Inches(box.y), width=Inches(box.w))
            return pic
        scale = min(box.w / iw, box.h / ih)
        w, h = iw * scale, ih * scale
        x = box.x + {"left": 0, "center": (box.w - w) / 2, "right": box.w - w}[align]
        y = box.y + (box.h - h) / 2
        pic = self.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
        if caption:
            self.caption(caption, below=Box(box.x, y, box.w, h))
        return pic

    def preliminary(self, box: Box, size=28, angle=-25):
        """Light-grey 'PRELIMINARY' watermark across an unpublished result."""
        tb = self.text("PRELIMINARY", box, size=size, color=RGBColor(0xD9, 0xD9, 0xD9),
                       bold=True, align="center", anchor="middle")
        tb.rotation = angle
        return tb

    # -- emphasis components -----------------------------------------------
    def callout(self, text, box: Box = Box(0.5, 5.75, 12.33, 0.95), size=22, fill=RED, color=WHITE):
        """Rounded red bar carrying the slide's take-away sentence."""
        sh = self.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(box.x), Inches(box.y),
                                   Inches(box.w), Inches(box.h))
        sh.adjustments[0] = 0.18
        sh.fill.solid()
        sh.fill.fore_color.rgb = _rgb(fill)
        sh.line.fill.background()
        sh.shadow.inherit = False
        tf = sh.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for i, line in enumerate(text.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            add_rich_text(p, line, size=size, color=color, bold=True, accent=WHITE)
        return sh

    def kpi(self, value, label, source=None, box: Box = Box(0.5, 5.55, 3.4, 1.3), fill=RED):
        """Big-number box: value on top, one-line meaning, optional source."""
        sh = self.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(box.x), Inches(box.y),
                                   Inches(box.w), Inches(box.h))
        sh.adjustments[0] = 0.12
        sh.fill.solid()
        sh.fill.fore_color.rgb = _rgb(fill)
        sh.line.fill.background()
        sh.shadow.inherit = False
        tf = sh.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        add_rich_text(p, value, size=34, color=WHITE, bold=True, accent=WHITE)
        for extra, sz, italic in ((label, 14, False), (source, 12, True)):
            if extra:
                q = tf.add_paragraph()
                q.alignment = PP_ALIGN.CENTER
                add_rich_text(q, extra, size=sz, color=WHITE, accent=WHITE)
                for r in q.runs:
                    r.font.italic = italic
        return sh

    def kpi_transition(self, before, after, box: Box = Box(7.3, 0.95, 5.5, 1.6)):
        """Grey 'before' box → red 'after' box, e.g. (('8.4 %', 'Solar Fusion III'), ('X %', 'This work'))."""
        bw = (box.w - 0.6) / 2
        self.kpi(before[0], before[1], None, Box(box.x, box.y, bw, box.h), fill=GREY)
        arr = self.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(box.x + bw + 0.08), Inches(box.y + box.h / 2 - 0.22),
                                    Inches(0.44), Inches(0.44))
        arr.fill.solid()
        arr.fill.fore_color.rgb = TEXT
        arr.line.fill.background()
        self.kpi(after[0], after[1], None, Box(box.x + bw + 0.6, box.y, bw, box.h), fill=RED)

    def cards(self, columns, box: Box = Box(0.5, 1.4, 12.33, 2.9), size=15, gap=0.2):
        """Parallel columns with coloured headers: [(header, colour, [bullets]), ...]."""
        n = len(columns)
        cw = (box.w - gap * (n - 1)) / n
        for i, (header, colour, items) in enumerate(columns):
            x = box.x + i * (cw + gap)
            hd = self.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(box.y), Inches(cw), Inches(0.5))
            hd.fill.solid()
            hd.fill.fore_color.rgb = _rgb(colour)
            hd.line.fill.background()
            hd.shadow.inherit = False
            p = hd.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            add_rich_text(p, header, size=16, color=WHITE, bold=True, accent=WHITE)
            body = self.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(box.y + 0.5), Inches(cw),
                                         Inches(box.h - 0.5))
            body.fill.solid()
            body.fill.fore_color.rgb = LIGHT
            body.line.fill.background()
            body.shadow.inherit = False
            self.bullets(items, Box(x + 0.1, box.y + 0.62, cw - 0.2, box.h - 0.7), size=size, gap_pt=6)

    def person(self, photo, caption, box: Box = Box(10.9, 4.9, 1.9, 1.9)):
        """Photo plus credit line (e.g. 'A. Student, PhD work'), used when a student did the work."""
        self.figure(photo, Box(box.x, box.y, box.w, box.h - 0.4))
        self.text(caption, Box(box.x - 0.4, box.y + box.h - 0.4, box.w + 0.8, 0.4), size=14, bold=True,
                  align="center")

    def arrow(self, x1, y1, x2, y2, color=RED, width_pt=2.5):
        """Straight connector with an arrow head, coordinates in inches."""
        from pptx.enum.shapes import MSO_CONNECTOR

        c = self.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        c.line.color.rgb = _rgb(color)
        c.line.width = Pt(width_pt)
        ln = c.line._get_or_add_ln()
        tail = etree.SubElement(ln, qn("a:tailEnd"))
        tail.set("type", "triangle")
        return c

    def box_outline(self, box: Box, color=RED, width_pt=2.5, rounded=True):
        """Unfilled outline to point at part of a figure or equation."""
        shape = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
        sh = self.shapes.add_shape(shape, Inches(box.x), Inches(box.y), Inches(box.w), Inches(box.h))
        sh.fill.background()
        sh.line.color.rgb = _rgb(color)
        sh.line.width = Pt(width_pt)
        sh.shadow.inherit = False
        return sh

    def equation(self, tex, x, y, size=24, color=TEXT, usetex=None):
        """Typeset LaTeX maths as a transparent PNG placed at its true point size.

        tex is the math body without $...$. Uses a LaTeX installation when present
        (usetex=None autodetects), otherwise Matplotlib mathtext.
        """
        import hashlib
        import shutil

        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if usetex is None:
            usetex = shutil.which("latex") is not None
        hexcol = "#" + str(_rgb(color))
        key = hashlib.sha1(f"{tex}|{size}|{hexcol}|{usetex}".encode()).hexdigest()[:12]
        out = self.deck.cache_dir / f"eq-{key}.png"
        if not out.exists():
            dpi = 400
            with plt.rc_context({"text.usetex": usetex, "mathtext.fontset": "cm",
                                 "text.latex.preamble": r"\usepackage{amsmath}"}):
                fig = plt.figure(figsize=(0.01, 0.01))
                body = rf"\displaystyle {tex}" if usetex else tex
                fig.text(0, 0, f"${body}$", fontsize=size, color=hexcol)
                fig.savefig(out, dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.02)
                plt.close(fig)
        from PIL import Image

        with Image.open(out) as im:
            pw, ph = im.size
        return self.shapes.add_picture(str(out), Inches(x), Inches(y), Inches(pw / 400), Inches(ph / 400))

    def logo(self, path, box: Box):
        """Place a user-supplied logo image (no logos are bundled with the skill)."""
        return self.figure(path, box)

    # -- notes ----------------------------------------------------------------
    def notes(self, text):
        """Speaker notes. Start with the time budget: '1.5 min. ...'."""
        self.slide.notes_slide.notes_text_frame.text = text
        return self


class Deck:
    """A deck in the house layout or on a user-supplied template.

    template="house" (default): 16:9 canvas drawn by this module (red header bar,
    white title, grey footer rule, full-red title/divider slides).
    Any other value is a .pptx path whose slides are ignored and whose layouts
    are reused.
    """

    def __init__(self, template=HOUSE, footer="", date="", page_numbers=True):
        self.kind = HOUSE if template in (None, HOUSE) else "custom"
        if self.kind == HOUSE:
            self.prs = Presentation()
            self.prs.slide_width, self.prs.slide_height = Inches(W), Inches(H)
        else:
            self.prs = Presentation(str(template))
            _drop_all_slides(self.prs)
        self.footer = footer
        self.date = date
        self.page_numbers = page_numbers
        self._page = 0
        self.layouts = {l.name: l for m in self.prs.slide_masters for l in m.slide_layouts}
        import tempfile

        self.cache_dir = Path(tempfile.mkdtemp(prefix="deck-eq-"))

    # -- slide factories --------------------------------------------------------
    def _layout(self, *names):
        for n in names:
            if n in self.layouts:
                return self.layouts[n]
        for l in self.layouts.values():  # first layout with a title placeholder
            if any(ph.placeholder_format.idx == 0 for ph in l.placeholders):
                return l
        return self.prs.slide_layouts[0]

    def _red_slide(self):
        s = self.prs.slides.add_slide(self._layout("Blank", "DEFAULT"))
        for ph in list(s.placeholders):
            ph._element.getparent().remove(ph._element)
        bg = s.background.fill
        bg.solid()
        bg.fore_color.rgb = RED
        return Slide(self, s)

    def watermark(self, slide: "Slide", path, box: Box = Box(8.6, 3.0, 4.6, 4.6), percent=12):
        """Faded user-supplied image (e.g. your own emblem) on a red slide."""
        wm = slide.shapes.add_picture(str(path), Inches(box.x), Inches(box.y), Inches(box.w), Inches(box.h))
        _set_picture_alpha(wm, percent)
        return wm

    def _title_layout_slide(self, title, lines=()):
        """custom: the template's own title layout (placeholders 0, 11, 12, 13)."""
        sl = self.prs.slides.add_slide(self._layout("Titolo", "Title Slide", "Cover presentazione"))
        values = {0: title, 11: lines[0] if len(lines) > 0 else "", 12: lines[1] if len(lines) > 1 else "",
                  13: lines[2] if len(lines) > 2 else ""}
        for ph in list(sl.placeholders):
            v = values.get(ph.placeholder_format.idx, "")
            if v:
                ph.text_frame.text = ""
                add_rich_text(ph.text_frame.paragraphs[0], v, size=28 if ph.placeholder_format.idx == 0 else 18,
                              color=WHITE if ph.placeholder_format.idx == 0 else TEXT, bold=ph.placeholder_format.idx == 0)
            else:
                ph._element.getparent().remove(ph._element)
        return Slide(self, sl)

    def title_slide(self, title, subtitle="", author="", affiliation="", event="", date="",
                    logos=()):
        """Full-red title slide. logos: paths to your own image files."""
        if self.kind != HOUSE:
            return self._title_layout_slide(title, (f"**{author}**", affiliation, date or self.date))
        s = self._red_slide()
        s.text(title, Box(0.62, 1.55, 11.8, 1.6), size=32, color=WHITE, bold=True, font="Cambria",
               anchor="bottom", line_spacing=1.0)
        if subtitle:
            tb = s.text(subtitle, Box(0.62, 3.2, 11.8, 0.5), size=16, color=WHITE)
            for p in tb.text_frame.paragraphs:
                for r in p.runs:
                    r.font.italic = True
        if author:
            s.text(author, Box(0.62, 4.2, 6.5, 0.5), size=28, color=WHITE)
        if affiliation:
            s.text(affiliation, Box(0.62, 4.75, 6.0, 0.6), size=14, color=WHITE)
        if event or date:
            s.text(f"**{event}**\n{date}", Box(0.62, 5.8, 8.0, 1.0), size=20, color=WHITE)
        for i, lg in enumerate(logos):
            s.logo(lg, Box(6.3 + 2.6 * i, 4.8, 2.4, 2.4))
        return s

    def section(self, title, logo=None):
        """Divider slide ('Part 1: Direct measurement'); logo is an optional image path."""
        if self.kind != HOUSE:
            return self._title_layout_slide(title)
        s = self._red_slide()
        s.text(title, Box(0.8, 2.8, 8.0, 0.8), size=40, color=WHITE, bold=True, anchor="middle")
        if logo:
            s.logo(logo, Box(8.8, 1.6, 3.7, 3.6))
        return s

    def closing(self, title="Thank you", line="", logos=()):
        """Closing slide; line names the collaborations, logos are your own image paths."""
        if self.kind != HOUSE:
            return self._title_layout_slide(title, (line,))
        s = self._red_slide()
        s.text(title, Box(0.8, 2.4, 11.5, 1.2), size=40, color=WHITE, bold=True, anchor="bottom")
        if line:
            s.text(line, Box(0.8, 3.6, 11.5, 0.45), size=20, color=WHITE)
        for i, lg in enumerate(logos):
            s.logo(lg, Box(0.8 + 2.5 * i, 4.5, 2.3, 2.3))
        return s

    def content(self, title, badge=None):
        """Standard slide with title, footer and page number.

        badge: optional path to a small image shown in the header bar.
        """
        house = self.kind == HOUSE
        sl = self.prs.slides.add_slide(self._layout("Title Only", "Diapositiva neutra", "Titolo e contenuto"))
        self._page += 1
        own_number = house
        if house:
            _house_frame(sl)
        for ph in list(sl.placeholders):
            idx, typ = ph.placeholder_format.idx, str(ph.placeholder_format.type)
            if idx == 0:
                ph.text_frame.text = ""
                p = ph.text_frame.paragraphs[0]
                if house:  # white, bold, in the red bar
                    ph.left, ph.top, ph.width, ph.height = Inches(0.5), Inches(0.01), Inches(12.33), Inches(0.73)
                    ph.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
                    ph.text_frame.word_wrap = True
                    add_rich_text(p, title, size=20, color=WHITE, bold=True, accent=WHITE)
                    p.alignment = PP_ALIGN.LEFT
                else:      # inherit the layout's title style
                    add_rich_text(p, title, size=28, color=WHITE, bold=True, accent=WHITE)
            elif "FOOTER" in typ:
                if self.footer:
                    ph.text_frame.text = self.footer
                else:
                    ph._element.getparent().remove(ph._element)
            elif "DATE" in typ and self.date:
                ph.text_frame.text = self.date
            elif "SLIDE_NUMBER" in typ and self.page_numbers:
                ph.text_frame.text = str(self._page)
            else:
                ph._element.getparent().remove(ph._element)
        s = Slide(self, sl)
        if house and self.footer:
            s.text(self.footer, Box(0.5, 7.09, 11.5, 0.35), size=10, color=GREY)
        if self.page_numbers and own_number:
            s.text(str(self._page), Box(12.4, 7.08, 0.8, 0.35), size=10, color=GREY, align="right")
        if badge:  # small user-supplied image in the header bar, right end
            s.logo(badge, Box(12.55, 0.04, 0.7, 0.66) if house else Box(11.3, 0.13, 0.9, 0.9))
        return s

    def build(self, title, steps, badge=None, notes=None):
        """Progressive reveal as duplicated slides (the user's preferred build).

        steps is a list of callables f(slide); slide k runs steps[0..k]. All
        slides share one page number and the same notes.
        """
        slides = []
        for k in range(len(steps)):
            s = self.content(title, badge=badge)
            if k:
                self._page -= 1
                _replace_page_number(s, self._page)
            for f in steps[: k + 1]:
                f(s)
            if notes:
                s.notes(notes)
            slides.append(s)
        return slides

    def video(self, mp4, poster=None, title=None, notes=None, badge=None, full_bleed=True):
        """Embed a Manim clip that plays on click.

        The poster is shown before the click and in every PDF export: pass a
        meaningful frame (scripts/video_poster.py --at last), never the empty
        first frame. full_bleed=False puts a 16:9 video under a normal title.
        """
        poster = str(poster) if poster else None
        if full_bleed:
            sl = self.prs.slides.add_slide(self._layout("Blank", "Diapositiva vuota", "DEFAULT"))
            for ph in list(sl.placeholders):
                ph._element.getparent().remove(ph._element)
            bg = sl.background.fill
            bg.solid()
            bg.fore_color.rgb = NAVY
            s = Slide(self, sl)
            s.shapes.add_movie(str(mp4), 0, 0, Inches(W), Inches(H), poster_frame_image=poster,
                               mime_type="video/mp4")
        else:
            s = self.content(title or "", badge=badge)
            h = BODY.h
            w = h * 16 / 9
            s.shapes.add_movie(str(mp4), Inches(BODY.x + (BODY.w - w) / 2), Inches(BODY.y), Inches(w), Inches(h),
                               poster_frame_image=poster, mime_type="video/mp4")
        if notes:
            s.notes(notes)
        return s

    def backup(self):
        return self.section("Backup")

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(path))
        return path


def _house_frame(slide):
    """Red header bar and grey footer rule, sent behind the slide's placeholders."""
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(W), Inches(0.75))
    bar.fill.solid()
    bar.fill.fore_color.rgb = RED
    bar.line.fill.background()
    bar.shadow.inherit = False
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(7.06), Inches(12.33), Inches(0.01))
    rule.fill.solid()
    rule.fill.fore_color.rgb = GREY
    rule.line.fill.background()
    rule.shadow.inherit = False
    tree = slide.shapes._spTree
    for el in (rule._element, bar._element):
        tree.remove(el)
        tree.insert(2, el)


def _drop_all_slides(prs):
    lst = prs.slides._sldIdLst
    for sld in list(lst):
        prs.part.drop_rel(sld.rId)
        lst.remove(sld)


def _set_picture_alpha(pic, percent):
    blip = pic._element.find(".//" + qn("a:blip"))
    amf = etree.SubElement(blip, qn("a:alphaModFix"))
    amf.set("amt", str(int(percent * 1000)))


def _replace_page_number(slide: Slide, n):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.isdigit() and sh.top > Inches(7.0):
            sh.text_frame.paragraphs[0].runs[0].text = str(n)


def duplicate_slide(prs, index):
    """Append a copy of slide `index` (0-based) to an existing deck; media rels are shared."""
    src = prs.slides[index]
    dst = prs.slides.add_slide(src.slide_layout)
    for ph in list(dst.placeholders):
        ph._element.getparent().remove(ph._element)
    for el in src.shapes._spTree.iterchildren():
        if el.tag.endswith("}nvGrpSpPr") or el.tag.endswith("}grpSpPr"):
            continue
        dst.shapes._spTree.append(copy.deepcopy(el))
    # re-point relationship ids (images, media) used by the copied XML
    mapping = {}
    for rid, rel in src.part.rels.items():
        if "notesSlide" in rel.reltype or "slideLayout" in rel.reltype or rel.is_external:
            continue
        mapping[rid] = dst.part.relate_to(rel.target_part, rel.reltype)
    for el in dst.shapes._spTree.iter():
        for attr in (qn("r:embed"), qn("r:link"), qn("r:id")):
            v = el.get(attr)
            if v in mapping:
                el.set(attr, mapping[v])
    return dst
