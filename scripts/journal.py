"""Append one line to JOURNAL.md:  python scripts/journal.py "what I did / what I learned" """
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
msg = " ".join(sys.argv[1:]).strip()
if not msg:
    sys.exit("give a message")
with open(ROOT / "JOURNAL.md", "a", encoding="utf-8") as f:
    f.write(f"- {time.strftime('%F %H:%M')} {msg}\n")
print("journal updated")
