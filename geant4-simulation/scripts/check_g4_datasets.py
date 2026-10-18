#!/usr/bin/env python3
"""Check that the Geant4 datasets are where the running application will look (standard library only).

Geant4 reads each dataset from an environment variable (G4NEUTRONHPDATA, G4LEDATA, ...). This script
reports, for each variable: set or not, directory present and non-empty, expected content present, and,
if geant4-config is available, whether the path it reports agrees with the environment and exists.
Package managers may install datasets under directory names that differ from the names geant4-config
prints (for example NDL4.7 instead of G4NDL4.7); trust the directory that exists, set by the
environment's own activation scripts, and record it.

    python3 check_g4_datasets.py                 # JSON report; exit 1 if a required dataset is missing
    python3 check_g4_datasets.py --tsl           # also require the neutron thermal-scattering data
    python3 check_g4_datasets.py --require G4NEUTRONHPDATA G4LEDATA
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# variable -> (sub-paths of which at least one must exist, description)
MARKERS = {
    "G4NEUTRONHPDATA": (("Capture", "Elastic", "Inelastic"), "neutron HP data (< 20 MeV)"),
    "G4LEDATA": (("livermore", "penelope", "brem_SB"), "low-energy electromagnetic data"),
    "G4LEVELGAMMADATA": (("z1.a3", "z26.a56", "z6.a12"), "photon evaporation (nuclear levels)"),
    "G4RADIOACTIVEDATA": (("z27.a60", "z55.a137", "z1.a3"), "radioactive decay"),
    "G4PARTICLEXSDATA": (("neutron", "proton"), "particle cross sections"),
    "G4ENSDFSTATEDATA": (("ENSDFSTATE.dat",), "nuclide ground and isomeric states"),
    "G4PIIDATA": ((), "PIXE / particle-induced X-ray data"),
    "G4REALSURFACEDATA": ((), "optical surfaces"),
    "G4SAIDXSDATA": ((), "SAID nucleon cross sections"),
    "G4ABLADATA": ((), "ABLA de-excitation"),
    "G4INCLDATA": ((), "INCL cascade"),
    "G4PARTICLEHPDATA": ((), "optional charged-particle HP data (TENDL)"),
    "G4CHANNELINGDATA": ((), "optional channeling data"),
}
DEFAULT_REQUIRED = ("G4NEUTRONHPDATA", "G4LEDATA", "G4LEVELGAMMADATA", "G4RADIOACTIVEDATA",
                    "G4PARTICLEXSDATA", "G4ENSDFSTATEDATA")


def geant4_config_datasets(exe: str | None) -> dict:
    """{variable: path} from `geant4-config --datasets`, or {} if unavailable."""
    exe = exe or shutil.which("geant4-config")
    if not exe:
        return {}
    try:
        out = subprocess.run([exe, "--datasets"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    found = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1].startswith("G4"):
            found[parts[1]] = parts[2]
    return found


def check(env: dict, required=DEFAULT_REQUIRED, tsl: bool = False, config_exe: str | None = None) -> dict:
    cfg = geant4_config_datasets(config_exe)
    report, problems = {}, []
    for var in sorted(set(MARKERS) | set(cfg) | set(required)):
        markers, desc = MARKERS.get(var, ((), ""))
        path = env.get(var)
        item = {"description": desc, "env": path, "exists": False, "non_empty": False, "content_ok": None}
        if path:
            p = Path(path)
            item["exists"] = p.is_dir()
            item["non_empty"] = item["exists"] and any(p.iterdir())
            if markers and item["exists"]:
                item["content_ok"] = any((p / m).exists() for m in markers)
            if var == "G4NEUTRONHPDATA" and item["exists"]:
                item["thermal_scattering"] = (p / "ThermalScattering").is_dir()
        if var in cfg:
            item["geant4_config"] = cfg[var]
            item["geant4_config_exists"] = Path(cfg[var]).is_dir()
            item["agrees_with_geant4_config"] = bool(path) and Path(cfg[var]) == Path(path)
        report[var] = item
        if var in required:
            if not path:
                problems.append(f"{var} is not set")
            elif not item["non_empty"]:
                problems.append(f"{var} does not point to a non-empty directory: {path}")
            elif item["content_ok"] is False:
                problems.append(f"{var} lacks the expected content ({', '.join(markers)}): {path}")
    if tsl and not report.get("G4NEUTRONHPDATA", {}).get("thermal_scattering"):
        problems.append("G4NEUTRONHPDATA has no ThermalScattering/ directory (needed for G4ThermalNeutrons)")
    notes = [f"{v}: geant4-config reports {i['geant4_config']} (missing), environment uses {i['env']}"
             for v, i in report.items() if i.get("geant4_config") and not i["geant4_config_exists"] and i["exists"]]
    return {"ok": not problems, "problems": problems, "notes": notes, "datasets": report}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--require", nargs="*", default=list(DEFAULT_REQUIRED))
    ap.add_argument("--tsl", action="store_true", help="require neutron thermal-scattering data")
    ap.add_argument("--geant4-config", default=None, help="path of geant4-config (default: on PATH)")
    a = ap.parse_args(argv)
    r = check(dict(os.environ), tuple(a.require), a.tsl, a.geant4_config)
    print(json.dumps(r, indent=2))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
