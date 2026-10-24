---
name: research-slides
description: Plan, build, animate and check scientific talks (conference talks, seminars, working-group updates, technical meetings) in nuclear physics and nuclear astrophysics in the user's own PowerPoint style: .pptx decks built with python-pptx in the house layout or on a user template, Manim animations as click-to-play video slides, and a render and audit of every slide. Use whenever the user asks for slides, a deck, a talk, a presentation, a seminar, speaker notes or a Manim animation for a talk, or wants an existing deck restyled, shortened, timed or checked; figures for papers use `prc-figures`.
---

# Research slides

A talk has to be followed by a room at speaking pace, so each slide carries one claim, figures carry the evidence, animations show a mechanism that unfolds in time, and the speaker notes fit the slot. This skill reproduces the user's own style rather than inventing a new look. You need the talk type and slot, the audience, and the result files and figures the talk reports. You get a .pptx deck, its rendered PDF, the animation sources and clips, and a list of what still needs the user.

## Where this fits

- Comes from: result files and plots of a [nuclear-research-project](../nuclear-research-project/SKILL.md) layout and publications, at the Write-up stage (7) of `analysis-chain`; the interview talk of a `proposal-project`.
- Goes to: the user, as the deck, the PDF and the clips for presenting.
- Checked by: `check_deck.py`, `render_deck.py` and a look at every rendered slide; `demo_deck.py` shows every component working.

## Before building

1. Establish the talk type and slot (conference 12–25 min, seminar 45–60 min, working-group meeting, technical meeting), audience, date, venue, and which layout to use. The default is the built-in `house` layout, drawn by `deck.py` with no template file. A .pptx the user supplies is used with `Deck(template="path.pptx")`, which keeps its masters and drops its slides. The skill bundles no logos or institutional templates, so the user's own files are used only where the user is entitled to them.
2. Collect the evidence: result files and plots from the project (`results/`, `plots/`), publications, and what is unpublished. Every number on a slide must trace to a source; never invent values, citations, lifetimes, uncertainties or collaborator credits. Mark unpublished results PRELIMINARY.
3. Write the storyboard before any code, one line per slide with its claim title, the figure or animation, the build steps and the minutes. [narrative-and-notes.md](references/narrative-and-notes.md) gives the arc, title style, build and timing rules. Show the storyboard to the user for a talk longer than a few slides.

## Build

The measured geometry, colours, typography and the component catalogue are in [house-style.md](references/house-style.md). Build with `scripts/deck.py`:

```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts")
from deck import Deck, Box, LEFT_FIG, RIGHT_TEXT, BLUE, GREEN, RED
d = Deck(footer="A. Author  |  Institute  |  Conference 2026")
d.title_slide(title, subtitle=..., author=..., affiliation=..., event=..., date=...)
d.video("clip.mp4", poster="clip_poster.png", notes="1.5 min. ...")      # Manim clip, plays on click
d.section("Part 1: Direct measurement")                 # logo="my_logo.png" optional
d.build("One state controls the extrapolation", [step1, step2], notes="1.5 min. ...")
s = d.content("Impact"); s.figure(...); s.bullets([...]); s.kpi_transition(...); s.notes(...)
d.closing(line="Collaboration A  •  Collaboration B"); d.backup(); d.save("talk.pptx")
```

Text helpers accept `**bold**`, `==red accent==`, `^{sup}`, `_{sub}` and Unicode symbols. `s.equation(tex, x, y, size)` typesets LaTeX at its true point size. Plots are made with `plt.style.use("SKILL_DIR/assets/slides.mplstyle")` at the size they occupy on the slide. `python3 SKILL_DIR/scripts/demo_deck.py --out NEW_DIR` shows every component working.

Build steps are separate full slides, each adding one element, because duplicated slides survive PDF export and remote presenting where PowerPoint entrance animations do not (narrative-and-notes.md). When editing an existing deck, inspect every slide first, keep its masters, fonts and footer, and change only what was asked. `deck.duplicate_slide(prs, i)` copies a slide for a new build step.

## Animate

Read [manim-animations.md](references/manim-animations.md) before writing a scene. Start from `assets/manim/house_style.py` and `assets/manim/template_scene.py`, which give the dark navy background, LaTeX labels and semantic colours. Each clip carries one message and is split at every point where the speaker must talk, with the next part rebuilding the frozen frame so that the seam is invisible. Preview with `manim -ql` and render finals with `manim -qh` (1080p60) into the project's `presentations/animations/`, never into the skills directory. Extract a poster with `scripts/video_poster.py clip.mp4 --at last --out poster.png`. Manim scenes start empty, so a blank first-frame poster makes the slide empty in every PDF.

## Check

1. `python3 SKILL_DIR/scripts/check_deck.py talk.pptx --minutes SLOT` reports small text, off-canvas shapes, missing titles and notes, dense slides, low-resolution images, blank video posters, and the time planned in the notes against the slot. It sums the `N min.` budgets at the start of the notes. Fix every ERROR; judge each WARN.
2. `python3 SKILL_DIR/scripts/render_deck.py talk.pptx --out RENDER_DIR` exports a PDF through PowerPoint on macOS (LibreOffice elsewhere), then PNGs and contact sheets. Look at every slide for overlaps, clipped text, unreadable labels, inconsistent units or energy frames, and a figure that does not show the claim in the title.
3. Play each video once in PowerPoint or Keynote on the presenting machine when possible; state in the handoff if this was not done.

## What to deliver

- The .pptx and the rendered PDF.
- The animation sources and the rendered clips.
- A short list of what still needs the user: unverified numbers, missing figures, placeholders, and slides over time.
