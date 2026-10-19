import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_gate_blocks_before_research_is_done():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "paper_gate.py")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 1 and "NOT READY" in r.stdout


def test_finalpaper_command_exists_and_uses_gate():
    t = (ROOT / ".opencode" / "commands" / "finalpaper.md").read_text(encoding="utf-8")
    assert "paper_gate.py" in t and "build_paper.py" in t
