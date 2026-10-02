---
name: prc-figures
description: Make clean nuclear-physics figures with matplotlib in a PRC / ROOT-like style — closed frames, inward major+minor ticks on all sides, serif STIX fonts, step histograms, black data points, fixed colour roles, legends outside the data. Use for gamma-ray spectra, stacked signal/background/summing components, S-factor and cross-section plots with literature data, excitation functions, angular distributions, 2D heatmaps (energy vs angle, partition maps), multi-panel selection comparisons, Geant4 render annotation, and for checking rendered figures for overlaps before they go into a LaTeX report or talk.
---
# PRC figures

Figures answer one question each and look like Physical Review C figures drawn by a ROOT user:
closed frame, inward ticks on all four sides with minor ticks, serif (STIX/Times) text, no grid,
histograms as steps, measured points in black with error bars, models as lines with bands.

## Start

```python
import sys; sys.path.insert(0, "~/Desktop/Skills/prc-figures/scripts")   # or copy prcstyle.py into the project (src/plotting/style.py)
import prcstyle as ps
ps.apply()                                   # rcParams
fig, ax = plt.subplots(figsize=(ps.COL_1, 2.7))   # PRC single column 3.4 in, double 7.0 in
```
`prcstyle.py` also provides: `C` / `LS` colour and line-style roles, `minor(ax)`, `label(ax, "(a)")`,
`stacked_stairs(...)` (stacked components on a background with a black outline), `annotate_peaks(...)`
(labels above the local maximum, with per-label x offsets), `legend_above(ax, ...)`, `log_ticks(ax, [...])`,
`heatmap(ax, ...)` (log colour, masked zeros), `place_on_image(...)` helpers, and `check_render(pdf)`
(renders to PNG with pdftoppm for visual inspection).

Run `python3 scripts/demo.py --out /tmp/prc-demo`: it builds every figure type from synthetic data and prints PASS.

## Rules (read [references/style-rules.md](references/style-rules.md) for details and examples)

1. **Roles, not decoration.** One colour per physical role, constant across all figures of a report and talk: data black; true signal red; summing-in / dominant background blue; secondary components light blue, green, grey; scenario/alternative orange. Distinguish also by line style for greyscale.
2. **Legends and titles never sit on data.** Default: `legend_above` (outside the axes, several columns) or a figure-level legend above multi-panel stacks. Panel labels "(a)" inside the frame with a white bbox. Check every render.
3. **Counts are histograms** (`ax.stairs`), never smoothed lines. Stacked components: background first, then minor to major, signal last on top; draw the total outline in black.
4. **Peaked spectra:** provide both linear and log versions when the lines are sharp; on log axes set a floor at a fraction of the background level, not at 0.
5. **Do not cut physics:** never mask a region of a curve and let the line connect across it (it looks like a flattened resonance). Draw the full curve and let it leave the axes, or insert NaN.
6. **Stay inside stored data:** if events were stored only in a window, the plotted range must stay inside it (empty edge bins look like missing data).
7. **Text over dense areas** gets `bbox=dict(facecolor="white", edgecolor="none", pad=1)`.
8. **Units and frames in labels:** "$E$ (keV, c.m.)", "$E_p$ (keV, lab)", "counts / 4 keV", "$S(E)$ (keV b)".
9. **Explanatory figures beat 3D displays.** Show the discriminating quantity directly (e.g. a 2D map of the variable the algorithm cuts on, with the expected lines marked) rather than an event display.
10. **Every number printed on a figure comes from the same arrays used in the tables.**
11. **Always render and look** (`check_render`), at the size used in the document; fix overlaps before delivering.
