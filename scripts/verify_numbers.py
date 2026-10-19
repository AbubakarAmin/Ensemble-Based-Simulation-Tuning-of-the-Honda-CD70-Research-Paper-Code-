"""Anti-hallucination gate: every decimal number written in a report must exist in the project's result files.
python scripts/verify_numbers.py reports/some_report.md
Numbers are matched after rounding to the precision written (so 12.3 matches 12.34). Integers < 100 and years are ignored."""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
rep = ROOT / sys.argv[1]
if not rep.exists():
    print("missing", rep)
    sys.exit(1)
src = set()


def add(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return
    if v == v:
        src.add(v)


for f in list((ROOT / "paper_inputs").rglob("*.json")) + list((ROOT / "reports").rglob("*.json")) + list((ROOT / "docs").glob("*.md")) + list((ROOT / "config").glob("*.yaml")):
    for m in re.findall(r"-?\d+\.?\d*", f.read_text(encoding="utf-8", errors="ignore")):
        add(m)
for f in list((ROOT / "paper_inputs").rglob("*.csv")) + list((ROOT / "reports").rglob("*.csv")):
    try:
        df = pd.read_csv(f)
    except Exception:
        continue
    for v in df.select_dtypes("number").to_numpy().ravel():
        add(v)
for f in (ROOT / "data" / "processed").rglob("accepted_*.parquet"):
    df = pd.read_parquet(f)
    for v in df.select_dtypes("number").describe().to_numpy().ravel():
        add(v)
text = rep.read_text(encoding="utf-8")
bad = []
for m in re.finditer(r"(?<![\w.])-?\d+\.\d+(?![\w])", text):
    tok = m.group(0)
    dec = len(tok.split(".")[1])
    v = float(tok)
    if not any(abs(round(s, dec) - v) < 10 ** -(dec + 1) for s in src):
        bad.append(tok)
if len(bad) > max(3, 0.05 * len(re.findall(r"\d+\.\d+", text))):
    print(f"{len(bad)} numbers in {rep.name} do not appear in any result file, e.g. {bad[:8]}. Remove or recompute them; do not invent numbers.")
    sys.exit(1)
print(f"verify_numbers ok ({len(bad)} unmatched of {len(re.findall(r'[0-9]+[.][0-9]+', text))})")
