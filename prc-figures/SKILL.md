---
name: prc-figures
description: Make nuclear-physics figures with matplotlib in a PRC / ROOT-like style (closed frames, inward major+minor ticks on all sides, serif STIX fonts, step histograms, black data points, fixed colour roles, legends outside the data) and check renders for overlaps before a LaTeX report or talk. Use for gamma-ray spectra, stacked signal/background/summing components, S-factor and cross-section plots with literature data, excitation functions, angular distributions, 2D heatmaps (energy vs angle, partition maps), multi-panel selection comparisons and Geant4 render annotation; slide layouts use `research-slides`.
---
# PRC figures

A figure in a report or paper answers one question, and the reader should see the answer without decoding the drawing. The figures made with this skill look like Physical Review C figures drawn by a ROOT user: closed frame, inward ticks on all four sides with minor ticks, serif (STIX/Times) text, no grid, histograms as steps, measured points in black with error bars, models as lines with bands. You need the arrays behind the figure, taken from the same result files as the tables. You get the figure at the size used in the document, rendered and inspected for overlaps.

## Where this fits

- Comes from: the result arrays and tables of the analysis skills, for example the lifetime plots of `delta-beta-dsam`, and the Write-up stage (7) of `analysis-chain`.
- Goes to: the LaTeX report of a `nuclear-research-project`, manuscripts written with `clear-experimental-writing`, and the figures of a `proposal-project`. Slides are built with `research-slides`, which has its own plot style.
- Checked by: `scripts/demo.py`, which must print PASS, and `check_render` on every figure at its final size.

## Method

The style lives in `prcstyle.py`, which sets the rcParams and provides helpers for the recurring figure types. Its figure-type recipes (which figure answers which question) and the pitfalls met so far are in [references/style-rules.md](references/style-rules.md).

1. Load the style and choose the size from the journal column, PRC single column 3.4 in, double 7.0 in, with fonts of 7–10 pt at the final size:

```python
import sys; sys.path.insert(0, "<this skill>/scripts")   # or copy prcstyle.py into the project (src/plotting/style.py)
import prcstyle as ps
ps.apply()                                   # rcParams
fig, ax = plt.subplots(figsize=(ps.COL_1, 2.7))   # PRC single column 3.4 in, double 7.0 in
```

2. Draw with the helpers. `prcstyle.py` also provides `C` / `LS` colour and line-style roles, `minor(ax)`, `label(ax, "(a)")`, `stacked_stairs(...)` for stacked components on a background with a black outline, `annotate_peaks(...)` for labels above the local maximum with per-label x offsets, `legend_above(ax, ...)`, `log_ticks(ax, [...])`, `heatmap(ax, ...)` with log colour and masked zeros, and the `place_on_image(...)` helpers.
3. Render with `check_render(pdf)`, which converts the PDF to PNG with pdftoppm, and look at the result at the size used in the document.

`python3 scripts/demo.py --out /tmp/prc-demo` builds every figure type from synthetic data and prints PASS.

## Rules and their reasons

1. Colours mark roles, not decoration. Each physical role has one colour, constant across all figures of a report and talk: data black; true signal red; summing-in or dominant background blue; secondary components light blue, green, grey; scenario or alternative orange. Components are also distinguished by line style, so that the figure still reads in greyscale.
2. Legends and titles never sit on data or on each other. The default is `legend_above`, outside the axes and in several columns, or a figure-level legend above a multi-panel stack, with `fig.tight_layout(rect=(0,0,1,0.9))` leaving room for it. Panel labels "(a)" go inside the frame with a white bbox. Every render is checked for such overlaps.
3. Counts are histograms drawn with `ax.stairs`, never smoothed lines. Stacked components are drawn background first, then from minor to major, with the signal last on top and the total outline in black.
4. A peaked spectrum gets both a linear and a log version when the lines are sharp, because a thick-target line shape or a resonance in one bin is unreadable on a linear scale alone; the caption then explains the physical shape. On log axes the floor is set at a fraction of the background level, not at 0.
5. Physics is not cut. Never mask a region of a curve and let the line connect across it, because the joined line looks like a flattened resonance. Draw the full curve and let it leave the axes, or insert NaN.
6. The plotted range stays inside the stored data. If events were stored only in a window, empty edge bins outside it look like missing data.
7. Text over dense areas, such as dotted guide lines or bars, gets `bbox=dict(facecolor="white", edgecolor="none", pad=1)`.
8. Labels carry units and frames: "$E$ (keV, c.m.)", "$E_p$ (keV, lab)", "counts / 4 keV", "$S(E)$ (keV b)".
9. Explanatory figures beat 3D displays. Show the discriminating quantity directly, for example a 2D map of the variable the algorithm cuts on with the expected lines marked, rather than an event display. Event-topology heatmaps did not explain the discrimination, 3D displays came out cluttered with grey panes and overlapping labels, and perspective renderings misled about the axes, so side views of Geant4 geometry use an orthographic projection.
10. Every number printed on a figure comes from the same arrays used in the tables. Numbers typed by hand into captions or prose drift when the simulations are rerun.
11. Always render and look with `check_render`, at the size used in the document, and fix overlaps before delivering.

## What to deliver

- The figure as a vector PDF at the document size; heatmaps inside it rasterised at 300 dpi with `rasterized=True`.
- The rendered PNG that was inspected, and linear and log versions for sharp peaks.
- The script that builds the figure from the result files, so that printed numbers stay generated.
