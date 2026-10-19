"""Repository health check.  python scripts/health.py [--quick]
Fails (exit 1) if: lint errors, tests fail, stray root files, forbidden file names, locks broken."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {"AGENTS.md", "README.md", "JOURNAL.md", "DECISIONS.md", "OPEN_ITEMS.md", "BLOCKERS.md", "FINAL_HANDOFF.md",
              "STUCK_REPORT.md", "opencode.json", "pyproject.toml", "requirements.txt", ".gitignore"}
ROOT_DIRS = {"src", "scripts", "tests", "config", "docs", "tasks", "state", "reports", "figures", "paper_inputs", "paper", "runs",
             "data", ".opencode", ".git", ".venv", ".ruff_cache", ".pytest_cache", "__pycache__"}
FORBIDDEN = re.compile(r"(^|[_\-])(final|new|copy|temp|tmp|backup|old|v2|v3|test2|untitled)($|[_\-])|\(\d\)", re.I)


def sh(cmd):
    r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    quick = "--quick" in sys.argv
    problems = []
    for p in ROOT.iterdir():
        if p.is_dir() and p.name not in ROOT_DIRS:
            problems.append(f"stray root folder: {p.name} (move or delete it)")
        if p.is_file() and p.name not in ROOT_FILES:
            problems.append(f"stray root file: {p.name} (move to the right folder or delete it)")
    for sub in ("src", "scripts", "tests"):
        for f in (ROOT / sub).rglob("*.py"):
            if "__pycache__" in f.parts:
                continue
            if FORBIDDEN.search(f.stem) and f.stem not in {"final_handoff"}:
                problems.append(f"bad file name (no final/new/copy/temp/old/v2 in names): {f.relative_to(ROOT)}")
    code, out = sh("python -m ruff check src scripts tests")
    if code:
        problems.append("ruff errors:\n" + "\n".join(out.splitlines()[-12:]) + "\n(try: python -m ruff check --fix src/cd70/custom scripts/custom tests/custom)")
    if not quick:
        code, out = sh("python -m pytest tests -x -q")
        if code:
            problems.append("tests fail:\n" + "\n".join(out.splitlines()[-15:]))
    code, out = sh("python scripts/locks.py check")
    if code:
        problems.append(out)
    if problems:
        print("HEALTH: PROBLEMS")
        for p in problems:
            print("-", p)
        return 1
    print("HEALTH: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
