#!/usr/bin/env python3
"""Create a non-destructive nuclear-physics research project scaffold."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path


DIRECTORIES = (
    "configs",
    "environment",
    "data/raw",
    "data/external/exfor",
    "data/external/literature",
    "data/external/collaborators",
    "data/stopping-power/raw",
    "data/stopping-power/processed",
    "data/calibration",
    "data/processed",
    "data/metadata",
    "r-matrix/master",
    "r-matrix/data",
    "r-matrix/studies",
    "r-matrix/runs",
    "r-matrix/validation",
    "simulation/geometry",
    "simulation/macros",
    "simulation/physics",
    "simulation/runs",
    "simulation/analysis",
    "simulation/validation",
    "src/physics",
    "src/utilities",
    "src/plotting",
    "scripts",
    "notebooks",
    "tests",
    "results/tables",
    "results/summaries",
    "results/model-exports",
    "results/manifests",
    "results/validation",
    "plots/diagnostics",
    "plots/report",
    "plots/presentations",
    "report/build",
    "presentations/animations",
    "presentations/assets",
    "presentations/build",
    "work",
)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "research-project"


def latex_escape(value: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render(text: str, title: str, author: str) -> str:
    values = {
        "@@PROJECT_TITLE@@": title,
        "@@PROJECT_TITLE_LATEX@@": latex_escape(title),
        "@@PROJECT_TITLE_YAML@@": yaml_escape(title),
        "@@AUTHOR@@": author,
        "@@AUTHOR_LATEX@@": latex_escape(author),
        "@@AUTHOR_YAML@@": yaml_escape(author),
        "@@DATE@@": date.today().isoformat(),
        "@@PROJECT_SLUG@@": slugify(title),
    }
    for token, value in values.items():
        text = text.replace(token, value)
    return text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the canonical nuclear research project structure."
    )
    parser.add_argument("project_dir", type=Path, help="Destination directory")
    parser.add_argument("--title", help="Scientific project title")
    parser.add_argument("--author", default="Research team", help="Report author")
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Add missing directories and files to an existing project; never overwrite",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print planned changes without writing"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = args.project_dir.expanduser().resolve()
    title = args.title or target.name.replace("-", " ").replace("_", " ").strip().title()
    template_root = Path(__file__).resolve().parent.parent / "assets" / "project-template"

    if not template_root.is_dir():
        print(f"Template directory is missing: {template_root}", file=sys.stderr)
        return 2

    if target.exists() and any(target.iterdir()) and not args.merge:
        print(
            f"Destination is not empty: {target}\n"
            "Use --merge to add only missing scaffold files, or choose an empty directory.",
            file=sys.stderr,
        )
        return 2

    template_files = sorted(path for path in template_root.rglob("*") if path.is_file())
    planned_files: list[tuple[Path, Path]] = []
    for source in template_files:
        relative = source.relative_to(template_root)
        if relative.name == "_gitignore":
            relative = relative.with_name(".gitignore")
        planned_files.append((source, target / relative))

    print(f"Project: {target}")
    print(f"Title:   {title}")
    print(f"Create {len(DIRECTORIES)} directories and {len(planned_files)} template files")

    if args.dry_run:
        for directory in DIRECTORIES:
            print(f"DIR  {target / directory}")
        for _, destination in planned_files:
            status = "SKIP" if destination.exists() else "FILE"
            print(f"{status} {destination}")
        return 0

    target.mkdir(parents=True, exist_ok=True)
    for directory in DIRECTORIES:
        (target / directory).mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    for source, destination in planned_files:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            skipped += 1
            continue
        content = source.read_text(encoding="utf-8")
        destination.write_text(render(content, title, args.author), encoding="utf-8")
        created += 1

    print(f"Created {created} files; skipped {skipped} existing files")
    print("Next: complete project.yaml and docs/ASSUMPTIONS.md before analysis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
