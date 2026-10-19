"""Regression tests for the v13 tooling fixes (blockers and open items from the v12 run)."""
import random
import struct
import subprocess
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import locks  # noqa: E402


def _png(path: Path) -> None:
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    rnd = random.Random(1)  # incompressible pixels, so the file is a realistic size
    raw = b"".join(b"\x00" + rnd.randbytes(64 * 3) for _ in range(64))
    ihdr = struct.pack(">IIBBBBB", 64, 64, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def _check(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "check_stage.py"), *args],
                          capture_output=True, text=True, cwd=ROOT).returncode


def test_lock_keys_are_posix_paths():
    assert locks.files(), "no locked files found"
    assert all("\\" not in f for f in locks.files())
    assert "docs/DESIGN_NOTES.md" not in locks.files()


def test_png_passes_binary_file_check(tmp_path):
    png = tmp_path / "figure.png"
    _png(png)
    assert _check("file", str(png)) == 0


def test_non_png_named_png_is_rejected(tmp_path):
    fake = tmp_path / "fake.png"
    fake.write_bytes(b"not a png" * 300)
    assert _check("file", str(fake)) == 1


def test_pytest_gate_rejects_partial_failure(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("tests/x.py::test_a FAILED\n=== 1 failed, 31 passed in 2s ===\n", encoding="utf-8")
    good = tmp_path / "good.txt"
    good.write_text("tests/x.py::test_runner_captures_errors PASSED\n=== 32 passed in 3s ===\n", encoding="utf-8")
    assert _check("pytest", str(bad)) == 1
    assert _check("pytest", str(good)) == 0


def test_capture_writes_utf8_and_returns_exit_code(tmp_path):
    out = "reports/_capture_test.txt"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "capture.py"), out, "--", sys.executable, "-c",
                        "print('zeichen ✓')"], capture_output=True, text=True, cwd=ROOT)
    target = ROOT / out
    try:
        assert r.returncode == 0
        assert "✓" in target.read_text(encoding="utf-8")
    finally:
        target.unlink(missing_ok=True)
