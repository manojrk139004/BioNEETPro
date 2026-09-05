"""
BioNEETPro - Authoritative NCERT Textbook Ingestion Pipeline
============================================================
Processes all NCERT Biology PDFs in `Textbook/`:
1. Discovers and inspects every PDF dynamically.
2. Extracts TOC from prelims PDFs (kebo1ps.pdf, lebo1ps.pdf).
3. Extracts text page-by-page with accurate NCERT printed page tracking.
4. Identifies chapter numbers, chapter titles, sections, subsections.
5. Performs semantic chunking respecting paragraph and section boundaries.
6. Extracts biological concepts and keywords per chunk.
7. Generates persistent local cache in `data/ncert_textbook_index.json`.
8. Provides index statistics and searchable interface.
"""

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf

BASE_DIR = Path(__file__).resolve().parent
TEXTBOOK_DIR = BASE_DIR / "Textbook"
DATA_DIR = BASE_DIR / "data"
INDEX_FILE = DATA_DIR / "ncert_textbook_index.json"
CACHE_CHECKSUM_FILE = DATA_DIR / "ncert_textbook_checksums.json"


class NCERTIngestionPipeline:
    """
    Robust local ingestion pipeline for NCERT Biology textbook PDFs.
    """

    STOP_WORDS = {
        "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with",
        "by", "from", "up", "about", "into", "through", "during", "before", "after",
        "above", "below", "between", "under", "is", "are", "was", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "can", "could",
        "shall", "should", "will", "would", "may", "might", "must", "it", "its",
        "this", "that", "these", "those", "they", "them", "their", "we", "our",
        "you", "your", "he", "him", "his", "she", "her", "i", "me", "my", "also",
        "which", "who", "whom", "whose", "what", "where", "when", "why", "how",
        "all", "any", "both", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
        "very", "reprint", "figure", "table", "given", "see", "shown", "called",
        "known", "biology", "chapter", "unit", "class"
    }

    def __init__(self, textbook_dir: Path = TEXTBOOK_DIR, index_file: Path = INDEX_FILE):
        self.textbook_dir = textbook_dir
        self.index_file = index_file
        self.chunks: List[Dict[str, Any]] = []
        self.chapter_toc_11: Dict[int, str] = {}
        self.chapter_toc_12: Dict[int, str] = {}
        self._load_tocs()

    def _load_tocs(self):
        """Extracts authoritative Table of Contents from prelims PDFs if available."""
        ps11 = self.textbook_dir / "kebo1ps.pdf"
        ps12 = self.textbook_dir / "lebo1ps.pdf"

        if ps11.exists():
            try:
                doc11 = pymupdf.open(ps11)
                for page in doc11:
                    txt = page.get_text()
                    matches = re.findall(r'Chapter\s*(\d+)\s*:\s*([^\n\d]+)', txt, re.IGNORECASE)
                    for num, title in matches:
                        clean_title = re.sub(r'\s+', ' ', title).strip()
                        self.chapter_toc_11[int(num)] = clean_title
                doc11.close()
            except Exception as e:
                print(f"Warning loading kebo1ps TOC: {e}")

        if ps12.exists():
            try:
                doc12 = pymupdf.open(ps12)
                for page in doc12:
                    txt = page.get_text()
                    matches = re.findall(r'Chapter\s*(\d+)\s*:\s*([^\n\d]+)', txt, re.IGNORECASE)
                    for num, title in matches:
                        clean_title = re.sub(r'\s+', ' ', title).strip()
                        self.chapter_toc_12[int(num)] = clean_title
                doc12.close()
            except Exception as e:
                print(f"Warning loading lebo1ps TOC: {e}")

    def _compute_dir_hash(self) -> str:
        """Calculates hash of all PDFs in Textbook dir to detect changes."""
        hasher = hashlib.md5()
        for pdf_path in sorted(self.textbook_dir.glob("*.pdf")):
            hasher.update(pdf_path.name.encode())
            hasher.update(str(pdf_path.stat().st_size).encode())
            hasher.update(str(pdf_path.stat().st_mtime).encode())
        return hasher.hexdigest()

    def is_cache_valid(self) -> bool:
        """Returns True if index file exists and source PDFs have not changed."""
        if not self.index_file.exists() or not CACHE_CHECKSUM_FILE.exists():
            return False
        try:
            with open(CACHE_CHECKSUM_FILE, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
            current_hash = self._compute_dir_hash()
            return saved_data.get("hash") == current_hash and saved_data.get("chunks_count", 0) > 0
        except Exception:
            return False

    def load_cached_index(self) -> bool:
        """Loads precomputed index from disk if valid."""
        if self.is_cache_valid():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                print(f"Loaded {len(self.chunks)} NCERT chunks from cache: {self.index_file.name}")
                return True
            except Exception as e:
                print(f"Error loading cache: {e}")
        return False

    def get_actual_page_number(self, page: pymupdf.Page, doc_pno: int) -> int:
        """
        Extracts the official printed NCERT page number from headers/footers.
        """
        try:
            txt = page.get_text()
            lines = [l.strip() for l in txt.split('\n') if l.strip()]
            if not lines:
                return doc_pno

            # Check first 3 lines (top of page)
            for l in lines[:3]:
                if l.isdigit():
                    num = int(l)
                    if 1 <= num <= 400:
                        return num

            # Check last 3 lines (bottom of page)
            for l in lines[-3:]:
                if l.isdigit():
                    num = int(l)
                    if 1 <= num <= 400:
                        return num
        except Exception:
            pass
        return doc_pno

    def clean_page_text(self, text: str, chapter_title: str) -> str:
        """
        Removes running headers, footers ('Reprint 2026-27'), page numbers, and artifact watermarks.
        """
        lines = text.split('\n')
        cleaned_lines = []

        chap_upper = chapter_title.upper()
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if re.search(r'reprint\s*\d{4}-\d{2}', s, re.IGNORECASE):
                continue
            if s.isdigit() and len(s) <= 3:
                continue
            if s.upper() in {"BIOLOGY", "UNIT I", "UNIT II", "UNIT III", "UNIT IV", "UNIT V",
                            "UNIT VI", "UNIT VII", "UNIT VIII", "UNIT IX", "UNIT X", chap_upper}:
                continue
            if re.match(r'^Figure\s*\d+\.\d+.*$', s) and len(s) < 60:
                continue
            cleaned_lines.append(s)

        joined = "\n".join(cleaned_lines)
        joined = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', joined)
        return joined

    def extract_keywords_and_concepts(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Extracts recognized biology concepts and key technical terms from text.
        """
        lower_text = text.lower()
        words = re.findall(r'\b[a-zA-Z]{3,}\b', lower_text)

        bio_keywords = set()
        for w in words:
            if w in self.STOP_WORDS:
                continue
            if (w.endswith("ase") or w.endswith("ose") or w.endswith("sis") or
                w.endswith("tion") or w.endswith("cyte") or w.endswith("soma") or
                w.endswith("some") or w.endswith("phyll") or w.endswith("plast") or
                w.endswith("karyote") or w.endswith("karyotic") or w.endswith("gen") or
                w.endswith("genesis") or w.endswith("phore") or w.endswith("oid")):
                bio_keywords.add(w)

        known_concepts = [
            "mitochondria", "cristae", "atp", "atp synthase", "chloroplast", "thylakoid",
            "stroma", "granum", "nucleus", "ribosome", "endoplasmic reticulum", "golgi apparatus",
            "lysosome", "vacuole", "centrosome", "chromosome", "dna", "rna", "mrna", "trna",
            "transcription", "translation", "replication", "photosynthesis", "cellular respiration",
            "glycolysis", "krebs cycle", "calvin cycle", "light reaction", "electron transport system",
            "photophosphorylation", "rubisco", "pep carboxylase", "kranz anatomy", "cell theory",
            "cell cycle", "mitosis", "meiosis", "prophase", "metaphase", "anaphase", "telophase",
            "crossing over", "pachytene", "synapsis", "homologous chromosomes", "enzyme", "substrate",
            "amino acid", "protein", "carbohydrate", "lipid", "nucleic acid", "nephron", "glomerulus",
            "loop of henle", "countercurrent mechanism", "dialysis", "heart", "cardiac cycle",
            "pacemaker", "sa node", "av node", "erythrocyte", "leukocyte", "platelet", "hemoglobin",
            "neuron", "axon", "dendrite", "synapse", "myelin sheath", "action potential", "reflex arc",
            "cerebrum", "cerebellum", "medulla", "hypothalamus", "thalamus", "forebrain", "midbrain",
            "hindbrain", "sarcomere", "actin", "myosin", "sliding filament", "troponin", "tropomyosin",
            "hormone", "endocrine", "pituitary", "thyroid", "adrenal", "insulin", "glucagon",
            "mendel", "allele", "genotype", "phenotype", "dominance", "segregation", "independent assortment",
            "linkage", "sex determination", "mutation", "pedigree", "genetic code", "lac operon",
            "human genome project", "dna fingerprinting", "darwin", "natural selection", "homologous",
            "analogous", "hardy weinberg", "speciation", "adaptive radiation", "pathogen", "immunity",
            "innate immunity", "acquired immunity", "antibody", "antigen", "allergy", "aids", "cancer",
            "recombinant dna", "restriction enzyme", "plasmid", "vector", "pcr", "gel electrophoresis",
            "transgenic", "bt cotton", "bioreactor", "ecosystem", "trophic level", "food chain",
            "energy flow", "productivity", "biodiversity", "conservation", "biosphere reserve",
            "earthworm", "pheretima", "annelida", "metamerism", "setae", "clitellum", "hirudinaria",
            "leech", "frog", "rana", "ascaris", "taenia", "plasmodium", "euglena", "paramecium"
        ]

        found_concepts = []
        for c in known_concepts:
            if re.search(r'\b' + re.escape(c) + r'\b', lower_text):
                found_concepts.append(c.title() if len(c) > 3 else c.upper())

        word_counts = {}
        for w in words:
            if w not in self.STOP_WORDS and len(w) > 3:
                word_counts[w] = word_counts.get(w, 0) + 1

        top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = list(bio_keywords.union({w for w, _ in top_words}))[:12]

        return found_concepts[:8], keywords

    def process_chapter_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Parses an individual NCERT chapter PDF into semantic chunks.
        """
        doc = pymupdf.open(pdf_path)
        filename = pdf_path.name.lower()

        is_class_11 = "kebo" in filename
        class_name = "Class XI" if is_class_11 else "Class XII"
        book_name = f"NCERT Biology {class_name}"

        m_ch = re.search(r'[a-z]+1(\d{2})', filename)
        chapter_num = int(m_ch.group(1)) if m_ch else 1

        toc_dict = self.chapter_toc_11 if is_class_11 else self.chapter_toc_12
        chapter_title = toc_dict.get(chapter_num, f"Chapter {chapter_num}")

        current_section = f"{chapter_num}.0 Overview"
        current_subsection = "Introduction"

        chunks = []
        running_text_blocks = []

        def flush_chunk():
            nonlocal running_text_blocks, chunks
            if not running_text_blocks:
                return
            chunk_text = " ".join(b[0] for b in running_text_blocks)
            if len(chunk_text.split()) < 35:
                return

            avg_page = running_text_blocks[0][1]
            sec = running_text_blocks[0][2]
            subsec = running_text_blocks[0][3]

            concepts, keywords = self.extract_keywords_and_concepts(chunk_text)
            chunk_id = f"NCERT-{class_name[:8].replace(' ', '')}-CH{chapter_num:02d}-P{avg_page:03d}-{len(chunks)+1:02d}"

            chunks.append({
                "chunk_id": chunk_id,
                "class": class_name,
                "book": book_name,
                "chapter_number": chapter_num,
                "chapter_title": chapter_title,
                "section": sec,
                "subsection": subsec,
                "page_number": avg_page,
                "text": chunk_text,
                "concepts": concepts,
                "keywords": keywords,
                "source_file": pdf_path.name
            })
            running_text_blocks = []

        # Regex for section heading matching this chapter number (e.g. 8.1, 8.5.4)
        sec_pattern = re.compile(rf'^{chapter_num}\.\d+(?:\.\d+)?(?:\.\d+)?')

        for doc_pno, page in enumerate(doc):
            actual_page = self.get_actual_page_number(page, doc_pno + 1)
            raw_text = page.get_text()
            cleaned_text = self.clean_page_text(raw_text, chapter_title)

            lines = [l.strip() for l in cleaned_text.split('\n') if l.strip()]
            i = 0
            while i < len(lines):
                line = lines[i]

                # Check if this line is a section heading
                m_sec = sec_pattern.match(line)
                if m_sec:
                    sec_code = m_sec.group(0)
                    rest = line[len(sec_code):].strip()
                    if not rest and i + 1 < len(lines) and not sec_pattern.match(lines[i+1]):
                        rest = lines[i+1].strip()
                        i += 1

                    if rest and len(rest) < 70:
                        # Flush previous section chunk
                        flush_chunk()
                        current_section = f"{sec_code} {rest}"
                        current_subsection = rest
                        i += 1
                        continue

                # Accumulate line text into paragraph
                para_lines = [line]
                while i + 1 < len(lines) and not sec_pattern.match(lines[i+1]) and not (lines[i].endswith(".") and len(lines[i+1]) > 0 and lines[i+1][0].isupper() and len(para_lines) > 4):
                    i += 1
                    para_lines.append(lines[i])

                para_text = " ".join(para_lines).strip()
                if para_text:
                    running_text_blocks.append((para_text, actual_page, current_section, current_subsection))
                    total_words = sum(len(b[0].split()) for b in running_text_blocks)
                    if total_words >= 200:
                        flush_chunk()

                i += 1

        flush_chunk()
        doc.close()
        return chunks

    def build_and_save_index(self, force: bool = False) -> Dict[str, Any]:
        """
        Executes full ingestion across all Textbook PDFs and writes persistent index.
        """
        if not force and self.load_cached_index():
            return {
                "status": "cached",
                "total_chunks": len(self.chunks),
                "index_file": str(self.index_file)
            }

        print("=== Starting NCERT Textbook Ingestion Pipeline ===")
        all_chunks = []
        pdf_files = sorted(self.textbook_dir.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files in {self.textbook_dir}")

        processed_chapters = set()

        for pdf_path in pdf_files:
            if "ps.pdf" in pdf_path.name.lower():
                continue

            try:
                ch_chunks = self.process_chapter_pdf(pdf_path)
                all_chunks.extend(ch_chunks)
                if ch_chunks:
                    c_info = f"{ch_chunks[0]['class']} - Ch {ch_chunks[0]['chapter_number']}: {ch_chunks[0]['chapter_title']}"
                    processed_chapters.add(c_info)
                    print(f"  [OK] {pdf_path.name} -> {len(ch_chunks)} chunks ({c_info})")
            except Exception as e:
                print(f"  [ERROR] Processing {pdf_path.name}: {e}")

        self.chunks = all_chunks

        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2)

        current_hash = self._compute_dir_hash()
        with open(CACHE_CHECKSUM_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "hash": current_hash,
                "chunks_count": len(self.chunks),
                "chapters_count": len(processed_chapters),
                "timestamp": str(pymupdf.__version__)
            }, f, indent=2)

        print(f"\nSuccessfully generated {len(self.chunks)} NCERT chunks across {len(processed_chapters)} chapters!")
        print(f"Saved persistent index to: {self.index_file}")

        return {
            "status": "success",
            "total_chunks": len(self.chunks),
            "chapters_count": len(processed_chapters),
            "chapters": sorted(list(processed_chapters)),
            "index_file": str(self.index_file)
        }

    def search_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Lightweight lexical + concept search across textbook chunks.
        """
        if not self.chunks:
            self.load_cached_index()

        q_lower = query.lower()
        q_tokens = set(re.findall(r'\b[a-zA-Z]{3,}\b', q_lower)) - self.STOP_WORDS

        scored = []
        for c in self.chunks:
            score = 0.0
            text_lower = c["text"].lower()
            title_lower = c["chapter_title"].lower()
            sec_lower = c["section"].lower()

            for concept in c.get("concepts", []):
                if concept.lower() in q_lower:
                    score += 4.0

            for token in q_tokens:
                if token in sec_lower:
                    score += 3.0
                elif token in title_lower:
                    score += 2.0
                elif token in text_lower:
                    score += 1.0

            if score > 0:
                scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]


ncert_ingestion = NCERTIngestionPipeline()

if __name__ == "__main__":
    result = ncert_ingestion.build_and_save_index(force=True)
    print("\nSummary Result:")
    print(f"Total Chunks: {result['total_chunks']}")
    print(f"Chapters Count: {result['chapters_count']}")
