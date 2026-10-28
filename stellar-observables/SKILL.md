---
name: stellar-observables
description: Physics of the stellar observables a reaction rate can change: surface, wind and grain ratios (12C/13C, 14N/15N, 16O/17O, 16O/18O, 25Mg/26Mg, 26Al/27Al), Li, C, N, O, Na, Al and s-process tracers; the burning and phase that expose them (dredge-up, extra mixing above the RGB bump, hot-bottom burning, winds); levers larger than the rate (mass, metallicity, mixing, rotation, mass loss, code); comparison with observed stars or presolar grains. Use when planning or interpreting a rate-to-observable question, or asking whether a rate change could show at a stellar surface or in grains and which observations would test it; numbers come from models, data or papers read, not memory.
---
# Stellar observables

A rate changes an observable only if three conditions hold. The reaction must run in a layer hot enough, for long enough, to move the local abundance. Some mixing or mass-loss process must carry that layer to a surface, a wind or a grain. And the change must be larger than what mass, metallicity, mixing and the code already do at that phase. Check them in this order, from cheap to expensive, and stop at the first one that fails. You need the rate pair under study, the observable (an isotopic ratio such as 12C/13C, 14N/15N, 16O/17O, 16O/18O, 25Mg/26Mg or 26Al/27Al, an element abundance, or an s-process tracer) and the stars or grains that measure it. You get the burning site and the phase that expose the observable, the non-nuclear levers with their sizes, the model pairs worth running, and a statement of the shift with its uncertainty next to the larger levers and the matched observations.

## Where this fits

- Comes from: local equilibrium and transient values from `reaction-network`; model pairs, profiles and histories from `stellar-evolution`; observed stars and presolar grains from the papers read.
- Goes to: the specification of the stellar-model pairs run with `stellar-evolution`, and the statement of a rate's observable effect for the report or proposal.
- Checked by: `physics-referee` for the numbers and `citation-checker` for the literature statements (step 10).

Running the star (templates, networks, rate tables, mixing controls, run checks, resources) belongs to `stellar-evolution`, and the local effect of a rate at fixed conditions or along a trajectory, including Monte Carlo with correlated rates, belongs to `reaction-network`. Primordial abundances and the Population III starting composition belong to `big-bang-nucleosynthesis`. This skill decides which of those calculations an observable needs and how to read them. Its references hold:

- which burning and which phase set each observable, and the levers: [burning-and-mixing.md](references/burning-and-mixing.md);
- matching models with observed stars: [observations.md](references/observations.md);
- presolar grains as tests: [grains.md](references/grains.md);
- a worked example with numbers (12C(p,γ), 13C(p,γ) and 12C/13C in giants): [example-12c13c.md](references/example-12c13c.md).

Literature statements cite Zotero keys of the Astrophysics project's snapshot (`tools/zotlib.py text KEY`). The Karakas & Lattanzio 2014 and Charbonnel & Lagarde 2010 numbers were checked against the arXiv preprints held there.

## Working method for a new rate or observable

1. Burning site. Name the layer where the reaction runs (core, H shell, envelope base, intershell, pocket), its temperature and the cycle the reaction belongs to ([burning-and-mixing.md](references/burning-and-mixing.md)). Take the temperatures from a model trajectory, not from memory.
2. Network and rate coverage. The network must hold every species and reaction of the chain, isomers included (26Al ground state and isomer). It must not use compound links where the observable sits: MESA's `ro16_to_o17` and `ro17_to_o18`-type rates hide the intermediates. Every rate the observable depends on needs a named source, and a branching needs both branches (17O(p,α) and 17O(p,γ)). Replace built-in defaults by tables (`stellar-evolution/references/nuclear.md`). Tables are bare and cover the temperatures of the site; name any extrapolated range. s-process observables need a large network or post-processing, which is not tested here.
3. Local effect first. Run a one-zone network (`reaction-network`) at those conditions with both rates. Does the local value move? Is it an equilibrium value, set by rate ratios, or a transient one, set by the burning time? How large is the shift once the rate uncertainty and its correlations are included?
4. Exposure. Find the process that brings the layer to an observable place (dredge-up, extra mixing, hot-bottom burning, wind, ejection) and the phase at which it acts. If no process does, the rate has no surface observable in that star. Say so.
5. Larger levers. List the non-nuclear levers at that phase with their sizes, from the literature or from models: mass, metallicity, mixing prescription and efficiency, rotation, convective boundaries (overshoot, depth of the third dredge-up), mass loss, the code, opacities and composition.
6. Stellar models only for what passed. Run pairs that differ only in the rates under study: one evaluation replaces another, and all other rates and physics stay the same. Cross them with the dominant lever, at the mass and Z of the observed stars. Start pairs on the pre-main sequence where possible. A pair branched from a common model measures the effect from the branch point on.
7. Resolution that binds. Tighten the time step and the mesh over the interval where the observable changes. Then check that the tighter control acted, for example that the time step did get shorter there. For thermohaline mixing, refine the composition-term smoothing with the mesh, or the finer mesh switches the mixing off numerically (`stellar-evolution/references/mixing.md`).
8. Same phase. Compare at a physical phase (end of a dredge-up, bump, tip, a given pulse, C/O > 1), never at the same age.
9. Matched observations ([observations.md](references/observations.md)): same stage, mass and [Fe/H], one point per star, clump stars against tip values, and the code spread stated.
10. Rate uncertainty and the statement. Propagate the uncertainty either with runs on ±1σ tables (correlations kept) or, only where the observable is an equilibrium value, through the one-zone sensitivity d ln(obs)/d ln(rate). Say which. The statement gives the observable, phase, mass and Z, mixing (prescription and coefficient), rate pair, the shift with its uncertainty, the larger levers, and the lever the data actually constrain. Send the numbers to `physics-referee` and the literature statements to `citation-checker`.

## Rules

1. Every number comes with its phase, mixing and sample.
2. A rate effect is a ratio within one code. Absolute values differ between codes by as much as a rate effect does. Do not carry mass or metallicity factors from one code to another either.
3. Compare the rate effect with the larger levers before calling it observable.
4. Write "not tested here" where neither the project nor a paper we read has checked a statement.
5. Every number traces to a file or a page: a model summary, a data table with provenance, or a paper in the library (table, equation or section).

## Pitfalls

Each of these was met in this project; the examples are from case 02, 2026-10-24.

- A code's default rate may come from an old compilation; MESA hard-codes 16 NACRE reactions. Name the rate source of the "default" partner.
- A network changed on a loaded model starts the new isotopes at zero (13C here). Start from the pre-main sequence with the final network.
- A weak mixing prescription is not "no mixing". MESA's `Brown_Garaud_Stellmach_13` lowered a 1 Msun ratio from 28.69 to 27.68. The zero-mixing run has coefficient 0.
- A "post-dredge-up" value can be read while the dredge-up is still going: 72.49 (NACRE) for 0.8 Msun at He core 0.20 Msun, against 36.82 once it is complete.
- History `surface_*` columns may come from cells outside the convective envelope. In the 5 Msun AGB model the outer ~0.006 Msun stayed unmixed and read 18.86 against an envelope value of 10.2 (cause open). Check, and where the two differ take the envelope value from the profiles.
- A branched pair measures the rate effect from the branch point on. Any earlier offset is inherited, not added, and hot-bottom burning partly erases it as the envelope approaches equilibrium. Quote the branch point; the full effect needs pairs from the pre-main sequence. A partner branched after the process under study has started is not a one-change comparison.
- A resolution test whose limiter never acts tests nothing.
- A finer mesh can switch thermohaline mixing off. With MESA's default 3-cell smoothing of the composition term, the 1.25 Msun tip ratio rose from 8.20 to 13.72 at `mesh_delta_coeff` 0.5 and to the dredge-up value 26.88 at 0.25; with the smoothing widened to 9 cells, the onset returned to the bump. Read a late onset on a finer mesh as an artefact until the profiles show one connected thermohaline region (2026-10-28).
- A 26Al/27Al from a network with a single `al26` species is a total. It does not test the ground/isomer branching (the `al26al27_before` of the case-02 AGB summary is such a value).
- Mass fractions are not number ratios: multiply X12/X13 by 13/12.
- An equilibrium value is not a floor. A burning layer passes through a transient minimum below it. Dilution is different: it cannot go below its lowest component, because the mixed ratio is a ratio of sums.
- A rate effect need not be monotonic in the mixing efficiency. Quote it per prescription.
