"""Read an AZURE2 reactionrates.out and set it against the REACLIB rate in
pynucastro; optionally return a callable usable as a `replace` entry in
../bbn-lithium/bbn.py or any pynucastro-based network script.

usage: python3 compare_rate.py reactionrates.out "c12(p,g)n13"
"""
import sys
import numpy as np
import pynucastro as pyna


def load_azure_rate(path):
    T9, v = np.loadtxt(path, skiprows=1, usecols=(0, 1), unpack=True)
    lT, lv = np.log(T9), np.log(np.maximum(v, 1e-300))
    return lambda TK: float(np.exp(np.interp(np.log(TK / 1e9), lT, lv)))


if __name__ == "__main__":
    path, name = sys.argv[1], sys.argv[2]
    az = load_azure_rate(path)
    rl = pyna.ReacLibLibrary().get_rate_by_name(name)
    print(f"REACLIB set(s): {[s.labelprops for s in rl.sets]}")
    print(f"{'T9':>6s} {'AZURE2':>11s} {'REACLIB':>11s} {'ratio':>7s}")
    for T9 in [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]:
        a, r = az(T9 * 1e9), rl.eval(T9 * 1e9)
        print(f"{T9:6.2f} {a:11.4e} {r:11.4e} {a / r:7.3f}")
