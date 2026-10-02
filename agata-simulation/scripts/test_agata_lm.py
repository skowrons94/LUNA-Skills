#!/usr/bin/env python3
"""Offline test: parse a synthetic GammaEvents file, pack per segment, check energy conservation.
Prints PASS on success."""
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agata_lm import convert_lm, load  # noqa: E402

LM = """AGATA 
OUTPUT_MASK 111001000
$
-100	         1
 -101    0.00169  0.00000  0.00000  1.00000
 -102      0.000    0.000    0.000
   -1   6791.400  0.95169 -0.30616  0.02364 0
   -1    765.000  0.66625 -0.22275 -0.71168 1
    1   1000.000  -38.150   24.481   39.336 04
    1   2000.000  -38.250   24.581   39.436 04
    2    765.000   10.000   20.000   50.000 35
-100	         2
 -101    0.00169  0.00000  0.00000  1.00000
 -102      0.000    0.000    0.000
   -1   7445.000  0.0 0.0 1.0 2
"""

with tempfile.TemporaryDirectory() as t:
    f = Path(t) / "GammaEvents.0000"
    f.write_text(LM)
    n = convert_lm(f, Path(t) / "hits.npz")
    d = load(Path(t) / "hits.npz")
    assert n == 2 and int(d["n_events"]) == 2
    assert len(d["e"]) == 2, "two segments hit in event 0 after packing"
    k = np.argmax(d["e"])
    assert abs(d["e"][k] - 3000.0) < 1e-3 and d["seg"][k] == 4 and d["det"][k] == 1
    assert abs(d["x"][k] - (-38.150 * 1000 - 38.250 * 2000) / 3000) < 1e-3
    assert d["seg"][np.argmin(d["e"])] == 3 * 6 + 5
    dep = np.bincount(d["event"], weights=d["e"], minlength=2)
    emit = np.bincount(d["g_event"], weights=d["g_e"], minlength=2)
    assert np.all(dep <= emit + 1.0)
print("PASS")
