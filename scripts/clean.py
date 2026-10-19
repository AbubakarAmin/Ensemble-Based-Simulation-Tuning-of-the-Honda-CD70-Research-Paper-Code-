"""The only allowed deletion.  python scripts/clean.py smoke   (removes runs/smoke after the rehearsal)"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if sys.argv[1:] == ["smoke"]:
    shutil.rmtree(ROOT / "runs" / "smoke", ignore_errors=True)
    for f in (ROOT / "state" / "stage_done").glob("*-smoke-*.done"):
        f.unlink()
    for f in (ROOT / "state" / "stage_done").glob("*-smoke.done"):
        f.unlink()
    print("runs/smoke removed")
else:
    sys.exit("usage: python scripts/clean.py smoke")
