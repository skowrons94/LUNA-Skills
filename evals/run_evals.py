#!/usr/bin/env python3
"""Evaluate the skills as an agent uses them, not only their scripts.

  python3 evals/run_evals.py selftest                 offline: every checker passes its reference
                                                      answer and fails a naive one; routing file valid
  python3 evals/run_evals.py routing [--model M]      does each prompt load the expected skill?
  python3 evals/run_evals.py tasks [--model M]        graded tasks with known answers and traps
  python3 evals/run_evals.py report                   pass rates per model and repository state

routing and tasks drive the Claude Code CLI headless (`claude -p`) in a fresh temporary directory
whose .claude/skills links to the skills of this working tree, so uncommitted edits are tested.
Each result is appended to evals/ledger.jsonl with the model, git commit, dirty flag and a hash of
every SKILL.md, so a change in score can be traced to a change in a skill. Agents run with edits
accepted inside the temporary directory; run on a machine or container where that is acceptable.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from tasks import TASKS  # noqa: E402

LEDGER = HERE / "ledger.jsonl"


def skills():
    return sorted(p.parent.name for p in REPO.glob("*/SKILL.md"))


def repo_state():
    git = lambda *a: subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True).stdout.strip()
    return {
        "commit": git("rev-parse", "--short", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "skill_hashes": {s: hashlib.sha256((REPO / s / "SKILL.md").read_bytes()).hexdigest()[:10]
                         for s in skills()},
    }


def sandbox():
    d = Path(tempfile.mkdtemp(prefix="skill-eval-"))
    sk = d / ".claude" / "skills"
    sk.mkdir(parents=True)
    for s in skills():
        (sk / s).symlink_to(REPO / s)
    return d


def run_claude(prompt, cwd, model, tools, budget, timeout):
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--setting-sources", "project", "--no-session-persistence",
           "--max-budget-usd", str(budget), "--allowedTools", *tools]
    if model:
        cmd += ["--model", model]
    if "Write" in tools or "Edit" in tools:
        cmd += ["--permission-mode", "acceptEdits"]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        out = p.stdout
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    invoked, cost, model_used = [], None, None
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "system" and ev.get("model"):
            model_used = ev["model"]
        if ev.get("type") == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "tool_use" and c.get("name") == "Skill":
                    invoked.append(c.get("input", {}).get("skill", "").split(":")[-1])
        if ev.get("type") == "result":
            cost = ev.get("total_cost_usd")
    return {"skills_invoked": invoked, "cost_usd": cost, "model": model_used or model,
            "seconds": round(time.time() - t0, 1)}


def log(rec):
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec) + "\n")


def load_routing():
    return [json.loads(l) for l in (HERE / "routing.jsonl").read_text().splitlines() if l.strip()]


# ------------------------------------------------------------------ commands

def cmd_selftest(_):
    ok = True
    known = set(skills()) | {"none"}
    ids = set()
    for r in load_routing():
        bad = [s for s in r["expect"] if s not in known]
        if bad or r["id"] in ids:
            print(f"FAIL  routing {r['id']}: unknown skill {bad} or duplicate id")
            ok = False
        ids.add(r["id"])
    print(f"{'PASS' if ok else 'FAIL'}  routing.jsonl: {len(ids)} prompts, expected skills exist")
    for tid, t in TASKS.items():
        for kind, want in (("reference", True), ("baseline", False)):
            d = Path(tempfile.mkdtemp(prefix="eval-selftest-"))
            truth = t.generate(d)
            getattr(t, kind)(d, truth)
            res = t.check(d, truth)
            passed = all(r[1] for r in res)
            good = passed == want
            ok &= good
            why = "; ".join(f"{n}: {'ok' if p else 'x'} {i}" for n, p, i in res)
            print(f"{'PASS' if good else 'FAIL'}  {tid} {kind} {'passes' if passed else 'fails'}  [{why}]")
            shutil.rmtree(d)
    for tid, t in TASKS.items():
        bad = [s for s in t.skills if s not in known]
        if bad:
            print(f"FAIL  {tid}: unknown skills {bad}")
            ok = False
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def cmd_routing(a):
    state = repo_state()
    rows = [r for r in load_routing() if not a.only or r["id"] in a.only]
    n_ok = 0
    for r in rows:
        for rep in range(a.repeat):
            d = sandbox()
            res = run_claude(r["prompt"], d, a.model, ["Skill"], a.budget, a.timeout)
            first = res["skills_invoked"][0] if res["skills_invoked"] else "none"
            passed = first in r["expect"]
            n_ok += passed
            print(f"{'PASS' if passed else 'FAIL'}  {r['id']}  expected {r['expect']} got {first}")
            log({"kind": "routing", "id": r["id"], "passed": passed, "expected": r["expect"],
                 "got": first, **res, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), **state})
            shutil.rmtree(d)
    print(f"{n_ok}/{len(rows) * a.repeat} routed as expected")


def cmd_tasks(a):
    state = repo_state()
    tools = ["Skill", "Read", "Write", "Edit", "Glob", "Grep", "Bash"]
    for tid, t in TASKS.items():
        if a.only and tid not in a.only:
            continue
        for rep in range(a.repeat):
            d = sandbox()
            truth = t.generate(d)
            res = run_claude(t.prompt, d, a.model, tools, a.budget, a.timeout)
            checks = t.check(d, truth)
            passed = all(c[1] for c in checks)
            print(f"{'PASS' if passed else 'FAIL'}  {tid}  skills {res['skills_invoked']}  "
                  + "; ".join(f"{n}: {'ok' if p else 'x'} {i}" for n, p, i in checks))
            log({"kind": "task", "id": tid, "passed": passed,
                 "checks": [{"name": n, "passed": bool(p), "info": i} for n, p, i in checks],
                 "expected_skills": t.skills, **res, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), **state})
            if a.keep:
                print(f"      kept {d}")
            else:
                shutil.rmtree(d)


def cmd_report(_):
    if not LEDGER.exists():
        print("no ledger yet")
        return
    agg = defaultdict(lambda: [0, 0, 0.0])
    for l in LEDGER.read_text().splitlines():
        r = json.loads(l)
        k = (r["kind"], r.get("model") or "default", r["commit"] + ("+" if r["dirty"] else ""), r["id"])
        agg[k][0] += r["passed"]
        agg[k][1] += 1
        agg[k][2] += r.get("cost_usd") or 0.0
    for (kind, model, commit, tid), (p, n, c) in sorted(agg.items()):
        print(f"{kind:8s} {model:28s} {commit:10s} {tid:22s} {p}/{n}  ${c:.2f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    sub.add_parser("report")
    for name, budget, timeout in (("routing", 0.5, 300), ("tasks", 3.0, 1800)):
        p = sub.add_parser(name)
        p.add_argument("--model", help="model alias or id (default: CLI default)")
        p.add_argument("--only", nargs="*", help="ids to run")
        p.add_argument("--repeat", type=int, default=1, help="runs per item (agents are not deterministic)")
        p.add_argument("--budget", type=float, default=budget, help="USD cap per run")
        p.add_argument("--timeout", type=int, default=timeout, help="seconds per run")
        if name == "tasks":
            p.add_argument("--keep", action="store_true", help="keep the sandbox for inspection")
    a = ap.parse_args()
    if a.cmd in ("routing", "tasks") and not shutil.which("claude"):
        sys.exit("claude CLI not found")
    return {"selftest": cmd_selftest, "routing": cmd_routing, "tasks": cmd_tasks,
            "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main() or 0)
