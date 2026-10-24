# Which burning sets an observable, which phase shows it, which levers matter

Keys are Zotero keys of the Astrophysics project's snapshot (`tools/zotlib.py text KEY`). K&L is Karakas & Lattanzio 2014 (99Q6KV5X) and C&L is Charbonnel & Lagarde 2010 (BIDNYM5H); their numbers were checked against the arXiv preprints in the snapshot. "Not tested here" means that neither a project run nor a paper we read checks the statement.

## Observables and their burning

| Observable | Burning that sets it | Equilibrium or transient | Exposed by | Anchor |
|---|---|---|---|---|
| 12C/13C | CN cycle (partial burning above the core; H shell; HBB); worked example: one-zone burns at 20–80 MK | CN equilibrium ≈ 3 (K&L 3.6.1); as a number ratio the equilibrium is λ13/λ12 (CN branch without 15N recycling), and while 12C burns the ratio passes a transient minimum ≈ λ13/λ12 − 1 (derived; check: LUNA 3.531 − 1 = 2.53 against 2.548 from the case-02 one-zone scan, `one_zone/results/exposure_ratio.json`) | FDU, extra mixing above the bump, HBB; TDU raises it (K&L 3.5.1) | K&L Table 1, 3.6.1; worked example |
| 14N/15N | CN cycle destroys 15N, makes 14N | ≳ 10 000 under HBB (K&L 3.6.1, 6 Msun, Z = 0.02 model) | FDU (472 → 884 at 1 Msun), HBB | K&L Table 1, 3.6.1 |
| 16O/17O | 17O made by the CNO bi-cycle, destroyed by 17O(p,α), 17O(p,γ); its equilibrium with 16O is very temperature sensitive (Palmerini et al. 2011, NRLFHW6Q, abstract) | depends on the 17O + p branching | FDU, non-monotonic in mass (Z = 0.02: 2720 at 1 Msun, minimum 214.6 at 2.25 Msun, 375.5 at 5 Msun); RGB extra mixing changes it only marginally; HBB → final value ≈ 465 (6 Msun, Z = 0.02) | K&L Table 1, 3.6.1; Straniero et al. 2017 (TDY9DYWG, abstract: post-FDU 16O/17O ~20 % larger with the revised 17O(p,α) rate) |
| 16O/18O | 18O destroyed by H burning | under HBB > 1e6 (6 Msun, Z = 0.02) | FDU (524 → 556 at 1 Msun), HBB | K&L Table 1, 3.6.1 |
| 7Li | destroyed above about 2.5 MK (K&L 2.4); made by the Cameron–Fowler mechanism (3He(α,γ)7Be, 7Be carried to cooler layers before p capture) | depends on mixing speed versus 7Be lifetime | FDU dilutes it; thermohaline mixing destroys it on the RGB (C&L Table 2: N(Li) 1.1 → −1.3 at 1 Msun); HBB in bright AGB stars makes it | K&L 2.4, 3.6.3; C&L abstract |
| 3He | made in low-mass main-sequence stars, burnt by 3He(3He,2p) above the bump (drives thermohaline mixing) | — | FDU; reduced but net positive yields for solar-Z low-mass stars | C&L Sect. 1, abstract |
| 23Na | Ne–Na chain: 22Ne(p,γ) makes 23Na; above 90 MK 23Na is destroyed; leakage to Mg–Al via 23Na(p,α)/(p,γ) | rate ratio sets leakage | FDU from ~1.5 Msun up (K&L Table 1: X(23Na) 3.904e-5 unchanged at 1 Msun; 5.567e-5 after FDU, 5.962e-5 after SDU at 5 Msun), SDU, HBB at low Z | K&L Table 1, 3.6.2 |
| 25Mg, 26Mg, 26Al/27Al | Mg–Al chain: 25Mg(p,γ)26Al, 26Al(p,γ) → 27Al, 26Al decay feeds 26Mg, 24Mg needs higher T; in He burning 22Ne(α,n)25Mg and 22Ne(α,γ)26Mg above ~300 MK (K&L 3.5.6). 26Al ground and isomer are separate species out of thermal equilibrium (K&L 3.6.2); Straniero et al. 2013 (AEGNXTUH, abstract) revise 25Mg(p,γ) to the isomer at 50–150 MK, "the range of temperature at which the Mg–Al cycle operates in a H-burning zone" | ground/isomer branching sets 26Al | At 6 Msun, Z = 0.02 (peak T_bce 82 MK) Ne–Na and Mg–Al are only marginally active: 25Mg, 26Mg, 27Al rise mainly through TDU, Na barely; strong at Z = 0.004 (95 MK) (K&L 3.6.2) | K&L 3.5.6, 3.6.2; AEGNXTUH |
| C/O, C stars | 12C from He burning in the intershell | — | TDU makes C stars; HBB prevents them | K&L Sects. 1, 3.2 |
| s-process (Zr, Ba, Pb; Rb) | 13C(α,n)16O in the 13C pocket (low-mass AGB); 22Ne(α,n)25Mg, needs T ≳ 300 MK (intermediate-mass AGB; switch ≃ 4 Msun at Z = 0.02, K&L 3.7.2) | neutron exposure | TDU; Rb-rich bright O-rich AGB stars observed (K&L 3.7.4) | K&L 3.7, 3.7.2, 3.7.4 |

A trap with 26Al: no network shipped with MESA r26.04.1 has separate ground and isomer species (`sagb_NeNa_MgAl.net` has one total `al26`; `stellar-evolution/references/nuclear.md`). A 26Al/27Al from such a network is a total and does not test the branching.

## Phases that expose burnt matter

| Phase | What reaches the surface | Main levers besides rates | Anchor |
|---|---|---|---|
| First dredge-up (base of the RGB) | partially H-burnt matter from above the former core (CN products, 13C, 14N, 17O) | mass and metallicity (C&L Sect. 1); rotation; opacity and composition of the code | K&L Table 1, Sect. 2 |
| Above the RGB bump | layers just above the H shell, through extra mixing: thermohaline from the 3He μ-inversion (C&L), rotation, magnetic buoyancy (K&L 2.3.5; Palmerini et al. 2011, abstract) | prescription and coefficient (C_t), mass (efficiency rises as mass falls) | C&L abstract, Sect. 1 |
| Core He flash, clump | inherits the tip composition; thermohaline mixing can continue if 3He remains (C&L Sect. 1, citing Cantiello & Langer) | mass limit of the flash (2.1 Msun solar, 1.75 at [Fe/H] = −2.3) | K&L 2.6.2 |
| Second dredge-up (M ≳ 4 Msun, early AGB) | deeper, matter exposed to complete H burning (K&L Table 1, 5 Msun: Y 0.291 → 0.309, Na up); K&L Table 1 "SDU" rows below ~4 Msun are early-AGB values | mass | K&L 2.5 |
| Third dredge-up (TP-AGB) | intershell He-burning products: 12C, 22Ne, s-process elements | convective-boundary mixing (overshoot), mass, Z, mass loss | K&L 3.3, 3.5.5, 3.7; `stellar-evolution/references/mixing.md` |
| Hot-bottom burning (M ≥ 4.5 Msun at Z = 0.02, K&L 3.2.2) | CN, Ne–Na, Mg–Al burning at the envelope base itself, T_bce > 50 MK (≳ 100 MK for low Z and high mass, at a few g cm⁻³) | α_MLT (K&L 4.1.2, Ventura & D'Antona 2005a), mass, Z (more efficient at lower Z), mass loss (HBB needs ≳ 1 Msun of envelope) | K&L 3.2, 3.2.2, 3.6.1 |
| Winds, planetary nebulae, grains | time-integrated envelope composition | mass-loss rate; the Li-rich phase has been used to constrain it (Ventura et al. 2000, via K&L 3.6.3) | K&L 3.6.3; [grains.md](grains.md) |
| Explosions (novae, supernovae) | explosive burning products | not tested here | — |

## Levers to weigh against a rate effect (within one code each)

- Mass. After the first dredge-up, 12C/13C falls by a factor 1.12 from 1.0 to 1.25 Msun (C&L Table 2, 28.8 → 25.74) and by 1.17 from 1.0 to 1.3 Msun (K&L Table 1, 28.26 → 24.07). At the C_t = 1000 tip the factor is 1.28 (C&L, 8.1 → 10.4 for 1.0 → 1.25 Msun). 16O/17O after the first dredge-up varies by a factor ~13 between 1 and 2.25 Msun (K&L Table 1).
- Rotation. The 1.25 Msun first-dredge-up 12C/13C is 25.6 with thermohaline mixing only and 18.6 with rotation at 110 km/s, a factor 1.38 (C&L Table 2).
- Mixing efficiency. Above the bump it dominates: in the worked example the tip ratio is 29.6 with weak thermohaline mixing and 8.2 with C_t = 1000.
- Metallicity. Hot-bottom burning is more efficient at low Z (K&L 3.6.1). The final 12C/13C after thermohaline mixing is lower at lower Z (K&L 2.3.4, citing Eggleton et al. 2008 and C&L; the numbers of the original papers are not checked here).
- Code and composition. The 1 Msun first-dredge-up 12C/13C is 28.26 in K&L, 28.8 in C&L and 30.64 in MESA with NACRE rates (worked example). The spread is as large as a rate effect.
- Another rate. A reaction can shift an observable thought to belong to another: 14N(p,γ) changes the temperature and so the 17O after the first dredge-up (Palmerini et al. 2011, abstract).
