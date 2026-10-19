---
description: Build the publication-ready paper draft (only works after the research is complete)
---
You are the CD70 paper-assembly agent. Follow AGENTS.md. Gate result:

!`python scripts/paper_gate.py`

If the gate line starts with NOT READY: tell the user exactly that line and STOP. Do nothing else.

If READY, do these steps in order and do NOT write any numbers or paragraphs by hand (the draft is generated from result files):
1. `python scripts/build_paper.py`
2. `python scripts/verify_numbers.py paper/PAPER_DRAFT.md`
3. `python scripts/show.py paper/CHECKLIST.md 60` and fix every FAIL by re-running the missing earlier step (never by editing results). If something cannot be fixed, write it in OPEN_ITEMS.md.
4. `python scripts/make_upload_bundle.py` (creates paper/supplement with the spec sheet, code zip and raw-results zip)
5. `python scripts/health.py --quick`
6. Tell the user in 7 lines: (include the contents of paper/supplement/UPLOAD_CHECKLIST.md as the last line pointing to it) where `paper/arxiv_source.zip` (arXiv upload) and `paper/ARXIV_METADATA.md` are, where `paper/PAPER_DRAFT.docx` and `paper/PAPER_DRAFT.md` are, the number of figures and tables in it, the target-journal advice in paper/SUBMISSION_GUIDE.md, the list in `paper/PLACEHOLDERS.md` they must fill (code link, data link, authors, funding), any FAIL left, the single most important next step, and that a smart model can polish the language but must not change numbers or claim words.
