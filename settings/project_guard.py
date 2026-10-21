#!/usr/bin/env python3
"""Claude Code PreToolUse hook that enforces a research project's boundaries.

Tier 2 (deny):   writing, moving or deleting anything under the protected evidence paths
                 (default data/raw/, data/external/) by Edit/Write or by a shell command.
Tier 1 (ask):    changing the authoritative model (default r-matrix/master/) and anything that
                 leaves the machine: git push, gh pr/release/issue/repo create, scp/rsync/sftp to a
                 host, curl/wget uploads, mail.
Tier 0 (allow):  everything else.

Paths are configured per project in .claude/guard.json:
  {"deny": ["data/raw/", "data/external/"], "ask": ["r-matrix/master/"]}
Reads the hook event (JSON) on stdin and answers with a permission decision on stdout.
The shell check is a heuristic: it catches the usual write commands, not every possible one.
"""

import json
import os
import re
import shlex
import sys
from pathlib import Path

DEFAULT = {"deny": ["data/raw/", "data/external/"], "ask": ["r-matrix/master/"]}
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
# commands that modify their path arguments
MODIFYING = {"rm", "mv", "cp", "sed", "perl", "truncate", "tee", "chmod", "chown", "touch", "ln",
             "rsync", "dd", "install", "unlink", "rmdir", "mkdir", "git"}
OUTBOUND = [
    (r"\bgit\s+push\b", "git push publishes commits"),
    (r"\bgh\s+(pr|release|issue|repo|gist)\s+(create|edit|merge|comment|delete|upload)\b", "gh writes to GitHub"),
    (r"\b(scp|sftp)\b", "copies files to another host"),
    (r"\brsync\b[^|;&]*\S+:\S*", "rsync to a remote host"),
    (r"\bcurl\b[^|;&]*(\s-X\s*(POST|PUT|PATCH|DELETE)|\s(-d|--data\S*|-F|--form|-T|--upload-file)\b)", "curl uploads data"),
    (r"\bwget\b[^|;&]*--post", "wget posts data"),
    (r"\b(mail|mailx|sendmail)\b", "sends e-mail"),
]


def config(root):
    f = root / ".claude" / "guard.json"
    if f.exists():
        try:
            return {**DEFAULT, **json.loads(f.read_text())}
        except json.JSONDecodeError:
            pass
    return DEFAULT


def under(path, prefixes, root):
    try:
        rel = os.path.relpath(Path(path if os.path.isabs(path) else root / path).resolve(), root.resolve())
    except ValueError:
        return None
    rel = rel.replace(os.sep, "/") + ("/" if Path(root / rel).is_dir() else "")
    for p in prefixes:
        p = p.rstrip("/") + "/"
        if (rel + "/").startswith(p) or rel.startswith(p):
            return p
    return None


def bash_targets(cmd, prefixes, root):
    """Protected paths a shell command would modify (redirections and modifying commands)."""
    hits = set()
    for m in re.finditer(r"(?:^|[^<>&0-9])(>>?|&>)\s*([^\s;|&]+)", cmd):
        p = under(m.group(2), prefixes, root)
        if p:
            hits.add(p)
    for part in re.split(r"(?:&&|\|\||;|\|)", cmd):
        try:
            words = shlex.split(part)
        except ValueError:
            words = part.split()
        if not words:
            continue
        prog = os.path.basename(words[0])
        if prog in ("sudo", "env", "command", "xargs") and len(words) > 1:
            words = words[1:]
            prog = os.path.basename(words[0])
        if prog not in MODIFYING:
            continue
        if prog == "sed" and not any(w.startswith("-i") or w == "--in-place" for w in words):
            continue
        if prog == "perl" and not any(w.startswith("-i") or w.startswith("-pi") for w in words):
            continue
        if prog == "git" and not (len(words) > 1 and words[1] in ("rm", "mv", "checkout", "restore", "clean")):
            continue
        if prog == "cp" or prog == "rsync" or prog == "install":
            args = [w for w in words[1:] if not w.startswith("-")]
            candidates = args[-1:]  # only the destination is modified
        else:
            candidates = [w for w in words[1:] if not w.startswith("-")]
        for w in candidates:
            p = under(w, prefixes, root)
            if p:
                hits.add(p)
    return hits


def decide(event, root):
    cfg = config(root)
    tool, inp = event.get("tool_name", ""), event.get("tool_input", {}) or {}
    if tool in WRITE_TOOLS:
        path = inp.get("file_path") or inp.get("notebook_path") or ""
        p = under(path, cfg["deny"], root)
        if p:
            return "deny", (f"{p} holds immutable evidence. Write a corrected copy to data/processed/ "
                            f"and record the reason in docs/PROVENANCE.md instead.")
        p = under(path, cfg["ask"], root)
        if p:
            return "ask", f"{p} is the authoritative model; changing it needs a recorded decision."
    if tool == "Bash":
        cmd = inp.get("command", "")
        hits = bash_targets(cmd, cfg["deny"], root)
        if hits:
            return "deny", (f"this command would modify {', '.join(sorted(hits))}, which holds immutable "
                            f"evidence. Write to data/processed/ instead.")
        hits = bash_targets(cmd, cfg["ask"], root)
        if hits:
            return "ask", f"this command modifies the authoritative model in {', '.join(sorted(hits))}."
        for pat, why in OUTBOUND:
            if re.search(pat, cmd):
                return "ask", f"outbound action: {why}. Confirm before anything leaves the machine."
    return None, ""


def main():
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd())
    decision, reason = decide(event, root)
    if decision:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                  "permissionDecision": decision,
                                                  "permissionDecisionReason": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
