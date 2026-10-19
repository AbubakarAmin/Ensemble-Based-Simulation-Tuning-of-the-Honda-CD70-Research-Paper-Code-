"""Gate for /finalpaper: the paper can only be built after the research is complete.  python scripts/paper_gate.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
st = json.loads((ROOT / "state" / "STATE.json").read_text(encoding="utf-8")) if (ROOT / "state" / "STATE.json").exists() else {"tasks": {}}
tasks = [p.stem for p in sorted((ROOT / "tasks").glob("T-*.md"))]
t = st.get("tasks", {})
left = [x for x in tasks if t.get(x, {}).get("status") not in ("done", "blocked")]
blocked = [x for x in tasks if t.get(x, {}).get("status") == "blocked"]
ok = t.get("T-080", {}).get("status") == "done" and (ROOT / "FINAL_HANDOFF.md").exists() and (ROOT / "paper_inputs" / "RESULTS_FACTS.json").exists()
if not ok:
    print(f"NOT READY: the research is not finished ({len(left)} tasks left, first: {left[:3]}). Run /work in a new session until it prints RESEARCH COMPLETE, then run /finalpaper.")
    sys.exit(1)
print(f"READY: research complete ({len(blocked)} blocked tasks: {blocked}). Build the paper.")
