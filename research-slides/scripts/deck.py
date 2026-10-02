"""Build PowerPoint decks in the user's house style with python-pptx.

The default template is the Università di Padova conference master used for the
NPA 2026 talk (red header bar, right-aligned white title, grey footer rule).
Every helper places shapes in inches on a 13.33 x 7.50 in canvas.

    import sys; sys.path.insert(0, "SKILL_DIR/scripts")
    from deck import Deck, LEFT_FIG, RIGHT_TEXT

    d = Deck(footer="J. Skowronski  |  Università di Padova & INFN Padova  |  NPA 2026")
    d.title_slide("Direct and indirect approaches ...", subtitle="The ^{14}N(p,γ)^{15}O reaction ...",
                  author="Jakub Skowronski", affiliation="Università degli Studi di Padova & INFN",
                  event="Nuclear Physics in Astrophysics 2026", date="10/09/2026")
    s = d.content("CNO neutrinos: a probe limited by nuclear physics", badge="luna")
    s.figure("plots/borexino.png", LEFT_FIG, caption="Borexino, Nature 587 (2020)")
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
TEMPLATES = {
    "unipd": SKILL_DIR / "assets/templates/unipd-conference.pptx",
    "luna": SKILL_DIR / "assets/templates/luna-seminar.pptx",
}
LOGOS = {
    "luna": SKILL_DIR / "assets/logos/luna-logo.png",
    "agata": SKILL_DIR / "assets/logos/agata-logo.jpg",
    "infn": SKILL_DIR / "assets/logos/infn-logo.wmf",
    "unipd": SKILL_DIR / "assets/logos/unipd-logo-white.png",
    "seal": SKILL_DIR / "assets/logos/unipd-seal-watermark.png",
}

# Palette measured from the NPA 2026 and IAEA 2026 decks.
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
        """Photo plus credit line ('Elia Pilotto's PhD'), used when a student did the work."""
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

    def logo(self, name_or_path, box: Box):
        path = LOGOS.get(name_or_path, name_or_path)
        return self.figure(path, box)

    # -- notes ----------------------------------------------------------------
    def notes(self, text):
        """Speaker notes. Start with the time budget: '1.5 min. ...'."""
        self.slide.notes_slide.notes_text_frame.text = text
        return self


class Deck:
    """A deck built on one of the user's templates.

    template="unipd" (default): Padova conference master, red title/divider slides.
    template="luna": older LUNA/INFN seminar master (white, red rounded title box,
    grey footer bar with date | footer | page). Any other value is a .pptx path whose
    slides are ignored and whose layouts are reused.
    """

    def __init__(self, template="unipd", footer="", date="", page_numbers=True):
        self.kind = template if template in TEMPLATES else "custom"
        path = TEMPLATES.get(template, template)
        self.prs = Presentation(str(path))
        if self.kind == "custom":
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
        s = self.prs.slides.add_slide(self._layout("DEFAULT", "Tappo atertura e chiusura"))
        bg = s.background.fill
        bg.solid()
        bg.fore_color.rgb = RED
        wm = s.shapes.add_picture(str(LOGOS["seal"]), Inches(8.6), Inches(3.0), Inches(4.6), Inches(4.6))
        _set_picture_alpha(wm, 12)
        return Slide(self, s)

    def _title_layout_slide(self, title, lines=()):
        """luna/custom: the template's own title layout (placeholders 0, 11, 12, 13)."""
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
                    logos=("infn",)):
        if self.kind != "unipd":
            return self._title_layout_slide(title, (f"**{author}**", affiliation, date or self.date))
        s = self._red_slide()
        s.figure(LOGOS["unipd"], Box(0.62, 0.5, 3.96, 1.0), align="left")
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
        """Divider slide ('Direct Measurements: LUNA'): full red on unipd."""
        if self.kind != "unipd":
            return self._title_layout_slide(title)
        s = self._red_slide()
        s.text(title, Box(0.8, 2.8, 8.0, 0.8), size=40, color=WHITE, bold=True, anchor="middle")
        if logo:
            s.logo(logo, Box(8.8, 1.6, 3.7, 3.6))
        return s

    def closing(self, title="Thank you", line="", logos=("luna", "agata", "infn")):
        if self.kind != "unipd":
            return self._title_layout_slide(title, (line,))
        s = self._red_slide()
        s.text(title, Box(0.8, 2.4, 11.5, 1.2), size=40, color=WHITE, bold=True, anchor="bottom")
        if line:
            s.text(line, Box(0.8, 3.6, 11.5, 0.45), size=20, color=WHITE)
        for i, lg in enumerate(logos):
            s.logo(lg, Box(0.8 + 2.5 * i, 4.5, 2.3, 2.3))
        return s

    def content(self, title, badge=None):
        """Standard slide with title, footer and page number from the template."""
        unipd = self.kind == "unipd"
        sl = self.prs.slides.add_slide(self._layout("Diapositiva neutra", "Titolo e contenuto", "Title Only"))
        self._page += 1
        own_number = unipd
        for ph in list(sl.placeholders):
            idx, typ = ph.placeholder_format.idx, str(ph.placeholder_format.type)
            if idx == 0:
                ph.text_frame.text = ""
                p = ph.text_frame.paragraphs[0]
                if unipd:  # white, bold, right-aligned in the red bar
                    add_rich_text(p, title, size=20, color=WHITE, bold=True, accent=WHITE)
                    p.alignment = PP_ALIGN.RIGHT
                else:      # inherit the layout's title style
                    add_rich_text(p, title, size=28, color=WHITE, bold=True, accent=WHITE)
            elif "FOOTER" in typ or (unipd and idx == 11):
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
        if self.page_numbers and own_number:
            s.text(str(self._page), Box(12.4, 7.08, 0.8, 0.35), size=10, color=GREY, align="right")
        if self.kind == "luna":  # python-pptx does not copy date/footer/number placeholders
            for txt, box, al in ((self.date, Box(0.3, 7.08, 3.0, 0.35), "left"),
                                 (self.footer, Box(3.33, 7.08, 6.68, 0.35), "center"),
                                 (str(self._page) if self.page_numbers else "", Box(10.08, 7.08, 3.0, 0.35), "right")):
                if txt:
                    s.text(txt, box, size=12, color=WHITE, bold=True, align=al, anchor="middle")
        if badge:  # small collaboration logo sitting in the header bar
            s.logo(badge, Box(4.62, 0.04, 0.7, 0.66) if unipd else Box(11.3, 0.13, 0.9, 0.9))
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
            sl = self.prs.slides.add_slide(self._layout("Diapositiva vuota", "DEFAULT", "Blank"))
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
