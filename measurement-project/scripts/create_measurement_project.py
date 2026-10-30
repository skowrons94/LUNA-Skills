#!/usr/bin/env python3
"""Create the folder of a measurement project (layout in ../references/layout.md). Non-destructive: existing files
are never overwritten, so the script can also complete an existing project.

CHAIN.md is copied from analysis-chain/assets and CLAIMS.toml from nuclear-research-project/assets when those skills
sit next to this one, so that each template has a single source.

Usage: python3 create_measurement_project.py PATH [--reaction 14npg --setup bgo --target solid --years 2023-2025]
                                                  [--title "..."] [--author "..."] [--dry-run]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / "assets" / "project-template"
SKILLS = SKILL.parent

STAGES = [   # folder, title, analysis-chain stage, skills
    ("00_audit", "Data audit", "0 Data audit", "data-auditor subagent, yield-analysis"),
    ("01_beam", "Beam energy, charge, dead time", "0-1 (normalisation inputs)", "yield-analysis, target-analysis"),
    ("02_calibration", "Detector energy calibration and resolution", "1 (energy scale)", "peak-shape-analysis, yield-analysis"),
    ("03_background", "Room background and beam-induced contaminants", "1 (backgrounds)",
     "yield-analysis, peak-shape-analysis, underground-gamma-simulation"),
    ("04_efficiency", "Efficiency, summing, angular correlations", "2 Efficiency",
     "efficiency-analysis, underground-gamma-simulation"),
    ("05_target", "Target profiles, stoichiometry, degradation", "3 Target, effective energy", "target-analysis, peak-shape-analysis"),
    ("06_yield", "Yields", "1 Yields", "yield-analysis, peak-shape-analysis"),
    ("07_sfactor", "Cross sections, S factors, uncertainty budget", "4 Cross section / S factor", "yield-analysis, uncertainty-audit"),
    ("08_rmatrix", "R-matrix fit and extrapolation", "4-5 R-matrix, extrapolation", "r-matrix, resonance-search, rmatrix-posterior"),
    ("09_rate", "Reaction rate and astrophysical impact", "5b-5c", "reaction-network, stellar-evolution, big-bang-nucleosynthesis"),
]
DIRS = [
    "data/raw", "data/root", "data/external/exfor", "data/external/literature", "data/external/collaborators",
    "data/logbook_sources",
    "docs/papers", "docs/theses", "docs/manuals", "docs/talks", "docs/drawings", "docs/photos", "docs/elog",
    "docs/shift_reports", "docs/correspondence",
    "simulation/geometry", "simulation/macros", "simulation/runs", "simulation/validation",
    "tools", "report/sections", "report/tables", "report/figures", "report/build", "slides", "_claude",
] + [f"analysis/{s[0]}/{sub}" for s in STAGES for sub in ("inputs", "results", "figures")]
ROOT_FILES = ["README.md", "CLAUDE.md", "HANDOFF.md", "PROBLEMS.md", "LITERATURE.md", "DECISIONS.md",
              "ASSUMPTIONS.md", "CHANGELOG.md"]


def fill(text: str, subs: dict) -> str:
    for k, v in subs.items():
        text = text.replace("@@" + k + "@@", v)
    return text


def write(path: Path, text: str, dry: bool, made: list) -> None:
    if path.exists():
        return
    made.append(path)
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", type=Path)
    ap.add_argument("--reaction", default="")
    ap.add_argument("--setup", default="")
    ap.add_argument("--target", default="")
    ap.add_argument("--years", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--author", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    root = a.path.resolve()
    name = "_".join(x for x in (a.reaction, a.setup, a.target, a.years) if x)
    if name and root.name != name:
        print(f"note: folder name {root.name!r} differs from the convention {name!r}", file=sys.stderr)
    subs = dict(TITLE=a.title or root.name, REACTION=a.reaction or "TODO", SETUP=a.setup or "TODO",
                TARGET=a.target or "TODO", YEARS=a.years or "TODO", DATE=date.today().isoformat(),
                AUTHOR=a.author or "TODO")
    made: list[Path] = []
    for d in DIRS:
        p = root / d
        if not p.exists():
            made.append(p)
            if not a.dry_run:
                p.mkdir(parents=True, exist_ok=True)
    for f in ROOT_FILES:
        write(root / f, fill((TEMPLATE / f).read_text(), subs), a.dry_run, made)
    write(root / ".gitignore", (TEMPLATE / "_gitignore").read_text(), a.dry_run, made)
    stage_tpl = (TEMPLATE / "stage_README.md").read_text()
    for folder, title, chain, skills in STAGES:
        write(root / "analysis" / folder / "README.md",
              fill(stage_tpl, dict(STAGE=folder, STAGE_TITLE=title, CHAIN_STAGE=chain, SKILLS=skills)), a.dry_run, made)
    for f in ("report/main.tex", "report/Makefile", "report/references.bib", "slides/README.md", "tools/README.md"):
        write(root / f, fill((TEMPLATE / f).read_text(), subs), a.dry_run, made)
    for f in sorted((TEMPLATE / "report" / "sections").glob("*.tex")):
        write(root / "report" / "sections" / f.name, f.read_text(), a.dry_run, made)
    chain = SKILLS / "analysis-chain" / "assets" / "CHAIN.md"
    claims = SKILLS / "nuclear-research-project" / "assets" / "project-template" / "docs" / "CLAIMS.toml"
    for src, dst in ((chain, "CHAIN.md"), (claims, "CLAIMS.toml")):
        if src.exists():
            write(root / dst, src.read_text(), a.dry_run, made)
        else:
            print(f"warning: {src} not found; create {dst} by hand", file=sys.stderr)
    for p in ("data/file_map.csv",):
        write(root / p, "source_path,local_path,sha256,note\n", a.dry_run, made)
    print(("would create" if a.dry_run else "created") + f" {len(made)} items in {root}")
    for p in made[:12]:
        print("  ", p.relative_to(root))
    if len(made) > 12:
        print(f"   ... and {len(made) - 12} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
