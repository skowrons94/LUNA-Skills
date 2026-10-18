#!/usr/bin/env python3
"""Create a non-destructive grant-proposal project scaffold (see ../references/layout.md)."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

DIRECTORIES = (
    "proposal/source",
    "proposal/figures",
    "proposal/build",
    "proposal/review",
    "proposal/archive",
    "analysis/scripts",
    "analysis/results",
    "analysis/plots",
    "analysis/data",
    "docs",
    "private",
)
# Added with --tools (see ../references/tools-layout.md).
TOOL_DIRECTORIES = (
    "analysis/chains",
    "r-matrix/master",
    "r-matrix/studies",
    "r-matrix/runs",
    "simulation",
    "transport",
)
# Sub-directories of one study, by kind (--study KIND/NAME).
STUDY_DIRECTORIES = {
    "simulation": ("src", "macros", "scripts", "inputs", "runs"),
    "transport": ("scripts", "model", "runs"),
}
# Directories that stay empty after scaffolding get a .gitkeep so that git keeps them;
# git-ignored directories get none.
NO_GITKEEP = {"private", "analysis/chains", "r-matrix/runs"}
STUDY_NAME = re.compile(r"^(simulation|transport)/[A-Za-z0-9][A-Za-z0-9._-]*$")


def render(text: str, acronym: str, call: str, study: str = "") -> str:
    for token, value in {"@@ACRONYM@@": acronym, "@@CALL@@": call, "@@STUDY@@": study,
                         "@@DATE@@": date.today().isoformat()}.items():
        text = text.replace(token, value)
    return text


def directories(tools: bool, studies: tuple[str, ...]) -> list[str]:
    dirs = list(DIRECTORIES)
    if tools or studies:
        dirs += TOOL_DIRECTORIES
    for study in studies:
        kind = study.split("/", 1)[0]
        dirs += [f"{study}/{sub}" for sub in STUDY_DIRECTORIES[kind]]
    return dirs


def plan(target: Path, assets: Path, dirs: list[str],
         studies: tuple[str, ...] = ()) -> list[tuple[Path | None, Path, str]]:
    """(template source, destination, study) triples; source None means an empty .gitkeep."""
    files: list[tuple[Path | None, Path, str]] = []
    template_root = assets / "proposal-template"
    for source in sorted(p for p in template_root.rglob("*") if p.is_file()):
        rel = source.relative_to(template_root)
        if rel.name == "_gitignore":
            rel = rel.with_name(".gitignore")
        files.append((source, target / rel, ""))
    for study in studies:
        for source in sorted(p for p in (assets / "study-template").glob("*") if p.is_file()):
            files.append((source, target / study / source.name, study.split("/", 1)[1]))
    filled = {dest.parent for _, dest, _ in files}
    parents = {str(a) for d in dirs for a in Path(d).parents}  # directories with sub-directories
    for d in dirs:
        ignored = d in NO_GITKEEP or (d.startswith("transport/") and d.endswith("/runs"))
        if not ignored and d not in parents and target / d not in filled:
            files.append((None, target / d / ".gitkeep", ""))
    return files


def create(target: Path, acronym: str, call: str, merge: bool = False, dry_run: bool = False,
           out=sys.stdout, tools: bool = False, studies: tuple[str, ...] = ()) -> int:
    assets = Path(__file__).resolve().parent.parent / "assets"
    for name in ("proposal-template", "study-template"):
        if not (assets / name).is_dir():
            print(f"Template directory is missing: {assets / name}", file=sys.stderr)
            return 2
    studies = tuple(studies)
    bad = [s for s in studies if not STUDY_NAME.match(s)]
    if bad:
        print(f"Study must be simulation/NAME or transport/NAME: {', '.join(bad)}", file=sys.stderr)
        return 2
    if target.exists() and not target.is_dir():
        print(f"Destination exists and is not a directory: {target}", file=sys.stderr)
        return 2
    if target.exists() and any(target.iterdir()) and not merge:
        print(f"Destination is not empty: {target}\nUse --merge to add only missing pieces.",
              file=sys.stderr)
        return 2
    dirs = directories(tools, studies)
    files = plan(target, assets, dirs, studies)
    print(f"Project: {target}\nAcronym: {acronym}\nCall:    {call}", file=out)
    if dry_run:
        for d in dirs:
            print(f"DIR  {target / d}", file=out)
        for _, dest, _ in files:
            print(f"{'SKIP' if dest.exists() else 'FILE'} {dest}", file=out)
        if (target / ".gitignore").is_file():
            report_missing_ignore_rules(target, assets, tools or bool(studies), out)
        return 0
    for d in dirs:
        (target / d).mkdir(parents=True, exist_ok=True)
    created = skipped = 0
    for source, dest, study in files:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            skipped += 1
            continue
        text = "" if source is None else render(source.read_text(encoding="utf-8"), acronym, call, study)
        dest.write_text(text, encoding="utf-8")
        created += 1
    print(f"Created {created} files; skipped {skipped} existing files", file=out)
    report_missing_ignore_rules(target, assets, tools or bool(studies), out)
    print("Next: fill docs/CALL.md before writing.", file=out)
    return 0


def missing_ignore_rules(target: Path, assets: Path) -> list[str]:
    """Tool rules of the template .gitignore that an existing project .gitignore lacks."""
    template = (assets / "proposal-template" / "_gitignore").read_text(encoding="utf-8").splitlines()
    start = next((i for i, line in enumerate(template) if line.startswith("# Tool outputs")), len(template))
    rules = [line for line in template[start:] if line and not line.startswith("#")]
    gi = target / ".gitignore"
    have = set(gi.read_text(encoding="utf-8").splitlines()) if gi.is_file() else set()
    return [r for r in rules if r not in have]


def report_missing_ignore_rules(target: Path, assets: Path, tools: bool, out) -> None:
    if not tools:
        return
    missing = missing_ignore_rules(target, assets)
    if missing:  # never edit an existing .gitignore: list the rules instead
        print(".gitignore exists without the tool rules; add these lines by hand "
              "(references/tools-layout.md, Size policy):", file=out)
        for rule in missing:
            print(f"    {rule}", file=out)


def main() -> int:
    p = argparse.ArgumentParser(description="Create a grant-proposal project scaffold.")
    p.add_argument("project_dir", type=Path)
    p.add_argument("--acronym", required=True)
    p.add_argument("--call", default="[[call name and edition]]")
    p.add_argument("--tools", action="store_true",
                   help="add r-matrix/, simulation/, transport/ and analysis/chains/ (tools-layout.md)")
    p.add_argument("--study", action="append", default=[], metavar="KIND/NAME",
                   help="add one study, simulation/NAME or transport/NAME (repeatable; implies --tools)")
    p.add_argument("--merge", action="store_true", help="add missing pieces only; never overwrite")
    p.add_argument("--dry-run", action="store_true", help="print planned changes without writing")
    a = p.parse_args()
    return create(a.project_dir.expanduser().resolve(), a.acronym, a.call, a.merge, a.dry_run,
                  tools=a.tools, studies=tuple(a.study))


if __name__ == "__main__":
    raise SystemExit(main())
