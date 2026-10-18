#!/usr/bin/env python3
"""Run the self-tests of every pure-Python helper of the geant4-simulation skill; prints PASS on success.
Needs only the Python standard library; Geant4 is not required (the C++ template has its own build
test, see assets/neutron-counter/README.md).

    python3 selftest.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import counting  # noqa: E402
import test_helpers  # noqa: E402
import test_kinematics  # noqa: E402

failed = []


def check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    if not cond:
        failed.append(name)


for label, fn in (("kinematics", test_kinematics.run), ("counting", counting.selftest),
                  ("datasets and run_checked", test_helpers.run)):
    print(f"# {label}")
    fn(check)

print("FAIL" if failed else "PASS")
sys.exit(1 if failed else 0)
