#!/usr/bin/env python3
"""Check a project's claims register (docs/CLAIMS.toml, or CLAIMS.toml at the root of a measurement-project)
against its files and documents.

  python3 check_claims.py PROJECT                     check evidence, dependencies, staleness
  python3 check_claims.py PROJECT --text report/main.tex presentations/notes.md
                                                      also match quoted values in documents
  python3 check_claims.py PROJECT --accept C1 C2      mark claims accepted and freeze their evidence

Accepting a claim records the SHA-256 of each evidence file in docs/claims.lock.json. A later
change to that file makes the claim STALE, and every claim that depends on a stale, challenged or
revised claim is flagged too, so a regenerated result cannot silently keep its old wording in the
paper. Exit code 1 if any error is found. Python >= 3.11 (tomllib), standard library only.
"""

import argparse
import hashlib
import json
import re
import sys
import tomllib
from datetime import date
from pathlib import Path

KINDS = {"measured", "derived", "extrapolated", "literature", "assumption"}
CONF = {"high", "medium", "low"}
STATUS = {"open", "challenged", "revised", "accepted"}
# a number followed by an uncertainty: 4.3 \pm 0.4, 4.3 ± 0.4, 4.3 +/- 0.4, 4.3(4), 4.3^{+0.5}_{-0.3}
QUOTED = re.compile(r"\d+(?:\.\d+)?(?:\s*(?:\\pm|±|\+/-)\s*\d+(?:\.\d+)?|\(\d+\)|\s*\^\{\+[\d.]+\}_\{-[\d.]+\})")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def norm(s):
    return re.sub(r"\s+", "", s.replace("±", r"\pm").replace("+/-", r"\pm").replace("$", ""))


def load(root):
    # docs/CLAIMS.toml (nuclear-research-project) or CLAIMS.toml at the root (measurement-project, whose docs/ holds
    # documents); the lock file sits next to the register
    f = root / "docs" / "CLAIMS.toml"
    if not f.exists() and (root / "CLAIMS.toml").exists():
        f = root / "CLAIMS.toml"
    if not f.exists():
        sys.exit(f"no claims register at {root / 'docs' / 'CLAIMS.toml'} or {root / 'CLAIMS.toml'}")
    claims = tomllib.loads(f.read_text()).get("claim", [])
    lockf = f.parent / "claims.lock.json"
    lock = json.loads(lockf.read_text()) if lockf.exists() else {}
    return claims, lock, lockf


def check(root, claims, lock):
    errors, warnings = [], []
    ids = {}
    for c in claims:
        cid = c.get("id", "?")
        if cid in ids:
            errors.append(f"{cid}: duplicate id")
        ids[cid] = c
        for field in ("statement", "kind", "confidence", "status"):
            if not c.get(field):
                errors.append(f"{cid}: missing {field}")
        if c.get("kind") and c["kind"] not in KINDS:
            errors.append(f"{cid}: kind '{c['kind']}' not in {sorted(KINDS)}")
        if c.get("confidence") and c["confidence"] not in CONF:
            errors.append(f"{cid}: confidence '{c['confidence']}' not in {sorted(CONF)}")
        if c.get("status") and c["status"] not in STATUS:
            errors.append(f"{cid}: status '{c['status']}' not in {sorted(STATUS)}")
        ev = c.get("evidence", [])
        if not ev and c.get("kind") != "assumption" and c.get("confidence") != "low":
            errors.append(f"{cid}: no evidence, so confidence must be 'low'")
        for e in ev:
            if re.match(r"^(doi:|https?://|arxiv:)", e, re.I):
                continue
            if not (root / e).exists():
                errors.append(f"{cid}: evidence file missing: {e}")
        if c.get("kind") == "extrapolated" and not c.get("limits"):
            errors.append(f"{cid}: extrapolated claim must state its limits (model dependence, range)")
        if c.get("kind") != "literature" and c.get("status") == "accepted" and not c.get("produced_by") and ev:
            warnings.append(f"{cid}: accepted without produced_by (command that regenerates the evidence)")

    stale = set()
    for c in claims:
        cid = c.get("id")
        if c.get("status") != "accepted":
            continue
        frozen = lock.get(cid, {}).get("evidence", {})
        if not frozen:
            warnings.append(f"{cid}: accepted but evidence not frozen (run with --accept {cid})")
        for e, h in frozen.items():
            p = root / e
            if p.exists() and sha(p) != h:
                stale.add(cid)
                errors.append(f"{cid}: STALE, evidence changed since acceptance: {e}")

    # propagate through depends_on
    def bad(cid, seen=()):
        c = ids.get(cid)
        if c is None or cid in seen:
            return None
        if cid in stale or c.get("status") in ("challenged", "revised"):
            return cid
        for d in c.get("depends_on", []):
            r = bad(d, seen + (cid,))
            if r:
                return r
        return None

    for c in claims:
        cid = c.get("id")
        for d in c.get("depends_on", []):
            if d not in ids:
                errors.append(f"{cid}: depends_on unknown claim {d}")
        for d in c.get("depends_on", []):
            r = bad(d, (cid,))
            if r:
                errors.append(f"{cid}: depends on {r}, which is stale, challenged or revised")
                break
    return errors, warnings, ids


def check_texts(texts, ids):
    errors, warnings = [], []
    values = {norm(c["value"]): cid for cid, c in ids.items() if c.get("value")}
    for t in texts:
        s = Path(t).read_text(errors="ignore")
        found = {norm(m.group(0)) for m in QUOTED.finditer(s)}
        for v in sorted(found - set(values)):
            warnings.append(f"{t}: quoted value '{v}' matches no claim")
        for v in sorted(found & set(values)):
            c = ids[values[v]]
            if c.get("status") != "accepted":
                errors.append(f"{t}: uses {values[v]} ('{v}') whose status is {c.get('status')}")
    return errors, warnings


def accept(root, claims, lock, lockf, which):
    today = date.today().isoformat()
    by_id = {c["id"]: c for c in claims}
    for cid in which:
        c = by_id.get(cid)
        if c is None:
            sys.exit(f"unknown claim {cid}")
        files = {e: sha(root / e) for e in c.get("evidence", []) if (root / e).exists()}
        lock[cid] = {"accepted": today, "evidence": files}
        print(f"froze {cid}: {len(files)} evidence file(s); set status = \"accepted\" in CLAIMS.toml")
    lockf.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", type=Path)
    ap.add_argument("--text", nargs="*", default=[], help="documents whose quoted values must match claims")
    ap.add_argument("--accept", nargs="*", help="claim IDs to freeze")
    a = ap.parse_args()
    root = a.project.resolve()
    claims, lock, lockf = load(root)
    if a.accept:
        accept(root, claims, lock, lockf, a.accept)
        return 0
    errors, warnings, ids = check(root, claims, lock)
    e2, w2 = check_texts(a.text, ids)
    errors += e2
    warnings += w2
    for w in warnings:
        print(f"WARN   {w}")
    for e in errors:
        print(f"ERROR  {e}")
    print(f"{len(claims)} claims, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
