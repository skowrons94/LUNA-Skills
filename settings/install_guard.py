#!/usr/bin/env python3
"""Install the project guard into a research project's .claude/settings.json.

  python3 install_guard.py /path/to/project [--dry-run]

Merges a PreToolUse hook (project_guard.py from this repository) into the project's settings
without removing anything already there, and writes .claude/guard.json with the default
protected paths if it does not exist. Edit guard.json to change what is denied or asked.
"""

import argparse
import json
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().with_name("project_guard.py")
MATCHER = "Edit|Write|MultiEdit|NotebookEdit|Bash"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    root = a.project.expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"not a directory: {root}")
    sf = root / ".claude" / "settings.json"
    settings = json.loads(sf.read_text()) if sf.exists() else {}
    hook = {"type": "command", "command": f'python3 "{GUARD}"'}
    pre = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    present = any(h.get("command") == hook["command"] for e in pre for h in e.get("hooks", []))
    if not present:
        pre.append({"matcher": MATCHER, "hooks": [hook]})
    gf = root / ".claude" / "guard.json"
    guard_cfg = {"deny": ["data/raw/", "data/external/"], "ask": ["r-matrix/master/"]}
    print(json.dumps(settings, indent=2))
    if a.dry_run:
        return 0
    sf.parent.mkdir(exist_ok=True)
    sf.write_text(json.dumps(settings, indent=2) + "\n")
    if not gf.exists():
        gf.write_text(json.dumps(guard_cfg, indent=2) + "\n")
    print(f"{'already installed in' if present else 'installed into'} {sf}; protected paths in {gf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
