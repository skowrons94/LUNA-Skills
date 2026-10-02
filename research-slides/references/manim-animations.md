# Manim animations for talks

The user's reference clips (NPA 2026): `OpeningPart1` (Sun, core, metallicity question, CNO neutrinos, 20 s), `OpeningPart2` (CNO cycle running three laps and stalling at ¹⁴N(p,γ)¹⁵O, 20 s), and `DSAMScene` (the event-by-event Δβ = β_reac − β_emis ∝ τ method, 42 s, slow, narrated). They attract attention because they show a process happening, not because they move.

## When to animate

Animate when time or causality is the point:

- **Opening hook**: the astrophysical site and the chain from star to nuclear quantity (burning cycles, neutrino emission, nucleosynthesis flows).
- **A method**: kinematics and Doppler shifts, a beam slowing in a target, DSAM, coincidence tagging, γ-ray tracking, how a thick-target yield scans a narrow resonance, summing in a close geometry, underground background reduction layer by layer.
- **A physical concept the audience must hold for the rest of the talk**: the Gamow peak as Maxwell–Boltzmann × tunnelling, a sub-threshold state interfering with a resonance, R-matrix extrapolation from data to stellar energies, MCMC walkers exploring a posterior.
- **A result reveal**: data points appearing, then the model, then the stellar window.

Do not animate a static plot, a list, or a table. One to three clips in a 25-min talk is the user's current balance.

## Style (assets/manim/house_style.py)

- Background `#0B1220`; semantic colours: gold = stellar context and questions, red `#D0141A` = the bottleneck or the measured quantity, blue = neutrinos/photons/data, green = detectors, orange/light blue = two contrasting cases. Keep a colour's meaning across clips.
- All text through `T()`/`M()` (LaTeX), so ¹⁵O, β_reac and fractions look like the slides. Title at the top (≈40–44 font size), one message line at the bottom (≈30), labels ≥ 22.
- A title that states the idea ("The velocity lost before the γ-ray is emitted"), a frozen final frame that states the conclusion (Δβ ∝ τ).
- Schematic geometry is fine; label it and keep proportions honest where the audience will read them (angles, ordering of energies, direction of shifts). Values shown as numbers must match the slides and the notes; read them from the project's results files rather than typing them twice.

## Structure

- Build every state in functions (`part1_objects()`, `part1_play()`, `part1_final()`), never by copy-paste.
- **Split at every pause**: where the speaker must talk, end the clip frozen (`self.wait(...)` at the end) and start the next clip by rebuilding exactly that frame with `scene.add(...)` before animating. The join is invisible; `template_scene.py` shows the pattern and the check (mean pixel difference between the last frame of part 1 and the first of part 2 should be ≈0).
- Also render the parts back-to-back as one scene (`Full`/`OpeningScene`) for a single-click version.
- Narrated pace: 1–2 s per simple step, 3–5 s holds after each key reveal, 20–45 s per clip. Speed up after rehearsal, not before.
- Use `ValueTracker` + updaters for live read-outs (velocity, energy) and `always_redraw` for arrows that follow moving objects, as in `DSAMScene`.

## Render

```bash
cd PROJECT/presentations/animations
manim -ql scenes.py Part1 Part2            # preview, 480p15
manim -qh scenes.py Part1 Part2            # final 1080p60 -> media/videos/scenes/1080p60/
manim -qh -s scenes.py Part2               # last frame as PNG (static fallback / backup slide)
python3 SKILL_DIR/scripts/video_poster.py media/videos/scenes/1080p60/Part2.mp4 --at last --out Part2_poster.png
```

Keep the scene source, a README with the render command, and the final MP4s next to the deck. The `media/` cache (Tex/, texts/, partial_movie_files/) is regenerable; do not commit or package it.

Output is H.264, yuv420p, 1920 × 1080, 60 fps: plays in PowerPoint (Mac/Windows) and Keynote. A 40 s clip is ≈2.5 MB.

## Put it in the deck

- `d.video(mp4, poster=poster_png, notes="1.5 min. ...")` makes a full-bleed slide on navy with click-to-play. Use `full_bleed=False` to place the clip under a normal title bar.
- **Poster frame**: always the frozen final frame or a representative frame. Manim scenes start empty, so the default first-frame poster makes the slide blank in the PDF, in handouts and on the organiser's laptop if video fails. `check_deck.py` flags a blank poster as an ERROR (the NPA 2026 deck has this problem on its video slides).
- **Two parts, one click each**: either consecutive slides (part 2 starts from part 1's final frame, so the slide change is invisible), or both videos stacked on one slide as the user describes in the NPA README: part 1 starts automatically or on click, part 2 on the next click with "Hide While Not Playing", both without "Rewind after playing".
- Add a backup static slide (the `-s` frame) after the Backup divider when presenting from a machine you have not tested.

## Check

Watch each final clip end to end: labels inside the frame, nothing overlapping at the frozen frame, text readable at 720p, the seam between parts invisible, the final frame saying the take-away. Then render the deck and confirm the poster appears on the video slide.
