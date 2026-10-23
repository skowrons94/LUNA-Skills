---
name: mirror-nucleus
description: Use charge symmetry between mirror nuclei (7Be/7Li, 3He+alpha/t+alpha, p+X/n+X) as a constraint or a test — predict a mirror spectrum with a cluster potential fixed in one nucleus, the ratio of mirror ANCs (robust where each ANC is not), reduced widths compared at a common channel radius, Thomas-Ehrman shifts relative to thresholds, and the free-versus-constrained refit of a mirror R-matrix evaluation that measures what transferring widths costs the data. Use when a task asks whether a level, width or ANC of one nucleus implies something for its mirror, whether two mirror R-matrix fits are consistent, or how to test charge symmetry quantitatively; such tests must be computed, not estimated from memory.
---
# Mirror nuclei

Charge symmetry is a strong constraint, but it does not hold for everything. It equates the nuclear part of mirror states. It does not equate their Coulomb barriers, thresholds or the continuum each channel couples to. A useful mirror test says which side of that line a quantity is on.

## Route the task

- **The cluster potential** both nuclei share: `cluster-potential` (this skill imports its library).
- **The mirror R-matrix fits** and their refits: `azure2`. The refit design is in [method.md](references/method.md).
- **Shell-model mirror states**, identical without Coulomb: `shell-model`.
- **Scattering lengths of the two s waves**: `effective-range`.
- Everything else: methods in [method.md](references/method.md); checks and lessons in [validation.md](references/validation.md).

## Non-negotiable boundaries

1. **Fix in one nucleus, predict in the other.** A mirror comparison in which both sides are fitted tests nothing. Change only Z1Z2 and the masses (`mirror_system`).
2. **Compare reduced widths at the same radius.** Mirror fits often use different channel radii (7Be 4.7 fm, 7Li 4.2 fm). Re-evaluate θ² at a common radius (`theta2_at_radii`), or show that the ratio does not depend on it.
3. **Prefer ratios.** The ANC ratio is robust where each ANC is not: 7Be/7Li ground state 1.333 ± 0.006 while each C² varied by 70 % over the geometry. Quote the ratio with its geometry spread.
4. **Refer energies to the right thresholds.** A nucleon-on-core state belongs to the core+nucleon threshold of each nucleus. A cluster state belongs to the cluster threshold. The Thomas–Ehrman shift is the difference after that referencing.
5. **A constrained mirror refit needs a fair control.** Run the same level structure with the transferred widths free, and quote Δχ² against that. In AZURE2, carry parameters by identity (raw .azr energy, J^π, pair, l, s), not by name, and use one session per process. Fix the fitted amplitude (the formal θ² is linear in it), not an observed width that moves with the energy.
6. **Say which data the test sees.** A mirror project without the nucleon-channel data (e.g. 7Li without n+6Li) can test the cluster widths only.

## Working method

1. Fix the cluster potential in the better-known nucleus (`cluster-potential`). Predict the mirror spectrum with `predict_levels` and compare with the evaluated levels.
2. ANCs: `anc_ratio` over ≥ 5 geometries. Combine the ratio with a measured ANC of one nucleus to constrain the other.
3. Widths: re-evaluate both fits' θ² at common radii and form the ratio.
4. R-matrix test: build the free and constrained variants of the mirror project on one level structure (method.md), refit both, and report Δχ², the datasets that pay, and where the constrained levels move.
5. Interpret: quantities that agree are properties of the states; ones that do not are continuum or Coulomb effects. Say which, with the evidence.

## Scripts (Python with numpy, scipy, mpmath; needs cluster-potential next to this skill)

```bash
python3 SKILL_DIR/scripts/selftest.py     # must print PASS (7Li predicted from 7Be depths; ANC ratio 1.333)
```
```python
import sys; sys.path.insert(0, "SKILL_DIR/scripts"); import mirror as mr; cl = mr.cl
be7 = cl.System("alpha", "3He", thr_ex=1.5866, n_min=3); li7 = mr.mirror_system(be7, thr_ex=2.4675)
rows, ratio, spread = mr.anc_ratio(be7, -1.5866, li7, -2.4675, l=1, nodes=1)    # 1.333 +- 0.006
```
