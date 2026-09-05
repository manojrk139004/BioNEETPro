"""
BioNEET Pro - Local Algorithmic Tutor Engine
Implements:
1. ConceptSearchEngine: TF-IDF Vector Space Model + Cosine Similarity Ranking (scikit-learn)
2. PedagogicalTracker: 4-Step Socratic State Machine (Definition -> Mechanism -> Traps -> Quiz)
3. KnowledgeTracingEngine: Bayesian Knowledge Tracing (BKT) for dynamic mastery modeling
4. Local CSV Persistence: Saves session trajectories to data/student_learning_tracker.csv
"""

import csv
import datetime
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from retrieval_engine import retrieval_engine
from learner_model import learner_manager
from nlp_pipeline import nlp_pipeline
from concept_graph import concept_graph

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
KB_PATH = DATA_DIR / "neet_knowledge_base.csv"
GRAPH_PATH = DATA_DIR / "concept_dependency_graph.csv"
TRACKER_PATH = DATA_DIR / "student_learning_tracker.csv"


class ConceptSearchEngine:
    """
    Backward-compatibility wrapper delegating to HybridRetrievalEngine.
    """
    def __init__(self, kb_path: Path = KB_PATH, graph_path: Path = GRAPH_PATH):
        self.engine = retrieval_engine

    @property
    def df(self):
        return self.engine.df

    @property
    def feature_names(self):
        return self.engine.feature_names

    @property
    def kb_path(self):
        return self.engine.kb_path

    def load_and_fit(self):
        self.engine.load_and_index()

    def match_concept(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        results = self.engine.search(query, top_k=top_k * 2)
        kb_results = [r for r in results if r.get("origin") == "knowledge_base"]
        chosen = kb_results[:top_k] if kb_results else results[:top_k]
        mapped = []
        for r in chosen:
            raw = r.get("raw_data", {})
            overlap = [w for w in query.lower().split() if w in (r.get("title", "") + " " + r.get("topic", "")).lower()]
            mapped.append({
                "concept_id": r.get("concept_id"),
                "chapter_id": r.get("chapter_id"),
                "chapter_name": r.get("chapter_name"),
                "topic": r.get("topic"),
                "title": r.get("title"),
                "similarity_score": r.get("hybrid_score", 0.0),
                "matched_terms": overlap or [r.get("title", "").lower().split()[0]],
                "related_nodes": [],
                "raw_data": raw,
            })
        return mapped


class KnowledgeTracingEngine:
    """
    Bayesian Knowledge Tracing (BKT) Engine.
    Models latent knowledge state P(L_t) across learning steps.
    """
    def __init__(
        self,
        p_l0: float = 0.50,   # Prior probability of knowing concept
        p_t: float = 0.15,    # Probability of learning transition
        p_s: float = 0.10,    # Probability of slip (knows, but errs)
        p_g: float = 0.25,    # Probability of guess (doesn't know, but correct)
    ):
        self.p_l0 = p_l0
        self.p_t = p_t
        self.p_s = p_s
        self.p_g = p_g

    def update(self, prior_mastery: float, is_correct: bool) -> float:
        """
        Calculates posterior mastery P(L_t | Evidence) then transitions by P(T).
        """
        p_l = max(0.01, min(0.99, prior_mastery))
        if is_correct:
            p_posterior = (p_l * (1.0 - self.p_s)) / (
                (p_l * (1.0 - self.p_s)) + ((1.0 - p_l) * self.p_g)
            )
        else:
            p_posterior = (p_l * self.p_s) / (
                (p_l * self.p_s) + ((1.0 - p_l) * (1.0 - self.p_g))
            )
        p_next = p_posterior + (1.0 - p_posterior) * self.p_t
        return round(float(min(0.99, max(0.01, p_next))), 3)


class PedagogicalTracker:
    """
    Manages 4-Step Socratic state progression and writes to local CSV tracker.
    """
    STEPS = {
        1: "Concept Anchor & Definition",
        2: "Step-by-Step Biological Mechanism",
        3: "NEET Traps, Exceptions & Tips",
        4: "Diagnostic Micro-Check"
    }

    def __init__(self, tracker_path: Path = TRACKER_PATH):
        self.tracker_path = tracker_path
        # We removed self.search_engine here and use the global retrieval_engine
        self.bkt = KnowledgeTracingEngine()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._ensure_tracker_file()

    @property
    def df(self) -> pd.DataFrame:
        return retrieval_engine.df
        
    @property
    def feature_names(self) -> List[str]:
        return retrieval_engine.feature_names
        
    @property
    def kb_path(self) -> Path:
        return retrieval_engine.kb_path

    def _ensure_tracker_file(self):
        if not self.tracker_path.exists():
            self.tracker_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tracker_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "session_id", "timestamp", "student_id", "query_text",
                    "matched_concept_id", "similarity_score", "current_step",
                    "mastery_score", "feedback_status"
                ])

    def log_interaction(
        self,
        session_id: str,
        student_id: str,
        query_text: str,
        concept_id: str,
        similarity: float,
        step: int,
        mastery: float,
        feedback: str
    ):
        with open(self.tracker_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                session_id,
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
                student_id,
                query_text.replace("\n", " ")[:150],
                concept_id,
                f"{similarity:.4f}",
                step,
                f"{mastery:.3f}",
                feedback
            ])

    def start_query_session(
        self, query: str, student_id: str = "student_local", history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Step 1: Matches query to local concept using TF-IDF and initializes session.
        """
        nlp_res = nlp_pipeline.process_query(query, history)
        resolved_query = nlp_res.get("resolved_query", query)
        expanded_query = nlp_res.get("expanded_query", resolved_query)
        
        all_matches = retrieval_engine.search(query=query, expanded_query=expanded_query, top_k=6)
        kb_matches = [m for m in all_matches if m.get("origin") == "knowledge_base"]
        matches = kb_matches if kb_matches else all_matches

        min_cutoff = getattr(retrieval_engine, "MIN_RELEVANCE_THRESHOLD", 0.12)
        if not matches or matches[0].get("hybrid_score", 0) < min_cutoff:
            return {
                "status": "low_confidence",
                "message": "No direct NCERT concept matched your query above confidence threshold.",
                "suggested_topics": [
                    "Try asking about: Photosynthesis light reaction, Calvin cycle, Lac operon, Mitosis crossing over, DNA replication, or Cardiac cycle."
                ]
            }

        top_match = matches[0]
        concept_data = dict(top_match.get("raw_data") or top_match)
        if "title" not in concept_data:
            concept_data["title"] = top_match.get("title", "NCERT Biology Concept")
        if "definition" not in concept_data:
            concept_data["definition"] = top_match.get("definition", "")
        session_id = f"sess-{uuid.uuid4().hex[:8]}"
        c_id = top_match["concept_id"]
        profile = learner_manager.get_or_create_profile(student_id)
        c_mastery = profile.get("concept_mastery", {}).get(c_id, {}).get("mastery")
        if c_mastery is not None:
            initial_mastery = float(c_mastery)
        else:
            initial_mastery = float(profile.get("overall_mastery", 0.50))
        
        # Format related nodes
        related_nodes = []
        c_id = top_match["concept_id"]
        neighbors = concept_graph.get_neighbors(c_id)
        for link in neighbors:
            related_nodes.append({
                "target_id": link["target_id"],
                "target_title": link["target_title"],
                "relationship": link["relationship"]
            })

        session = {
            "session_id": session_id,
            "student_id": student_id,
            "query": query,
            "resolved_query": resolved_query,
            "concept_id": top_match["concept_id"],
            "chapter_id": top_match["chapter_id"],
            "chapter_name": top_match["chapter_name"],
            "title": top_match["title"],
            "similarity_score": top_match.get("hybrid_score", 0),
            "matched_terms": [], # retrieval_engine doesn't provide matched_terms exactly the same way
            "current_step": 1,
            "mastery_score": initial_mastery,
            "concept_data": concept_data,
            "related_nodes": related_nodes
        }
        self.active_sessions[session_id] = session
        # Bound in-memory sessions (single-process Flask): evict oldest beyond 200.
        if len(self.active_sessions) > 200:
            oldest = next(iter(self.active_sessions))
            self.active_sessions.pop(oldest, None)

        # Log step 1 to local CSV
        self.log_interaction(
            session_id=session_id,
            student_id=student_id,
            query_text=query,
            concept_id=top_match["concept_id"],
            similarity=top_match.get("hybrid_score", 0),
            step=1,
            mastery=initial_mastery,
            feedback="initialized"
        )

        return self.get_step_content(session_id, 1)

    def predict_next_learning_steps(self, concept_id: str, concept_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Intelligently predicts what the student might need next based on:
        1. Concept dependency graph links (builds_on, prerequisite, connects_to)
        2. High-frequency NEET exam pairings in the same chapter
        3. Diagnostic error-prevention traps and memory retention mnemonics
        """
        predictions = []

        # 1. Check dependency graph for relational next steps
        neighbors = concept_graph.get_neighbors(concept_id)
        for link in neighbors:
            predictions.append({
                "title": str(link["target_title"]),
                "prompt": f"Can you explain {link['target_title']}?",
                "reason": f"Predicted logical next topic ({link['relationship']}): NEET questions frequently link these together!",
                "type": "relational"
            })

        # 2. Check other concepts in same chapter from knowledge base
        df = retrieval_engine.df
        chapter_id = concept_data.get("chapter_id")
        if not df.empty and chapter_id and "chapter_id" in df.columns and "concept_id" in df.columns:
            same_chap = df[(df["chapter_id"] == chapter_id) & (df["concept_id"] != concept_id)]
            for _, row in same_chap.head(2).iterrows():
                if len(predictions) >= 3:
                    break
                predictions.append({
                    "title": str(row["title"]),
                    "prompt": f"Teach me about {row['title']}",
                    "reason": f"Chapter synergy: High probability exam connection in {row['chapter_name']}.",
                    "type": "chapter_adjacent"
                })

        # 3. Fallback high-yield predictive suggestions if needed
        if len(predictions) < 3:
            title = concept_data.get("title", "this topic")
            chap = concept_data.get("chapter_name", "Biology")
            fallbacks = [
                {
                    "title": f"Exam Traps in {chap}",
                    "prompt": f"What are the top 3 tricks examiners use in {title}?",
                    "reason": "Diagnostic prediction: Review the trickiest question patterns asked in recent NEET exams.",
                    "type": "diagnostic"
                },
                {
                    "title": f"Memory Mnemonic for {title}",
                    "prompt": f"Can you give me a simple memory trick or mnemonic for {title}?",
                    "reason": "Retention hack: Long-term memory consolidation so you never blank out in the hall.",
                    "type": "mnemonic"
                }
            ]
            for fb in fallbacks:
                if len(predictions) < 3:
                    predictions.append(fb)

        return predictions[:3]

    def get_step_content(self, session_id: str, step_number: int) -> Dict[str, Any]:
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session expired or not found. Please ask a new doubt."}

        step_number = max(1, min(4, step_number))
        session["current_step"] = step_number
        data = session["concept_data"]
        title = data["title"]
        chap = data["chapter_name"]

        content = ""
        quiz = None

        if step_number == 1:
            content = (
                f"### 👩‍⚕️ Dr. Priya (AI Biology Mentor):\n"
                f"*\"Great to explore this with you! **{title}** is one of the most high-frequency conceptual questions in {chap}. Let's look at the core NCERT foundation:\"*\n\n"
                f"**Chapter**: {chap} ({data['chapter_id'].upper()})  \n"
                f"**Core Topic**: {data['topic']} — *{title}*\n\n"
                f"> **NCERT Anchor**: {data['definition']}\n\n"
                f"*💡 Tip: Take a moment to understand this definition before we move into the biological machinery in Step 2!*"
            )
        elif step_number == 2:
            steps_raw = str(data["mechanism_steps"]).split(" -> ")
            formatted_steps = "\n".join(f"- **{s.strip()}**" for s in steps_raw)
            content = (
                f"### 👩‍⚕️ Dr. Priya (AI Biology Mentor) — Step 2: Biological Mechanism & Process Steps\n"
                f"*\"Now, let's look behind the scenes! Follow this step-by-step sequence carefully—NEET examiners love asking questions on the chronological order of these events:\"*\n\n"
                f"{formatted_steps}\n\n"
                f"*Does this biological sequence make sense? In Step 3, I'll show you the exact traps students fall into.*"
            )
        elif step_number == 3:
            content = (
                f"### 👩‍⚕️ Dr. Priya (AI Biology Mentor) — Step 3: NEET Traps & Hacks\n"
                f"*\"Pay very close attention here! Over 40% of students lose negative marks because examiners twist these exact points:\"*\n\n"
                f"**⚠️ Critical NEET Traps & Common Exam Pitfalls**:\n\n"
                f"{data['neet_traps']}\n\n"
                f"*Remember these distinctions—they frequently appear in statement-based and assertion-reason questions!*"
            )
        elif step_number == 4:
            options = str(data["sample_options"]).split("|")
            quiz = {
                "question": data["sample_question"],
                "options": options,
                "correct_index": int(data["correct_answer"])
            }
            content = (
                f"### 👩‍⚕️ Dr. Priya (AI Biology Mentor):\n"
                f"*\"You've learned the concept, the mechanism, and the traps! Now let's do a 30-second rapid diagnostic check to test your mastery. Select your answer below:\"*"
            )

        # Log progression
        self.log_interaction(
            session_id=session_id,
            student_id=session["student_id"],
            query_text=session["query"],
            concept_id=session["concept_id"],
            similarity=session["similarity_score"],
            step=step_number,
            mastery=session["mastery_score"],
            feedback=f"viewed_step_{step_number}"
        )

        predictions = self.predict_next_learning_steps(session["concept_id"], data)

        return {
            "session_id": session_id,
            "step_number": step_number,
            "step_name": self.STEPS[step_number],
            "total_steps": 4,
            "title": data["title"],
            "chapter_name": data["chapter_name"],
            "chapter_id": data["chapter_id"],
            "similarity_score": session["similarity_score"],
            "matched_terms": session["matched_terms"],
            "mastery_score": session["mastery_score"],
            "content": content,
            "quiz": quiz,
            "related_nodes": session["related_nodes"],
            "predicted_next_steps": predictions,
            "mentor": {
                "name": "Dr. Priya",
                "role": "Senior AI Biology Mentor & NEET Specialist",
                "avatar": "👩‍⚕️",
                "tagline": "Interactive Socratic Mentorship • Predictive Step Guidance"
            },
            "has_next_step": step_number < 4,
            "has_prev_step": step_number > 1
        }

    def verify_quiz(
        self, session_id: str, selected_index: int
    ) -> Dict[str, Any]:
        """
        Step 4 Quiz Verification + Bayesian Knowledge Tracing Mastery Update.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found."}

        data = session["concept_data"]
        correct_index = int(data["correct_answer"])
        is_correct = (selected_index == correct_index)

        # Update BKT mastery
        prior = session["mastery_score"]
        updated_mastery = self.bkt.update(prior, is_correct)
        session["mastery_score"] = updated_mastery

        # Log result
        self.log_interaction(
            session_id=session_id,
            student_id=session["student_id"],
            query_text=session["query"],
            concept_id=session["concept_id"],
            similarity=session["similarity_score"],
            step=4,
            mastery=updated_mastery,
            feedback="quiz_correct" if is_correct else "quiz_incorrect"
        )
        
        # Connect to persistent learner model
        try:
            learner_manager.record_attempt(
                student_id=session['student_id'],
                concept_id=session['concept_id'],
                chapter_id=session['chapter_id'],
                is_correct=is_correct,
                difficulty='medium',
                cognitive_level='BT2'
            )
        except Exception as e:
            print(f"Failed to record attempt in learner model: {e}")

        return {
            "session_id": session_id,
            "is_correct": is_correct,
            "correct_index": correct_index,
            "explanation": data["explanation"],
            "prior_mastery": prior,
            "updated_mastery": updated_mastery,
            "delta": round(updated_mastery - prior, 3)
        }

    def get_tracker_summary(self, limit: int = 20) -> Dict[str, Any]:
        """
        Reads local CSV tracker and returns audit trail for examiners.
        """
        if not self.tracker_path.exists():
            return {"records": [], "total": 0}

        df = pd.read_csv(self.tracker_path)
        records = df.tail(limit).to_dict(orient="records")
        return {
            "total_logged_interactions": len(df),
            "recent_records": records,
            "unique_concepts_studied": int(df["matched_concept_id"].nunique()),
            "average_mastery": round(float(df["mastery_score"].mean()), 3) if not df.empty else 0.0
        }


# Global singleton instance
tutor_engine = PedagogicalTracker()

def get_tutor_engine() -> PedagogicalTracker:
    return tutor_engine
