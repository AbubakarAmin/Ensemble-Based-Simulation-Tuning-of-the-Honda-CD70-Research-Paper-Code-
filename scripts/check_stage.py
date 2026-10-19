"""Gate helper (v13: binary-safe).
  python scripts/check_stage.py done KEY [KEY...]
  python scripts/check_stage.py group GROUP SCALE
  python scripts/check_stage.py cal TIMING SCALE MIN_ACCEPTED
  python scripts/check_stage.py exists PATH                  (any file or folder)
  python scripts/check_stage.py file PATH [MIN_LINES] [TEXT] (text files; binary files such as PNG are checked for existence, size and signature)
  python scripts/check_stage.py pytest PATH                  (a pytest report from scripts/capture.py: summary passed, no failures)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINARY = {".png", ".jpg", ".jpeg", ".pdf", ".parquet", ".npz", ".docx", ".xlsx", ".zip"}
PNG_SIG = b"\x89PNG\r\n\x1a\n"
MIN_BINARY_BYTES = 1000


def fail(msg):
    print(msg)
    return 1


def check_file(a):
    p = ROOT / a[1]
    if not p.exists():
        return fail(f"missing file {a[1]}")
    if p.suffix.lower() in BINARY:
        if p.stat().st_size < MIN_BINARY_BYTES:
            return fail(f"{a[1]} is too small ({p.stat().st_size} bytes)")
        head = p.read_bytes()[:8]
        if p.suffix.lower() == ".png" and head != PNG_SIG:
            return fail(f"{a[1]} is not a valid PNG")
        print("file ok (binary)", a[1])
        return 0
    txt = p.read_text(encoding="utf-8")
    if len(a) > 2 and len(txt.splitlines()) < int(a[2]):
        return fail(f"{a[1]} has fewer than {a[2]} lines")
    if len(a) > 3 and a[3] not in txt:
        return fail(f"{a[1]} must contain the text: {a[3]}")
    print("file ok", a[1])
    return 0


def check_pytest(a):
    p = ROOT / a[1]
    if not p.exists():
        return fail(f"missing report {a[1]}")
    txt = p.read_text(encoding="utf-8")
    lines = [line for line in txt.splitlines() if line.strip()]
    last = lines[-1] if lines else ""
    if not re.search(r"\d+ passed", last):
        return fail(f"last line of {a[1]} is not a pytest summary with passed tests: {last[:120]}")
    if re.search(r"\b\d+ (failed|errors?)\b", last) or re.search(r"\bFAILED\b|\bERROR\b", txt):
        return fail(f"{a[1]} contains failed or errored tests")
    print("pytest report ok", a[1], "-", last.strip("= "))
    return 0


def main(a):
    if a[0] == "done":
        miss = [k for k in a[1:] if not (ROOT / "state" / "stage_done" / f"{k}.done").exists()]
        if miss:
            print("NOT FINISHED YET:", miss)
            print("Start/continue with: python scripts/jobs.py status   (and the job command in the task text)")
            return 1
        print("all stages finished")
        return 0
    if a[0] == "exists":
        if not (ROOT / a[1]).exists():
            return fail(f"missing {a[1]}")
        print("exists", a[1])
        return 0
    if a[0] == "group":
        sys.path.insert(0, str(ROOT / "scripts"))
        from run_many import cmds
        miss = [k for k, _ in cmds(a[1], a[2]) if not (ROOT / "state" / "stage_done" / f"{k}.done").exists()]
        if miss:
            print(f"GROUP {a[1]} NOT FINISHED: {len(miss)} runs missing, first: {miss[:3]}")
            return 1
        print(f"group {a[1]} finished")
        return 0
    if a[0] == "cal":
        t, scale, mn = a[1], a[2], int(a[3])
        p = (ROOT / "data" / "processed" if scale == "full" else ROOT / "runs" / "smoke") / f"cal_summary_{t}.json"
        if not p.exists():
            return fail("no calibration summary yet")
        s = json.loads(p.read_text(encoding="utf-8"))
        print(f"accepted {s['accepted']} (needed {mn}), acceptance rate {s['acceptance_rate']:.4f}, rounds {s.get('rounds')}")
        return 0 if s["accepted"] >= mn else 1
    if a[0] == "file":
        return check_file(a)
    if a[0] == "pytest":
        return check_pytest(a)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
