"""House style for Manim clips that go into the user's talks.

Distilled from npa_scenes.py (NPA 2026): dark navy background, gold/red/blue
semantic colours, every label typeset with LaTeX so isotopes and Greek letters
match the slides. Import with `from house_style import *` next to the scene file.
"""
import numpy as np
from manim import (BLUE, DOWN, LEFT, RIGHT, UP, WHITE, Axes, Circle, Create, Dot, FadeIn, FadeOut,
                   LaggedStart, MathTex, Tex, VGroup, config)

# ---- palette (keep semantic meaning stable across clips) -------------------------
BG = "#0B1220"        # background
SOFT = "#C9D1DE"      # secondary text, axes, arrows
RED_U = "#D0141A"     # the bottleneck / the quantity we measure (UniPD red on dark)
GOLD = "#E3B23C"      # stellar context, questions to the audience
BLUE_N = "#5DA9FF"    # neutrinos, photons from the source, "data"
GREEN_A = "#5CC46A"   # detectors (AGATA, HPGe, BGO)
ORANGE_S = "#FF7A45"  # case A (short lifetime, high energy, ...)
BLUE_L = "#7FB3FF"    # case B (long lifetime, low energy, ...)

config.background_color = BG


def T(text, size=32, color=WHITE, **kw):
    """LaTeX text at a given font size (48 = Manim default). Isotopes: r'$^{15}$O'."""
    return Tex(text, font_size=size, color=color, **kw)


def M(tex, size=36, color=WHITE, **kw):
    """Display maths."""
    return MathTex(tex, font_size=size, color=color, **kw)


def nuc(label, color=WHITE, r=0.46, fill=BG):
    """Nucleus node for reaction networks and level schemes."""
    c = Circle(radius=r, color=color, stroke_width=3, fill_color=fill, fill_opacity=1)
    t = Tex(label, color=color).scale(0.75)
    return VGroup(c, t)


def title(text, size=42):
    """Slide-like title at the top of the frame."""
    return T(text, size).to_edge(UP, buff=0.45)


def message(text, size=30, color=WHITE):
    """One-sentence take-away at the bottom of the frame."""
    return T(text, size, color).to_edge(DOWN, buff=0.5)


def data_axes(x_range, y_range, x_label, y_label, log_y=False, width=7.5, height=4.2):
    """Axes styled for measured data. For log_y give y_range in decades, e.g. [-3, 1, 1]."""
    from manim import LogBase

    y_cfg = {"scaling": LogBase(custom_labels=True)} if log_y else {}
    ax = Axes(x_range=x_range, y_range=y_range, x_length=width, y_length=height,
              axis_config={"color": SOFT, "stroke_width": 2, "include_numbers": True, "font_size": 22},
              y_axis_config=y_cfg, tips=False)
    labels = ax.get_axis_labels(Tex(x_label, font_size=26, color=SOFT), Tex(y_label, font_size=26, color=SOFT))
    return VGroup(ax, labels), ax


def data_points(ax, x, y, color=BLUE_N, r=0.045):
    """Measured points as dots (error bars rarely read in a moving clip; show them on the slide)."""
    return VGroup(*[Dot(ax.c2p(xi, yi), radius=r, color=color) for xi, yi in zip(x, y)])


def reveal_points(dots, run_time=2.0):
    return LaggedStart(*[FadeIn(d, scale=0.5) for d in dots], lag_ratio=0.03, run_time=run_time)


def model_curve(ax, f, x_range, color=RED_U, width=4):
    return ax.plot(f, x_range=x_range, color=color, stroke_width=width)
