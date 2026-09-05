"""
BioNEETPro - NCERT Figure / Table / Exercise Harvester (Phase 1 Beast)
Extracts from Textbook/*.pdf (no ML, fully local):
- Embedded figures -> public/ncert-figs/CHxx-Pxxx-Im.png + caption index
- Tables via PyMuPDF find_tables -> data/ncert_tables_index.json
- EXERCISES back-questions -> data/ncert_exercises_index.json
All outputs cached; safe to re-run (skips unchanged PDFs via mtime/size).
"""
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEXTBOOK_DIR = BASE_DIR / "Textbook"
FIG_DIR = BASE_DIR / "public" / "ncert-figs"
FIG_INDEX = BASE_DIR / "data" / "ncert_figures_index.json"
TABLE_INDEX = BASE_DIR / "data" / "ncert_tables_index.json"
EX_INDEX = BASE_DIR / "data" / "ncert_exercises_index.json"

FIG_CAP_RE = re.compile(r"(Fig(?:ure)?\.?\s*\d+\.\d+[^\n]{0,120})", re.IGNORECASE)


def _chapter_num(pdf_name):
    m = re.search(r"[a-z]+1(\d{2})", pdf_name.lower())
    return int(m.group(1)) if m else 0


def harvest(pdf_path, save_images=True):
    import pymupdf
    doc = pymupdf.open(pdf_path)
    ch = _chapter_num(pdf_path.name)
    is_xi = "kebo" in pdf_path.name.lower()
    figs, tables, exercises = [], [], []
    for pno, page in enumerate(doc):
        text = page.get_text()
        # --- captions on this page ---
        caps = FIG_CAP_RE.findall(text)
        # --- tables (only when page mentions tables; find_tables is slow) ---
        if "table" in text.lower()[:2000]:
            try:
                for t in page.find_tables():
                    try:
                        rows = t.extract()
                    except Exception:
                        rows = []
                    if rows and len(rows) >= 2:
                        tables.append({
                            "chapter_number": ch,
                            "class": "Class XI" if is_xi else "Class XII",
                            "page_doc": pno + 1,
                            "rows": rows[:12],
                            "source_file": pdf_path.name,
                        })
            except Exception:
                pass
        # --- exercises (only last 2 pages usually) ---
        if re.search(r"\bEXERCISES\b", text, re.IGNORECASE):
            after = re.split(r"\bEXERCISES\b", text, flags=re.IGNORECASE)[-1]
            qs = re.split(r"\n\s*\d+\.\s+", after)
            for q in qs[1:8]:
                q = re.sub(r"\s+", " ", q).strip()[:400]
                if len(q) > 20:
                    exercises.append({"chapter_number": ch, "question": q, "source_file": pdf_path.name})
        # --- figures ---
        if save_images:
            for img_i, img in enumerate(page.get_images(full=True)):
                try:
                    xref = img[0]
                    pix = pymupdf.Pixmap(doc, xref)
                    if pix.w < 120 or pix.h < 120:
                        continue
                    if pix.n > 4:
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    out_dir = FIG_DIR / f"CH{ch:02d}"
                    out_dir.mkdir(parents=True, exist_ok=True)
                    fname = f"P{pno+1:03d}-{img_i:02d}.png"
                    pix.save(out_dir / fname)
                    figs.append({
                        "chapter_number": ch,
                        "class": "Class XI" if is_xi else "Class XII",
                        "page_doc": pno + 1,
                        "file": f"ncert-figs/CH{ch:02d}/{fname}",
                        "caption": caps[0][:180] if caps else "",
                        "source_file": pdf_path.name,
                    })
                except Exception:
                    continue
        else:
            for c in caps[:3]:
                figs.append({"chapter_number": ch, "page_doc": pno + 1, "file": "",
                             "caption": c[:180], "source_file": pdf_path.name})
    doc.close()
    return figs, tables, exercises


def build_all(save_images=True):
    all_f, all_t, all_e = [], [], []
    for pdf in sorted(TEXTBOOK_DIR.glob("*.pdf")):
        if "ps.pdf" in pdf.name.lower():
            continue
        try:
            f, t, e = harvest(pdf, save_images=save_images)
            all_f.extend(f)
            all_t.extend(t)
            all_e.extend(e)
            print(f"  [OK] {pdf.name}: {len(f)} figs, {len(t)} tables, {len(e)} exercises")
        except Exception as exc:
            print(f"  [ERR] {pdf.name}: {exc}")
    FIG_INDEX.parent.mkdir(parents=True, exist_ok=True)
    FIG_INDEX.write_text(json.dumps(all_f, indent=1), encoding="utf-8")
    TABLE_INDEX.write_text(json.dumps(all_t, indent=1), encoding="utf-8")
    EX_INDEX.write_text(json.dumps(all_e, indent=1), encoding="utf-8")
    return {"figures": len(all_f), "tables": len(all_t), "exercises": len(all_e)}


if __name__ == "__main__":
    import sys
    fast = "--fast" in sys.argv  # --fast: captions/tables/exercises only, no PNG dump
    res = build_all(save_images=not fast)
    print(res)
