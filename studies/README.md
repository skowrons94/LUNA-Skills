# Studies: open problems in nuclear astrophysics

Exploratory calculations on top of the skills in this repository, pynucastro
(REACLIB rates, networks) and AZURE2/pyazr (R-matrix). Each folder is
self-contained and reproducible from its scripts.

| Folder | Question | Status |
|---|---|---|
| `bbn-lithium/` | Can nuclear physics solve the cosmological ⁷Li problem? | done: no; see its README |
| `azure2-to-pynucastro/` | Hand an AZURE2 rate to a pynucastro network | pipeline works; needs a fitted evaluation |

## Where the field says the open points are

Main sources: the community white paper *Horizons: Nuclear Astrophysics in the
2020s and Beyond* (Schatz et al., J. Phys. G 49, 110502, 2022), the earlier
*White paper on nuclear astrophysics and low-energy nuclear physics*
(Arcones et al., Prog. Part. Nucl. Phys. 94, 1, 2017), and Solar Fusion III
(Acharya et al., 2024). The recurring open points, in the order the LUNA + AZURE2 +
pynucastro toolkit can reach them:

| # | Problem | Key reactions | Toolkit fit |
|---|---|---|---|
| 1 | Primordial D/H as a precision cosmology probe (Ω_b h², N_eff); 2σ tension between BBN with the LUNA d(p,γ) rate and observed D/H, and an 8–10 % gap between LUNA and ab initio d(p,γ) | d(p,γ)³He, d(d,n)³He, d(d,p)t | High. BBN code here gives D/H sensitivities (−0.31, −0.54, −0.46). AZURE2 already handles identical-particle dd channels (`tests/identical_dd_mott`). A Bayesian R-matrix evaluation of dd + d(p,γ) with LUNA data could move Ω_b h²(BBN) |
| 2 | Cosmological ⁷Li | ³He(α,γ)⁷Be, ⁷Be(n,p), ⁷Be(d,p) | Done here: a nuclear solution is excluded |
| 3 | Solar composition problem via CNO neutrinos (Borexino, SNO+, JUNO) | ¹⁴N(p,γ)¹⁵O, ¹²C(p,γ), ¹³C(p,γ) | High: LUNA measures, AZURE2 extrapolates (ground-state transition of ¹⁴N(p,γ) is the open piece) |
| 4 | ¹²C/¹³C in giants, deep mixing | ¹²C(p,γ), ¹³C(p,γ) | High: LUNA data exist; AZURE2 ¹³N evaluation is in the AZURE2 test suite |
| 5 | s-process neutron sources | ¹³C(α,n), ²²Ne(α,n) vs ²²Ne(α,γ) | Medium–high: LUNA measured ¹³C(α,n); ²²Ne(α,γ) low-energy resonances are the gap |
| 6 | Globular-cluster anticorrelations (Na–O, Mg–Al) | ²²Ne(p,γ), ²³Na(p,α)/(p,γ), ²⁵Mg(p,γ) | Medium: LUNA measured several; pynucastro hot-H-burning networks make the sensitivity quick |
| 7 | Classical novae and presolar grains | ¹⁷O(p,α)/(p,γ), ¹⁸F(p,α) | Medium: the `azure2` skill already ships the ¹⁷O THM example |
| 8 | Helium burning and the pair-instability black-hole mass gap (LIGO/Virgo) | ¹²C(α,γ)¹⁶O | High stakes, long project: global AZURE2 analysis (deBoer et al. 2017 style) plus stellar models (MESA), not just a network |
| 9 | Carbon burning, type Ia / superbursts | ¹²C+¹²C | Low for this toolkit: the physics is heavy-ion fusion hindrance, not R-matrix |
| 10 | r-process sites, kilonovae, nuclear masses | n-rich masses, β-decay, fission | Low: needs radioactive beams, not an underground accelerator |
