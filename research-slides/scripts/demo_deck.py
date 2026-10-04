#!/usr/bin/env python3
"""Build a short example deck that exercises every component, then audit it.

    python3 demo_deck.py --out NEW_DIR [--template house|path.pptx] [--video clip.mp4]

Uses synthetic data only. With --video, the clip is embedded full-bleed with a
poster taken from its last frame. Render afterwards with render_deck.py.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from deck import (BLUE, GREEN, LEFT_FIG, RED, RIGHT_TEXT, Box, Deck)  # noqa: E402


def make_figure(path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.style.use(str(HERE.parent / "assets/slides.mplstyle"))
    rng = np.random.default_rng(1)
    E = np.linspace(0.1, 1.0, 25)
    model = 1.6 + 0.4 * E
    fig, ax = plt.subplots()
    ax.errorbar(E, model + rng.normal(0, 0.04, E.size), 0.05, fmt="o", label="synthetic data")
    ax.plot(E, model, color="#AA0004", label="model")
    ax.set_xlabel(r"$E_{\rm c.m.}$ (MeV)")
    ax.set_ylabel(r"$S$ (keV b)")
    ax.legend()
    fig.savefig(path)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--template", default="house")
    ap.add_argument("--video", type=Path)
    a = ap.parse_args()
    if a.out.exists() and any(a.out.iterdir()):
        sys.exit(f"{a.out} is not empty")
    a.out.mkdir(parents=True, exist_ok=True)
    fig = a.out / "s_factor.png"
    make_figure(fig)

    d = Deck(template=a.template, footer="A. Author  |  Institute  |  Demo",
             date="01/01/2027")
    d.title_slide("Example talk:\nthe ^{14}N(p,γ)^{15}O reaction", subtitle="Synthetic content for testing",
                  author="A. Author", affiliation="Institute",
                  event="Demo Conference", date="01/01/2027").notes("12 min talk: 3 min motivation, 7 min results, 2 min summary.")
    if a.video:
        poster = a.out / (a.video.stem + "_poster.png")
        subprocess.run([sys.executable, str(HERE / "video_poster.py"), str(a.video), "--at", "last", "--out", str(poster)],
                       check=True)
        d.video(a.video, poster=poster, notes="1 min. Opening animation; click to play.")
    d.section("Direct measurement").notes("~7 min for the results.")

    def step1(s):
        s.figure(fig, LEFT_FIG, caption="Synthetic data, demo only")
        s.bullets(["S_{114}(0) from **seven data sets**", ("Priors", ["ANCs from transfer", "Γ_{6.79} from a lifetime"])],
                  RIGHT_TEXT)

    def step2(s):
        s.callout("One state controls the ==extrapolation==")

    d.build("One state controls the extrapolation", [step1, step2],
            notes="1.5 min. Point at the low-energy points, then reveal the take-away.")

    s = d.content("The Doppler formula")
    s.equation(r"E_\gamma = E_0\,\frac{\sqrt{1-\beta^2}}{1-\beta\cos\theta}", 0.8, 1.6, size=32)
    s.bullets(["β from the **silicon detector** kinematics", "θ from γ-ray **tracking**"], Box(7.3, 1.6, 5.5, 2.5))
    s.kpi("1.0 ± 0.5 fs", "τ of a state (made up)", "demo value", Box(0.8, 4.4, 4.0, 1.4))
    s.notes("1.5 min. Formula, then the result box.")

    s = d.content("Impact")
    s.kpi_transition(("10 %", "before"), ("5 %", "after"))
    s.figure(fig, Box(0.5, 0.95, 6.4, 4.5))
    s.preliminary(Box(1.0, 2.2, 5.4, 1.2))
    s.bullets(["Uncertainty **below every other input**"], Box(7.3, 2.9, 5.5, 2.0))
    s.notes("1 min. Before/after.")

    s = d.content("Summary")
    s.cards([("Direct", BLUE, ["Angular distributions"]), ("Indirect", GREEN, ["Lifetime from Δβ"]),
             ("Impact", RED, ["**5 %** on S(0)"])])
    s.callout("Direct and indirect data are not alternatives", Box(0.5, 5.0, 12.33, 1.0))
    s.notes("1 min. Close the loop.")
    d.closing(line="Collaboration A  •  Collaboration B")
    d.backup()
    out = d.save(a.out / "demo.pptx")
    print("Deck:", out)
    r = subprocess.run([sys.executable, str(HERE / "check_deck.py"), str(out), "--minutes", "12"])
    print("PASS: deck built and audited" if r.returncode == 0 else "FAIL: audit reported errors")
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
