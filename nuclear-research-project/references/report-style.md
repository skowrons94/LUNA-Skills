# LaTeX feasibility reports

## Communication job

A feasibility report is an options-and-decision document supported by physics. It is not a chronological lab diary and not a catalog of scripts. Begin with the scientific question and the experimental consequence, then introduce only the calculations needed to support the decision.

Use this default narrative:

1. Aim and measurable success criterion.
2. Physical inputs and competing evaluations.
3. Experimental or computational method.
4. Validation against measurements, calibration, or an independent calculation.
5. Predicted yields, spectra, backgrounds, or sensitivities.
6. Uncertainties and limiting assumptions.
7. Feasibility conclusion, preferred configuration, and the next test that could change it.

Merge or reorder sections when the physics requires it. Do not force an abstract when the document is a short internal note, but include a short executive conclusion near the front when the intended readers need a decision quickly.

## Language

Write in simple scientific English:

- Prefer short declarative sentences and concrete subjects.
- State what was calculated, from which input, under which assumption, and what it implies.
- Use active voice when it clarifies responsibility: “We use the geometric mean as a neutral working value.”
- Define a symbol at first use and use it consistently.
- Distinguish measured, calculated, assumed, adopted, and extrapolated quantities.
- Avoid promotional adjectives, inflated claims, unexplained jargon, and repeated scene-setting.
- Do not hide limitations. A bounded statement such as “feasible above 2.4 MeV under the adopted background model” is stronger than an unqualified claim.
- Keep code names, file paths, and implementation details out of the scientific narrative unless they affect reproducibility or interpretation. Put them in the handoff or provenance documents.

## Quantitative discipline

- State projectile/target, laboratory versus center-of-mass energy, charge state, beam-current convention, target composition, detector acceptance, and counting-time definition.
- Use `siunitx` for units and consistent significant figures.
- Define yield, efficiency, background window, confidence interval, and time-to-precision calculations.
- Show model envelopes and direct data without cosmetic rescaling. Explain justified normalization explicitly.
- Pair every central estimate with the dominant uncertainty or scenario range.
- Validate simulations with calibration sources, benchmark data, a measured yield curve, or a transparent analytical limit before using them for the feasibility decision.

## Figures and tables

Each figure must answer a question. Captions should say what is compared, which assumption matters, and what the reader should notice. Use vector PDF for plots when possible and a high-resolution raster only for detector images, maps, or dense simulated spectra.

Tables are for exact values and option comparisons. Use `booktabs`, align numbers and units, avoid vertical rules, and bold only the value or option that the text is discussing. Do not repeat every table value in prose.

The project template uses `plots/report/` as the preferred figure source. Generate report-specific figures from the same numerical results used by the presentation.

## LaTeX requirements

- Keep `report/main.tex` small and split content into ordered files under `report/sections/`.
- Keep bibliography data in `report/references.bib`, preferably exported from Zotero with stable citation keys.
- Compile into `report/build/`; do not mix auxiliary files with source.
- Fail on LaTeX errors, render the PDF, and visually inspect every page for clipping, bad float placement, unreadable labels, missing references, and incorrect units.
- Keep source, bibliography, and final PDF together so another researcher can rebuild the document.

## Patterns observed in the reference feasibility studies

Good published feasibility studies and internal feasibility notes share a useful pattern:

- They motivate the measurement with one specific limitation at the relevant energy.
- They introduce the apparatus only to the level needed to understand acceptance, efficiency, resolution, or background.
- They make feasibility quantitative by comparing expected signal with measured or modeled background.
- They validate the model before extrapolating it.
- Their conclusion says which region or configuration works, which does not, and what measurement or hardware change is still required.

Use that pattern without copying wording from any paper.
