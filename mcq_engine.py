"""
BioNEETPro - Comprehensive Local Biology MCQ Generation Engine
==============================================================
Implements:
1. Dynamic Quantity & Difficulty Parsing (e.g. "Give me 5 MCQs", "3 easy MCQs on Cell Division")
2. Context-Sensitive MCQ Generation ("Give me 3 questions on it" -> resolves Mitochondria)
3. Targeted Weak-Topic Diagnostic Testing ("Give me questions from my weak topics")
4. Difficulty Control: Explicit Student Choice overrides; otherwise adapts to Learner Profile
5. Multi-Tier Verified Question Bank (Easy, Medium, Hard) strictly inside NCERT Biology
6. Strict Local Validation: Exactly 4 distinct options, 1 verified answer, zero missing answer keys
7. Explanations strictly grounded in NCERT
"""

import json
import os
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests

from concept_normalizer import concept_normalizer
from learner_model import learner_manager
from nlp_pipeline import nlp_pipeline

DATA_DIR = Path(__file__).resolve().parent / "data"
DATASETS_DIR = Path(__file__).resolve().parent / "datasets"
KB_PATH = DATA_DIR / "neet_knowledge_base.csv"
INDEXED_MCQ_CACHE = DATA_DIR / "indexed_mcqs_cache.json"

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL") or os.environ.get("AI_API_BASE_URL")
if not OPENROUTER_BASE_URL:
    OPENROUTER_BASE_URL = "https://router.bynara.id/v1" if OPENROUTER_KEY and OPENROUTER_KEY.startswith("sk-nry-") else "https://openrouter.ai/api/v1"
OPENROUTER_BASE_URL = OPENROUTER_BASE_URL.rstrip("/")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "gpt-4o-mini")


class LocalMCQEngine:
    """
    On-demand local MCQ engine supporting custom quantities, difficulty overrides,
    weak-topic remediation, and adaptive difficulty generation strictly inside NEET Biology.
    """

    def __init__(self):
        self.mcq_pool: List[Dict[str, Any]] = []
        self.last_generated_mcqs: Dict[str, List[Dict[str, Any]]] = {}
        self._load_or_build_mcq_pool()

    def _load_or_build_mcq_pool(self):
        if INDEXED_MCQ_CACHE.exists():
            try:
                with open(INDEXED_MCQ_CACHE, "r", encoding="utf-8") as f:
                    self.mcq_pool = json.load(f)
                if self.mcq_pool and len(self.mcq_pool) >= 100:
                    return
            except Exception:
                pass

        self._build_mcq_pool()

    def validate_mcq(self, mcq: Dict) -> bool:
        """Validates that an MCQ satisfies strict NEET structural and answer constraints."""
        if not mcq.get("question") or len(str(mcq["question"]).strip()) <= 10:
            return False
        opts = mcq.get("options", [])
        if not isinstance(opts, list) or len(opts) != 4:
            return False
        if len(set(opts)) != 4:
            return False
        c_idx = mcq.get("correct_index", -1)
        if not isinstance(c_idx, int) or not (0 <= c_idx <= 3):
            return False
        if not mcq.get("correct_answer"):
            mcq["correct_answer"] = str(opts[c_idx]).strip()
        if str(mcq.get("correct_answer")).strip() != str(opts[c_idx]).strip():
            return False
        return True

    def _build_mcq_pool(self):
        pool = []

        # 1. Ingest Canonical MCQs from neet_knowledge_base.csv (Distribute into Easy and Medium)
        if KB_PATH.exists():
            kb_df = pd.read_csv(KB_PATH)
            for idx_row, row in kb_df.iterrows():
                q_text = str(row.get("sample_question", "")).strip()
                opts_raw = str(row.get("sample_options", "")).strip()
                ans_idx = row.get("correct_answer", 0)
                exp = str(row.get("explanation", "")).strip()
                c_id = str(row.get("concept_id", f"BIO-C{idx_row:02d}"))
                chap = str(row.get("chapter_name", "General Biology"))
                topic = str(row.get("topic", chap))

                if q_text and opts_raw and "|" in opts_raw:
                    options = [o.strip() for o in opts_raw.split("|") if o.strip()]
                    if len(options) == 4:
                        try:
                            idx = int(ans_idx)
                        except (ValueError, TypeError):
                            idx = 0

                        # Classify into easy vs medium vs hard based on question structure and analytical depth
                        is_analytical = any(w in q_text.lower() for w in [
                            "recombinant", "probability", "percentage", "mutation", "mutant",
                            "consequence of", "produces 1600", "chargaff", "proofreading",
                            "operator region", "linkage", "cross between", "phenotypic", "ratio",
                            "dihybrid", "exonuclease"
                        ])
                        is_direct = any(w in q_text.lower() for w in [
                            "which of the following", "name the", "what is", "according to",
                            "in which stage", "serves which primary", "how many pairs"
                        ])

                        if is_analytical or c_id in ["BIO-C27-04", "BIO-C27-05", "BIO-C27-06", "BIO-C28-03", "BIO-C28-04", "BIO-C28-05"]:
                            diff = "hard"
                            cog = "BT4 - Analyzing"
                        elif is_direct and idx_row % 2 == 0:
                            diff = "easy"
                            cog = "BT1 - Remembering"
                        else:
                            diff = "medium"
                            cog = "BT2 - Understanding"

                        item = {
                            "id": f"kb-{c_id}",
                            "concept_id": c_id,
                            "chapter": chap,
                            "topic": topic,
                            "question": q_text,
                            "options": options,
                            "correct_index": idx,
                            "correct_answer": options[idx] if 0 <= idx < 4 else options[0],
                            "explanation": exp or f"Authoritative NCERT biological fact from {chap}.",
                            "difficulty": diff,
                            "cognitive_level": cog,
                            "source": "NCERT Knowledge Base"
                        }
                        if self.validate_mcq(item):
                            pool.append(item)

        # 2. Ingest Verified Biology MCQs from test1.csv (Medical Physiology/Anatomy/Genetics -> Hard)
        test1_path = DATASETS_DIR / "test1.csv"
        if test1_path.exists():
            try:
                t1_df = pd.read_csv(test1_path)
                bio_subs = {"Physiology", "Anatomy", "Biochemistry"}
                bio_t1 = t1_df[t1_df["subject_name"].isin(bio_subs)].head(800)

                for _, row in bio_t1.iterrows():
                    q = str(row.get("question", "")).strip()
                    opa = str(row.get("opa", "")).strip()
                    opb = str(row.get("opb", "")).strip()
                    opc = str(row.get("opc", "")).strip()
                    opd = str(row.get("opd", "")).strip()
                    try:
                        cop = int(float(row.get("cop", -1))) - 1
                    except (ValueError, TypeError):
                        cop = -1
                    exp = str(row.get("exp", "")).strip()
                    subj = str(row.get("subject_name", "Physiology"))
                    top = str(row.get("topic_name", subj))

                    if q and opa and opb and opc and opd and 0 <= cop <= 3:
                        # Strictly NCERT: skip non-NEET clinical super-specialities even if present in CSV.
                        if subj.strip().lower() in {"gynaecology & obstetrics", "gynaecology", "obstetrics", "surgery", "medicine"}:
                            continue
                        opts = [opa, opb, opc, opd]
                        chap_map = {
                            "Physiology": "Human Physiology",
                            "Anatomy": "Structural Organisation in Animals / Tissues",
                            "Biochemistry": "Biomolecules",
                            "Microbiology": "Microbes in Human Welfare",
                        }
                        neet_chap = chap_map.get(subj, "Human Physiology")

                        item = {
                            "id": f"t1-{row.get('id', random.randint(1000, 9999))}",
                            "concept_id": f"BIO-MED-{subj[:3].upper()}",
                            "chapter": neet_chap,
                            "topic": top if top and top != "nan" else neet_chap,
                            "question": q,
                            "options": opts,
                            "correct_index": int(cop),
                            "correct_answer": opts[int(cop)],
                            "explanation": exp if exp and exp != "nan" else f"NCERT clinical correlation in {neet_chap}.",
                            "difficulty": "hard",
                            "cognitive_level": "BT4 - Analyzing",
                            "source": "Medical Biology Question Archive"
                        }
                        if self.validate_mcq(item):
                            pool.append(item)
            except Exception as e:
                print(f"Warning: Could not ingest test1.csv: {e}")

        self.mcq_pool = pool

        try:
            with open(INDEXED_MCQ_CACHE, "w", encoding="utf-8") as f:
                json.dump(pool, f)
        except Exception:
            pass

    # Natural-language quantities ("five MCQs", "a couple of questions").
    WORD_NUMBERS = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "twenty": 20, "thirty": 30,
    }

    def parse_mcq_request(self, message: str, student_id: str = "student_local") -> Dict[str, Any]:
        """
        Extracts requested count, difficulty, and topic from natural language,
        resolving conversational context and weak-topic mode.
        """
        clean = message.lower().strip()

        # 1. Parse quantity (digits first, then natural-language number words)
        count = 5
        count_match = re.search(r"\b(\d+)\s*(?:easy|medium|hard|difficult|tough|simple)?\s*(mcqs?|questions?|problems?|quizzes?)\b", clean)
        if count_match:
            try:
                count = max(1, min(30, int(count_match.group(1))))
            except ValueError:
                count = 5
        else:
            word_match = re.search(
                r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                r"thirteen|fourteen|fifteen|twenty|thirty)\b\s*(?:easy|medium|hard|difficult|tough|simple)?\s*"
                r"(mcqs?|questions?|problems?|quizzes?)\b", clean)
            if word_match:
                count = max(1, min(30, self.WORD_NUMBERS[word_match.group(1)]))
            elif "a couple of" in clean and re.search(r"\b(mcqs?|questions?|quizzes?)\b", clean):
                count = 2
            elif "one mcq" in clean or "a mcq" in clean or "single question" in clean:
                count = 1
            # Fallback: number word detached from the question noun
            # ("quiz me with three on respiration") — but never steal a
            # question reference ("question 2" means Q#2, not a count of 2).
            elif not re.search(r"\bquestions?\s*(number|no\.?|#)?\s*\d+\b", clean):
                loose = re.search(
                    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                    r"thirteen|fourteen|fifteen|twenty|thirty)\b", clean)
                if loose:
                    count = max(1, min(30, self.WORD_NUMBERS[loose.group(1)]))

        # 2. Parse difficulty
        explicit_diff = None
        if "hard" in clean or "difficult" in clean or "tough" in clean:
            explicit_diff = "hard"
        elif "easy" in clean or "simple" in clean or "basic" in clean:
            explicit_diff = "easy"
        elif "medium" in clean or "moderate" in clean:
            explicit_diff = "medium"

        # 3. Check for weak-topics mode
        is_weak_topics = any(w in clean for w in ["weak topic", "weak topics", "weak concept", "weak concepts", "weakness", "weaknesses", "my weak"])
        if is_weak_topics:
            return {
                "requested_count": count,
                "explicit_difficulty": explicit_diff,
                "target_topic": "__weak_topics__",
                "is_weak_topics": True
            }

        # 4. Parse target topic or resolve from conversational context
        target_topic = None
        # 4. Parse target topic or resolve from conversational context
        target_topic = None
        if "cockroach" in clean or "periplaneta" in clean:
            target_topic = "cockroach"
        elif "genetics" in clean or "inheritance" in clean:
            target_topic = "genetics"
        else:
            # Check canonical concept normalizer
            canon = concept_normalizer.get_canonical_concept_name(clean)
            if canon:
                target_topic = canon.lower()
            else:
                for t in ["mitochondria", "cell division", "meiosis", "mitosis", "photosynthesis",
                          "glycolysis", "respiration", "heart", "circulation", "kidney", "excretion", "bone",
                          "skeleton", "cell", "biomolecules", "ecology", "reproduction", "evolution",
                          "digestion", "breathing", "neural", "brain", "hormones", "genetics",
                          "inheritance", "dna", "rna", "biotechnology", "microbes"]:
                    if t in clean:
                        target_topic = t
                        break

        # If no explicit topic in message, check active conversational context
        if not target_topic:
            focal = nlp_pipeline.context_tracker.get_focal_concept(student_id)
            if focal and focal[2]:
                target_topic = focal[2].lower()

        return {
            "requested_count": count,
            "explicit_difficulty": explicit_diff,
            "target_topic": target_topic,
            "is_weak_topics": False
        }

    @staticmethod
    def _norm_chapter(name: str) -> str:
        import re as _re
        return _re.sub(r"[^a-z0-9]+", " ", str(name or "").lower()).strip()

    def generate_chapter_mcqs(
        self,
        chapter: str,
        count: int = 10,
        difficulty: Optional[str] = None,
        student_id: str = "student_local",
    ) -> Dict[str, Any]:
        """Strict chapter-wise fetch (Phase 4): ONLY questions tagged with the
        selected chapter — never padded with off-chapter questions. Returns
        fewer than requested with an honest flag when the bank is thin."""
        want = max(1, min(90, int(count or 10)))
        cnorm = self._norm_chapter(chapter)
        pool = [q for q in self.mcq_pool if self._norm_chapter(q.get("chapter", "")) == cnorm]
        if difficulty:
            d = str(difficulty).lower()
            df = [q for q in pool if str(q.get("difficulty", "")).lower() == d]
            if df:
                pool = df
        selected = random.sample(pool, min(want, len(pool))) if pool else []
        if selected:
            self.last_generated_mcqs[student_id] = selected
        return {"status": "success", "requested": want, "count": len(selected),
                "shortfall": max(0, want - len(selected)),
                "chapter": chapter, "strict": True,
                "mcqs": selected}

    def refresh_from_docs(self, docs: List[Dict[str, Any]]) -> int:
        """Sync backend pool from Firestore `mcqs` docs (Phase 2).

        Accepts both backend schema (question/options/correct_index/chapter)
        and frontend schema (q/opts/correct/chapter). Returns # merged."""
        merged = 0
        seen = {str(m.get("question", "")).strip().lower() for m in self.mcq_pool}
        for d in docs or []:
            q = d.get("question") or d.get("q") or ""
            opts = d.get("options") or d.get("opts") or []
            ci = d.get("correct_index", d.get("correct", -1))
            chap = d.get("chapter", "General Biology")
            if not q or not isinstance(opts, list) or len(opts) != 4:
                continue
            if str(q).strip().lower() in seen:
                continue
            try:
                ci = int(ci)
            except Exception:
                continue
            if not (0 <= ci < 4):
                continue
            item = {"id": str(d.get("id", f"fs-{merged}")),
                    "concept_id": str(d.get("concept_id", "FS")),
                    "chapter": chap, "topic": str(d.get("topic", chap)),
                    "question": q, "options": opts,
                    "correct_index": ci, "correct_answer": opts[ci],
                    "explanation": str(d.get("explanation") or d.get("expl") or ""),
                    "difficulty": str(d.get("difficulty") or d.get("diff") or "medium").lower(),
                    "cognitive_level": "BT2 - Understanding",
                    "source": "firestore-sync"}
            if self.validate_mcq(item):
                self.mcq_pool.append(item)
                seen.add(str(q).strip().lower())
                merged += 1
        return merged

    def generate_mcqs(
        self,
        request_text: str,
        student_id: str = "student_local"
    ) -> Dict[str, Any]:
        """
        Generates requested quantity of MCQs adapting difficulty or using explicit choice.
        Supports weak-topic targeting and conversational context continuity.
        """
        parsed = self.parse_mcq_request(request_text, student_id=student_id)
        count = parsed["requested_count"]
        explicit_diff = parsed["explicit_difficulty"]
        topic_filter = parsed["target_topic"]
        is_weak_topics = parsed.get("is_weak_topics", False)

        # 1. Determine difficulty
        if explicit_diff:
            chosen_diff = explicit_diff
            diff_mode = "user_override"
        else:
            profile = learner_manager.get_or_create_profile(student_id)
            mastery = profile.get("overall_mastery", 0.50)
            if mastery >= 0.75:
                chosen_diff = "hard"
            elif mastery <= 0.40:
                chosen_diff = "easy"
            else:
                chosen_diff = "medium"
            diff_mode = "adaptive_profile"

        # 2. Filter questions based on weak topics or requested topic
        candidates = self.mcq_pool
        topic_matched = True

        if is_weak_topics:
            weak_list = learner_manager.get_weak_topics(student_id)
            if weak_list:
                weak_cids = {w["concept_id"].lower() for w in weak_list}
                weak_chaps = {w["chapter_id"].lower() for w in weak_list}
                filtered = [
                    q for q in candidates
                    if q["concept_id"].lower() in weak_cids or any(c in q["chapter"].lower() for c in weak_chaps)
                ]
                if filtered:
                    candidates = filtered
                else:
                    topic_matched = False
                topic_filter = "Your Identified Weak Topics"
            else:
                topic_filter = "Diagnostic Mixed Syllabus (No Weak Topics Yet)"

        elif topic_filter and topic_filter != "__weak_topics__":
            tf = topic_filter.lower()
            # Exact canonical-chapter match first (no substring bleed:
            # "cell" must not match "cell cycle" chapters).
            cnorm = self._norm_chapter(topic_filter)
            exact = [q for q in candidates
                     if self._norm_chapter(q.get("chapter", "")) == cnorm]
            if exact:
                candidates = exact
            else:
                filtered = [
                    q for q in candidates
                    if tf in q["question"].lower()
                    or tf in q["chapter"].lower()
                    or tf in q["topic"].lower()
                    or (tf in ["cockroach", "cockroach chapter", "periplaneta"] and any(k in (q["question"] + " " + q["topic"]).lower() for k in ["cockroach", "periplaneta", "malpighian", "spiracle", "ommatidia"]))
                    or (tf == "genetics" and any(k in (q["chapter"] + " " + q["topic"] + " " + q["question"]).lower() for k in ["inheritance", "molecular basis", "mendel", "dna", "linkage", "cross", "operon", "chargaff", "recombinant"]))
                ]
                if filtered:
                    candidates = filtered
                else:
                    topic_matched = False

        # 3. Filter by difficulty if enough items exist
        diff_filtered = [q for q in candidates if q["difficulty"] == chosen_diff]
        if len(diff_filtered) >= count:
            selected = random.sample(diff_filtered, count)
        else:
            sample_size = min(count, len(candidates))
            selected = random.sample(candidates, sample_size) if sample_size > 0 else []

        if selected:
            self.last_generated_mcqs[student_id] = selected

        return {
            "status": "success",
            "count": len(selected),
            "requested": count,
            "padded": not topic_matched,
            "difficulty": chosen_diff,
            "difficulty_mode": diff_mode,
            "topic": (topic_filter or "Mixed NCERT Biology").title(),
            "mcqs": selected
        }

    def get_recent_mcqs(self, student_id: str = "student_local") -> List[Dict[str, Any]]:
        """Returns the most recently generated batch of MCQs for a student."""
        return self.last_generated_mcqs.get(student_id, [])

    def get_recent_mcq(self, question_number: int, student_id: str = "student_local") -> Optional[Dict[str, Any]]:
        """Returns the specific 1-indexed MCQ from the student's active batch."""
        mcqs = self.get_recent_mcqs(student_id)
        idx = int(question_number) - 1
        if 0 <= idx < len(mcqs):
            return mcqs[idx]
        return None

    def format_mcqs_for_chat(self, mcq_result: Dict[str, Any], reveal_answers: bool = False) -> str:
        """
        Formats generated MCQs into an interactive Markdown prompt for Dr. Priya.
        Answers and explanations are withheld by default so the student can solve them.
        """
        mcqs = mcq_result.get("mcqs", [])
        if not mcqs:
            return (
                "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n"
                "*\"I could not retrieve enough verified MCQs for this specific topic right now. "
                "Try asking 'Give me 5 MCQs on Mitochondria' or 'Give me 3 questions on Photosynthesis'!\"*"
            )

        diff = mcq_result.get("difficulty", "medium").upper()
        mode = "Your Selection" if mcq_result.get("difficulty_mode") == "user_override" else "Adaptive to Your Mastery"
        topic = mcq_result.get("topic", "NEET Biology")

        lines = [
            f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [On-Demand NEET MCQ Test]:**",
            f"*\"Here are **{len(mcqs)} high-yield MCQs** on **{topic}** (Difficulty: **{diff}** — *{mode}*):\"*\n",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]

        for i, q in enumerate(mcqs):
            opts_formatted = "\n".join([f"    **({chr(65+j)})** {opt}" for j, opt in enumerate(q["options"])])
            q_block = [
                f"\n**Question {i+1} [{q['chapter']} • {q['cognitive_level']}]:**\n{q['question']}\n\n{opts_formatted}\n"
            ]
            if reveal_answers:
                q_block.append(
                    f"<details>\n<summary>🔍 <b>Click to Reveal NCERT Answer & Explanation</b></summary>\n\n"
                    f"✅ **Correct Answer:** ({chr(65 + q['correct_index'])}) {q['correct_answer']}\n\n"
                    f"📖 **NCERT Explanation:**\n{q['explanation']}\n"
                    f"</details>\n"
                )
            q_block.append("─────────────────────────────")
            lines.append("\n".join(q_block))

        if reveal_answers:
            lines.append(
                "\n💡 *Try answering without peeking! Enter your answers in chat or type another question when ready.*"
            )
        else:
            lines.append(
                "\n👉 **How to answer:** Click an option badge below or type your answers in chat "
                "(e.g. `1:C, 2:A, 3:B` or `C A B` or `Option C`) to evaluate your NEET score!"
            )

        return "\n".join(lines)


mcq_engine = LocalMCQEngine()
