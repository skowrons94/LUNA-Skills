#!/usr/bin/env python3
"""Bounded cascade enumeration and exact independent-photon peak/no-interaction summing.

The graph is REVIEWED input: level IDs, transition probabilities including all
modes, and gamma emission probabilities (conversion can instead emit no gamma).
No energy-nearest heuristic or automatic assumption of complete adopted levels.
"""

import itertools, json, argparse
from pathlib import Path
import numpy as np


def enumerate_paths(scheme, max_paths=10000, max_depth=40):
    edges = scheme["transitions"]
    terminal = set(map(str, scheme.get("terminal_levels", ["0"])))
    group = {}
    for t in edges:
        t = dict(t)
        t["from"] = str(t["from"])
        t["to"] = str(t["to"])
        if (
            not np.isfinite(
                [t["energy_keV"], t["probability"], t.get("gamma_probability", 1)]
            ).all()
            or not 0 <= t["probability"] <= 1
            or not 0 <= t.get("gamma_probability", 1) <= 1
            or t["energy_keV"] <= 0
        ):
            raise ValueError("Invalid transition probability/energy")
        group.setdefault(t["from"], []).append(t)
    for level, ts in group.items():
        if not np.isclose(sum(t["probability"] for t in ts), 1, rtol=0, atol=1e-8):
            raise ValueError(f"Outgoing probabilities for level {level} must sum to 1")
    paths = []

    def walk(level, prob, energies, visited):
        if len(paths) >= max_paths or len(visited) > max_depth:
            raise ValueError("Cascade limit exceeded; no silent truncation")
        if level in visited:
            raise ValueError("Cycle in cascade graph")
        if level in terminal:
            paths.append((prob, energies))
            return
        if level not in group:
            raise ValueError(f"Incomplete cascade at level {level}")
        for t in group[level]:
            g = t.get("gamma_probability", 1)
            p = prob * t["probability"]
            seen = visited | {level}
            if p * g > 0:
                walk(t["to"], p * g, energies + [t["energy_keV"]], seen)
            if p * (1 - g) > 0:
                walk(t["to"], p * (1 - g), energies, seen)

    populations = scheme["populations"]
    if not np.isclose(sum(populations.values()), 1, atol=1e-8, rtol=0):
        raise ValueError("Initial level populations must sum to 1")
    for level, p in populations.items():
        if not 0 <= p <= 1:
            raise ValueError("Invalid initial population")
        if p:
            walk(str(level), p, [], set())
    return paths


def peak_probability(
    paths, energy_keV, tolerance_keV, peak_eff, total_eff, max_photons=12
):
    """Sum disjoint photopeak/no-interaction outcomes, including sum-in and sum-out.

    Independent prompt photons, ideal ROI on summed full energies; Compton continua,
    angular correlations, electron/X-ray signals and timing acceptance are excluded.
    """
    if energy_keV <= 0 or tolerance_keV <= 0:
        raise ValueError("Positive energy and matching tolerance required")
    total = 0.0
    for branch, energies in paths:
        if len(energies) > max_photons:
            raise ValueError("Too many photons for exact subset enumeration")
        ep = np.asarray([peak_eff(e) for e in energies])
        et = np.asarray([total_eff(e) for e in energies])
        if (
            not np.isfinite([ep, et]).all()
            or (ep < 0).any()
            or (et < ep).any()
            or (et > 1).any()
        ):
            raise ValueError("Require 0 <= peak efficiency <= total efficiency <= 1")
        for size in range(1, len(energies) + 1):
            for subset in itertools.combinations(range(len(energies)), size):
                if abs(sum(energies[i] for i in subset) - energy_keV) <= tolerance_keV:
                    chosen = set(subset)
                    total += branch * np.prod(
                        [
                            ep[i] if i in chosen else 1 - et[i]
                            for i in range(len(energies))
                        ]
                    )
    return float(total)


def efficiency_table(path):
    a = np.genfromtxt(path, delimiter=",", names=True, ndmin=1)
    if (
        not {"energy_keV", "peak", "total"} <= set(a.dtype.names or ())
        or not np.isfinite([a["energy_keV"], a["peak"], a["total"]]).all()
        or (np.diff(a["energy_keV"]) <= 0).any()
    ):
        raise ValueError("Efficiency CSV needs ordered energy_keV,peak,total")

    def interp(e, col):
        if e < a["energy_keV"][0] or e > a["energy_keV"][-1]:
            raise ValueError("Efficiency extrapolation forbidden")
        return float(np.interp(e, a["energy_keV"], a[col]))

    return lambda e: interp(e, "peak"), lambda e: interp(e, "total")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("scheme", type=Path)
    p.add_argument("--efficiencies", type=Path, required=True)
    p.add_argument("--energy-keV", type=float, required=True)
    p.add_argument("--tolerance-keV", type=float, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    scheme = json.loads(a.scheme.read_text())
    paths = enumerate_paths(scheme)
    ep, et = efficiency_table(a.efficiencies)
    result = {
        "peak_probability_per_initial_event": peak_probability(
            paths, a.energy_keV, a.tolerance_keV, ep, et
        ),
        "paths": len(paths),
        "path_probability_sum": sum(x[0] for x in paths),
        "assumptions": "Independent prompt photons; no angular correlations, Compton sum-in, X-rays or electron response",
    }
    with a.out.open("x") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps(result, indent=2))
