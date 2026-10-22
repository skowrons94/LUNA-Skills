# Configuration file

One JSON file describes one network calculation. `burn.py` runs it once; `sensitivity.py` runs it many times with varied rates. Relative paths resolve against the configuration file's directory. Keep the configuration, the tables it points to and the outputs in the project (one study directory per question), not in the skill folder.

```json
{
  "network": {
    "nuclei": ["p", "he4", "ne20", "ne21", "ne22", "na22", "na23", "mg24", "mg25", "mg26",
               "al25", "al26", "al27", "si27", "si28"],
    "with_reverse": true,
    "exclude": [],
    "screening": "chugunov_2007"
  },
  "starlib": {"file": "/path/to/STARLIB/starlib.dat", "use": "uncertainty"},
  "rates": [
    {"rate": "mg25(p,g)al26", "table": "rates/mg25pg_azure.csv", "reverse": "derive",
     "label": "lu26", "outside": "error"},
    {"branch": {"rate": "mg25(p,g)al26", "products": ["mg26"], "fraction": 0.18,
                "why": "isomer feeding; f_m from the measured ground-state branching"}},
    {"rate": "al26(p,g)si27", "multiply": 1.0},
    {"add": {"reactants": ["be7", "d"], "products": ["p", "he4", "he4"]},
     "table": "rates/be7dp.csv", "reverse": "none"}
  ],
  "uncertainty": {"fu": {"mg25(p,g)al26": "rates/mg25pg_azure.csv", "al26(p,g)si27": 1.6},
                  "default_fu": null},
  "initial": {"X": {"p": 0.70, "he4": 0.2965, "mg24": 5.2e-4}, "normalize": false},
  "conditions": {"type": "constant", "T_K": 6.0e7, "rho_cgs": 30.0, "t_end_s": 3.0e9},
  "output": {"n_log": 40, "observables": ["X(al26)", "X(al26)/X(al27)", "Y(mg24)/Y(mg25)", "E"]},
  "solver": {"rtol": 1e-6, "atol": 1e-20, "method": "BDF"}
}
```

## network

- `nuclei`: pynucastro names (`p`, `n`, `d`, `he4`, `c12`, `al26`, …). The network contains every REACLIB rate linking them (`ReacLibLibrary().linking_nuclei`). Requested nuclei that no rate links stay in as inert species (they still count in the composition and the screening) and are listed in `info.inert`.
- `with_reverse` (default true): include REACLIB reverse rates. Needed wherever photodisintegration or (p,α)↔(α,p) balance matters (T9 ≳ 0.3, explosive burning); harmless at lower T.
- `exclude`: rate names to remove; each removal is recorded.
- `screening`: `chugunov_2007` (default), `screen5`, `chugunov_2009`, `potekhin_1998`, `debye_huckel`, `none`.

## starlib

- `use: "uncertainty"` attaches STARLIB's factor uncertainty fu(T) to every network rate that matches a STARLIB entry, and keeps the REACLIB rate itself. Use it for a first sensitivity pass. The REACLIB rate and the STARLIB median can differ, which is visible with `rates.py compare`.
- `use: "rates"` replaces matched rates by the STARLIB median as a table and uses its fu. This is the consistent choice for a Monte Carlo study, because median and spread come from the same evaluation.
- `only`: list of rate names to restrict either mode to.
- STARLIB has separate ²⁶Al ground state (`al-6`) and isomer (`al*6`) entries. pynucastro's REACLIB has only total `al26`. Totals match totals; for the split see `branch` below and [physics.md](physics.md).

## rates (applied in order, after STARLIB)

| Item | Effect |
|---|---|
| `{"rate": N, "table": F}` | Replace rate N by the table (rate-table contract: `T9,rate[,fu]`). `outside`: `error` (default), `clamp` or `zero` beyond the table. |
| `{"rate": N, "reaclib_sets": [[a0..a6], …]}` | Replace by REACLIB-form sets (e.g. from `rates.py fit`). |
| `reverse` (with a replacement) | `derive` (default when the network has the reverse): reverse from detailed balance of the new forward rate, with pynucastro partition functions and Q from the mass table. `keep` (recorded as a warning) or `drop`. |
| `{"rate": N, "multiply": f}` | Constant factor, recorded. |
| `{"branch": {"rate": N, "products": [...], "fraction": f}}` | Split the flow of N: fraction f goes to the new products, 1−f stays. Both branches share N's uncertainty and random variable. Use for isomer feeding (²⁵Mg(p,γ)²⁶Alᵐ → ²⁶Mg) and other effective channels. |
| `{"add": {"reactants": [...], "products": [...]}, "table": F}` | A rate that REACLIB lacks. `reverse: "derive"` adds its detailed-balance reverse. |

Rate tables can be made with `rates.py from-azure` (AZURE2 output), `from-band` (columns T9 low adopted high, 68 %: fu = √(high/low)) and `from-sfactor` (S(0), S′, S″ → bare non-resonant rate, bare-nucleus reduced mass).

Names are pynucastro short names (`mg25(p,g)al26`, `he4(aa,g)c12`, `al26(g,p)mg25`) or `fname`s (`p_Mg25__Al26`). An ambiguous name stops the build.

## uncertainty

- `fu`: per rate, a constant (≥ 1) or a rate-table file with an `fu` column. The reverse rate and any branch share it.
- `correlations`: `[{"rates": [A, B], "rho": r, "why": "..."}]`. The groups' normal variables are drawn with this correlation (Cholesky). For two rates sharing a fully correlated fractional systematic s (e.g. a stopping-power or normalisation uncertainty), ρ(T) = ln(1+s)²/(ln fu_A ln fu_B). `rates.py shared-rho A.csv B.csv --shared s --T9 ...` prints it; use its value at the site temperature. Ratios of correlated rates are much better known than either rate.
- `default_fu`: a factor for every non-weak rate without one. It is off by default. Each use is written to `info.warnings`, because an assumed factor shapes the ranking as much as a measured one does.
- Rates without fu are held fixed in Monte Carlo and listed in `info.fixed`. Report that list with any ranking.

## initial, conditions, output, solver

- `initial.X`: mass fractions by nucleus. They must sum to 1 within 10⁻⁶ unless `normalize: true`. State where the composition comes from (solar mixture and reference, a stellar model's shell, a test case).
- `conditions`: `{"type": "constant", "T_K", "rho_cgs", "t_end_s"}` or `{"type": "trajectory", "file": F}` (thermo-trajectory contract: `time_s,T_K,rho_cgs`), with optional `T_scale` and `rho_scale` for scans. Trajectories are interpolated linearly in (t, ln T, ln ρ), and the integration restarts at each trajectory point.
- `output.observables`: `X(nuc)`, `Y(nuc)`, ratios of two such terms, and `E` (integrated specific energy, erg/g), all at the final time. `n_log` or `times_s` set the rows of `abundances.csv`.
- `solver`: `rtol` (1e-6), `atol` on Y (1e-20), `method` (`BDF`, `Radau` or `LSODA`). Check convergence with `burn.py --check-tolerance`.
