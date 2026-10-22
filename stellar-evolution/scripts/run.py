#!/usr/bin/env python3
"""Set up and run a MESA case reproducibly from a JSON spec (references/running.md).

  python3 run.py setup spec.json            copy template, apply edits, write manifest
  python3 run.py run spec.json [--no-mk]    setup (if needed), ./mk, ./rn, check, manifest

spec.json:
{
  "template": "$MESA_DIR/star/test_suite/simplex_solar_calibration",
  "run_dir": "runs/solar_nominal",              (relative to the spec file)
  "env": "/path/to/mesa_env.sh",                (sourced before mk and rn)
  "skip_optional": true,                         (MESA_SKIP_OPTIONAL=t: start from shipped models)
  "threads": 3,
  "inlists": {"inlist_solar": {"star_job": {"num_special_rate_factors": "1", ...},
                               "controls": {"max_age": "4.61d9"}}},
  "profile_columns": ["add_screened_rates"],     (appended to profile_columns.list)
  "history_columns": [],
  "files": {"rates/r_mg25_pg_al26.dat": "r_mg25_pg_al26.dat"}   (copied into the run dir)
}
The run directory gets manifest.json: MESA and SDK versions, template, every edit, SHA-256 of
the inlists and copied files, wall time and the check-run result.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import mesa  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    base = Path(spec_path).resolve().parent
    spec["_base"] = base
    spec["_run"] = (base / spec["run_dir"]).resolve()
    return spec


def env_vars(spec):
    """Environment after sourcing the MESA env file."""
    out = subprocess.run(["bash", "-c", f"source {spec['env']} >/dev/null && env -0"],
                         capture_output=True, check=True)
    env = dict(x.split("=", 1) for x in out.stdout.decode().split("\0") if "=" in x)
    env["OMP_NUM_THREADS"] = str(spec.get("threads", 2))
    if spec.get("skip_optional"):
        env["MESA_SKIP_OPTIONAL"] = "t"
    return env


def setup(spec):
    run = spec["_run"]
    env = env_vars(spec)
    tpl = Path(os.path.expandvars(spec["template"].replace("$MESA_DIR", env["MESA_DIR"])))
    if run.exists():
        raise SystemExit(f"{run} exists: one run directory per configuration; remove it or "
                         "choose a new run_dir")
    shutil.copytree(tpl, run, symlinks=True)
    # test-suite cases refer to MESA_DIR relative paths in their make/ and rn; a copy works with
    # MESA_DIR set, which the env file provides
    for fname, nls in spec.get("inlists", {}).items():
        for nl, kv in nls.items():
            mesa.set_inlist(run / fname, nl, list(kv.items()))
    for listname, key in (("profile_columns.list", "profile_columns"),
                          ("history_columns.list", "history_columns")):
        extra = spec.get(key, [])
        if extra:
            p = run / listname
            if not p.exists():
                shutil.copy(Path(env["MESA_DIR"]) / "star" / "defaults" / listname, p)
            p.write_text(p.read_text().rstrip() + "\n\n" + "\n".join(f"   {c}  ! added by run.py"
                                                                    for c in extra) + "\n")
    copied = {}
    for src, dst in spec.get("files", {}).items():
        s = (spec["_base"] / src).resolve()
        shutil.copy(s, run / dst)
        copied[dst] = {"from": str(s), "sha256": sha(s)}
    man = {
        "template": str(tpl),
        "spec": {k: v for k, v in spec.items() if not k.startswith("_")},
        "mesa_dir": env["MESA_DIR"],
        "mesasdk_version": env.get("MESASDK_VERSION", ""),
        "mesa_version": (Path(env["MESA_DIR"]) / "data" / "version_number").read_text().strip()
        if (Path(env["MESA_DIR"]) / "data" / "version_number").exists() else "",
        "inlist_sha256": {p.name: sha(p) for p in run.glob("inlist*")},
        "files": copied,
        "setup_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (run / "manifest.json").write_text(json.dumps(man, indent=1))
    print(f"set up {run}")
    return man


def run_case(spec, mk=True):
    run = spec["_run"]
    if not (run / "manifest.json").exists():
        setup(spec)
    env = env_vars(spec)
    t0 = time.time()
    if mk:
        r = subprocess.run(["bash", "-c", "./mk > mk.log 2>&1"], cwd=run, env=env)
        if r.returncode != 0:
            raise SystemExit(f"./mk failed: see {run / 'mk.log'}")
    subprocess.run(["bash", "-c", "nice -n 10 ./rn > rn.log 2>&1"], cwd=run, env=env)
    chk = mesa.check_run(run)
    man = json.loads((run / "manifest.json").read_text())
    man.update({"wall_min": (time.time() - t0) / 60, "check": chk,
                "end_time": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
    (run / "manifest.json").write_text(json.dumps(man, indent=1))
    print(json.dumps(chk, indent=1))
    return 0 if chk["ok"] else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["setup", "run"])
    ap.add_argument("spec")
    ap.add_argument("--no-mk", action="store_true")
    a = ap.parse_args(argv)
    spec = load(a.spec)
    if a.cmd == "setup":
        setup(spec)
        return 0
    return run_case(spec, mk=not a.no_mk)


if __name__ == "__main__":
    sys.exit(main())
