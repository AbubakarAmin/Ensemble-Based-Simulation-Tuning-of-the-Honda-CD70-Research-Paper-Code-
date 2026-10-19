"""Package what must be uploaded with the paper.  python scripts/make_upload_bundle.py
Creates paper/supplement/ : S1 spec sheet, code zip, raw-data zip (processed parquet/json), UPLOAD_CHECKLIST.md."""
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "paper" / "supplement"
S.mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / "docs" / "spec_sheet_v11.md", S / "S1_specification_sheet.md")


def pack(name, items, skip=("__pycache__", ".pytest_cache", ".ruff_cache")):
    n = 0
    with zipfile.ZipFile(S / name, "w", zipfile.ZIP_DEFLATED) as z:
        for it in items:
            p = ROOT / it
            files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()] if p.exists() else []
            for f in files:
                if any(x in f.parts for x in skip):
                    continue
                z.write(f, f.relative_to(ROOT).as_posix())
                n += 1
    return n


nc = pack("S2_code.zip", ["src", "scripts", "config", "tests", "tasks", "docs", "AGENTS.md", "README.md", "opencode.json", "pyproject.toml", "requirements.txt", ".opencode", "JOURNAL.md", "DECISIONS.md", "FINAL_HANDOFF.md"])
nd = pack("S3_raw_results.zip", ["data/processed", "paper_inputs", "reports", "figures", "state/LOCKS.json"])
size = {f.name: f.stat().st_size / 1e6 for f in S.iterdir() if f.is_file()}
(S / "UPLOAD_CHECKLIST.md").write_text("# What to upload and where\n\n"
    f"1. `S1_specification_sheet.md` - attach to the journal submission as Supplementary File S1 (and put it in the repository).\n"
    f"2. `S2_code.zip` ({nc} files, {size.get('S2_code.zip', 0):.1f} MB) - upload to GitHub, then create a release and let Zenodo mint a DOI. Put the link in `[[CODE_URL]]`. Add a LICENSE file (MIT or Apache-2.0 for code) first.\n"
    f"3. `S3_raw_results.zip` ({nd} files, {size.get('S3_raw_results.zip', 0):.1f} MB) - upload to Zenodo (up to 50 GB; GitHub allows only 100 MB per file). Put the link in `[[DATA_URL]]`. Use CC-BY-4.0.\n"
    "4. Fill every `[[...]]` in `paper/PAPER_DRAFT.docx`, then submit the docx (or PDF) with S1 as the supplement.\n", encoding="utf-8")
print((S / "UPLOAD_CHECKLIST.md").read_text(encoding="utf-8"))
