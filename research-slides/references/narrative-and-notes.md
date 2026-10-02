# Narrative, builds and speaker notes

## The arc of a conference talk

The NPA 2026 talk (25 min) is the reference structure:

1. **Title** (notes: the time plan, e.g. "25 min: ~9 min motivation + LUNA, ~14 min AGATA + impact, ~2 min summary").
2. **Hook animation** (1.5–3 min): the astrophysical context in motion, ending on the one nuclear quantity that matters ("its rate sets the CNO neutrino flux — and it hinges on one nuclear state").
3. **Why it matters, quantified**: the observable, what limits it, and a big number ("8.4 % uncertainty on S₁₁₄(0)"). The talk's goal in one bullet ("how LUNA and AGATA bring it to the few-% level").
4. **The nuclear-physics bottleneck**: the level scheme, the table of contributions, the take-away bar naming the state or parameter.
5. **Part dividers**, one per method or facility. Inside each: facility or setup (with the student's photo and credit), the data generations in order, the new measurement, status.
6. **The method slide**, often animated and marked "core slide" in the notes: the idea explained once, slowly.
7. **Results** as build sequences: data → correction → result → PRELIMINARY if unpublished.
8. **Impact**: before → after KPI, literature comparison plot, "Next:" callout for work in progress.
9. **Summary**: three cards (method A / method B / impact) and one red sentence joining them.
10. **Thank you** with collaborations, then **Backup** (details a referee-minded audience may ask for: corrections, extraction steps, alternative fits, full tables).

Seminars (45–60 min) use the same arc with more background and more build steps; the ND seminar has about 100 slides because each build step is a slide. Working-group updates drop the hook and the dividers and end on "What must be done" and "Further ideas for discussion". Technical meetings (e.g. IAEA UQ) follow the problem → approach → result → upgrade path of the method itself ("How it started", "Frequentist approach", "Bayesian approach", "Advanced Bayesian approach"), with the defining equation fixed at the top of each slide while the evidence below changes.

## Titles

- Content titles state the claim when the evidence supports one: "One state controls the extrapolation: ¹⁵O at 6.79 MeV", "CNO neutrinos: a probe limited by nuclear physics", "Why the wide angular coverage matters". Topic titles ("AGATA Array", "Summary") are fine for setup and structure slides.
- Title Case is the user's habit in slide titles; keep it consistent within a deck.
- Isotopes with true superscripts (¹⁴N(p,γ)¹⁵O); energies with their frame (E_c.m., E_lab) where it matters.

## Builds

The user builds by duplicating slides, not with PowerPoint entrance animations: each step is a full slide that adds one element (a panel, an overlay, a bullet, the callout). This survives PDF export and remote presenting. Use `d.build(title, [step1, step2, ...])`.

- One new idea per step; the last step usually adds the take-away bar or the KPI.
- Keep everything already shown in the same position.
- All steps share the page number and the notes.

## Speaker notes

Every main-talk slide gets notes. Start with the time budget, then the content the speaker needs but the slide does not show:

```
1.5 min. Borexino 2020: first detection of CNO neutrinos; flux ∝ core C+N abundance → direct handle on
the solar abundance problem. In the Borexino CN-abundance budget, S114 is the second largest contribution
after statistics. JUNO and SNO+ will bring the statistics down ...
```

- The budget format is `N min.` (e.g. `1.5 min.`); `check_deck.py` sums it and compares it with the slot. Summaries like "~8 min for the LUNA part" on a divider are not counted.
- Include the numbers behind the slide (values, uncertainties, energies, references with journal and year) so questions can be answered from the notes.
- Mark the slides that must not be rushed ("Core slide.").
- Put sources for borrowed figures and non-trivial claims in the notes as well as under the figure.

## Pace

- About 1–1.5 min per unique slide (build steps count once); animations 20–45 s of video plus talking over the frozen frame.
- A 12-min talk: ≈8 unique slides plus title; 20 min: ≈13–15; 25 min: ≈16–18.
- Leave 10 % of the slot unallocated.

## Content rules

- Every number traces to a result file, a publication, or the notes. Do not round differently on different slides.
- Name the students and collaborators whose work is shown; credit borrowed figures on the slide.
- Mark unpublished results PRELIMINARY on the figure and in the notes.
- Put assumptions next to the number they affect.
- Keep units, energy frame and uncertainty convention (1σ, 68 % credible interval) consistent with the paper or report.
