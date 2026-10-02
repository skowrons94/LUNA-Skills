"""Starter scene in the user's style: copy next to house_style.py and edit.

    manim -ql template_scene.py Part1 Part2     # quick preview, 480p15
    manim -qh template_scene.py Part1 Part2     # final, 1080p60 -> media/videos/template_scene/1080p60/

Pattern: split the story at every point where the speaker must talk. Part 1 ends
frozen on a frame; Part 2 rebuilds that exact frame instantly (`part1_final`) and
continues, so two videos on consecutive slides (or stacked on one slide) join
without a visible seam. Build state in functions, never by copy-paste.
"""
import numpy as np
from manim import *  # noqa: F401,F403

from house_style import *  # noqa: F401,F403


def part1_objects():
    """Everything visible at the end of Part 1, in its final position."""
    ttl = title(r"The cross section drops steeply towards stellar energies")
    grp, ax = data_axes([0, 1.0, 0.2], [-4, 0, 1], r"$E_{\rm c.m.}$ (MeV)", r"$\sigma$ (arb. units)", log_y=True)
    grp.shift(DOWN * 0.3)
    E = np.linspace(0.1, 0.95, 26)
    S = 10 ** (-3.5 + 3.2 * E)            # placeholder data: replace with results/*.csv
    dots = data_points(ax, E, S)
    return ttl, grp, ax, dots


def part1_play(scene):
    ttl, grp, ax, dots = part1_objects()
    scene.play(Write(ttl), Create(grp), run_time=1.5)
    scene.play(reveal_points(dots), run_time=2.5)
    scene.wait(1.0)
    return ttl, grp, ax, dots


def part1_final(scene):
    ttl, grp, ax, dots = part1_objects()
    scene.add(ttl, grp, dots)
    return ttl, grp, ax, dots


def part2_play(scene, ttl, grp, ax, dots):
    curve = model_curve(ax, lambda e: 10 ** (-3.5 + 3.2 * e), [0.02, 1.0]).set_z_index(-1)  # behind the data
    gamow = Polygon(ax.c2p(0.02, 1e-4), ax.c2p(0.06, 1e-4), ax.c2p(0.06, 1.0), ax.c2p(0.02, 1.0),
                    stroke_width=0, fill_color=GOLD, fill_opacity=0.35).set_z_index(-2)
    scene.play(Create(curve), run_time=2.0)
    scene.play(FadeIn(gamow), FadeIn(message(r"the stellar energies lie \textit{below} the data", 30, GOLD)),
               run_time=1.2)
    scene.wait(3.0)                       # ends frozen: this frame is the poster


class Part1(Scene):
    def construct(self):
        part1_play(self)
        self.wait(0.5)


class Part2(Scene):
    def construct(self):
        objs = part1_final(self)
        self.wait(0.1)
        part2_play(self, *objs)


class Full(Scene):
    """Both parts in one file, for a single-click version."""
    def construct(self):
        objs = part1_play(self)
        part2_play(self, *objs)
