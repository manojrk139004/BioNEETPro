"""
BioNEET Pro - Kaggle & External Dataset Ingestion Pipeline
=========================================================
Purpose:
Allows dropping ANY biology/NEET dataset downloaded from Kaggle (or elsewhere)
into the local system, transforming it into the 12-column canonical knowledge base schema,
and updating the TF-IDF Search Engine and Pedagogical Tracker in real-time.

Usage:
  1. Drop CSV files into: data/kaggle_imports/
     Then run: python scripts/import_kaggle_dataset.py
  OR
  2. Directly import a specific file:
     python scripts/import_kaggle_dataset.py "C:\\path\\to\\kaggle_biology_dataset.csv"
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DATA_DIR = BASE_DIR / "data"
IMPORTS_DIR = DATA_DIR / "kaggle_imports"
KB_PATH = DATA_DIR / "neet_knowledge_base.csv"
GRAPH_PATH = DATA_DIR / "concept_dependency_graph.csv"
TRACKER_PATH = DATA_DIR / "student_learning_tracker.csv"

CANONICAL_COLUMNS = [
    "concept_id",
    "chapter_id",
    "chapter_name",
    "topic",
    "title",
    "definition",
    "mechanism_steps",
    "neet_traps",
    "sample_question",
    "sample_options",
    "correct_answer",
    "explanation"
]

COLUMN_ALIASES = {
    "title": ["title", "concept", "concept_name", "topic_name", "headline", "name"],
    "topic": ["topic", "subtopic", "unit", "section", "category"],
    "chapter_name": ["chapter_name", "chapter", "unit_name", "subject", "module"],
    "chapter_id": ["chapter_id", "chap_id", "c_id", "cid"],
    "definition": ["definition", "summary", "concept_summary", "description", "content", "theory", "answer", "ans"],
    "mechanism_steps": ["mechanism_steps", "steps", "mechanism", "process", "pathway", "workflow", "details"],
    "neet_traps": ["neet_traps", "traps", "exam_tips", "neet_tips", "important_points", "key_points", "notes"],
    "sample_question": ["sample_question", "question", "q", "problem", "mcq_question", "query"],
    "sample_options": ["sample_options", "options", "opts", "choices"],
    "correct_answer": ["correct_answer", "correct", "answer_idx", "correct_option", "key"],
    "explanation": ["explanation", "expl", "solution", "rationale", "reason"]
}


def find_column_match(df_cols: List[str], candidate_keys: List[str]) -> Optional[str]:
    """Finds matching column in the external dataset using fuzzy lowercase checking."""
    df_cols_clean = {re.sub(r"[^a-z0-9]", "", c.lower()): c for c in df_cols}
    for candidate in candidate_keys:
        cand_clean = re.sub(r"[^a-z0-9]", "", candidate.lower())
        if cand_clean in df_cols_clean:
            return df_cols_clean[cand_clean]
    return None


def extract_options_from_row(row: pd.Series) -> Tuple[str, int]:
    """
    Attempts to extract options if stored in separate columns (e.g. Option A, Option B, etc.).
    Returns (pipe_separated_options, correct_idx).
    """
    # Check separate option columns
    opt_a = row.get("Option A") or row.get("A") or row.get("opt_a") or row.get("option_1")
    opt_b = row.get("Option B") or row.get("B") or row.get("opt_b") or row.get("option_2")
    opt_c = row.get("Option C") or row.get("C") or row.get("opt_c") or row.get("option_3")
    opt_d = row.get("Option D") or row.get("D") or row.get("opt_d") or row.get("option_4")

    if opt_a and opt_b:
        opts = [str(opt_a).strip(), str(opt_b).strip()]
        if opt_c:
            opts.append(str(opt_c).strip())
        if opt_d:
            opts.append(str(opt_d).strip())

        # Determine correct index from answer column
        ans_raw = str(row.get("Answer") or row.get("answer") or row.get("correct") or "A").strip()
        ans_clean = ans_raw.upper()
        if ans_clean in ["A", "1", "OPT_A"]:
            correct_idx = 0
        elif ans_clean in ["B", "2", "OPT_B"]:
            correct_idx = 1
        elif ans_clean in ["C", "3", "OPT_C"]:
            correct_idx = 2
        elif ans_clean in ["D", "4", "OPT_D"]:
            correct_idx = 3
        else:
            try:
                correct_idx = int(ans_raw)
            except ValueError:
                correct_idx = 0

        return "|".join(opts), correct_idx

    return "", 0


def transform_external_dataframe(ext_df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """
    Transforms any incoming Kaggle/external dataframe into the canonical 12-column schema.
    """
    rows_to_add = []
    existing_df = pd.read_csv(KB_PATH) if KB_PATH.exists() else pd.DataFrame(columns=CANONICAL_COLUMNS)
    existing_titles = set(existing_df["title"].str.lower().tolist()) if "title" in existing_df.columns else set()
    start_id_num = len(existing_df) + 1

    # Map column names
    col_mapping = {}
    for canon_col, candidates in COLUMN_ALIASES.items():
        match = find_column_match(list(ext_df.columns), candidates)
        if match:
            col_mapping[canon_col] = match

    for idx, row in ext_df.iterrows():
        # Title
        raw_title = ""
        if "title" in col_mapping:
            raw_title = str(row[col_mapping["title"]]).strip()
        elif "sample_question" in col_mapping:
            q_text = str(row[col_mapping["sample_question"]]).strip()
            raw_title = q_text[:75] + ("..." if len(q_text) > 75 else "")
        else:
            raw_title = f"Kaggle Concept {start_id_num + idx}"

        if not raw_title or raw_title.lower() in existing_titles or raw_title == "nan":
            continue

        # Chapter Name & ID
        chap_name = "NEET Biology"
        if "chapter_name" in col_mapping:
            chap_name = str(row[col_mapping["chapter_name"]]).strip()
        chap_id = "c00"
        if "chapter_id" in col_mapping:
            chap_id = str(row[col_mapping["chapter_id"]]).strip()
        elif chap_name != "NEET Biology":
            chap_id = "c" + re.sub(r"[^0-9]", "", chap_name).zfill(2)
            if chap_id == "c":
                chap_id = "c99"

        # Topic
        topic = "High-Yield NEET Concept"
        if "topic" in col_mapping:
            topic = str(row[col_mapping["topic"]]).strip()

        # Definition / Answer
        definition = ""
        if "definition" in col_mapping:
            definition = str(row[col_mapping["definition"]]).strip()
        if not definition or definition == "nan":
            definition = f"{raw_title} is a core NCERT Biology concept frequently tested in NEET UG."

        # Explanation
        explanation = definition
        if "explanation" in col_mapping:
            explanation = str(row[col_mapping["explanation"]]).strip()

        # Mechanism Steps
        mechanism = ""
        if "mechanism_steps" in col_mapping:
            mechanism = str(row[col_mapping["mechanism_steps"]]).strip()
        if not mechanism or mechanism == "nan":
            mechanism = f"Step 1: Initiation and biological foundation of {raw_title} -> Step 2: Cellular and biochemical execution -> Step 3: Physiological outcome and regulation."

        # NEET Traps
        traps = ""
        if "neet_traps" in col_mapping:
            traps = str(row[col_mapping["neet_traps"]]).strip()
        if not traps or traps == "nan":
            traps = f"NEET Trap: Pay close attention to exception cases, exact numerical ratios, and terminology variations in {raw_title} as per NCERT."

        # Question & Options
        question = ""
        options = ""
        correct_answer = 0

        # Try to parse options from row
        sep_opts, parsed_correct = extract_options_from_row(row)
        if sep_opts:
            options = sep_opts
            correct_answer = parsed_correct
        elif "sample_options" in col_mapping:
            options = str(row[col_mapping["sample_options"]]).strip()
            if "correct_answer" in col_mapping:
                try:
                    correct_answer = int(row[col_mapping["correct_answer"]])
                except (ValueError, TypeError):
                    correct_answer = 0

        if "sample_question" in col_mapping:
            question = str(row[col_mapping["sample_question"]]).strip()
        if not question or question == "nan":
            question = f"Which of the following statements regarding {raw_title} is scientifically accurate according to NCERT?"
            if not options:
                options = f"{definition[:60]}...|It occurs exclusively in anaerobic organisms|It is completely independent of cellular regulation|It produces no measurable biological effect"
                correct_answer = 0

        concept_id = f"KAG-{source_name[:3].upper()}-{str(start_id_num + len(rows_to_add)).zfill(3)}"

        record = {
            "concept_id": concept_id,
            "chapter_id": chap_id,
            "chapter_name": chap_name,
            "topic": topic,
            "title": raw_title,
            "definition": definition,
            "mechanism_steps": mechanism,
            "neet_traps": traps,
            "sample_question": question,
            "sample_options": options,
            "correct_answer": correct_answer,
            "explanation": explanation
        }
        rows_to_add.append(record)
        existing_titles.add(raw_title.lower())

    return pd.DataFrame(rows_to_add)


def import_dataset(file_path: Path) -> int:
    """Imports a single dataset file into the canonical knowledge base."""
    if not file_path.exists():
        print(f"[ERROR] File does not exist: {file_path}")
        return 0

    print(f"\n[INFO] Loading external dataset: {file_path.name}...")
    try:
        if file_path.suffix.lower() == ".csv":
            ext_df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
        elif file_path.suffix.lower() == ".json":
            ext_df = pd.read_json(file_path)
        else:
            print(f"[WARNING] Unsupported file format: {file_path.suffix}. Expected .csv or .json")
            return 0
    except Exception as e:
        print(f"[ERROR] Could not read {file_path.name}: {e}")
        return 0

    print(f"  Total raw rows read: {len(ext_df)}")
    print(f"  Detected columns: {list(ext_df.columns)}")

    source_tag = re.sub(r"[^a-zA-Z0-9]", "", file_path.stem)[:6]
    transformed = transform_external_dataframe(ext_df, source_tag)

    if transformed.empty:
        print("  [SKIP] No new unique concepts to add (all already present or empty).")
        return 0

    # Append to knowledge base
    if KB_PATH.exists():
        transformed.to_csv(KB_PATH, mode="a", header=False, index=False, encoding="utf-8")
    else:
        transformed.to_csv(KB_PATH, index=False, encoding="utf-8")

    added_count = len(transformed)
    print(f"  [SUCCESS] Successfully added {added_count} new concepts to {KB_PATH.name}!")
    return added_count


def scan_and_import_all() -> int:
    """Scans data/kaggle_imports/ and imports all CSV/JSON files found."""
    if not IMPORTS_DIR.exists():
        IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Created folder: {IMPORTS_DIR}")

    files = list(IMPORTS_DIR.glob("*.csv")) + list(IMPORTS_DIR.glob("*.json"))
    if not files:
        print(f"[INFO] No files found in {IMPORTS_DIR}.")
        print("       Drop any Kaggle biology CSV files there and re-run this script!")
        return 0

    total_added = 0
    for f in files:
        total_added += import_dataset(f)
    return total_added


def retrain_search_engine_and_verify():
    """Retrains the local ConceptSearchEngine and prints test query results."""
    print("\n" + "=" * 60)
    print("[INFO] Re-indexing TF-IDF Vector Space Model with updated dataset...")
    print("=" * 60)
    try:
        from tutor_engine import get_tutor_engine
        engine = get_tutor_engine()
        engine.search_engine.load_and_fit()

        total_concepts = len(engine.search_engine.df)
        print(f"[READY] Knowledge base now contains {total_concepts} total concepts!")
        print(f"       TF-IDF vocabulary size: {len(engine.search_engine.feature_names)} n-grams")

        # Test sample queries
        test_queries = [
            "Why is brain white?",
            "Why does human heart have 4 chambers?",
            "DNA replication Meselson Stahl",
            "Mendel Law of Segregation"
        ]
        print("\n--- Running Sample Test Queries Against Local Dataset ---")
        for q in test_queries:
            matches = engine.search_engine.match_concept(q, top_k=1)
            if matches:
                top = matches[0]
                print(f"Query: \"{q}\" -> Matched: [{top['concept_id']}] {top['title']} (Cosine Sim: {top['similarity_score']:.4f})")
            else:
                print(f"Query: \"{q}\" -> No match")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"[WARNING] Could not automatically re-train engine: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BioNEET Pro Kaggle Dataset Ingestion Tool")
    parser.add_argument("file", nargs="?", help="Optional path to a specific CSV/JSON dataset file")
    args = parser.parse_args()

    print("=" * 60)
    print("BioNEET Pro - Local Dataset Ingestion Pipeline")
    print(f"Knowledge Base: {KB_PATH}")
    print(f"Drop-in Folder: {IMPORTS_DIR}")
    print("=" * 60)

    added = 0
    if args.file:
        target_path = Path(args.file)
        added = import_dataset(target_path)
    else:
        added = scan_and_import_all()

    retrain_search_engine_and_verify()
    print(f"\n[DONE] Pipeline finished. Total newly imported concepts: {added}\n")
