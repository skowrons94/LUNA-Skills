#!/usr/bin/env python3
"""Energy-conservation check of converted AGATA runs (npz from agata_lm.convert_lm).
Usage: check_energy.py run1/hits.npz [run2/hits.npz ...]  -> exit 1 if any event has Edep > Eemitted + 1 keV."""
import sys

import numpy as np

bad = 0
for f in sys.argv[1:]:
    d = np.load(f)
    n = int(d["n_events"])
    dep = np.bincount(d["event"], weights=d["e"], minlength=n)
    emit = np.bincount(d["g_event"], weights=d["g_e"], minlength=n)
    k = int(np.sum(dep > emit + 1.0))
    print(f"{f}: {n} events, {k} violate energy conservation")
    bad += k
sys.exit(1 if bad else 0)
