#!/usr/bin/env python3
"""Create a non-destructive grant-proposal project scaffold (see ../references/layout.md)."""

from __future__ import annotations

import argparse
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
    "analysis/data/raw",
    "analysis/data/external",
    "analysis/data/processed",
    "docs",
    "private",
)


def render(text: str, acronym: str, call: str) -> str:
    for token, value in {"@@ACRONYM@@": acronym, "@@CALL@@": call,
                         "@@DATE@@": date.today().isoformat()}.items():
        text = text.replace(token, value)
    return text


def plan(target: Path, template_root: Path) -> list[tuple[Path, Path]]:
    files = []
    for source in sorted(p for p in template_root.rglob("*") if p.is_file()):
        rel = source.relative_to(template_root)
        if rel.name == "_gitignore":
            rel = rel.with_name(".gitignore")
        files.append((source, target / rel))
    return files


def create(target: Path, acronym: str, call: str, merge: bool = False, dry_run: bool = False,
           out=sys.stdout) -> int:
    template_root = Path(__file__).resolve().parent.parent / "assets" / "proposal-template"
    if not template_root.is_dir():
        print(f"Template directory is missing: {template_root}", file=sys.stderr)
        return 2
    if target.exists() and any(target.iterdir()) and not merge:
        print(f"Destination is not empty: {target}\nUse --merge to add only missing pieces.",
              file=sys.stderr)
        return 2
    files = plan(target, template_root)
    print(f"Project: {target}\nAcronym: {acronym}\nCall:    {call}", file=out)
    if dry_run:
        for d in DIRECTORIES:
            print(f"DIR  {target / d}", file=out)
        for _, dest in files:
            print(f"{'SKIP' if dest.exists() else 'FILE'} {dest}", file=out)
        return 0
    for d in DIRECTORIES:
        (target / d).mkdir(parents=True, exist_ok=True)
    created = skipped = 0
    for source, dest in files:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            skipped += 1
            continue
        dest.write_text(render(source.read_text(encoding="utf-8"), acronym, call), encoding="utf-8")
        created += 1
    print(f"Created {created} files; skipped {skipped} existing files", file=out)
    print("Next: fill docs/CALL.md before writing.", file=out)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Create a grant-proposal project scaffold.")
    p.add_argument("project_dir", type=Path)
    p.add_argument("--acronym", required=True)
    p.add_argument("--call", default="[[call name and edition]]")
    p.add_argument("--merge", action="store_true", help="add missing pieces only; never overwrite")
    p.add_argument("--dry-run", action="store_true", help="print planned changes without writing")
    a = p.parse_args()
    return create(a.project_dir.expanduser().resolve(), a.acronym, a.call, a.merge, a.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
