#!/usr/bin/env python3
"""Build and smoke-test the neutron-counter template (needs Geant4; not part of selftest.py).

Configures and builds assets/neutron-counter in BUILD_DIR, then runs macros/smoke.mac three times
through run_checked.py: twice with the same seeds (outputs must be identical) and once with other seeds
(outputs must differ). Passes when every run is clean, registers thermal scattering for the moderator
hydrogen, has gas captures > 0, and the checks hold. It also checks that the application refuses to run
without explicit seeds and with a non-HP physics list. Configure, build and runs use nice; choose --jobs
from the current load (uptime), not from the core count.

    python3 test_template.py --build-dir /data/scratch/ncounter-build --jobs 4
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_g4_datasets  # noqa: E402
import run_checked  # noqa: E402

TEMPLATE = HERE.parent / "assets" / "neutron-counter"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build-dir", type=Path, required=True, help="scratch directory on a data disk")
    ap.add_argument("--jobs", type=int, default=2, help="parallel compile jobs (keep low on shared machines)")
    ap.add_argument("--cxx", default=None, help="C++ compiler (default: CMake's choice)")
    a = ap.parse_args()
    failed = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            failed.append(name)

    if not shutil.which("geant4-config"):
        print("SKIP  geant4-config not on PATH: activate the Geant4 environment first")
        return 2
    ds = check_g4_datasets.check(dict(__import__("os").environ), tsl=True)
    check("Geant4 datasets found (with thermal scattering)", ds["ok"])
    for p in ds["problems"]:
        print("      " + p)
    build = a.build_dir.resolve()
    build.mkdir(parents=True, exist_ok=True)
    cfg = ["cmake", "-S", str(TEMPLATE), "-B", str(build), "-DCMAKE_BUILD_TYPE=Release"]
    if a.cxx:
        cfg.append(f"-DCMAKE_CXX_COMPILER={a.cxx}")
    nice = ["nice", "-n", "10"]
    with open(build / "configure.log", "w") as log:
        ok = subprocess.run(nice + cfg, stdout=log, stderr=subprocess.STDOUT).returncode == 0
    with open(build / "build.log", "w") as log:
        ok = ok and subprocess.run(nice + ["cmake", "--build", str(build), "-j", str(a.jobs)],
                                   stdout=log, stderr=subprocess.STDOUT).returncode == 0
    exe = build / "ncounter"
    check("template configures and builds", ok and exe.is_file())
    if failed:
        print("FAIL")
        return 1
    macro = build / "macros" / "smoke.mac"
    for label, extra in (("without --seeds", []), ("with a non-HP list", ["--seeds", "1", "2", "--phys", "FTFP_BERT"])):
        r = subprocess.run([str(exe), str(macro), *extra], capture_output=True, text=True, cwd=build)
        check(f"refuses to run {label}", r.returncode == 2)
    runs = {}
    for name, seeds in (("same-a", ("12345", "67890")), ("same-b", ("12345", "67890")), ("other", ("24680", "13579"))):
        out = build / "smoke-runs" / name
        if out.exists():
            shutil.rmtree(out)
        m = run_checked.run(out, [str(exe), str(macro), "--seeds", *seeds],
                            expect=["out/smoke_r0.json", "out/smoke_r0_captures.csv"],
                            json_min=["out/smoke_r0.json:gas_captures=1", "out/smoke_r0.json:n_generated=3000"],
                            require_log=[r"Element TS_H_of_Polyethylene"], timeout=1800, nice=10)
        check(f"smoke run {name}: clean log, outputs present, gas captures > 0", m["status"] == "ok")
        for p in m["problems"]:
            print("      " + p)
        runs[name] = out
    if failed:
        print("FAIL")
        return 1
    s = {k: json.loads((v / "out/smoke_r0.json").read_text()) for k, v in runs.items()}
    csv = {k: (v / "out/smoke_r0_captures.csv").read_text() for k, v in runs.items()}
    check("same seeds reproduce the summary and the per-capture CSV",
          s["same-a"] == s["same-b"] and csv["same-a"] == csv["same-b"])
    check("other seeds give a different event sample", csv["same-a"] != csv["other"])
    check("all generated events accounted for", all(d["n_generated"] == 3000 for d in s.values()))
    e = s["same-a"]["efficiency_capture"]
    print(f"      efficiency_capture={e:.4f} (seeds 12345 67890), capture_time_mean_us="
          f"{s['same-a']['capture_time_mean_us']:.1f}")
    print("FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
