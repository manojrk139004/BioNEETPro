"""
BioNEETPro - Authoritative Context-Aware NCERT Hybrid Retrieval Engine
======================================================================
Combines:
1. Dual-Corpus TF-IDF Vector Space Model (Knowledge Base + NCERT Textbook Chunks)
2. Canonical Concept Matching (Concept-First broad query routing)
3. Direct Keyword & Biology Synonym Overlap
4. Section & Chapter Matching
5. Conversational Context Similarity
6. Biological Ontology Concept Graph Multi-Hop Bonus
7. Full NCERT Source Traceability (Class, Chapter, Section, Page, Chunk ID)
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import unicodedata
from functools import lru_cache

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from concept_graph import concept_graph
from concept_normalizer import concept_normalizer
from syllabus import syllabus_validator

DATA_DIR = Path(__file__).resolve().parent / "data"
KB_PATH = DATA_DIR / "neet_knowledge_base.csv"
TEXTBOOK_INDEX_PATH = DATA_DIR / "ncert_textbook_index.json"


class ContextAwareHybridRetrievalEngine:
    """
    Context-aware hybrid retrieval engine searching across both structured
    NEET knowledge base records and authoritative NCERT textbook chunks.
    Now includes character-level TF-IDF fallback for adversarial robustness.
    """

    MIN_RELEVANCE_THRESHOLD = 0.05
    HIGH_CONFIDENCE_THRESHOLD = 0.30
    MEDIUM_CONFIDENCE_THRESHOLD = 0.16

    WEIGHTS = {
        'semantic': 0.35,           # TF-IDF cosine similarity
        'canonical_concept': 0.25,  # Direct canonical concept match (fixes broad queries)
        'keyword': 0.15,            # Keyword overlap in title/section
        'section_match': 0.10,      # Section / subtopic alignment
        'context': 0.05,            # Conversation context continuity
        'chapter': 0.05,            # Chapter focus compatibility
        'graph': 0.05,              # Concept graph relationship
    }

    CHAR_FALLBACK_WEIGHT = 0.30  # Character-level score weight when word-level drops
    WORD_LEVEL_DROP_THRESHOLD = 0.15  # Trigger char fallback when word cosine < this

    STOP_WORDS = {
        "what", "is", "how", "does", "the", "and", "or", "in", "of", "to", "a", "an",
        "describe", "explain", "why", "are", "which", "called",
        # NOTE: domain nouns ("human", "plant") were once listed here but are
        # discriminative in Biology ("plant" vs human hormones) and must stay
        # in the search vector. Generic meta-words below remain stopwords.
        "types",
        "function", "functions", "functional", "role", "roles", "purpose", "importance",
        "significant", "significance", "overview", "system", "tell", "give", "work", "do", "it", "its", "with", "about",
        "me", "us", "teach", "can", "please", "for", "from"
    }

    # Intent-frame verbs: topical-looking but content-free for evidence purposes.
    FRAME_WORDS = {
        "please", "explain", "describe", "discuss", "teach", "tell", "learn", "revise",
        "define", "definition", "meaning", "elaborate", "summarize", "summary",
    }

    # Generic student-query filler nouns: content-free for evidence purposes.
    EXEMPT_WORDS = {
        "something", "anything", "everything", "nothing",
        "today", "tomorrow", "doubt", "doubts", "question", "questions",
        "answer", "answers", "topic", "topics", "chapter", "chapters",
        "concept", "concepts", "thing", "things", "again", "more",
        "regarding", "concerning", "overview", "overviews", "stepwise", "steps",
        "diagram", "diagrams", "pic", "pics", "image", "images",
        "figure", "figures", "chart", "charts", "table", "tables", "video",
    }
    HINGLISH_STOPS = {
        "kya", "hai", "hain", "ka", "ki", "ke", "ko", "kaa", "kee",
        "mein", "main", "se", "par", "aur", "yeh", "yah", "tha", "thi",
        "hota", "hoti", "hote", "kar", "karna", "kaise", "kaisa", "kese",
        "bata", "batao", "samjhao", "liye", "wala", "wali", "vale",
    }

    def __init__(self, kb_path: Path = KB_PATH, textbook_path: Path = TEXTBOOK_INDEX_PATH):
        self.kb_path = kb_path
        self.textbook_path = textbook_path

        # Knowledge Base index
        self.df: pd.DataFrame = pd.DataFrame()
        self.kb_vectorizer: Optional[TfidfVectorizer] = None
        self.kb_tfidf_matrix = None
        self.feature_names: List[str] = []

        # Character-level KB index (for typo/adversarial robustness)
        self.kb_char_vectorizer: Optional[TfidfVectorizer] = None
        self.kb_char_tfidf_matrix = None

        # Textbook Chunks index
        self.textbook_chunks: List[Dict[str, Any]] = []
        self.tb_vectorizer: Optional[TfidfVectorizer] = None
        self.tb_tfidf_matrix = None

        # Character-level Textbook index
        self.tb_char_vectorizer: Optional[TfidfVectorizer] = None
        self.tb_char_tfidf_matrix = None

        self.load_and_index()

    def load_and_index(self):
        """Builds TF-IDF vector representations for both Knowledge Base and Textbook Chunks.
        Includes parallel character-level TF-IDF for adversarial robustness.
        """
        # 1. Index Knowledge Base CSV
        if self.kb_path.exists():
            try:
                self.df = pd.read_csv(self.kb_path)
                self.df.fillna("", inplace=True)
                self.df_records = self.df.to_dict(orient="records")

                kb_corpus = []
                kb_char_corpus = []
                for _, row in self.df.iterrows():
                    title = str(row.get("title", ""))
                    chap = str(row.get("chapter_name", ""))
                    topic = str(row.get("topic", ""))
                    defn = str(row.get("definition", ""))
                    mech = str(row.get("mechanism_steps", ""))
                    traps = str(row.get("neet_traps", ""))
                    keywords = str(row.get("ncert_keywords", ""))
                    sample_q = str(row.get("sample_question", ""))
                    expl = str(row.get("explanation", ""))

                    combined = (
                        f"{title} {title} {title} "
                        f"{chap} {chap} {chap} "
                        f"{topic} {topic} "
                        f"{defn} {defn} "
                        f"{mech} {traps} {keywords} "
                        # Prose evidence fields: sample questions/explanations
                        # carry topic vocabulary (e.g. pneumatophores) absent
                        # from definitions. sample_options are deliberately
                        # excluded (distractor lists would pollute matches).
                        f"{sample_q} {expl}"
                    )
                    kb_corpus.append(combined.lower())
                    kb_char_corpus.append(combined.lower())

                if kb_corpus:
                    self.kb_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=8000)
                    self.kb_tfidf_matrix = self.kb_vectorizer.fit_transform(kb_corpus)
                    self.feature_names = self.kb_vectorizer.get_feature_names_out().tolist()
                    # Character-level vectorizer for typo/adversarial robustness
                    self.kb_char_vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=12000)
                    self.kb_char_tfidf_matrix = self.kb_char_vectorizer.fit_transform(kb_char_corpus)
            except Exception as e:
                print(f"Warning loading KB in retrieval engine: {e}")

        # 2. Index Textbook Chunks JSON
        if self.textbook_path.exists():
            try:
                with open(self.textbook_path, "r", encoding="utf-8") as f:
                    self.textbook_chunks = json.load(f)

                tb_corpus = []
                tb_char_corpus = []
                for c in self.textbook_chunks:
                    c_title = c.get("chapter_title", "")
                    c_sec = c.get("section", "")
                    c_subsec = c.get("subsection", "")
                    c_concepts = " ".join(c.get("concepts", []))
                    c_keywords = " ".join(c.get("keywords", []))
                    c_text = c.get("text", "")

                    combined = (
                        f"{c_title} {c_title} {c_title} "
                        f"{c_sec} {c_sec} {c_sec} "
                        f"{c_subsec} {c_subsec} "
                        f"{c_concepts} {c_concepts} "
                        f"{c_keywords} {c_text}"
                    )
                    tb_corpus.append(combined.lower())
                    tb_char_corpus.append(combined.lower())

                if tb_corpus:
                    self.tb_vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=12000)
                    self.tb_tfidf_matrix = self.tb_vectorizer.fit_transform(tb_corpus)
                    self.tb_char_vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=18000)
                    self.tb_char_tfidf_matrix = self.tb_char_vectorizer.fit_transform(tb_char_corpus)

                for c in self.textbook_chunks:
                    c["_sec_tokens"] = set(re.findall(r"[a-z0-9]+", c.get("section", "").lower()))
                    c["_text_tokens"] = set(re.findall(r"[a-z0-9]+", c.get("text", "").lower()))
                # Pre-warm static corpus metrics
                self._raw_corpus_words()
                self._kb_word_set()
                self._stem_set()
                self._load_figure_table_cache()
            except Exception as e:
                print(f"Warning loading Textbook Chunks in retrieval engine: {e}")


    def _retrieve_kb_candidates(
        self,
        clean_query: str,
        clean_search: str,
        query_tokens: set,
        raw_tokens: set,
        canonical_concept: Optional[str],
        focus_chapter_id: Optional[str],
        focal_context_name: Optional[str],
        rare: Optional[str] = None,
        phrases: Optional[List[str]] = None,
        ultras: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves and scores candidates from structured Knowledge Base."""
        if self.df.empty or self.kb_vectorizer is None or self.kb_tfidf_matrix is None:
            return []

        query_vec = self.kb_vectorizer.transform([clean_search])
        cosine_sims = cosine_similarity(query_vec, self.kb_tfidf_matrix)[0]

        scored = []
        for idx, base_cosine in enumerate(cosine_sims):
            row = self.df_records[idx] if getattr(self, "df_records", None) is not None else self.df.iloc[idx].to_dict()
            c_id = str(row.get("concept_id", ""))
            chap_id = str(row.get("chapter_id", "")).lower()
            title = str(row.get("title", "")).lower()
            chap_name = str(row.get("chapter_name", ""))
            topic = str(row.get("topic", "")).lower()
            definition = str(row.get("definition", "")).lower()

            score = 0.0

            # 1. Semantic score
            score += float(base_cosine) * self.WEIGHTS['semantic']

            # 2. Canonical concept match (Concept-First)
            concept_matched = False
            if canonical_concept:
                canon_lower = canonical_concept.lower()
                if canon_lower in title:
                    score += self.WEIGHTS['canonical_concept']
                    concept_matched = True
                    # If broad query matches foundational overview concept directly
                    if canon_lower == title.strip() or f"{canon_lower} :" in title or f"{canon_lower} -" in title:
                        score += 0.10
                elif canon_lower in topic or canon_lower in definition:
                    score += self.WEIGHTS['canonical_concept'] * 0.6
                    concept_matched = True

            # 3. Keyword match on title (with singular/plural & synonym awareness)
            clean_title = re.sub(r"[^\w\s]", " ", title).lower()
            title_tokens = set(clean_title.split())
            meaningful = {w for w in query_tokens if w not in self.STOP_WORDS and len(w) > 2}
            matched_terms = set()
            for w in meaningful:
                if w in title_tokens:
                    matched_terms.add(w)
                elif w.endswith("s") and w[:-1] in title_tokens:
                    matched_terms.add(w)
                elif f"{w}s" in title_tokens:
                    matched_terms.add(w)
                elif w == "leaf" and "leaves" in title_tokens:
                    matched_terms.add(w)
                elif w == "leaves" and "leaf" in title_tokens:
                    matched_terms.add(w)

            if matched_terms:
                score += min(1.0, len(matched_terms) / 2.0) * self.WEIGHTS['keyword']

            # Question-type alignment (e.g. 'why' question matching 'Why...' concept)
            if clean_query.startswith("why ") and title.startswith("why "):
                score += 0.05

            # 4. Section / subtopic alignment
            if any(w in topic for w in meaningful):
                score += self.WEIGHTS['section_match']

            # 5. Conversational context continuity
            if focal_context_name and focal_context_name.lower() in (title + " " + topic + " " + chap_name.lower()):
                score += self.WEIGHTS['context']

            # 6. Chapter focus boost
            if focus_chapter_id and focus_chapter_id.lower() in chap_id:
                score += self.WEIGHTS['chapter']
            if chap_name and chap_name.lower() in clean_query:
                score += 0.25

            # 7. Concept graph bonus
            neighbors = concept_graph.get_neighbors(c_id)
            for edge in neighbors:
                tgt_words = edge["target_title"].lower().split()
                if query_tokens.intersection(set(tgt_words)):
                    score += self.WEIGHTS['graph']
                    break

            # 8. No-overlap penalty: none of the meaningful query/expansion terms
            # appear in title/topic/definition — semantically similar but unrelated.
            # (Chapter ids are NOT used: KB/textbook/normalizer numbering schemes
            # diverge, so chapter equality is unreliable. The base-similarity gate
            # protects strong TF-IDF matches from false penalties.)
            haystack = f"{title} {topic} {definition}"
            vocab_terms = {w for w in query_tokens if len(w) > 3 and w not in self.STOP_WORDS}
            if canonical_concept:
                vocab_terms.update(re.findall(r"[a-z]{4,}", canonical_concept.lower()))
            if vocab_terms and float(base_cosine) < 0.15 and not any(w in haystack for w in vocab_terms):
                score -= 0.12

            # 9. Broad-query granularity: for overview queries, narrow qualified
            # titles ("Brain Anatomy: White Matter vs Grey Matter") lose to overviews.
            if canonical_concept and self._is_broad_overview_query(clean_query, canonical_concept):
                t = title.strip()
                if ":" in t or " vs " in t:
                    qual = t.split(":")[-1].lower() if ":" in t else t
                    qual_words = set(re.findall(r"[a-z]{4,}", qual))
                    if qual_words and not qual_words.intersection(raw_tokens):
                        score -= 0.35

            # 9b. Syllabus chapter affinity for KB records
            _affkb = set(re.findall(r"[a-z]{3,}", (canonical_concept or "").lower()))
            _affkb.update(w for w in raw_tokens if len(w) > 4)
            if _affkb and self._syllabus_affinity(chap_name, _affkb):
                score += 0.15

            # 9c. Pre-threshold evidence adjustment (rare terms + phrases + ultras)
            score += self._evidence_adjust(
                str(row.get("title", "")), str(row.get("topic", "")),
                str(row.get("definition", "")), rare, phrases or [], ultras,
                chap_name)

            if score < self.MIN_RELEVANCE_THRESHOLD:
                continue

            if not syllabus_validator.validate_concept_syllabus(row.get("title", ""), chap_name):
                continue

            # Confidence determination
            confidence = "LOW"
            if score >= self.HIGH_CONFIDENCE_THRESHOLD or (concept_matched and score >= 0.22):
                confidence = "HIGH"
            elif score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
                confidence = "MEDIUM"

            source_info = f"NCERT Class 11/12 Biology, Chapter: {chap_name} ({chap_id.upper()})"

            scored.append({
                "concept_id": c_id,
                "title": row.get("title", ""),
                "chapter_id": row.get("chapter_id", ""),
                "chapter_name": chap_name,
                "topic": row.get("topic", ""),
                "definition": row.get("definition", ""),
                "mechanism_steps": row.get("mechanism_steps", ""),
                "neet_traps": row.get("neet_traps", ""),
                "raw_data": row,
                "matched_terms": list(matched_terms),
                "base_cosine": round(float(base_cosine), 4),
                "hybrid_score": round(float(score), 4),
                "confidence": confidence,
                "source": source_info,
                "origin": "knowledge_base"
            })

        return scored

    def _retrieve_textbook_candidates(
        self,
        clean_query: str,
        clean_search: str,
        query_tokens: set,
        raw_tokens: set,
        canonical_concept: Optional[str],
        focus_chapter_id: Optional[str],
        focal_context_name: Optional[str],
        rare: Optional[str] = None,
        phrases: Optional[List[str]] = None,
        ultras: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves and scores candidates from authoritative NCERT Textbook Chunks."""
        if not self.textbook_chunks or self.tb_vectorizer is None or self.tb_tfidf_matrix is None:
            return []

        query_vec = self.tb_vectorizer.transform([clean_search])
        cosine_sims = cosine_similarity(query_vec, self.tb_tfidf_matrix)[0]

        scored = []
        meaningful = {w for w in query_tokens if w not in self.STOP_WORDS and len(w) > 2}
        canon_lower = canonical_concept.lower() if canonical_concept else None
        canon_re = re.compile(r"\b" + re.escape(canon_lower) + r"\b") if canon_lower else None
        broad = self._is_broad_overview_query(clean_query, canonical_concept)
        _aff = set(re.findall(r"[a-z]{3,}", canon_lower)) if canon_lower else set()
        _aff.update(w for w in raw_tokens if len(w) > 4)
        vocab_terms = {w for w in query_tokens if len(w) > 3 and w not in self.STOP_WORDS}
        if canon_lower:
            vocab_terms.update(re.findall(r"[a-z]{4,}", canon_lower))
        _win_terms = vocab_terms

        for idx, base_cosine in enumerate(cosine_sims):
            chunk = self.textbook_chunks[idx]
            sec_tokens = chunk.get("_sec_tokens") or set()
            if base_cosine < 0.01 and not (meaningful & sec_tokens):
                if not canon_lower:
                    continue
                t_low = chunk.get("text", "").lower()
                s_low = chunk.get("section", "").lower()
                if canon_lower not in s_low and canon_lower not in t_low:
                    continue

            sec = chunk.get("section", "").lower()
            subsec = chunk.get("subsection", "").lower()
            chap_title = chunk.get("chapter_title", "").lower()
            chap_num = chunk.get("chapter_number", 1)
            chap_id = f"c{chap_num:02d}"
            text_lower = chunk.get("text", "").lower()
            concepts = [c.lower() for c in chunk.get("concepts", [])]

            score = 0.0

            # 1. Semantic score
            score += float(base_cosine) * self.WEIGHTS['semantic']

            # 2. Canonical concept match (general mechanism — no per-query hardcodes).
            # Granularity (broad overview vs narrow subsection) is handled once in
            # the unified rule below, not scattered per branch.
            concept_matched = False
            canon_structural = False
            broad = self._is_broad_overview_query(clean_query, canonical_concept)
            depth = self._section_depth(sec)
            if canon_lower:
                sec_text = f"{sec} {subsec}"
                if canon_re.search(sec_text):
                    score += self.WEIGHTS['canonical_concept'] * 1.2
                    concept_matched = True
                    canon_structural = True
                    # Broad foundational query alignment (e.g. 'what is a cell' -> '8.1 what is a cell?')
                    if f"what is a {canon_lower}" in sec or f"what is {canon_lower}" in sec or f"overview of {canon_lower}" in sec:
                        score += 0.35
                    else:
                        score += 0.15
                elif canon_lower in sec_text:
                    # Substring-only (e.g. 'brain' inside 'hindbrain'): related but not the topic.
                    score += self.WEIGHTS['canonical_concept'] * 0.5
                    concept_matched = True
                    canon_structural = True
                elif canon_lower in concepts or canon_lower in text_lower:
                    concept_matched = True
                    if canon_lower in concepts:
                        # Concept-tagged section: structural topicality signal.
                        score += self.WEIGHTS['canonical_concept'] * 0.6
                        canon_structural = True
                    else:
                        # Body-text mention only: scale by mention frequency so a
                        # dedicated discussion (central neural: 'brain' x10)
                        # outranks an incidental passing mention (breathing
                        # overview name-dropping 'locomotion and movement').
                        # A dense sustained discussion counts as structural for
                        # granularity purposes.
                        occ = text_lower.count(canon_lower)
                        score += min(0.25, 0.05 * max(1, occ))
                        if occ >= 5:
                            canon_structural = True
                else:
                    # Canonical concept absent from section, concepts and text:
                    # likely a semantically-similar-but-unrelated chunk — penalize.
                    score -= 0.12

            # 2b. Unified broad-query granularity: overview sections preferred,
            # deep subsections demoted — for overview-style queries only.
            if broad:
                if depth <= 2 and canon_structural:
                    score += 0.15
                elif depth >= 3:
                    score -= 0.20

            # 3. Keyword exact match on section and chapter title
            sec_tokens = chunk.get("_sec_tokens")
            if sec_tokens is None:
                sec_tokens = set(re.sub(r"[^\w\s]", " ", sec).split())
            overlap = meaningful.intersection(sec_tokens)
            if overlap:
                score += min(1.0, len(overlap) / 2.0) * self.WEIGHTS['keyword']

            # 4. Section match
            if any(w in sec for w in meaningful):
                score += self.WEIGHTS['section_match']

            # Content sentence match for mechanism/why inquiries
            text_tokens = chunk.get("_text_tokens")
            if text_tokens is None:
                text_tokens = set(re.sub(r"[^\w\s]", " ", text_lower).split())
            text_meaningful = meaningful
            text_matches = text_meaningful.intersection(text_tokens)
            if ("used" in text_meaningful or "utilised" in text_meaningful) and ("utilised" in text_tokens or "utilize" in text_tokens or "used" in text_tokens):
                text_matches.add("used")
            if len(text_matches) >= 3:
                score += min(0.18, (len(text_matches) - 2) * 0.06)

            # 5. Conversational context continuity
            if focal_context_name and focal_context_name.lower() in (sec + " " + text_lower):
                score += self.WEIGHTS['context']

            # 6. Chapter focus boost
            if focus_chapter_id and focus_chapter_id.lower() in chap_id:
                score += self.WEIGHTS['chapter']
            if chap_title and chap_title in clean_query:
                score += 0.25

            # 6b. Syllabus chapter affinity (authoritative ownership signal)
            if _aff and self._syllabus_affinity(chap_title, _aff):
                score += 0.15

            # 7. No-overlap penalty
            haystack = f"{sec} {subsec} {chap_title} {' '.join(concepts)} {text_lower[:2000]}"
            if vocab_terms and float(base_cosine) < 0.15 and not any(w in haystack for w in vocab_terms):
                score -= 0.12

            # 7b. Pre-threshold evidence adjustment (rare terms + phrases + ultras)
            score += self._evidence_adjust(
                f"{chunk.get('chapter_title', '')} — {chunk.get('section', '')}",
                chunk.get("subsection", chunk.get("section", "")),
                chunk.get("text", ""), rare, phrases or [], ultras,
                chap_title)

            if score < self.MIN_RELEVANCE_THRESHOLD:
                continue

            confidence = "LOW"
            if score >= self.HIGH_CONFIDENCE_THRESHOLD or (concept_matched and score >= 0.20):
                confidence = "HIGH"
            elif score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
                confidence = "MEDIUM"

            source_info = (
                f"NCERT {chunk.get('class', 'Class XI')} Biology, "
                f"Chapter {chap_num}: {chunk.get('chapter_title', '')}, "
                f"Section: {chunk.get('section', '')}, Page: {chunk.get('page_number', 'N/A')}"
            )

            _win_terms = {w for w in query_tokens if len(w) > 3 and w not in self.STOP_WORDS}
            if canonical_concept:
                _win_terms.update(re.findall(r"[a-z]{4,}", canonical_concept.lower()))

            scored.append({
                "concept_id": chunk.get("chunk_id", ""),
                "title": f"{chunk.get('chapter_title', '')} — {chunk.get('section', '')}",
                "chapter_id": chap_id,
                "chapter_name": chunk.get("chapter_title", ""),
                "topic": chunk.get("subsection", chunk.get("section", "")),
                "definition": chunk.get("text", ""),
                "mechanism_steps": self._best_window(chunk.get("text", ""), _win_terms),
                "neet_traps": f"NCERT Class {chunk.get('class', '')} core syllabus fact.",
                "page_number": chunk.get("page_number"),
                "section": chunk.get("section"),
                "chunk_id": chunk.get("chunk_id"),
                "raw_data": chunk,
                "matched_terms": list(overlap),
                "base_cosine": round(float(base_cosine), 4),
                "hybrid_score": round(float(score), 4),
                "confidence": confidence,
                "source": source_info,
                "origin": "textbook_pdf",
                "_canon_section_exact": bool(canonical_concept) and bool(re.search(
                    r'\b' + re.escape(canonical_concept.lower()) + r'\b',
                    f"{sec} {subsec}")),
                "_canon_text_only": bool(canonical_concept) and (
                    canonical_concept.lower() in text_lower
                    or canonical_concept.lower() in " ".join(concepts)),
            })

        # Cross-candidate exactness: when some chunk's SECTION is dedicated to the
        # resolved concept, chunks mentioning it only in body text are demoted.
        # (General rule — resolves overview-vs-dedicated ties like Photosynthesis
        #  overview vs the dedicated GLYCOLYSIS section for glycolysis queries.)
        if canonical_concept and any(c.get("_canon_section_exact") for c in scored):
            for c in scored:
                if not c.get("_canon_section_exact") and c.get("_canon_text_only"):
                    c["hybrid_score"] = round(float(c["hybrid_score"]) - 0.15, 4)
        for c in scored:
            c.pop("_canon_section_exact", None)
            c.pop("_canon_text_only", None)

        return scored

    # ---------- Beast additions: rewrite / comparison / BM25-boost / figures ----------
    def _section_depth(self, section: str) -> int:
        """Depth of an NCERT numbered section: '18.4' -> 2 (overview), '18.4.3' -> 3 (narrow)."""
        m = re.match(r"\s*(\d+(?:\.\d+)*)", section or "")
        if not m:
            return 2
        return len(m.group(1).split("."))

    def _is_broad_overview_query(self, clean_query: str, canonical_concept: Optional[str]) -> bool:
        """Short 'teach me about X / what is X / explain X' queries want overview evidence."""
        if not canonical_concept:
            return False
        tokens = clean_query.split()
        if len(tokens) > 7:
            return False
        return bool(re.search(
            r"\b(teach|tell|explain|describe|what is|what are|define|overview|learn|guide|discuss)\b",
            clean_query))

    def _syllabus_chapter_keywords(self) -> Dict[str, str]:
        """Authoritative chapter name (normalized) -> keywords blob, built once."""
        if getattr(self, "_chap_kw", None) is None:
            blob: Dict[str, str] = {}
            for _cls in syllabus_validator.syllabus.values():
                for _unit in _cls.values():
                    for _cdata in _unit.get("chapters", {}).values():
                        norm = re.sub(r"[^a-z0-9]", "", _cdata.get("chapter_name", "").lower())
                        blob[norm] = " ".join(_cdata.get("keywords", [])).lower()
            self._chap_kw = blob
        return self._chap_kw

    def _syllabus_affinity(self, chap_title: str, terms) -> bool:
        """True when the authoritative syllabus keywords of this chapter own any
        of the given terms (canonical concept words + long query words)."""
        norm = re.sub(r"[^a-z0-9]", "", (chap_title or "").lower())
        kws = self._syllabus_chapter_keywords().get(norm, "")
        if not kws:
            return False
        return any(t in kws for t in terms)

    def _core_term(self, side: str) -> str:
        """Trim a comparison side ('phloem tissues including their structure ...') to its core concept."""
        s = re.sub(r"[^\w\s]", " ", side or "").strip()
        s_compact = re.sub(r"\s+", " ", s)
        # Prefer the longest known concept alias contained in the side (general, vocabulary-driven).
        best = ""
        low = f" {s_compact.lower()} "
        for alias in concept_normalizer.CONCEPT_ALIASES:
            if len(alias) >= 3 and f" {alias.lower()} " in low and len(alias) > len(best):
                best = alias
        if best:
            return best
        # Fallback: drop generic tail words, keep leading content words.
        tail = {"tissues", "tissue", "including", "their", "its", "structure", "structures",
                "function", "functions", "detail", "details", "detailed", "plants", "plant",
                "animals", "animal", "human", "cell", "cells", "types", "type", "process"}
        words = [w for w in s_compact.split() if w.lower() not in tail]
        return " ".join(words[:3]) if words else s_compact
    COMPARISON_RE = re.compile(
        r"\b(difference between|differences between|difference of|differentiate between|distinguish between|compare|contrast|versus|\bvs\b)\b(.+?)\b(and|vs\.?|versus|with)\b(.+)",
        re.IGNORECASE,
    )
    # "How are A and B different/compared/distinguished" comparison form.
    HOW_DIFF_RE = re.compile(
        r"\bhow\s+(are|is|do|does)\b(.+?)\b(and|vs\.?|versus|with|from)\b(.+?)\b(differ\w*|compar\w*|distinguish\w*)\b",
        re.IGNORECASE,
    )
    # Bare "A vs B" / "A versus B" without a leading keyword (e.g. "aerobic vs anaerobic respiration")
    BARE_VS_RE = re.compile(r"^\s*(.+?)\s+\bvs\.?\b\s+(.+?)\s*$", re.IGNORECASE)

    def rewrite_query(self, query: str) -> str:
        """Lightweight query rewriting: expand aliases, normalize why/compare phrasing."""
        q = (query or "").strip()
        canon = concept_normalizer.get_canonical_concept_name(q)
        if canon and canon.lower() not in q.lower():
            q = f"{q} ({canon})"
        q = re.sub(r"\bwhy\s+(is|are|does|do)\b", "reason mechanism function", q, flags=re.IGNORECASE)
        return q

    SHORT_TERM_EXPANSION = {
        "c3": "C3 Calvin cycle", "c4": "C4 Hatch Slack Kranz anatomy",
        "c2": "C2 photorespiration", "dna": "DNA", "rna": "RNA",
    }

    def _expand_short(self, term: str) -> str:
        t = (term or "").strip()
        key = re.sub(r"\s+", " ", t).lower()
        if key in self.SHORT_TERM_EXPANSION:
            return self.SHORT_TERM_EXPANSION[key]
        # Bare single letters/digits (e.g. "C3") gain their canonical concept name
        canon = concept_normalizer.get_canonical_concept_name(t)
        if canon and canon.lower() not in t.lower():
            return f"{t} {canon}"
        return t

    def split_comparison(self, query: str):
        for rx in (self.COMPARISON_RE, self.HOW_DIFF_RE):
            m = rx.search(query or "")
            if not m:
                continue
            a = re.sub(r"[^\w\s]", " ", m.group(2)).strip()
            b = re.sub(r"[^\w\s]", " ", m.group(4)).strip()
            break
        else:
            m = None
            a = b = None
        if not m:
            m2 = self.BARE_VS_RE.search(query or "")
            if m2:
                a = re.sub(r"[^\w\s]", " ", m2.group(1)).strip()
                b = re.sub(r"[^\w\s]", " ", m2.group(2)).strip()
            else:
                return None
        a = self._core_term(a)
        b = self._core_term(b)
        if len(a) < 2 or len(b) < 2:
            return None
        return self._expand_short(a), self._expand_short(b)

    def _bm25_boost(self, query_tokens: set, title: str, topic: str) -> float:
        """Cheap BM25-style exact-phrase/rarity boost without new deps."""
        t = f"{title} {topic}".lower()
        if not query_tokens or not t:
            return 0.0
        hit = sum(1 for w in query_tokens if len(w) > 2 and w not in self.STOP_WORDS and w in t)
        # Rare-term bonus: longer matched terms count more
        bonus = sum(min(len(w), 10) / 10.0 for w in query_tokens if len(w) > 3 and w in t)
        return min(0.12, hit * 0.03 + bonus * 0.02)

    def _load_figure_table_cache(self):
        self._figs_by_chap = defaultdict(list)
        self._tabs_by_chap = defaultdict(list)
        p1 = DATA_DIR / "ncert_figures_index.json"
        if p1.exists():
            try:
                with open(p1, encoding="utf-8") as fh:
                    for item in json.load(fh):
                        ch = item.get("chapter_number")
                        if ch is not None:
                            self._figs_by_chap[ch].append(item)
            except Exception:
                pass
        p2 = DATA_DIR / "ncert_tables_index.json"
        if p2.exists():
            try:
                with open(p2, encoding="utf-8") as fh:
                    for item in json.load(fh):
                        ch = item.get("chapter_number")
                        if ch is not None:
                            self._tabs_by_chap[ch].append(item)
            except Exception:
                pass

    def _attach_figures_tables(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        """Attach figure captions + tables for the record's chapter (pre-cached index)."""
        try:
            ch_raw = str(rec.get("chapter_id", ""))
            m = re.search(r"(\d+)", ch_raw)
            ch_num = int(m.group(1)) if m else None
            if ch_num is None:
                return rec
            if not hasattr(self, "_figs_by_chap"):
                self._load_figure_table_cache()
            figs = self._figs_by_chap.get(ch_num, [])[:2]
            tabs = self._tabs_by_chap.get(ch_num, [])[:1]
            if figs:
                rec["figures"] = figs
            if tabs:
                rec["tables"] = tabs
        except Exception:
            pass
        return rec

    def _term_holds(self, hay: str, term: str) -> bool:
        """Word-boundary term presence (singular/plural + morphological
        variants aware: 'secreted' matches 'secretion')."""
        vars_set = self._morph_variants(term)
        if not any(v in hay for v in vars_set):
            return False
        return any(re.search(r"(?<!\w)" + re.escape(v) + r"(?!\w)", hay)
                   for v in vars_set)

    def _term_holds_ultra(self, hay: str, term: str) -> bool:
        """Ultra-term presence: boundary/morph/space-folded matches PLUS
        compound-tail matches ('dialysis' in 'hemodialysis', 'juxtaglomerular'
        in 'juxta glomerular'). Ultra terms are long technical words where
        such matches are almost always the concept itself."""
        if self._term_holds(hay, term):
            return True
        vars_set = self._morph_variants(term)
        for v in vars_set:
            if v in hay and re.search(re.escape(v) + r"\b", hay):
                return True
        if term in hay:
            return True
        if " " in term and term.replace(" ", "") in hay:
            return True
        return False

    def _best_window(self, text: str, terms, width: int = 550) -> str:
        """Most query-relevant text window (presentation): centers the reply
        snippet on the sentence with the most query-term hits instead of
        always showing the chunk start."""
        if not text or len(text) <= width:
            return text
        terms = [t.lower() for t in (terms or []) if t]
        if not terms:
            return text[:width] + "..."
        sents = re.split(r"(?<=[.!?])\s+", text)
        best_i, best_score = 0, -1
        for i, s in enumerate(sents):
            sl = s.lower()
            sc = sum(1 for t in terms if t in sl)
            if sc > best_score:
                best_score, best_i = sc, i
        if best_score <= 0:
            return text[:width] + "..."
        start = max(0, sum(len(s) + 1 for s in sents[:best_i]) - 150)
        window = text[start:start + width].strip()
        return (("..." if start > 0 else "") + window + ("..." if start + width < len(text) else ""))

    def _evidence_adjust(self, title: str, topic: str, definition: str,
                         rares: Optional[List[str]], phrases: List[str],
                         ultras: Optional[List[str]] = None,
                         chap_title: str = "") -> float:
        """Pre-threshold evidence adjustment (general mechanism): holders of
        ANY rarest term +0.15, holders of ALL of them +0.10 extra; holders of
        an ultra-rare term +0.15 extra ONLY in the term's owning chapter (so a
        stray word-match in an absurd chapter is not promoted); multi-word
        concept-phrase joint presence +0.20. Demotions happen post-filter and
        only when an owning-chapter holder survived."""
        if not rares and not ultras and not phrases:
            return 0.0
        adj = 0.0
        hay = f"{title} {topic} {definition}".lower()
        if rares:
            held = [t for t in rares if self._term_holds(hay, t)]
            if held:
                adj += 0.15
                if len(held) == len(rares):
                    adj += 0.10
        if ultras:
            for t in ultras:
                if self._syllabus_affinity(chap_title, {t}) and self._term_holds_ultra(hay, t):
                    adj += 0.15
                    break
        for ph in phrases or []:
            if re.search(r"(?<!\w)" + re.escape(ph.lower()) + r"(?!\w)", hay):
                adj += 0.20
        return round(adj, 4)

    def _phrase_hits(self, clean_query: str) -> List[str]:
        """Multi-word concept-vocabulary phrases present in the query."""
        qc = f" {(clean_query or '').lower()} "
        hits = []
        for alias in concept_normalizer.CONCEPT_ALIASES:
            if len(alias.split()) >= 2 and f" {alias.lower()} " in qc:
                hits.append(alias.lower())
        return sorted(set(hits), key=len, reverse=True)[:3]

    def _content_vector_tokens(self, text: str):
        """Content-only tokens for the similarity vector: drops intent-frame
        words ('function', 'role', 'explain'), fillers and the ultra-generic
        plural 'cells' (present in hundreds of chunks; it lets 'Sertoli cells'
        match cell biology instead of spermatogenesis). Kept OUT of the
        TF-IDF query so frame words cannot inflate similarity with long
        texts that merely repeat them (e.g. Golgi 'function' density)."""
        return [t for t in (text or "").lower().split()
                if t not in self.STOP_WORDS and t not in self.FRAME_WORDS
                and t not in self.HINGLISH_STOPS and t not in self.EXEMPT_WORDS
                and t != "cells"]

    @lru_cache(maxsize=2048)
    def _morph_variants(self, tok: str):
        """Generous morphological variants for recall ('secreted' ->
        'secretion'/'secrete'; 'formation' -> 'form'). Unknown variants are
        ignored by the TF-IDF vocabulary, so over-generation is safe."""
        out = {tok}
        # Singular/plural symmetry at every length ("kreb"<->"krebs"): short
        # query terms need plural variants most; other derivations stay
        # behind the length guard below.
        if tok.endswith("s") and not tok.endswith("ss"):
            out.add(tok[:-1])
        else:
            out.add(tok + "s")
        if len(tok) <= 4:
            return {v for v in out if len(v) >= 3}
        if tok.endswith("ed"):
            b = tok[:-2]
            out.update({b, b + "e", b + "ion"})
        elif tok.endswith("ing"):
            b = tok[:-3]
            out.update({b, b + "e"})
        elif tok.endswith("ation"):
            out.add(tok[:-5])
        elif tok.endswith("ion"):
            out.update({tok[:-3] + "e", tok[:-3]})
        elif tok.endswith("ly"):
            out.add(tok[:-2])
        # Verb -> noun derivations (replicate->replication, translate->
        # translation, fertilize->fertilization): queries phrase processes as
        # verbs while NCERT text uses nominal forms, and vice versa.
        if tok.endswith("e") and len(tok) > 4:
            out.add(tok[:-1] + "ion")
        if tok.endswith("ate") and len(tok) > 5:
            out.add(tok[:-3] + "ation")
        return {v for v in out if len(v) >= 3}

    def _porter(self, w: str) -> str:
        """Compact Porter stemmer for support-check normalization
        ('reductional'/'reduction' -> 'reduct', 'conductor'/'conduction' ->
        'conduct'). Used only for evidence-support gating, not ranking."""
        if len(w) <= 3:
            return w
        vowels = set("aeiou")

        def has_vowel(s):
            return any(c in vowels for c in s)

        def measure(s):
            m, prev_v = 0, False
            for c in s:
                is_v = c in vowels or (c == "y" and prev_v is False and False) or False
                if c == "y":
                    is_v = not prev_v
                if is_v:
                    prev_v = True
                else:
                    if prev_v:
                        m += 1
                    prev_v = False
            return m

        def ends(s, suf):
            return s.endswith(suf)
        # Step 1a/1b
        if ends(w, "sses"):
            w = w[:-2]
        elif ends(w, "ies"):
            w = w[:-2]
        elif ends(w, "ss"):
            pass
        elif ends(w, "s") and has_vowel(w[:-1]):
            w = w[:-1]
        if ends(w, "eed"):
            if measure(w[:-3]) > 0:
                w = w[:-1]
        elif ends(w, "ed"):
            if has_vowel(w[:-2]):
                w = w[:-2]
                if ends(w, "at") or ends(w, "bl") or ends(w, "iz"):
                    w += "e"
        elif ends(w, "ing"):
            if has_vowel(w[:-3]):
                w = w[:-3]
                if ends(w, "at") or ends(w, "bl") or ends(w, "iz"):
                    w += "e"
        # Step 2-4 (common derivational)
        for suf, rep, cond in (("ational", "ate", 0), ("tional", "tion", 0),
                               ("enci", "ence", 0), ("anci", "ance", 0),
                               ("izer", "ize", 0), ("bli", "ble", 0),
                               ("alli", "al", 0), ("entli", "ent", 0),
                               ("eli", "e", 0), ("ousli", "ous", 0),
                               ("ization", "ize", 0), ("ation", "ate", 0),
                               ("ator", "ate", 0), ("alism", "al", 0),
                               ("iveness", "ive", 0), ("fulness", "ful", 0),
                               ("ousness", "ous", 0), ("aliti", "al", 0),
                               ("iviti", "ive", 0), ("biliti", "ble", 0),
                               ("icate", "ic", 0), ("ative", "", 0),
                               ("alize", "al", 0), ("iciti", "ic", 0),
                               ("ical", "ic", 0), ("ful", "", 0),
                               ("ness", "", 0), ("al", "", 1),
                               ("ance", "", 1), ("ence", "", 1),
                               ("er", "", 1), ("ic", "", 1),
                               ("able", "", 1), ("ible", "", 1),
                               ("ant", "", 1), ("ement", "", 1),
                               ("ment", "", 1), ("ent", "", 1),
                               ("ou", "", 1), ("ism", "", 1),
                               ("ate", "", 1), ("iti", "", 1),
                               ("ous", "", 1), ("ive", "", 1),
                               ("ize", "", 1)):
            if ends(w, suf) and measure(w[:-len(suf)]) > cond:
                w = w[:-len(suf)] + rep
                break
        if ends(w, "e") and (measure(w[:-1]) > 1 or (measure(w[:-1]) == 1 and not w[:-1][-1] in vowels)):
            w = w[:-1]
        if measure(w) > 1 and len(w) > 3 and w[-1] == w[-2] and w[-1] not in "lsz":
            w = w[:-1]
        return w

    def _raw_corpus_words(self) -> Dict[str, int]:
        """Word -> chunk count over RAW textbook text (no max_features cutoff)."""
        if getattr(self, "_raw_wc", None) is None:
            wc: Dict[str, int] = {}
            try:
                for c in self.textbook_chunks:
                    words = set(re.findall(r"[a-z]{3,}", (c.get("section", "") + " " + c.get("text", "")).lower()))
                    for wd in words:
                        wc[wd] = wc.get(wd, 0) + 1
            except Exception:
                pass
            self._raw_wc = wc
        return self._raw_wc

    def _kb_word_set(self) -> set:
        if getattr(self, "_kb_ws", None) is None:
            try:
                # All KB text fields: the TF-IDF index covers title, chapter,
                # topic, definition, mechanism, traps and keywords, so the
                # support gate must reflect the same vocabulary (a term living
                # only in mechanism_steps/sample text is still retrievable).
                blob = " ".join(
                    str(r.get("title", "")) + " " + str(r.get("topic", ""))
                    + " " + str(r.get("definition", ""))
                    + " " + str(r.get("mechanism_steps", ""))
                    + " " + str(r.get("neet_traps", ""))
                    + " " + str(r.get("sample_question", ""))
                    + " " + str(r.get("explanation", ""))
                    for _, r in self.df.iterrows()).lower()
                self._kb_ws = set(re.findall(r"[a-z]{3,}", blob))
            except Exception:
                self._kb_ws = set()
        return self._kb_ws

    def _stem_set(self) -> set:
        if getattr(self, "_stem_cache", None) is None:
            try:
                vocab = set(self.tb_vectorizer.vocabulary_.keys()) if self.tb_vectorizer is not None else set()
                vocab |= self._kb_word_set()
                self._stem_cache = {self._porter(w) for w in vocab}
            except Exception:
                self._stem_cache = set()
        return self._stem_cache

    def _word_variants(self, w: str):
        vs = {w}
        if len(w) > 4:
            if w.endswith("s") and not w.endswith("ss"):
                vs.add(w[:-1])
            else:
                vs.add(w + "s")
        return vs

    def _kb_vocab(self) -> dict:
        """Cached KB TF-IDF vocabulary set."""
        try:
            return set(self.kb_vectorizer.vocabulary_.keys()) if self.kb_vectorizer is not None else set()
        except Exception:
            return set()

    def _has_support(self, word: str) -> bool:
        """True when evidence for this word may exist: raw textbook text, KB
        text, singular/plural variants, Porter-stem match, or the known
        concept-vocabulary (e.g. 'glycolytic' via 'glycolytic pathway')."""
        w = (word or "").lower()
        if not w:
            return False
        if w in self._raw_corpus_words() or w in self._kb_word_set():
            return True
        for v in self._word_variants(w):
            if v in self._raw_corpus_words() or v in self._kb_word_set():
                return True
        if getattr(self, "_alias_words", None) is None:
            aws = set()
            for _alias in concept_normalizer.CONCEPT_ALIASES:
                for _w in re.findall(r"[a-z]{3,}", _alias.lower()):
                    aws.add(_w)
            self._alias_words = aws
        if w in self._alias_words:
            return True
        try:
            return self._porter(w) in self._stem_set()
        except Exception:
            return False

    def _content_terms(self, clean_query: str):
        """Topical content words: alpha, len>=3, not stopwords (custom, sklearn
        english, Hinglish fillers), not frame verbs."""
        try:
            from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as _SK
        except Exception:
            _SK = set()
        return [w for w in re.findall(r"[a-z]{3,}", (clean_query or "").lower())
                if w not in self.STOP_WORDS and w not in self.FRAME_WORDS
                and w not in self.HINGLISH_STOPS and w not in self.EXEMPT_WORDS
                and w not in _SK]

    def _rarest_term(self, clean_query: str):
        """Rarest corpus-supported topical term (TF-IDF idf as rarity proxy)."""
        terms = self._content_terms(clean_query)
        ranked = []
        for t in terms:
            if not self._has_support(t):
                continue
            idf = 99.0
            try:
                if self.tb_vectorizer is not None and t in self.tb_vectorizer.vocabulary_:
                    idf = float(self.tb_vectorizer.idf_[self.tb_vectorizer.vocabulary_[t]])
            except Exception:
                pass
            ranked.append((idf, t))
        ranked.sort(reverse=True)
        return ranked[0][1] if ranked else None

    def _ultra_terms(self, clean_query: str):
        """Query terms occurring in <=3 textbook chunks AND at least 7 chars:
        ultra-specific technical definienda ('juxtaglomerular', 'chloride',
        'dialysis', 'cristae', 'sertoli'). Short words ('shift', 'salty')
        are ordinary English that merely happens to be rare in NCERT — they
        must not trigger exclusivity. When any surviving candidate contains
        such a term in its owning chapter, candidates lacking it are demoted
        even if they hold other query terms."""
        out = []
        for t in self._content_terms(clean_query):
            if len(t) < 7 or not self._has_support(t):
                continue
            try:
                if self._raw_corpus_words().get(t, 0) <= 3:
                    out.append(t)
            except Exception:
                pass
        return out

    def _rarest_terms(self, clean_query: str, k: int = 2):
        """Top-k rarest supported topical terms. Evidence holders of EITHER are
        promoted; only candidates holding NEITHER are demoted — so 'root
        pressure' is not hijacked by 'pressure' alone, nor 'test cross' by
        'test' alone."""
        terms = self._content_terms(clean_query)
        ranked = []
        for t in terms:
            if not self._has_support(t):
                continue
            idf = 99.0
            try:
                if self.tb_vectorizer is not None and t in self.tb_vectorizer.vocabulary_:
                    idf = float(self.tb_vectorizer.idf_[self.tb_vectorizer.vocabulary_[t]])
            except Exception:
                pass
            ranked.append((idf, t))
        ranked.sort(reverse=True)
        seen, out = set(), []
        for _, t in ranked:
            if t not in seen:
                seen.add(t)
                out.append(t)
            if len(out) >= k:
                break
        return out

    def _unsupported_head(self, clean_query: str):
        """Topical head term with ZERO corpus support. Short words (<7 chars)
        are exempt — ordinary English ('salty', 'want', 'lubb') is often absent
        from NCERT text without implying missing evidence; long technical heads
        ('haversian', 'photoperiodism', 'periderm') with no support mean any
        answer would be fabricated."""
        terms = self._content_terms(clean_query)
        for t in sorted(set(terms), key=lambda x: (len(x), x)):
            if len(t) >= 7 and not self._has_support(t):
                return t
        return None

    def _single_search(
        self, query: str, expanded_query: Optional[str], top_k: int,
        focus_chapter_id: Optional[str], focal_context_name: Optional[str],
    ) -> List[Dict[str, Any]]:
        if query:
            query = unicodedata.normalize('NFKC', str(query))
            homoglyphs = str.maketrans({
                '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p', '\u0441': 'c', '\u0443': 'y', '\u0445': 'x',
                '\u0456': 'i', '\u0458': 'j', '\u0455': 's', '\u0410': 'A', '\u0412': 'B', '\u0415': 'E', '\u041a': 'K',
                '\u041c': 'M', '\u041d': 'H', '\u041e': 'O', '\u0420': 'P', '\u0421': 'C', '\u0422': 'T', '\u0425': 'X',
                '\u03bf': 'o', '\u03bd': 'v', '\u03c1': 'p'
            })
            query = query.translate(homoglyphs)
            query = re.sub(r"[\u200b-\u200d\ufeff\u0000-\u001f\u007f-\u009f]", "", query)
        clean_query = concept_normalizer.correct_typos(re.sub(r"[^\w\s]", " ", query).lower())
        # Zero-evidence gate: the head topical term has no corpus support at all
        # (e.g. 'haversian', 'photoperiodism', 'periderm'). Answering anyway can
        # only produce an unrelated answer — refuse instead (general rule).
        if self._unsupported_head(clean_query):
            return []
        rewritten = self.rewrite_query(expanded_query or query)
        # Content-only vector: frame/filler words and 'cells' are stripped so
        # they cannot inflate TF-IDF similarity (see _content_vector_tokens).
        _vec_toks = self._content_vector_tokens(clean_query) + self._content_vector_tokens(
            re.sub(r"[^\w\s]", " ", rewritten).lower())
        _morphs: set = set()
        for _tok in _vec_toks:
            _morphs.update(self._morph_variants(_tok))
        clean_search = f"{' '.join(_vec_toks)} {' '.join(_vec_toks)} {' '.join(sorted(_morphs))}".strip()

        canonical_concept = concept_normalizer.get_canonical_concept_name(query)
        if canonical_concept and canonical_concept.lower() not in clean_search:
            clean_search += f" {canonical_concept.lower()}"

        query_tokens = set(clean_search.split())
        raw_tokens = set(clean_query.split())
        # Evidence signals computed once, applied pre-threshold inside scoring.
        _rares = self._rarest_terms(clean_query)
        _phrases = self._phrase_hits(clean_query)
        _ultras = self._ultra_terms(clean_query)

        kb_results = self._retrieve_kb_candidates(
            clean_query, clean_search, query_tokens, raw_tokens,
            canonical_concept, focus_chapter_id, focal_context_name,
            _rares, _phrases, _ultras,
        )
        tb_results = self._retrieve_textbook_candidates(
            clean_query, clean_search, query_tokens, raw_tokens,
            canonical_concept, focus_chapter_id, focal_context_name,
            _rares, _phrases, _ultras,
        )

        # Character-level fallback: if word-level cosine is low, blend in char-level scores
        combined = kb_results + tb_results
        if combined:
            # Compute word-level max cosine for trigger decision
            word_cosines = [r.get("base_cosine", 0) for r in combined]
            max_word_cosine = max(word_cosines) if word_cosines else 0.0
            
            if max_word_cosine < self.WORD_LEVEL_DROP_THRESHOLD and self.kb_char_vectorizer and self.tb_char_vectorizer:
                # Compute character-level scores for all candidates
                char_query_vec_kb = self.kb_char_vectorizer.transform([clean_search])
                char_cosines_kb = cosine_similarity(char_query_vec_kb, self.kb_char_tfidf_matrix)[0]
                
                char_query_vec_tb = self.tb_char_vectorizer.transform([clean_search])
                char_cosines_tb = cosine_similarity(char_query_vec_tb, self.tb_char_tfidf_matrix)[0]
                
                # Map char scores back to combined results
                kb_count = len(kb_results)
                for i, r in enumerate(combined):
                    if i < kb_count:
                        char_score = float(char_cosines_kb[i])
                    else:
                        char_score = float(char_cosines_tb[i - kb_count])
                    
                    word_score = r.get("hybrid_score", 0)
                    # Linear interpolation: 70% word + 30% char
                    r["hybrid_score"] = round(
                        0.70 * word_score + 0.30 * char_score, 4
                    )
                    r["char_fallback_used"] = True
                combined.sort(key=lambda r: r["hybrid_score"], reverse=True)

        # Cross-encoder-style rerank stub: BM25 boost + exact title match + confidence prior
        for r in combined:
            r["hybrid_score"] = round(float(r.get("hybrid_score", 0)) + self._bm25_boost(
                query_tokens, str(r.get("title", "")), str(r.get("topic", ""))), 4)
            if canonical_concept and canonical_concept.lower() in str(r.get("title", "")).lower():
                r["hybrid_score"] = round(float(r["hybrid_score"]) + 0.04, 4)
        # Post-filter demotion: when rarest-term evidence survived, candidates
        # lacking it are demoted (precision rerank; recall was protected above).
        # Same guarded pattern for concept phrases (demote only if a holder
        # survived, so nicknames absent from NCERT text stay harmless).
        # Only apply if rarest terms actually exist in the vectorizer vocabulary.
        _vocab_kb = self.kb_vectorizer.vocabulary_ if self.kb_vectorizer else {}
        _vocab_tb = self.tb_vectorizer.vocabulary_ if self.tb_vectorizer else {}
        _rares_in_vocab = [t for t in _rares if t in _vocab_kb or t in _vocab_tb]
        _phrases_in_vocab = [p for p in _phrases if any(w in _vocab_kb or w in _vocab_tb for w in p.split())]
        _ultras_in_vocab = [u for u in _ultras if u in _vocab_kb or u in _vocab_tb]

        if _rares_in_vocab or _phrases_in_vocab or _ultras_in_vocab:
            _hays = [(str(r.get("title", "")) + " " + str(r.get("topic", "")) + " "
                      + str(r.get("definition", ""))).lower() for r in combined]

            def _holds(h: str) -> bool:
                if _rares_in_vocab and any(self._term_holds(h, t) for t in _rares_in_vocab):
                    return True
                return any(re.search(r"(?<!\w)" + re.escape(ph.lower()) + r"(?!\w)", h)
                           for ph in (_phrases_in_vocab or []))

            def _holds_all(h: str) -> bool:
                return bool(_rares_in_vocab) and all(self._term_holds(h, t) for t in _rares_in_vocab)

            def _holds_ultra(h: str) -> bool:
                return bool(_ultras_in_vocab) and any(self._term_holds_ultra(h, t) for t in _ultras_in_vocab)

            if any(_holds(h) for h in _hays):
                for r, h in zip(combined, _hays):
                    if not _holds(h):
                        r["hybrid_score"] = round(float(r["hybrid_score"]) - 0.15, 4)
                    elif _holds_all(h):
                        r["hybrid_score"] = round(float(r["hybrid_score"]) + 0.10, 4)
            # Ultra-rare exclusivity is chapter-aware: demotion fires only
            # when a holder sits in its owning chapter (syllabus affinity).
            _aff_terms = set()
            for _ut in (_ultras or []):
                _aff_terms.add(_ut)
                _aff_terms.update(re.findall(r"[a-z]{3,}", (canonical_concept or "").lower()))
            _chap_names = [str(r.get("chapter_name", "")) for r in combined]

            def _aff_holder(i: int) -> bool:
                return _holds_ultra(_hays[i]) and bool(_aff_terms) and self._syllabus_affinity(
                    _chap_names[i], _aff_terms)

            if _ultras and any(_holds_ultra(h) for h in _hays) and any(
                    _aff_holder(i) for i in range(len(combined))):
                for r, h in zip(combined, _hays):
                    if not _holds_ultra(h):
                        r["hybrid_score"] = round(float(r["hybrid_score"]) - 0.25, 4)
        # Distinctive-term coverage rerank (same guarded idiom): candidates are
        # tiered by how much of the query they cover. Tier 1: when a holder
        # covers EVERY distinctive query term, partial holders are demoted
        # ("plant growth hormones" prefers an all-terms plant-hormone holder
        # over human-hormone rows missing "plant"). Tier 2: otherwise, holders
        # covering >= min(2, n) terms win over narrower matches. Fires only
        # when a holder survived, so narrow queries and genuinely uncovered
        # topics are unaffected.
        _cov_terms = [t for t in dict.fromkeys(self._content_terms(clean_query))
                      if len(t) >= 4]
        _cov_need = min(2, len(_cov_terms))
        if len(_cov_terms) >= 2:
            _hays_cov = [(str(r.get("title", "")) + " " + str(r.get("topic", "")) + " "
                          + str(r.get("definition", ""))).lower() for r in combined]
            _cov_counts = [sum(1 for t in _cov_terms if self._term_holds(h, t))
                           for h in _hays_cov]
            _full = [c >= len(_cov_terms) for c in _cov_counts]
            if any(_full):
                for r, is_full in zip(combined, _full):
                    if not is_full:
                        r["hybrid_score"] = round(float(r["hybrid_score"]) - 0.30, 4)
                    else:
                        r["hybrid_score"] = round(float(r["hybrid_score"]) + 0.10, 4)
            else:
                _cov_holds = [c >= _cov_need for c in _cov_counts]
                if any(_cov_holds):
                    for r, holds in zip(combined, _cov_holds):
                        if not holds:
                            r["hybrid_score"] = round(float(r["hybrid_score"]) - 0.30, 4)
                        else:
                            r["hybrid_score"] = round(float(r["hybrid_score"]) + 0.10, 4)
        combined.sort(key=lambda r: r["hybrid_score"], reverse=True)
        return combined

    def evidence_covers(self, clean_query: str, record) -> int:
        """Count of distinctive query content terms present in a candidate's
        evidence text (title + topic + definition + mechanism + sample question).
        Used for admission and consistency decisions. General: no topic lists."""
        try:
            terms = [t for t in dict.fromkeys(self._content_terms(clean_query))
                     if len(t) >= 4]
            hay = (str((record or {}).get("title", "")) + " "
                   + str((record or {}).get("topic", "")) + " "
                   + str((record or {}).get("definition", "")) + " "
                   + str((record or {}).get("mechanism_steps", "")) + " "
                   + str((record or {}).get("sample_question", ""))).lower()
            return sum(1 for t in terms if self._term_holds(hay, t))
        except Exception:
            return 0

    def evidence_depth(self, clean_query: str, record) -> int:
        """Total occurrences of distinctive query terms in a candidate's
        evidence text. Distinguishes dedicated coverage (repeated topical
        terms, e.g. a pneumatophore Q&A row) from incidental single mentions
        (e.g. photoperiodism named once in passing)."""
        try:
            import re as _re
            terms = [t for t in dict.fromkeys(self._content_terms(clean_query))
                     if len(t) >= 4]
            hay = (str((record or {}).get("title", "")) + " "
                   + str((record or {}).get("topic", "")) + " "
                   + str((record or {}).get("definition", ""))).lower()
            total = 0
            for t in terms:
                for v in self._morph_variants(t):
                    total += len(_re.findall(r"(?<!\w)" + _re.escape(v)
                                             + r"(?!\w)", hay))
            return total
        except Exception:
            return 0

    def search(
        self,
        query: str,
        expanded_query: Optional[str] = None,
        top_k: int = 3,
        focus_chapter_id: Optional[str] = None,
        focal_context_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid dual-corpus search with rewrite + comparison-pair handling + figures.
        Comparison queries (A vs B) retrieve both sides and flag is_comparison.
        """
        # Defensive coercion: callers must pass a string, but a non-string
        # must never crash scoring with AttributeError.
        if focal_context_name is not None and not isinstance(focal_context_name, str):
            try:
                focal_context_name = str(focal_context_name)
            except Exception:
                focal_context_name = None
        pair = self.split_comparison(query or "")
        if pair:
            a, b = pair
            ra = self._single_search(a, a, top_k=2, focus_chapter_id=focus_chapter_id,
                                     focal_context_name=focal_context_name)
            rb = self._single_search(b, b, top_k=2, focus_chapter_id=focus_chapter_id,
                                     focal_context_name=focal_context_name)
            # Honest comparison requires evidence for BOTH sides; a missing side
            # means half the answer would be fabricated — refuse instead.
            if not ra or not rb:
                return []
            # Tag + interleave so generator can build a contrast table
            for r in ra:
                r["compare_side"] = "A"
            for r in rb:
                r["compare_side"] = "B"
            combined = (ra[:2] + rb[:2])
            combined.sort(key=lambda r: r["hybrid_score"], reverse=True)
            if combined:
                combined[0]["is_comparison"] = True
                combined[0]["compare_terms"] = [a, b]
            for r in combined:
                self._attach_figures_tables(r)
            return combined[: max(top_k, 4)]

        combined = self._single_search(query, expanded_query, top_k=top_k + 2,
                                       focus_chapter_id=focus_chapter_id,
                                       focal_context_name=focal_context_name)
        if combined:
            top_rec = combined[0]
            tb_only = [r for r in combined if r.get("origin") == "textbook_pdf"]
            if top_rec["origin"] == "knowledge_base" and tb_only:
                c_name = top_rec["chapter_name"].lower()
                for tb in tb_only:
                    if tb["chapter_name"].lower() == c_name:
                        top_rec["ncert_chunk"] = {
                            "chunk_id": tb.get("chunk_id"),
                            "section": tb.get("section"),
                            "page_number": tb.get("page_number"),
                            "source": tb.get("source"),
                            "text": tb.get("definition")
                        }
                        top_rec["source"] = tb["source"]
                        break
            final_res = combined[:top_k]
            for r in final_res:
                self._attach_figures_tables(r)
            return final_res
        return combined[:top_k]

    retrieve = search


retrieval_engine = ContextAwareHybridRetrievalEngine()
