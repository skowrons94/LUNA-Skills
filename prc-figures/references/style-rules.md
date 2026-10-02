# Style rules and lessons (from the LUAGATA feasibility study, 2026)

## Figure types and recipes

| Question | Figure | Recipe |
|---|---|---|
| What does the spectrum look like? | full spectrum, log y, 10 keV bins | total in black, key components in role colours, flat background dotted; `annotate_peaks` with offsets for close lines (e.g. "6.17" dx=-9, "SE" dx=+7; merge "5.18, 5.24") |
| How much of a peak is signal vs contamination? | zoom on the peak, stacked components, one panel per selection, linear + log versions | `stacked_stairs`, figure-level legend above in 2 columns, run conditions as a text line below the legend, counts "in window" printed per panel from the same arrays as the tables, window edges as dotted vertical lines |
| How does an algorithm discriminate? | the variable it cuts on, for both classes | e.g. residual of subset energy vs expected primary (1D, log), cumulative fraction vs window width with the adopted cut marked; or a 2D partition map (remainder energy vs separation) with expected lines labelled on the top axis |
| Model vs data | S factor (log y) vs E (c.m.) | model line + band (alpha 0.2–0.25), each data set its own marker (open circle, filled diamond, triangle…), all in dark colours; legend above in 2–3 columns; draw full resonances (let them leave the axes) |
| Method comparison | relative uncertainty vs energy, log y with readable ticks (`log_ticks([1,2,5,10,20,50,100])`) | one marker + line style per method, best method in the signal colour, legend above |
| Projection | data + projected points | projected points as squares with caps; alternative scenario as open squares shifted by a few keV for visibility (say so in the caption) |
| Geometry | rendered Geant4 image | crop margins, annotate with arrows placed from the image (`dark_blob_center`), use orthographic projection for side views when comparing axes |
| 2D distributions | energy vs angle, etc. | `heatmap` with log colour, masked zeros, colour-bar label with bin size and live time; overlay expected curves as white dashed lines |

## Pitfalls seen and fixed

- Legends/titles over data or over each other: always `legend_above` / figure legend + `fig.tight_layout(rect=(0,0,1,0.9))`.
- Panel text crossing dotted guide lines or bars: white bbox on text.
- "Missing bins at the edges": plot range exceeded the stored event window.
- "Resonance looks cut": masked interval + connected line; draw the full curve.
- Too peaked on linear scale (thick-target line shape, resonance in one bin): add the log version; explain the physical shape in the caption.
- Heatmap of event topology did not explain the discrimination: plot the discriminating variable instead.
- 3D event displays looked cluttered (grey panes, overlapping labels): avoid in reports unless essential.
- Perspective renderings mislead about axes: orthographic side view.
- Numbers written by hand in captions/prose drift when simulations are rerun: generate them.

## Sizes

PRC single column 3.4 in, double column 7.0 in; fonts 7–10 pt at final size; 300 dpi for rasterised content (heatmaps with `rasterized=True` in vector PDFs).
