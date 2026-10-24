---
name: mirror-nucleus
description: Test or use charge symmetry between mirror nuclei (7Be/7Li, 3He+alpha/t+alpha, p+X/n+X): a mirror spectrum predicted with a cluster potential fixed in one nucleus, mirror ANC ratios, reduced widths at a common channel radius, Thomas-Ehrman shifts, and a free-versus-constrained mirror R-matrix refit. Use when a task asks whether a level, width or ANC of one nucleus implies something for its mirror, whether two mirror R-matrix fits are consistent, or how to test charge symmetry quantitatively; such tests must be computed, not estimated from memory.
---
# Mirror nuclei

Charge symmetry equates the nuclear part of mirror states, and it is therefore a strong constraint between, for example, 7Be and 7Li. It does not equate their Coulomb barriers, their thresholds or the continuum each channel couples to, so it does not hold for everything a fit reports. A useful mirror test says which side of that line a quantity is on. You need the cluster potential fixed in the better-known nucleus, the evaluated levels of both, and for the R-matrix test the two mirror projects. You get the predicted mirror spectrum, ANC and width ratios with their geometry spread, Thomas–Ehrman shifts, and a Δχ² that measures what transferring widths costs the mirror data. The methods are described in [method.md](references/method.md).

## Where this fits

- Comes from: the cluster potential both nuclei share, from `cluster-potential`, whose library this skill imports; the mirror R-matrix fits from `azure2`, with the refit design in [method.md](references/method.md); mirror states from `shell-model`; s-wave scattering lengths from `effective-range`.
- Goes to: the refits in `azure2`; the scattering lengths of the two s waves in `effective-range`. Shell-model mirror states, identical without Coulomb, come from `shell-model`.
- Checked by: `scripts/selftest.py` (must print PASS) and the validation ladder in [validation.md](references/validation.md), which also records the lessons that changed results.

## Method

A quantity is fixed in one nucleus and predicted in the other; ratios are preferred over single values, and an R-matrix constraint is judged against a free control on the same level structure.

1. Fix the cluster potential in the better-known nucleus with `cluster-potential`. Predict the mirror spectrum with `predict_levels` and compare it with the evaluated levels.
2. Compute the ANCs with `anc_ratio` over ≥ 5 geometries. Combine the ratio with a measured ANC of one nucleus to constrain the other.
3. Re-evaluate the θ² of both fits at common radii and form the ratio.
4. For the R-matrix test, build the free and constrained variants of the mirror project on one level structure (method.md) and refit both. Report Δχ², the datasets that pay, and where the constrained levels move.
5. Interpret. Quantities that agree are properties of the states; quantities that do not are continuum or Coulomb effects. Say which, with the evidence.

## Rules and their reasons

1. A quantity is fixed in one nucleus and predicted in the other, because a mirror comparison in which both sides are fitted tests nothing. Only Z1Z2 and the masses change (`mirror_system`).
2. Reduced widths are compared at the same radius. Mirror fits often use different channel radii (7Be 4.7 fm, 7Li 4.2 fm), so θ² is re-evaluated at a common radius with `theta2_at_radii`, or the ratio is shown not to depend on it.
3. Ratios are preferred. The ANC ratio is robust where each ANC is not, because it is set by the asymptotic Coulomb and binding difference, which the geometry hardly touches (method.md). For the 7Be/7Li ground state the ratio is 1.333 ± 0.006 while each C² varied by 70 % over the geometry. The ratio is quoted with its geometry spread.
4. Energies are referred to the right thresholds. A nucleon-on-core state belongs to the core+nucleon threshold of each nucleus, and a cluster state to the cluster threshold. The Thomas–Ehrman shift is the difference that remains after that referencing.
5. A constrained mirror refit needs a fair control, which is the same level structure with the transferred widths free, and Δχ² is quoted against that control. In AZURE2, parameters are carried by identity (raw .azr energy, J^π, pair, l, s), not by name, because names shift when levels are inserted (method.md); one session is used per process. The fitted amplitude is fixed, since the formal θ² is linear in it, not an observed width that moves with the energy.
6. The test says which data it sees. A mirror project without the nucleon-channel data, for example 7Li without n+6Li, can test the cluster widths only.

## Scripts

The code needs Python with numpy, scipy and mpmath, and cluster-potential next to this skill. Replace SKILL_DIR with this skill's directory.

```bash
python3 SKILL_DIR/scripts/selftest.py     # must print PASS (7Li predicted from 7Be depths; ANC ratio 1.333)
```
```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts"); import mirror as mr; cl = mr.cl
be7 = cl.System("alpha", "3He", thr_ex=1.5866, n_min=3); li7 = mr.mirror_system(be7, thr_ex=2.4675)
rows, ratio, spread = mr.anc_ratio(be7, -1.5866, li7, -2.4675, l=1, nodes=1)    # 1.333 +- 0.006
```

## What to deliver

- The predicted mirror spectrum against the evaluated levels, with nothing refitted.
- ANC and θ² ratios with their spread over the geometries or common radii.
- Thomas–Ehrman shifts with the thresholds each energy is referred to and the fit the energies come from.
- For the R-matrix test: Δχ² of constrained against free, its per-dataset breakdown, the moved levels, and the channels the mirror data do not see.
