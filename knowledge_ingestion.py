"""
BioNEETPro - Unified Knowledge Ingestion & Validation Pipeline
=============================================================
Purpose:
1. Validates and normalizes candidate biology records into the canonical 12-column schema.
2. Filters out non-biology and out-of-syllabus content.
3. Checks for duplicates against existing knowledge base titles.
4. Automatically assigns canonical chapter IDs and syllabus metadata.
5. Safely appends validated concepts to data/neet_knowledge_base.csv.
6. Re-indexes the HybridRetrievalEngine in real time.
"""

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from concept_normalizer import concept_normalizer
from syllabus import syllabus_validator

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KB_PATH = DATA_DIR / "neet_knowledge_base.csv"

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
    "explanation",
]


class KnowledgeIngestionPipeline:
    """
    Automated ingestion, validation, and deduplication pipeline for NEET Biology knowledge base.
    """

    def __init__(self, kb_path: Path = KB_PATH):
        self.kb_path = kb_path
        self.existing_titles: Set[str] = set()
        self.existing_ids: Set[str] = set()
        self._load_existing_registry()

    def _load_existing_registry(self):
        if self.kb_path.exists():
            try:
                df = pd.read_csv(self.kb_path)
                self.existing_titles = set(df["title"].dropna().str.lower().str.strip())
                self.existing_ids = set(df["concept_id"].dropna().str.strip())
            except Exception:
                pass

    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validates whether a candidate record satisfies canonical NEET Biology criteria.
        """
        title = str(record.get("title", "")).strip()
        if not title or len(title) < 3:
            return False, "Title is missing or too short."

        if title.lower() in self.existing_titles:
            return False, f"Duplicate title already in knowledge base: '{title}'"

        definition = str(record.get("definition", "")).strip()
        if not definition or len(definition) < 15:
            return False, "Definition is missing or insufficient."

        chap_name = str(record.get("chapter_name", "")).strip()
        if not chap_name:
            return False, "Chapter name is required."

        # Syllabus check
        canon_chap = syllabus_validator.get_canonical_chapter_name(chap_name)
        if not syllabus_validator.validate_concept_syllabus(title, canon_chap):
            return False, f"Concept '{title}' in '{chap_name}' failed syllabus validation."

        # Verify MCQ if present
        sample_q = str(record.get("sample_question", "")).strip()
        sample_opts = str(record.get("sample_options", "")).strip()
        if sample_q and sample_opts:
            opts = [o.strip() for o in sample_opts.split("|") if o.strip()]
            if len(opts) != 4:
                return False, f"MCQ must have exactly 4 pipe-separated options (found {len(opts)})."
            try:
                ans_idx = int(record.get("correct_answer", 0))
                if not (0 <= ans_idx <= 3):
                    return False, f"correct_answer index must be 0-3 (found {ans_idx})."
            except (ValueError, TypeError):
                return False, "correct_answer index must be an integer."

        return True, None

    def ingest_dataframe(self, df: pd.DataFrame, source_tag: str = "EXT") -> Dict[str, Any]:
        """
        Processes a dataframe of candidate records, validates each, and appends valid ones.
        """
        self._load_existing_registry()
        valid_records = []
        rejected_records = []

        for idx, row in df.iterrows():
            rec = row.to_dict()
            # Normalize chapter name
            raw_chap = str(rec.get("chapter_name", "")).strip()
            canon_chap = syllabus_validator.get_canonical_chapter_name(raw_chap)
            rec["chapter_name"] = canon_chap

            # Resolve chapter ID
            chap_id = str(rec.get("chapter_id", "")).strip()
            if not chap_id or chap_id in ("c00", "c99", "NCERT"):
                resolved_id = syllabus_validator.get_chapter_id_for_name(canon_chap)
                if resolved_id:
                    rec["chapter_id"] = resolved_id

            # Ensure concept_id
            cid = str(rec.get("concept_id", "")).strip()
            if not cid or cid in self.existing_ids:
                new_num = len(self.existing_ids) + len(valid_records) + 1
                rec["concept_id"] = f"BIO-{source_tag.upper()}-{new_num:03d}"

            is_valid, reason = self.validate_record(rec)
            if is_valid:
                valid_records.append(rec)
                self.existing_titles.add(rec["title"].lower().strip())
                self.existing_ids.add(rec["concept_id"])
            else:
                rejected_records.append({"title": rec.get("title", f"Row {idx}"), "reason": reason})

        if valid_records:
            append_df = pd.DataFrame(valid_records)[CANONICAL_COLUMNS]
            if self.kb_path.exists():
                append_df.to_csv(self.kb_path, mode="a", header=False, index=False, encoding="utf-8")
            else:
                append_df.to_csv(self.kb_path, index=False, encoding="utf-8")

            # Trigger retrieval engine re-index
            try:
                from retrieval_engine import retrieval_engine
                retrieval_engine.load_and_index()
            except Exception:
                pass

        return {
            "total_evaluated": len(df),
            "ingested_count": len(valid_records),
            "rejected_count": len(rejected_records),
            "rejections": rejected_records[:10],
            "total_knowledge_base_records": len(self.existing_titles),
        }

    def generate_coverage_report(self) -> Dict[str, Any]:
        """
        Audits current knowledge base and returns syllabus coverage statistics.
        """
        if not self.kb_path.exists():
            return {"total_records": 0, "coverage_percent": 0.0, "chapters": {}}

        df = pd.read_csv(self.kb_path)
        chap_counts = df["chapter_name"].value_counts().to_dict()

        # Check coverage of 38 official chapters
        all_canonical = set()
        for class_key, class_data in syllabus_validator.syllabus.items():
            for unit_key, unit_data in class_data.items():
                for chap_id, chap_data in unit_data["chapters"].items():
                    all_canonical.add(chap_data["chapter_name"])

        covered_chaps = set(chap_counts.keys()).intersection(all_canonical)
        missing_chaps = all_canonical - set(chap_counts.keys())
        coverage_pct = round((len(covered_chaps) / max(len(all_canonical), 1)) * 100, 1)

        return {
            "total_records": len(df),
            "total_canonical_chapters": len(all_canonical),
            "covered_chapters_count": len(covered_chaps),
            "missing_chapters_count": len(missing_chaps),
            "coverage_percent": coverage_pct,
            "chapter_distribution": chap_counts,
            "missing_chapters": sorted(list(missing_chaps)),
        }


knowledge_ingestion = KnowledgeIngestionPipeline()

if __name__ == "__main__":
    report = knowledge_ingestion.generate_coverage_report()
    print("=== BioNEETPro Knowledge Base Coverage Report ===")
    print(f"Total Concepts: {report['total_records']}")
    print(f"Covered Chapters: {report['covered_chapters_count']} / {report['total_canonical_chapters']} ({report['coverage_percent']}%)")
    if report["missing_chapters"]:
        print(f"Missing Chapters ({len(report['missing_chapters'])}):")
        for mc in report["missing_chapters"]:
            print(f"  - {mc}")
