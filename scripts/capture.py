"""Run a command and save its output as UTF-8 text. No shell redirection, so it works the same in PowerShell, cmd and bash.
  python scripts/capture.py OUTFILE -- COMMAND [ARGS...]
The output file is always written. The exit code is the command's exit code."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    a = sys.argv[1:]
    if len(a) < 3 or a[1] != "--":
        print(__doc__)
        return 2
    out = ROOT / a[0]
    cmd = a[2:]
    if cmd[0] == "python":
        cmd[0] = sys.executable
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out.write_text(r.stdout + r.stderr, encoding="utf-8")
    print(f"wrote {a[0]} (exit {r.returncode})")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
