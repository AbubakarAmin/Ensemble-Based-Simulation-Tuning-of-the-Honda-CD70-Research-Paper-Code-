"""The ONLY way to move through the research. Commands:
  python scripts/task.py next              show the next task (full instructions)
  python scripts/task.py done T-0xx        run the task's gate; if it passes the task is ticked
  python scripts/task.py block T-0xx "why" give up on a task after 3 honest attempts (writes BLOCKERS.md)
  python scripts/task.py reopen T-0xx     undo a block (use after a pack fix has been applied)
  python scripts/task.py status            progress summary
  python scripts/task.py list              every task with its status
Never edit state/STATE.json by hand.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
STATE = ROOT / "state" / "STATE.json"


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"tasks": {}, "sessions": 0, "created": time.strftime("%F")}


def save_state(s):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1, sort_keys=True), encoding="utf-8")


def parse(path):
    txt = path.read_text(encoding="utf-8")
    assert txt.startswith("---"), f"{path} has no front matter"
    head, body = txt[3:].split("\n---", 1)
    meta = yaml.safe_load(head)
    meta["body"] = body.strip("\n")
    meta["path"] = path
    return meta


def all_tasks():
    return [parse(p) for p in sorted(TASKS.glob("T-*.md"))]


def status_of(s, tid):
    return s["tasks"].get(tid, {}).get("status", "todo")


def next_task(tasks, s):
    for t in tasks:
        if status_of(s, t["id"]) != "todo":
            continue
        needs = t.get("needs") or []
        if t.get("skip_if_blocked") and any(status_of(s, n) == "blocked" for n in needs):
            s["tasks"][t["id"]] = {"status": "blocked", "at": time.strftime("%F %H:%M"), "why": "a needed task is blocked (skipped automatically)"}
            save_state(s)
            journal(f"AUTO-SKIPPED {t['id']} because a needed task is blocked")
            continue
        if all(status_of(s, n) == "done" for n in needs):
            return t
    return None


def journal(msg):
    with open(ROOT / "JOURNAL.md", "a", encoding="utf-8") as f:
        f.write(f"- {time.strftime('%F %H:%M')} {msg}\n")


def run_gate(t):
    cmds = t.get("gate") or []
    if isinstance(cmds, str):
        cmds = [cmds]
    for c in cmds:
        r = subprocess.run(c, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=1800)
        if r.returncode != 0:
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-15:])
            print(f"GATE FAILED: {c}\n{tail}")
            return False
        print(f"gate ok: {c}")
    return True


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 1
    tasks = all_tasks()
    s = load_state()
    ids = {t["id"]: t for t in tasks}
    if a[0] == "next":
        t = next_task(tasks, s)
        if t is None:
            todo = [x["id"] for x in tasks if status_of(s, x["id"]) == "todo"]
            blocked = [x["id"] for x in tasks if status_of(s, x["id"]) == "blocked"]
            if not todo:
                print("ALL TASKS FINISHED. Write nothing more. Tell the user to read FINAL_HANDOFF.md.")
            else:
                print(f"NOTHING READY. Waiting tasks: {todo[:5]}. Blocked: {blocked}.")
                print("If a background job is running: python scripts/jobs.py status  (then wait or end the session).")
            return 0
        print(f"=== {t['id']}: {t['title']} ===\n(estimated: {t.get('est', '?')})\n")
        print(t["body"])
        print(f"\nWHEN FINISHED RUN: python scripts/task.py done {t['id']}")
        return 0
    if a[0] == "done":
        t = ids.get(a[1])
        if not t:
            print("unknown task id")
            return 1
        lk = subprocess.run([sys.executable, "scripts/locks.py", "check"], cwd=ROOT, capture_output=True, text=True)
        if lk.returncode != 0:
            print("LOCKED FILES WERE MODIFIED. Restore them (you may not edit locked files) before any task can be ticked:\n" + (lk.stdout + lk.stderr)[-800:])
            return 1
        if not run_gate(t):
            print("Task NOT done. Fix the problem and run the same command again.")
            return 1
        s["tasks"][t["id"]] = {"status": "done", "at": time.strftime("%F %H:%M")}
        save_state(s)
        journal(f"DONE {t['id']} {t['title']}")
        nxt = next_task(all_tasks(), s)
        print(f"TICKED {t['id']}. Next: {nxt['id'] + ' ' + nxt['title'] if nxt else 'nothing ready (see: python scripts/task.py next)'}")
        return 0
    if a[0] == "reopen":
        s["tasks"].pop(a[1], None)
        save_state(s)
        journal(f"REOPENED {a[1]}")
        print(f"{a[1]} reopened. Run: python scripts/task.py next")
        return 0
    if a[0] == "block":
        tid, why = a[1], " ".join(a[2:]) or "no reason given"
        s["tasks"][tid] = {"status": "blocked", "at": time.strftime("%F %H:%M"), "why": why}
        save_state(s)
        with open(ROOT / "BLOCKERS.md", "a", encoding="utf-8") as f:
            f.write(f"\n## {tid} blocked {time.strftime('%F %H:%M')}\n{why}\n")
        journal(f"BLOCKED {tid}: {why[:120]}")
        print("blocked recorded. Run: python scripts/task.py next")
        return 0
    if a[0] in ("status", "list"):
        cnt = {"todo": 0, "done": 0, "blocked": 0}
        for t in tasks:
            st = status_of(s, t["id"])
            cnt[st] += 1
            if a[0] == "list":
                print(f"{t['id']} [{st:7}] {t['title']}")
        print(f"done {cnt['done']} / {len(tasks)}   todo {cnt['todo']}   blocked {cnt['blocked']}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
