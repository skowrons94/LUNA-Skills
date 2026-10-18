#!/usr/bin/env python3
"""Offline tests of check_g4_datasets.py and run_checked.py with fake dataset trees and a fake
executable (no Geant4 needed). Run: python3 test_helpers.py -> PASS/FAIL lines, exit code 1 on failure."""
import json
import os
import stat
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_g4_datasets as D  # noqa: E402
import run_checked as R  # noqa: E402

FAKE_APP = """#!{py}
import json, os, sys
macro = open(sys.argv[1]).read()
os.makedirs("out", exist_ok=True)
mode = macro.strip()
if mode == "fatal":
    print("-------- EEEE ------- G4Exception-START -------- EEEE -------")
    print("*** Fatal Exception *** core dump ***")
    sys.exit(0)  # a zero return code must not hide the fatal exception
if mode == "overlap":
    print("Overlap is detected for volume Tube:0 (G4Tubs) with Channel:0 (G4Tubs)")
if mode != "nooutput":
    json.dump({{"gas_captures": 0 if mode == "zero" else 12, "n_generated": 100}}, open("out/s.json", "w"))
print("-------- WWWW ------- G4Exception-START -------- WWWW -------")
print("run finished")
"""


def run(check):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # --- datasets: a complete fake tree, then break it
        base = tmp / "data"
        (base / "NDL4.7/Capture").mkdir(parents=True)
        (base / "NDL4.7/ThermalScattering").mkdir()
        (base / "EMLOW8.5/livermore").mkdir(parents=True)
        (base / "PhotonEvaporation5.7").mkdir()
        (base / "PhotonEvaporation5.7/z26.a56").write_text("x")
        (base / "RadioactiveDecay5.6").mkdir()
        (base / "RadioactiveDecay5.6/z27.a60").write_text("x")
        (base / "PARTICLEXS4.0/neutron").mkdir(parents=True)
        (base / "ENSDFSTATE2.3").mkdir()
        (base / "ENSDFSTATE2.3/ENSDFSTATE.dat").write_text("x")
        env = {"G4NEUTRONHPDATA": str(base / "NDL4.7"), "G4LEDATA": str(base / "EMLOW8.5"),
               "G4LEVELGAMMADATA": str(base / "PhotonEvaporation5.7"),
               "G4RADIOACTIVEDATA": str(base / "RadioactiveDecay5.6"),
               "G4PARTICLEXSDATA": str(base / "PARTICLEXS4.0"), "G4ENSDFSTATEDATA": str(base / "ENSDFSTATE2.3")}
        cfg = tmp / "geant4-config"
        cfg.write_text(f"#!/bin/sh\necho 'G4NDL G4NEUTRONHPDATA {base}/G4NDL4.7'\n"
                       f"echo 'G4EMLOW G4LEDATA {base}/EMLOW8.5'\n")
        cfg.chmod(cfg.stat().st_mode | stat.S_IEXEC)
        r = D.check(env, tsl=True, config_exe=str(cfg))
        check("datasets: complete fake tree passes with --tsl", r["ok"])
        check("datasets: geant4-config name mismatch is reported as a note",
              any("G4NEUTRONHPDATA" in n and "missing" in n for n in r["notes"])
              and r["datasets"]["G4LEDATA"]["agrees_with_geant4_config"])
        r = D.check({k: v for k, v in env.items() if k != "G4LEDATA"}, config_exe=str(cfg))
        check("datasets: unset required variable fails", not r["ok"] and any("G4LEDATA" in p for p in r["problems"]))
        (base / "NDL4.7/ThermalScattering").rmdir()
        r = D.check(env, tsl=True, config_exe=str(cfg))
        check("datasets: missing ThermalScattering fails only with --tsl",
              not r["ok"] and D.check(env, config_exe=str(cfg))["ok"])
        r = D.check(dict(env, G4LEDATA=str(base / "PARTICLEXS4.0")), config_exe=str(cfg))
        check("datasets: wrong content is detected", not r["ok"])

        # --- run_checked with a fake application
        app = tmp / "fakeapp"
        app.write_text(FAKE_APP.format(py=sys.executable))
        app.chmod(app.stat().st_mode | stat.S_IEXEC)

        def go(name, mode, **kw):
            mac = tmp / f"{name}.mac"
            mac.write_text(mode)
            return R.run(tmp / "runs" / name, [str(app), str(mac)], expect=["out/s.json"],
                         json_min=["out/s.json:gas_captures=1"], timeout=60, **kw)

        m = go("ok", "ok")
        check("run: good run is ok", m["status"] == "ok" and m["return_code"] == 0)
        check("run: input copied and hashed", (tmp / "runs/ok/inputs/ok.mac").is_file() and
              all(len(v["sha256"]) == 64 for v in m["inputs"].values()))
        check("run: manifest written and warnings counted",
              json.loads((tmp / "runs/ok/manifest.json").read_text())["warnings_in_log"] == 1)
        check("run: fatal exception fails despite return code 0", go("fatal", "fatal")["status"] == "failed")
        check("run: overlap message fails", go("overlap", "overlap")["status"] == "failed")
        check("run: missing output fails", go("noout", "nooutput")["status"] == "failed")
        check("run: JSON threshold fails on zero captures", any("gas_captures" in p for p in go("zero", "zero")["problems"]))
        try:
            go("ok", "ok")
            refused = False
        except FileExistsError:
            refused = True
        check("run: refuses a non-empty run directory", refused)
        os.environ.setdefault("G4LEDATA", "/nonexistent")
        check("run: environment captured", "G4LEDATA" in go("env", "ok")["environment"])


if __name__ == "__main__":
    failed = []

    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            failed.append(name)

    run(check)
    print("FAIL" if failed else "PASS")
    sys.exit(1 if failed else 0)
