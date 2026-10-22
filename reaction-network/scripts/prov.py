"""Provenance block for results.json: what produced this number (standard library only)."""

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(cwd, *args):
    try:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def block(inputs=(), tools=None, argv=None):
    """Hashes of input files, skill and repository revision, tool versions, platform, time."""
    ins = {}
    for p in inputs:
        p = Path(p)
        if p.is_file():
            ins[str(p)] = sha(p)
    return {
        "inputs": ins,
        "command": " ".join(argv if argv is not None else sys.argv),
        "skill": "reaction-network",
        "skill_md_sha256": sha(SKILL_DIR / "SKILL.md") if (SKILL_DIR / "SKILL.md").exists() else "",
        "skills_repo_commit": _git(SKILL_DIR, "rev-parse", "HEAD"),
        "skills_repo_dirty": bool(_git(SKILL_DIR, "status", "--porcelain", "--", ".")),
        "tools": tools or {},
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def config_inputs(cfg):
    """Every file a configuration points to (rate tables, trajectories, STARLIB)."""
    d = Path(cfg.get("_dir", "."))
    files = []

    def add(rel):
        p = Path(os.path.expandvars(str(rel)))
        files.append(p if p.is_absolute() else d / p)

    if cfg.get("starlib", {}).get("file"):
        add(cfg["starlib"]["file"])
    for item in cfg.get("rates", []):
        if "table" in item:
            add(item["table"])
    if cfg.get("conditions", {}).get("file"):
        add(cfg["conditions"]["file"])
    for v in cfg.get("uncertainty", {}).get("fu", {}).values():
        if isinstance(v, str):
            add(v)
    return files


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=1, default=float))
