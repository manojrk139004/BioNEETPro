"""
BioNEETPro - Adaptive Pedagogical Biology AI Tutor Engine (Dr. Priya)
=====================================================================
Implements:
1. Socratic Mastery-Aware Teaching Adaptation (Novice to NEET Ready)
2. Context-Sensitive Anaphora Tracking & Pronoun Resolution
3. Pedagogical Strategy Switching for Weak Concepts & Repeated Mistakes
4. Causal Chains & Prerequisite Concept Linking via Concept Graph
5. High-Yield NCERT Exam Traps & Assertion-Reason Nuances
6. Dual-Mode Generation: Authoritative Local Template + AI API Polish
7. Rigorous NCERT Source Traceability (Class, Chapter, Section, Page, Chunk ID)
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from concept_graph import concept_graph
from concept_normalizer import concept_normalizer
from learner_model import learner_manager
from nlp_pipeline import nlp_pipeline
from retrieval_engine import retrieval_engine

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL") or os.environ.get("AI_API_BASE_URL")
if not OPENROUTER_BASE_URL:
    OPENROUTER_BASE_URL = "https://router.bynara.id/v1" if OPENROUTER_KEY and OPENROUTER_KEY.startswith("sk-nry-") else "https://openrouter.ai/api/v1"
OPENROUTER_BASE_URL = OPENROUTER_BASE_URL.rstrip("/")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "minimax-m3-free")


class AdaptiveBiologyTutor:
    """
    Adaptive Biology Tutor Engine embodying Dr. Priya's Socratic teaching methodology.
    """

    STRATEGIES = [
        "standard_ncert",      # Baseline: Definition + Steps + Traps
        "simplified_steps",    # Mastery < 0.50 or 1 error: Simpler vocabulary, bite-sized breakdown
        "concrete_analogy",    # 2 errors or "explain again": Concrete physical metaphor/analogy
        "process_flow",        # 3 errors: Strict chronological diagrammatic flow
        "remedial_diagnostic", # 4+ errors: Break down foundational prerequisite
        "advanced_concise",    # Mastery >= 0.80: Concise nuances + NEET traps
    ]

    ANALOGIES: Dict[str, str] = {
        "c04": "Think of Animal Kingdom classification like sorting a massive library: Phyla are the main sections, Classes are the bookshelves, and Species are the exact books.",
        "c08": "Think of a eukaryotic cell as an industrial city: the Nucleus is City Hall holding blueprints, Mitochondria are Power Stations churning out energy currency (ATP), Ribosomes are Factories assembling structural proteins, and the Plasma Membrane is the gated security wall.",
        "c11": "Think of Photosynthesis like a solar charging factory: The Light Reaction acts like solar panels charging battery packs (ATP and NADPH), which the Calvin cycle then uses as power to assemble sugar bricks.",
        "c12": "Think of Glycolysis and Respiration like currency exchange: One high-denomination bill of Glucose is broken down through a sequence of steps into 36-38 small coins of ATP that cell machines can spend instantly.",
        "c13": "Think of Photosynthesis like a solar charging factory: The Light Reaction acts like solar panels charging battery packs (ATP and NADPH), which the Calvin cycle then uses as power to assemble sugar bricks.",
        "c14": "Think of Glycolysis and Respiration like currency exchange: One high-denomination bill of Glucose is broken down through a sequence of steps into 36-38 small coins of ATP that cell machines can spend instantly.",
        "c16": "Think of the Nephron like a high-tech water recycling plant: The glomerulus dumps everything into the conveyor belt, and selective tubular reabsorption pulls back 99% of pure water and vital nutrients.",
        "c18": "Think of the Central Neural System like an air traffic control center: The Brain processes incoming sensory radar signals, evaluates them in association areas, and transmits motor flight plans to muscles.",
        "c19": "Think of the Nephron like a high-tech water recycling plant: The glomerulus dumps everything into the conveyor belt, and selective tubular reabsorption pulls back 99% of pure water and vital nutrients.",
        "c20": "Think of the Sarcomere sliding filament like a crew of rowers: The thick Myosin heads reach up like oars, bind to the Actin boat ropes using ATP energy, and pull them inward to shorten the muscle during contraction.",
        "c21": "Think of the Central Neural System like an air traffic control center: The Brain processes incoming sensory radar signals, evaluates them in association areas, and transmits motor flight plans to muscles.",
        "c22": "Think of Insulin and Glucagon like a household thermostat: When blood sugar gets too high after meals, Insulin turns on the cellular storage heater; when blood sugar dips during fasting, Glucagon opens glycogen vaults in the liver.",
        "c27": "Think of DNA replication and translation like a secure royal library: The master genome scrolls (DNA) never leave the nucleus vault; messengers transcribe a photocopy (mRNA) to carry out to the workshop floor (Ribosome)."
    }

    def __init__(self):
        self.retrieval = retrieval_engine
        self.nlp = nlp_pipeline
        self.graph = concept_graph
        self.learner = learner_manager

    def _model_chain(self) -> List[str]:
        """Working models first. minimax-m3-free is a dead route (HTML error page)."""
        chain = [OPENROUTER_MODEL, "agnes-2.0-flash", "minimax-m3-free"]
        return list(dict.fromkeys([m for m in chain if m]))

    def _evidence_pack(self, results) -> str:
        """Top-4 full evidence pack: definitions + mechanisms + traps + figures + both compare sides."""
        blocks = []
        for i, r in enumerate((results or [])[:4]):
            title = str(r.get("title", ""))
            source = str(r.get("source", "NCERT Biology"))
            section = str(r.get("section", r.get("topic", "")))
            page = r.get("page_number", "")
            definition = str(r.get("definition", ""))[:900]
            mech = str(r.get("mechanism_steps", ""))[:700]
            traps = str(r.get("neet_traps", ""))[:400]
            figs = "; ".join(f.get("caption", "")[:120] for f in (r.get("figures") or [])[:2])
            side = f" [COMPARE SIDE {r.get('compare_side')}]" if r.get("compare_side") else ""
            blocks.append(
                f"[Evidence {i+1}{side}]\nTitle: {title}\nSource: {source}"
                f"{' | Section: ' + section if section else ''}{' | Page: ' + str(page) if page else ''}\n"
                f"Definition: {definition}\nMechanism: {mech}\nNEET traps: {traps}"
                f"{chr(10) + 'Figures: ' + figs if figs else ''}"
            )
        return "\n\n".join(blocks)

    def _generate_api_grounded_response(
        self,
        query: str,
        top_evidence: Dict[str, Any],
        strategy: str,
        student_profile: Dict[str, Any],
        history: Optional[List[Dict[str, str]]] = None,
        retrieval_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        """
        ONE generator: strict RAG over the evidence pack. Cite-or-refuse.
        Model chain fails over fast; local template remains the offline fallback.
        """
        if not OPENROUTER_KEY:
            return None

        pack = self._evidence_pack(retrieval_results or [top_evidence])
        if not pack.strip():
            return None

        strategy_prompts = {
            "simplified_steps": "Student level: NOVICE. Use simple words, short numbered steps, one idea per line.",
            "concrete_analogy": "Student is stuck. Open with ONE vivid real-world analogy, then map each part back to biology.",
            "process_flow": "Present the mechanism as a strict chronological chain with arrows (Step 1 -> Step 2 -> Step 3).",
            "remedial_diagnostic": "Rebuild from the prerequisite first (one short paragraph), then the concept.",
            "advanced_concise": "Student level: STRONG. Skip basics. Hit subtle distinctions + assertion-reason traps only.",
            "standard_ncert": "Standard clear structured NCERT explanation.",
        }

        system_instruction = (
            "You are Dr. Priya, BioNEETPro's NEET Biology mentor. Answer ONLY from the VERIFIED NCERT EVIDENCE below. "
            "Rules: 1) Every fact must come from the evidence; never invent details, numbers, or examples. "
            "2) If the evidence cannot answer the question, say exactly: CANNOT ANSWER FROM EVIDENCE. "
            "3) Cite sources inline like [E1], [E2] after each paragraph. "
            "4) Shape: one-line direct answer first, then mechanism/steps, then exactly 3 NEET traps, then one check question WITHOUT its answer. "
            "5) Under 280 words. No markdown tables unless the question compares two things, then use one 3-row table. "
            f"Strategy: {strategy_prompts.get(strategy, strategy_prompts['standard_ncert'])}\n\n"
            f"--- VERIFIED NCERT EVIDENCE ---\n{pack}\n-------------------------------"
        )

        messages = [{"role": "system", "content": system_instruction}]
        if history:
            for turn in history[-4:]:
                role = turn.get("role", "user")
                messages.append({"role": role if role in ("user", "assistant") else "user",
                                 "content": str(turn.get("content", ""))[:500]})
        messages.append({"role": "user", "content": query})

        for model in self._model_chain():
            try:
                resp = requests.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENROUTER_KEY}"},
                    json={"model": model, "messages": messages, "max_tokens": 900, "temperature": 0.2},
                    timeout=25,
                )
                if resp.status_code != 200:
                    continue
                content = resp.json()["choices"][0]["message"]["content"].strip()
                low = content.lower()
                if len(content) < 60 or "cannot answer from evidence" in low or "cannot answer" in low:
                    continue
                header = (
                    f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [NCERT Grounded • {strategy.replace('_', ' ').title()}]:**\n\n"
                )
                return header + content
            except Exception:
                continue

        return None

    def _faithfulness(self, reply: str, evidence_texts) -> float:
        """Token-overlap faithfulness proxy: fraction of reply content words grounded in evidence."""
        try:
            ev = " ".join(t for t in evidence_texts if t).lower()
            ev_tokens = set(re.findall(r"[a-z]{4,}", ev))
            rep_tokens = re.findall(r"[a-z]{4,}", (reply or "").lower())
            if not rep_tokens or not ev_tokens:
                return 0.0
            # Ignore generic tutor scaffolding words
            scaffold = {"neet", "ncert", "priya", "mentor", "biology", "chapter", "traps",
                        "mechanism", "step", "explanation", "answer", "question", "ask", "follow"}
            content = [w for w in rep_tokens if w not in scaffold]
            if not content:
                return 1.0
            hit = sum(1 for w in content if w in ev_tokens)
            return round(hit / len(content), 3)
        except Exception:
            return 0.0

    def _citations(self, results) -> List[Dict[str, Any]]:
        cites = []
        for r in (results or [])[:3]:
            cites.append({
                "title": r.get("title", ""), "source": r.get("source", ""),
                "section": r.get("section", ""), "page_number": r.get("page_number"),
                "chunk_id": r.get("chunk_id", r.get("concept_id", "")),
                "confidence": r.get("confidence", ""), "score": r.get("hybrid_score", 0),
            })
        return cites

    def _check_mcq(self, top) -> Optional[Dict[str, Any]]:
        """Hidden-answer diagnostic check from the concept's verified MCQ."""
        try:
            raw = top.get("raw_data", {}) if isinstance(top.get("raw_data"), dict) else {}
            q = raw.get("sample_question") or top.get("sample_question") or ""
            opts_raw = raw.get("sample_options") or top.get("sample_options") or ""
            ans = raw.get("correct_answer", top.get("correct_answer", 0))
            exp = raw.get("explanation") or top.get("explanation") or top.get("neet_traps", "")
            if not q or not opts_raw:
                return None
            opts = [o.strip() for o in str(opts_raw).split("|") if o.strip()]
            if len(opts) != 4:
                return None
            idx = int(ans) if str(ans).strip().isdigit() else 0
            if not (0 <= idx < 4):
                idx = 0
            return {"question": str(q).strip(), "options": opts,
                    "correct_index": idx, "explanation": str(exp)[:600]}
        except Exception:
            return None

    def _comparison_table(self, results) -> str:
        """Build A-vs-B contrast table from compare_side tagged results."""
        try:
            a = next((r for r in results if r.get("compare_side") == "A"), None)
            b = next((r for r in results if r.get("compare_side") == "B"), None)
            if not a or not b:
                return ""
            def cell(r):
                return (str(r.get("definition", ""))[:280] + "…") if r.get("definition") else str(r.get("title", ""))
            return (
                "\n\n📊 **Compare at a glance (NEET favourite):**\n\n"
                f"| Feature | {a.get('title','A')[:60]} | {b.get('title','B')[:60]} |\n"
                "|---|---|---|\n"
                f"| Core idea | {cell(a)} | {cell(b)} |\n"
                f"| Chapter | {a.get('chapter_name','')} | {b.get('chapter_name','')} |\n"
                f"| Trap | {str(a.get('neet_traps','—'))[:120]} | {str(b.get('neet_traps','—'))[:120]} |\n"
            )
        except Exception:
            return ""

    def _enrich(self, out: Dict[str, Any], results, top) -> Dict[str, Any]:
        ev_texts = [str(r.get("definition", "")) + " " + str(r.get("mechanism_steps", "")) for r in (results or [])[:2]]
        out["citations"] = self._citations(results)
        out["figures"] = (top.get("figures", []) if isinstance(top, dict) else [])[:2]
        out["tables"] = (top.get("tables", []) if isinstance(top, dict) else [])[:1]
        out["check_mcq"] = self._check_mcq(top if isinstance(top, dict) else {})
        out["faithfulness"] = self._faithfulness(out.get("reply", ""), ev_texts)
        if out.get("status") == "success" and out["faithfulness"] < 0.25:
            out["faithfulness_warning"] = True
            out["reply"] += ("\n\n⚠️ *Low grounding — verify with the cited NCERT section above and ask a follow-up.*")
        return out

    def generate_tutoring_response(
        self,
        query: str,
        student_id: str = "student_local",
        history: Optional[List[Dict[str, str]]] = None,
        focus_chapter_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        NLP -> Context -> Hybrid Retrieval (rewrite+compare+rerank) -> Mastery Adaptation -> Grounded Socratic reply.
        """
        # 1. NLP Processing & Conversational Reference Resolution
        nlp_res = self.nlp.process_query(query, history or [], student_id=student_id)
        resolved_query = nlp_res["resolved_query"]

        # 2. Syllabus Boundary Gate
        if not nlp_res["syllabus_valid"]:
            refusal = nlp_res["syllabus_data"].get("refusal_message")
            return {
                "reply": refusal,
                "mode": "syllabus_restricted",
                "status": "out_of_syllabus",
                "resolved_query": resolved_query,
                "confidence": "REJECTED"
            }

        # 3. Hybrid Concept Retrieval (Dual-Corpus: KB + Textbook Chunks)
        focal_ctx = nlp_res.get("focal_concept")
        retrieval_results = self.retrieval.search(
            query=resolved_query,
            expanded_query=nlp_res["expanded_query"],
            top_k=4,
            focus_chapter_id=focus_chapter_id,
            focal_context_name=focal_ctx
        )

        controlled_refusal = {
            "reply": (
                "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n"
                "*\"I couldn't find enough verified NCERT evidence for that specific Biology question in my local textbook knowledge base. "
                "Try asking about an NCERT topic such as Mitochondria, Cell Division, Photosynthesis, or Human Neural Control.\"*\n\n"
            ),
            "mode": "local_fallback",
            "status": "no_match",
            "confidence": "LOW"
        }

        if not retrieval_results:
            return controlled_refusal

        top = retrieval_results[0]

        # Confidence Gate
        if top["confidence"] == "REJECTED":
            controlled_refusal["confidence"] = "REJECTED"
            return controlled_refusal

        c_id = top["concept_id"]
        chap_id = str(top.get("chapter_id", "c01")).lower()
        title = top["title"]
        chap_name = top["chapter_name"]
        canon_name = concept_normalizer.get_canonical_concept_name(title) or title

        # 4. Context Tracking: Persist focal concept for multi-turn conversations
        subtopic = top.get("topic") or top.get("section")
        self.nlp.context_tracker.track_concept(
            student_id=student_id,
            concept_id=c_id,
            title=title,
            canonical_name=canon_name,
            subtopic=subtopic
        )

        # 5. Student Learner Profile & Strategy Adaptation
        profile = self.learner.get_or_create_profile(student_id)
        concept_mastery = profile["concept_mastery"].get(c_id, {}).get("mastery", profile["overall_mastery"])
        trajectory = profile["trajectory_stage"]
        mistake_info = profile["repeated_mistakes"].get(c_id, {})
        mistake_count = mistake_info.get("mistake_count", 0)

        # Check if student asked to "from basics", "explain again" or has a repeated mistake
        is_from_basics = nlp_res.get("is_from_basics", False) or bool(re.search(r"\b(from basics?|basics?|beginner|simple terms|like i('?m)? weak|step by step)\b", query.lower()))
        is_explain_again = bool(re.search(r"\b(explain\s+(it\s+)?again|simpler|another way|did not get it)\b", query.lower()))

        if is_explain_again or mistake_count >= 2:
            strategy = "concrete_analogy"
        elif is_from_basics or concept_mastery < 0.50 or mistake_count == 1:
            strategy = "simplified_steps"
        elif mistake_count >= 4:
            strategy = "remedial_diagnostic"
        elif mistake_count == 3:
            strategy = "process_flow"
        elif concept_mastery >= 0.80:
            strategy = "advanced_concise"
        else:
            strategy = "standard_ncert"

        # 6. ONE generator: strict RAG over the evidence pack (model chain inside)
        api_reply = self._generate_api_grounded_response(
            query=resolved_query,
            top_evidence=top,
            strategy=strategy,
            student_profile=profile,
            history=history,
            retrieval_results=retrieval_results,
        )

        if api_reply:
            compare_block = self._comparison_table(retrieval_results) if top.get("is_comparison") else ""
            source_citation = (
                f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📚 **NCERT Source Traceability:**\n"
                f"• **Source:** {top.get('source', f'NCERT Biology {chap_name}')}\n"
                f"• **Section / Chunk:** {top.get('section', c_id)}\n"
                f"• **Match Confidence:** {top['confidence']} (Score: {top['hybrid_score']})\n\n"
                f"💬 *Ask any follow-up question or type 'Give me 3 questions on it' to test yourself!*"
            )
            out = {
                "reply": api_reply + compare_block + source_citation,
                "mode": "api_grounded",
                "status": "success",
                "confidence": top["confidence"],
                "hybrid_score": top["hybrid_score"],
                "concept_id": c_id,
                "title": title,
                "chapter_id": chap_id,
                "strategy": strategy,
                "strategy_used": strategy,
                "student_trajectory": trajectory,
                "concept_mastery": concept_mastery,
                "is_repeated_weakness": mistake_count >= 1 or is_explain_again,
                "resolved_query": resolved_query,
                "source": top.get("source")
            }
            return self._enrich(out, retrieval_results, top)

        # 7. Local-First Socratic Response Generation (100% Offline Capable)
        raw_steps = [s.strip() for s in str(top.get("mechanism_steps", "")).split(" -> ") if s.strip()]
        steps_list = []
        for i, s in enumerate(raw_steps):
            clean_s = re.sub(r"^Step\s*\d+:\s*", "", s)
            steps_list.append(f"  {i+1}. {clean_s}")
        steps_formatted = "\n".join(steps_list) if steps_list else top["definition"]

        intent = nlp_res["intent"]
        is_why = intent == "why" or "why" in resolved_query.lower()

        # Personality Header
        if is_explain_again or mistake_count >= 2:
            header_intro = (
                f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [Local Algorithmic Tutor • Analogy & Simplification]:**\n"
                f"*\"I noticed you want another look at **{title}**. "
                f"Let's step back and look at the intuitive biological mental model so this clicks completely!\"*"
            )
        elif strategy == "advanced_concise":
            header_intro = (
                f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [Local Algorithmic Tutor • NEET Mastery Mode]:**\n"
                f"*\"You have a solid foundation here! Let's zero in on high-yield NCERT nuances and exam traps for **{title}**:\"*"
            )
        elif strategy == "simplified_steps":
            header_intro = (
                f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [Local Algorithmic Tutor • Step-by-Step Foundations]:**\n"
                f"*\"Let's break down **{title}** into clear, bite-sized NCERT facts:\"*"
            )
        else:
            greeting_verb = "Why this works in NCERT Biology" if is_why else "Here is your authoritative NCERT breakdown"
            header_intro = (
                f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [Local Algorithmic Tutor]:**\n"
                f"*\"{greeting_verb} for **{title}**:\"*"
            )

        # Core Definition or Mechanism
        if intent == "definition":
            core_block = f"📖 **Chapter:** {chap_name}\n\n📌 **Core NCERT Content:**\n{top['definition']}\n\n🎯 **NEET Focus:**\n{top.get('neet_traps', 'Crucial NCERT fact.')}"
        elif intent == "why" or is_why:
            core_block = f"📖 **Chapter:** {chap_name}\n\n🧬 **The Core Biological Reason (Why):**\n{top['definition']}\n\n⚙️ **Mechanism & Significance:**\n{steps_formatted}"
        elif intent == "how_process":
            core_block = f"📖 **Chapter:** {chap_name}\n\n🔢 **Sequential Process:**\n{steps_formatted}"
        else:
            core_block = f"📖 **Chapter:** {chap_name}\n\n📌 **Authoritative NCERT Explanation:**\n{top['definition']}"

        # Analogy block
        m_c = re.search(r'\d+', chap_id)
        prefix_chap = f"c{int(m_c.group(0)):02d}" if m_c else chap_id[:3]

        analogy_text = ""
        if (strategy in ("concrete_analogy", "simplified_steps") or is_explain_again or mistake_count >= 2) and prefix_chap in self.ANALOGIES:
            analogy_text = f"\n\n💡 **Intuitive Analogy (Mental Model):**\n*{self.ANALOGIES[prefix_chap]}*"

        # Steps block
        steps_block = ""
        if intent not in ["why", "how_process"] and not is_why and steps_formatted != top["definition"]:
            steps_block = f"\n\n🔍 **Step-by-Step Biological Detail:**\n{steps_formatted}"

        # Traps block
        traps_block = f"\n\n⚠️ **NEET Traps & Key Facts:**\n{top.get('neet_traps', 'Remember to note the exact NCERT phrasing.')}"

        # Comparison table for A-vs-B questions (beast fix for mitosis-vs-meiosis)
        compare_block = self._comparison_table(retrieval_results) if top.get("is_comparison") else ""

        # Figure / table hints (served by frontend from citations payload too)
        visual_block = ""
        try:
            figs = (top.get("figures", []) or [])[:2]
            if figs:
                caps = "; ".join(f.get("caption", "")[:90] for f in figs if f.get("caption"))
                visual_block = f"\n\n🖼️ **NCERT Figure to revise:** {caps or 'see cited chapter figures'}"
            tabs = (top.get("tables", []) or [])[:1]
            if tabs and tabs[0].get("rows"):
                rows = tabs[0]["rows"][:4]
                md = "\n".join("| " + " | ".join(str(c)[:28] for c in r) + " |" for r in rows if r)
                visual_block += f"\n\n📋 **NCERT Table (first rows):**\n{md}"
        except Exception:
            pass

        # Socratic check prompt (answer hidden in check_mcq payload, not in text)
        socratic_block = "\n\n💬 *Quick check: I'll quiz you on this below — try answering before revealing! Type 'Give me 3 questions on it' for more.*"

        # Source Traceability
        source_block = (
            f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📚 **Authoritative NCERT Source Reference:**\n"
            f"• **Source:** {top.get('source', f'NCERT Biology {chap_name}')}\n"
            f"• **Section / Chunk:** {top.get('section', c_id)}\n"
            f"• **Match Confidence:** {top['confidence']} (Score: {top['hybrid_score']})\n"
            f"{socratic_block}"
        )

        full_reply = (
            f"{header_intro}\n\n"
            f"{core_block}"
            f"{analogy_text}"
            f"{steps_block}"
            f"{compare_block}"
            f"{traps_block}"
            f"{visual_block}"
            f"{source_block}"
        )

        out = {
            "reply": full_reply,
            "mode": "local_adaptive",
            "status": "success",
            "confidence": top["confidence"],
            "hybrid_score": top["hybrid_score"],
            "concept_id": c_id,
            "title": title,
            "chapter_id": chap_id,
            "strategy": strategy,
            "strategy_used": strategy,
            "student_trajectory": trajectory,
            "concept_mastery": concept_mastery,
            "is_repeated_weakness": mistake_count >= 1 or is_explain_again,
            "resolved_query": resolved_query,
            "source": top.get("source")
        }
        return self._enrich(out, retrieval_results, top)


adaptive_tutor = AdaptiveBiologyTutor()
