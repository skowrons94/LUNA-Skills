---
name: research-slides
description: Plan, build, animate and check scientific talks in the user's own PowerPoint style — conference talks, seminars, working-group updates and technical-meeting presentations in nuclear physics and nuclear astrophysics. Builds .pptx decks from the user's UniPD conference or LUNA/INFN seminar templates with python-pptx, adds Manim animations as click-to-play video slides, and renders and audits every slide. Use whenever the user asks for slides, a deck, a talk, a presentation, a seminar, speaker notes, or a Manim animation for a talk, or wants an existing deck restyled, shortened, timed or checked.
---

# Research slides

Make a talk that a room can follow at speaking pace: one claim per slide, figures that carry the evidence, animations where a mechanism unfolds in time, and speaker notes that fit the slot. Reproduce the user's style; do not invent a new look.

## Before building

1. Establish the talk type and slot (conference 12–25 min, seminar 45–60 min, working-group meeting, technical meeting), audience, date, venue, and which template: `unipd` (default since 2026: Padova conference master) or `luna` (older LUNA/INFN seminar look). A user-supplied .pptx can also serve as the template (`Deck(template="path.pptx")` keeps its masters and drops its slides).
2. Collect the evidence: result files and plots from the project (`results/`, `plots/` in a [nuclear-research-project](../nuclear-research-project/SKILL.md) layout), publications, and what is unpublished. Every number on a slide must trace to a source; never invent values, citations, lifetimes, uncertainties or collaborator credits. Mark unpublished results PRELIMINARY.
3. Write the storyboard before any code: one line per slide with its claim title, the figure or animation, the build steps, and minutes. Read [narrative-and-notes.md](references/narrative-and-notes.md) for the arc, title style, build and timing rules. Show the storyboard to the user for a talk longer than a few slides.

## Build

Read [house-style.md](references/house-style.md) for the measured geometry, colours, typography and the component catalogue. Build with `scripts/deck.py`:

```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts")
from deck import Deck, Box, LEFT_FIG, RIGHT_TEXT, BLUE, GREEN, RED
d = Deck(template="unipd", footer="J. Skowronski  |  Università di Padova & INFN Padova  |  NPA 2026")
d.title_slide(title, subtitle=..., author=..., affiliation=..., event=..., date=...)
d.video("clip.mp4", poster="clip_poster.png", notes="1.5 min. ...")      # Manim clip, plays on click
d.section("Direct Measurements: LUNA", logo="luna")
d.build("One state controls the extrapolation", [step1, step2], badge="luna", notes="1.5 min. ...")
s = d.content("Impact", badge="agata"); s.figure(...); s.bullets([...]); s.kpi_transition(...); s.notes(...)
d.closing(line="LUNA Collaboration  •  AGATA Collaboration"); d.backup(); d.save("talk.pptx")
```

Text helpers accept `**bold**`, `==red accent==`, `^{sup}`, `_{sub}` and Unicode symbols. `s.equation(tex, x, y, size)` typesets LaTeX at its true point size. Make plots with `plt.style.use("SKILL_DIR/assets/slides.mplstyle")` at the size they occupy on the slide. Run `python3 SKILL_DIR/scripts/demo_deck.py --out NEW_DIR` to see every component working.

When editing an existing deck, inspect every slide first, keep its masters, fonts and footer, and change only what was asked. `deck.duplicate_slide(prs, i)` copies a slide for a new build step.

## Animate

Read [manim-animations.md](references/manim-animations.md) before writing a scene. Start from `assets/manim/house_style.py` and `assets/manim/template_scene.py`: dark navy background, LaTeX labels, semantic colours, one message per clip, and a split at every point where the speaker must talk, with the next part rebuilding the frozen frame so the seam is invisible. Preview with `manim -ql`, render finals with `manim -qh` (1080p60) into the project's `presentations/animations/`, never into the skills directory. Extract a poster with `scripts/video_poster.py clip.mp4 --at last --out poster.png`; a blank first-frame poster makes the slide empty in every PDF.

## Check

1. `python3 SKILL_DIR/scripts/check_deck.py talk.pptx --minutes SLOT` reports small text, off-canvas shapes, missing titles and notes, dense slides, low-resolution images, blank video posters, and the time planned in the notes against the slot. Fix every ERROR; judge each WARN.
2. `python3 SKILL_DIR/scripts/render_deck.py talk.pptx --out RENDER_DIR` exports a PDF through PowerPoint on macOS (LibreOffice elsewhere), then PNGs and contact sheets. Look at every slide: overlaps, clipped text, unreadable labels, inconsistent units or energy frames, a figure that does not show the claim in the title.
3. Play each video once in PowerPoint or Keynote on the presenting machine when possible; state in the handoff if this was not done.

Deliver the .pptx, the rendered PDF, the animation sources and rendered clips, and a short list of what still needs the user: unverified numbers, missing figures, placeholders, and slides over time.
