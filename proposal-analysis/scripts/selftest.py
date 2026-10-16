#!/usr/bin/env python3
"""Run the self-tests of every proposal-analysis helper; prints PASS on success.

    python selftest.py              # default seeds
    python selftest.py --seed 17    # same seed for every stochastic check (robustness test)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backtest_skeleton  # noqa: E402
import peelle_demo  # noqa: E402
import power_skeleton  # noqa: E402
import sampling_checks  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=None)
seed = ap.parse_args().seed
failed = []


def check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    if not cond:
        failed.append(name)


for module in (sampling_checks, backtest_skeleton, peelle_demo, power_skeleton):
    print(f"# {module.__name__}")
    if seed is None:
        module.selftest(check)
    else:
        module.selftest(check, seed)

print("FAIL" if failed else "PASS")
sys.exit(1 if failed else 0)
