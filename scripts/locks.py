"""Hash locks for files the agent must not edit.  python scripts/locks.py check|build
`build` is for the pack author only. The agent only runs `check`."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "state" / "LOCKS.json"
PATTERNS = ["src/cd70/*.py", "src/cd70/data/*", "tests/locked/*.py", "config/*.yaml", "docs/*.md", "docs/paper_text/*.md", "scripts/*.py",
            "tasks/*.md", "AGENTS.md", "README.md", "opencode.json", "pyproject.toml", "requirements.txt",
            ".opencode/**/*.md"]
EXCLUDE = {"docs/DESIGN_NOTES.md"}


def files():
    out = set()
    for p in PATTERNS:
        for f in ROOT.glob(p):
            if f.is_file():
                rel = f.relative_to(ROOT).as_posix()  # always POSIX keys, so Windows and Linux builds agree
                if rel not in EXCLUDE:
                    out.add(rel)
    return sorted(out)


def digest(rel):
    return hashlib.sha256((ROOT / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "build":
        LOCK.write_text(json.dumps({f: digest(f) for f in files()}, indent=1), encoding="utf-8")
        print(f"locked {len(files())} files")
        return 0
    locked = json.loads(LOCK.read_text(encoding="utf-8"))
    bad = [f for f, h in locked.items() if not (ROOT / f).exists() or digest(f) != h]
    new = [f for f in files() if f not in locked]
    if bad or new:
        print("LOCK VIOLATION. Locked files were changed or added:")
        for f in bad + new:
            print("  ", f)
        print("Undo your change (git checkout -- FILE) or, if truly needed, run: python scripts/task.py block <task> 'need edit of FILE because ...'")
        return 1
    print(f"locks ok ({len(locked)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
