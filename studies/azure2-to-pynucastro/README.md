# AZURE2 → pynucastro hand-off

Purpose: replace a REACLIB rate in a pynucastro network (or in
`../bbn-lithium/bbn.py`, through `replace={name: callable}`) with a rate
computed by AZURE2 from an R-matrix evaluation.

- AZURE2 was built from source (`-DBUILD_GUI=OFF`; GSL and readline from apt)
  and passes all 13 physics regression tests.
- Rate mode from the CLI, non-interactively:
  `printf '5\n<entrance pair>\n<exit pair>\nno\n<Tmin>\n<Tmax>\n<step>\n<param.sav or blank>\n' | AZURE2 --no-gui project.azr`
  writes `output/reactionrates.out` (T9, N_A<σv>).
- `compare_rate.py` loads that file, compares it to REACLIB, and returns an
  interpolating callable.

`c12pg_azure2_rate.out` was computed from the ¹³N **regression fixture** in the
AZURE2 test suite. That fixture is not a best fit (χ² = 3.4 × 10⁵ for 593
points), so the 30 % difference from REACLIB `ls09` printed by the script **is
not a physics result**. A Minuit fit from the fixture stalled at χ² ≈ 5.2 × 10⁴
after 170 iterations. A real ¹²C(p,γ) rate needs the published evaluation's
`param.sav` (or a proper fit with free normalisations) in place of the fixture.
