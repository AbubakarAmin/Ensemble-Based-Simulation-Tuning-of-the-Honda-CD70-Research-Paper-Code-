"""arXiv package from paper/PAPER_DRAFT.md: paper/arxiv/{main.tex, figures/, main.pdf (if LaTeX present)}, ARXIV_METADATA.md, arxiv_source.zip.
python scripts/make_arxiv.py   (called by build_paper.py; safe to run alone)"""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "paper"
A = P / "arxiv"
src = (P / "PAPER_DRAFT.md").read_text(encoding="utf-8")
shutil.rmtree(A, ignore_errors=True)
(A / "figures").mkdir(parents=True)
lines = src.splitlines()
title = lines[0].lstrip("# ").strip()


def section(name):
    m = re.search(rf"^## {re.escape(name)}\s*$(.*?)(?=^## |\Z)", src, re.S | re.M)
    return m.group(1).strip() if m else ""


abstract_md = section("Abstract")
plain = re.sub(r"\*\*(.+?)\*\*", r"\1", abstract_md)
plain = re.sub(r"\s*\n\s*", " ", plain).strip()
kw = re.search(r"\*\*Keywords:\*\*\s*(.+)", src)
keywords = kw.group(1).strip() if kw else ""
body = re.sub(r"^## Highlights\s*$.*?(?=^## )", "", src, flags=re.S | re.M)
body = re.sub(r"^## Abstract\s*$.*?(?=^## )", "", body, flags=re.S | re.M)
body = "\n".join(l for l in body.splitlines()[1:] if not l.startswith(("Target journal", "[[AUTHORS]]", "[[AFFILIATIONS]]", "Corresponding author", "**Keywords:**")))
body = body.replace("](../figures/", "](figures/")
body = re.sub(r"!\[Figure \d+\. ", "![", body)
body = re.sub(r"(?<!\n)\n(#{2,4} |\*\*Table \d+)", r"\n\n\1", body)
for f in (ROOT / "figures").glob("*.png"):
    shutil.copy(f, A / "figures" / f.name)


def widen(m):  # relative column widths from content so pandoc wraps long cells
    rows = [r for r in m.group(0).splitlines()]
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows if not re.match(r"^\|[-: |]+\|$", r)]
    n = max(len(c) for c in cells)
    w = [max(6, min(40, max(len(c[i]) if i < len(c) else 0 for c in cells))) for i in range(n)]
    sep = "|" + "|".join("-" * x for x in w) + "|"
    out = []
    for r in rows:
        out.append(sep if re.match(r"^\|[-: |]+\|$", r) else r)
    return "\n".join(out)


body = re.sub(r"(?:^\|.*\|\n?)+", lambda m: widen(m) + "\n", body, flags=re.M)
(A / "body.md").write_text(body, encoding="utf-8")
hdr = r"""\usepackage[margin=1in]{geometry}
\usepackage{graphicx,booktabs,longtable,array,microtype,float}
\usepackage[font=small,labelfont=bf]{caption}
\setlength{\parskip}{0.5em}\setlength{\parindent}{0pt}
\renewcommand{\arraystretch}{1.15}
\let\oldlongtable\longtable
\renewcommand{\longtable}{\footnotesize\oldlongtable}
\DeclareUnicodeCharacter{2212}{\ensuremath{-}}
\DeclareUnicodeCharacter{00B0}{\ensuremath{^\circ}}
\DeclareUnicodeCharacter{00D7}{\ensuremath{\times}}
\DeclareUnicodeCharacter{00B3}{\ensuremath{^3}}
\DeclareUnicodeCharacter{00B2}{\ensuremath{^2}}
\DeclareUnicodeCharacter{00B1}{\ensuremath{\pm}}
\DeclareUnicodeCharacter{00B7}{\ensuremath{\cdot}}
\DeclareUnicodeCharacter{0159}{\v{r}}
\setkeys{Gin}{width=\linewidth,keepaspectratio}
"""
(A / "header.tex").write_text(hdr, encoding="utf-8")
meta = A / "meta.yaml"
def esc(s):
    return s.replace('"', "'")
meta.write_text(f'---\ntitle: "{esc(title)}"\nauthor: "[[AUTHORS]]"\ndate: ""\nabstract: |\n  {plain}\ngeometry: margin=1in\nfontsize: 11pt\n---\n', encoding="utf-8")
pd = shutil.which("pandoc")
status = "pandoc not found: tex not generated"
if pd:
    r = subprocess.run([pd, "body.md", "meta.yaml", "-s", "-o", "main.tex", "--shift-heading-level-by=-1", "-H", "header.tex", "-V", "fontfamily=mathptmx", "-f", "markdown+pipe_tables+implicit_figures-smart"], cwd=A, capture_output=True, text=True)
    status = "main.tex written" if r.returncode == 0 else "pandoc failed: " + r.stderr[:300]
    tex = A / "main.tex"
    if r.returncode == 0:
        t = tex.read_text(encoding="utf-8")
        t = t.replace("\\begin{document}", "\\begin{document}\n\\maketitle", 1) if "\\maketitle" not in t else t
        tex.write_text(t, encoding="utf-8")
        if shutil.which("pdflatex"):
            for _ in range(2):
                subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"], cwd=A, capture_output=True)
            status += "; main.pdf built" if (A / "main.pdf").exists() else "; pdflatex failed (see main.log)"
nfig = len(list((A / "figures").glob("*.png")))
pages = ""
if (A / "main.pdf").exists():
    try:
        out = subprocess.run(["pdfinfo", "main.pdf"], cwd=A, capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", out)
        pages = f"{m.group(1)} pages, " if m else ""
    except Exception:
        pass
(P / "ARXIV_METADATA.md").write_text(f"""# arXiv submission sheet (paste into the arXiv form)

**Title:** {title}

**Authors:** [[AUTHORS]]   (format: First Last, First Last)

**Abstract (plain text, {len(plain)} characters; arXiv limit 1920):**

{plain}

**Comments:** {pages}{nfig} figures; code and data: [[CODE_URL]] / [[DATA_URL]]

**Primary category (suggested):** physics.app-ph   **Cross-list (suggested):** cs.CE, stat.AP   (alternative primary: eess.SY)

**License (suggested):** CC BY 4.0

**Keywords (put in the paper, not the form):** {keywords}

## Upload
1. Upload `paper/arxiv_source.zip` (main.tex + figures/) as the source, or upload `paper/arxiv/main.pdf` as a PDF-only submission.
2. arXiv compiles main.tex itself; the file uses only standard packages (geometry, graphicx, booktabs, longtable, microtype, caption).
3. Fill every [[...]] first. Search main.tex for `[[`.
4. Check the preview PDF arXiv produces: figure axes readable, tables not cut at the margin.
5. First-time submitters in a category may need an endorsement; ask a co-author or colleague who has posted in that category.
""", encoding="utf-8")
with zipfile.ZipFile(P / "arxiv_source.zip", "w", zipfile.ZIP_DEFLATED) as z:
    if (A / "main.tex").exists():
        z.write(A / "main.tex", "main.tex")
    for f in (A / "figures").glob("*.png"):
        z.write(f, f"figures/{f.name}")
print("arxiv:", status, "| abstract chars", len(plain))
sys.exit(0 if "failed" not in status else 1)
