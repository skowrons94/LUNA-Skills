"""Park norm J of every unbound level of an AZURE2 fit, from pyazr alone.

In the Brune parameterization the observed reduced widths are the formal ones times one factor per level,
J = 1 / (1 + sum_c gamma_c^2 dS_c/dE)  (T.-S. Park, Phys. Rev. C 104, 064612 (2021)), so
J = theta2 / theta2_formal of pyazr's dimensionless_widths, the same for every open particle channel of the
level (checked: the script prints the spread).  It includes whatever exterior AZURE2 uses (e.g. a hybrid
nuclear tail).  1 - J is the share of the state outside the channel radius exactly for a bound state
(Thomas normalization) and by analogy for a resonance.  J << 1 marks a saturated level whose Brune widths
look ordinary.

    python park_norms.py model.azr param.sav [--jmin 0.5] [--bg 29]     # run from the directory the .azr expects
"""
import argparse
from collections import defaultdict

import numpy as np
from pyazr import azure2
from pyazr.bands import best_fit_params

ap = argparse.ArgumentParser()
ap.add_argument("azr"); ap.add_argument("sav")
ap.add_argument("--jmin", type=float, default=0.5, help="flag levels below this J")
ap.add_argument("--bg", type=float, default=29.0, help="E_x (MeV) above which levels count as background poles")
a = ap.parse_args()

with azure2(a.azr, cwd=".") as m:
    x = np.asarray(best_fit_params(m, path=a.sav), float)
    J = defaultdict(list)
    for c in m.dimensionless_widths(x):
        if c.radiation_type == "P" and c.value and c.theta2 and c.theta2_formal:
            J[(c.jpi, round(c.level_energy, 3))].append(c.theta2 / c.theta2_formal)
for (jpi, ex), v in sorted(J.items(), key=lambda kv: (kv[0][0], kv[0][1])):
    v = np.array(v); tag = "background pole" if ex >= a.bg else ("SATURATED" if v.mean() < a.jmin else "")
    print(f"{jpi:>6} E_x {ex:8.3f}  J = {v.mean():.4f}  (channel spread {v.max() - v.min():.1e})  {tag}")
