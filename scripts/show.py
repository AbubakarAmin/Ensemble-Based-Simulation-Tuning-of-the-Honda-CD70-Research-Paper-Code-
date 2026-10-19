"""Print the last N lines of a text file.  python scripts/show.py FILE [N]"""
import sys
from pathlib import Path

p = Path(__file__).resolve().parents[1] / sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
print("\n".join(p.read_text(encoding="utf-8").splitlines()[-n:]) if p.exists() else f"(no {sys.argv[1]})")
