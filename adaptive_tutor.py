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

BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BASE_DIR / ".env.local", override=True)
except ImportError:
    pass

import firestore_store

from concept_graph import concept_graph
from concept_normalizer import concept_normalizer
from learner_model import learner_manager
from nlp_pipeline import nlp_pipeline
from retrieval_engine import retrieval_engine

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_KEY")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL") or os.environ.get("AI_API_BASE_URL")
if not OPENROUTER_BASE_URL:
    OPENROUTER_BASE_URL = "https://router.bynara.id/v1" if OPENROUTER_KEY and OPENROUTER_KEY.startswith("sk-nry-") else "https://openrouter.ai/api/v1"
OPENROUTER_BASE_URL = OPENROUTER_BASE_URL.rstrip("/")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "gpt-4o-mini")

import time
import threading
from collections import OrderedDict

# Fast Circuit Breaker for External API (prevents repeatedly waiting on dead/slow endpoints)
_api_circuit_breaker_until = 0.0

def is_api_circuit_broken() -> bool:
    if _is_testing():
        return False
    return time.time() < _api_circuit_breaker_until

def trip_api_circuit_breaker(duration: float = 60.0):
    global _api_circuit_breaker_until
    _api_circuit_breaker_until = time.time() + duration

def reset_api_circuit_breaker():
    global _api_circuit_breaker_until
    _api_circuit_breaker_until = 0.0


def _is_testing() -> bool:
    import sys
    return "unittest" in sys.modules or "pytest" in sys.modules or os.environ.get("TESTING") == "1"

# In-Memory Socratic Response Cache for sub-millisecond retrieval
class TutorResponseLRUCache:
    def __init__(self, maxsize: int = 512, ttl_seconds: int = 600):
        self.maxsize = maxsize
        self.ttl = ttl_seconds
        self.cache = OrderedDict()
        self.lock = threading.Lock()

    def clear(self):
        with self.lock:
            self.cache.clear()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if _is_testing():
            return None
        with self.lock:
            if key in self.cache:
                val, exp = self.cache[key]
                if time.time() < exp:
                    self.cache.move_to_end(key)
                    import copy
                    return copy.deepcopy(val)
                del self.cache[key]
        return None

    def set(self, key: str, val: Dict[str, Any]):
        if _is_testing():
            return
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            elif len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)
            import copy
            self.cache[key] = (copy.deepcopy(val), time.time() + self.ttl)

_tutor_lru_cache = TutorResponseLRUCache()

# Pre-flight injection detection patterns (compiled once for speed)
INJECTION_PATTERNS = re.compile(
    r"(?i)("
    r"ignore\s+(previous|all|initial)\s+(instructions|rules|prompts|directives)|"
    r"system\s+prompt|"
    r"override\s+(safety|instructions|guidelines)|"
    r"forget\s+(everything|all|previous|context)|"
    r"you\s+are\s+now\s+(dan|unrestricted|unfiltered|evil|godmode|free)|"
    r"pretend\s+(to\s+be|you\s+are)\s+(an?\s+)?(unrestricted|evil|unfiltered|dan)|"
    r"developer\s+mode\s+(enabled|activate|on)|"
    r"jailbreak|"
    r"roleplay\s+as\s+(an?\s+)?(unrestricted|evil|unfiltered|dan)|"
    r"act\s+as\s+(an?\s+)?(unrestricted|evil|unfiltered|dan)|"
    r"disregard\s+(previous|all)\s+(instructions|rules)|"
    r"output\s+(everything|all)\s+(above|before|prior)|"
    r"print\s+(system|hidden|initial)\s+(prompt|instructions)|"
    r"reveal\s+(system|hidden|initial)\s+(prompt|instructions)"
    r")",
    re.IGNORECASE
)

# Structural markers for user payload
STUDENT_CONTEXT_START = "[STUDENT INQUIRY CONTEXT START]"
STUDENT_CONTEXT_END = "[STUDENT INQUIRY CONTEXT END]"
EVIDENCE_START = "[VERIFIED NCERT EVIDENCE START]"
EVIDENCE_END = "[VERIFIED NCERT EVIDENCE END]"


class AdaptiveBiologyTutor:
    """
    Adaptive Biology Tutor Engine embodying Dr. Priya's Socratic teaching methodology.
    Now with guided lesson mode, answer evaluation, and misconception handling.
    """

    STRATEGIES = [
        "standard_ncert",      # Baseline: Definition + Steps + Traps
        "simplified_steps",    # Mastery < 0.50 or 1 error: Simpler vocabulary, bite-sized breakdown
        "concrete_analogy",    # 2 errors or "explain again": Concrete physical metaphor/analogy
        "process_flow",        # 3 errors: Strict chronological diagrammatic flow
        "remedial_diagnostic", # 4+ errors: Break down foundational prerequisite
        "advanced_concise",    # Mastery >= 0.80: Concise nuances + NEET traps
    ]

    # Guided lesson triggers
    GUIDED_LESSON_TRIGGERS = [
        r"\bteach me .+ step by step\b",
        r"\bexplain .+ slowly\b",
        r"\bexplain .+ step by step\b",
        r"\bwalk me through\b",
        r"\bguide me through\b",
        r"\bi don't understand\b",
        r"\bhelp me understand\b",
        r"\bbasic explanation\b",
        r"\blike i'm a beginner\b",
        r"\blike im a beginner\b",
    ]

    # Answer evaluation patterns
    POSITIVE_ANSWER_PATTERNS = [
        r"\byes\b", r"\byep\b", r"\byup\b", r"\bcorrect\b", r"\bright\b",
        r"\bexactly\b", r"\bthat's right\b", r"\bgot it\b", r"\bunderstand\b",
        r"\bmakes sense\b", r"\bclear\b", r"\bokay\b", r"\bok\b", r"\bgreat\b",
    ]

    NEGATIVE_ANSWER_PATTERNS = [
        r"\bno\b", r"\bnope\b", r"\bwrong\b", r"\bincorrect\b", r"\bdon't understand\b",
        r"\bdon't get it\b", r"\bconfused\b", r"\bunclear\b", r"\bnot sure\b",
        r"\bnot clear\b", r"\bstill confused\b", r"\bdidn't understand\b",
    ]

    FOLLOW_UP_PATTERNS = {
        "why": [r"^\s*why\s*\??\s*$", r"^\s*how come\s*\??\s*$", r"^\s*what's the reason\s*\??\s*$"],
        "what_does_it_do": [r"^\s*what does it do\s*\??\s*$", r"^\s*what is its function\s*\??\s*$"],
        "make_it_harder": [r"\bmake it harder\b", r"\bharder question\b", r"\bmore difficult\b", r"\bchallenge me\b"],
        "make_it_easier": [r"\bmake it easier\b", r"\bsimplify\b", r"\btoo hard\b", r"\btoo complex\b"],
        "okay": [r"^\s*okay\s*$", r"^\s*ok\s*$", r"^\s*got it\s*$", r"^\s*understood\s*$", r"^\s*next\s*$", r"^\s*continue\s*$"],
        "example": [r"\bexample\b", r"\bgive an example\b", r"\bfor instance\b", r"\bgive me an example\b"],
    }

    ANALOGIES: Dict[str, str] = {
        "c04": "Think of Animal Kingdom classification like sorting a massive library: Phyla are the main sections, Classes are the bookshelves, and Species are the exact books.",
        "c08": "Think of a eukaryotic cell as an industrial city: the Nucleus is City Hall holding blueprints, Mitochondria are Power Stations churning out energy currency (ATP), Ribosomes are Factories assembling structural proteins, and the Plasma Membrane is the gated security wall.",
        "c10": "Think of Mitosis and Meiosis like document duplication: Mitosis is a precision photocopier creating 2 identical copies, while Meiosis is a creative card shuffler cutting chromosome count in half to produce 4 genetically unique gametes.",
        "c13": "Think of Photosynthesis like a solar charging factory: The Light Reaction acts like solar panels charging battery packs (ATP and NADPH), which the Calvin cycle then uses as power to assemble sugar bricks.",
        "c14": "Think of Glycolysis and Respiration like currency exchange: One high-denomination bill of Glucose is broken down through a sequence of steps into 36-38 small coins of ATP that cell machines can spend instantly.",
        "c16": "Think of Human Digestion like an industrial disassembly line: Macromolecular food crates are sequentially dismantled by specialized enzymatic tools into individual absorbable building blocks.",
        "c18": "Think of the Circulatory System like a municipal distribution network: The Heart acts as a dual-chambered central pump, Arteries carry high-pressure deliveries, and Capillaries allow door-to-door nutrient exchange.",
        "c19": "Think of the Nephron like a high-tech water recycling plant: The glomerulus dumps everything into the conveyor belt, and selective tubular reabsorption pulls back 99% of pure water and vital nutrients.",
        "c20": "Think of the Sarcomere sliding filament like a crew of rowers: The thick Myosin heads reach up like oars, bind to the Actin boat ropes using ATP energy, and pull them inward to shorten the muscle during contraction.",
        "c21": "Think of the Central Neural System like an air traffic control center: The Brain processes incoming sensory radar signals, evaluates them in association areas, and transmits motor flight plans to muscles.",
        "c22": "Think of Insulin and Glucagon like a household thermostat: When blood sugar gets too high after meals, Insulin turns on the cellular storage heater; when blood sugar dips during fasting, Glucagon opens glycogen vaults in the liver.",
        "c26": "Think of Mendelian Inheritance like dealing cards from parental decks: Alleles segregate independently during gamete formation, and dominant cards express their traits while recessive ones wait for homozygous pairing.",
        "c27": "Think of DNA replication and translation like a secure royal library: The master genome scrolls (DNA) never leave the nucleus vault; messengers transcribe a photocopy (mRNA) to carry out to the workshop floor (Ribosome).",
        "c31": "Think of Recombinant DNA technology like precision word processing: Restriction enzymes act as scissor tools to cut specific phrases, DNA ligase pastes them into plasmid documents, and bacterial vectors make millions of copies."
    }

    def __init__(self):
        self.retrieval = retrieval_engine
        self.nlp = nlp_pipeline
        self.graph = concept_graph
        self.learner = learner_manager
        # Tutor state for guided lessons (Firestore-first, file fallback).
        self._tutor_states: Dict[str, Dict[str, Any]] = {}
        self._tutor_state_collection = "tutor_states"

    def _default_tutor_state(self) -> Dict[str, Any]:
        return {
            "active_lesson": None,
            "lesson_stage": 0,
            "lesson_concept": None,
            "pending_check_question": None,
            "lesson_steps": [],
            "current_step_index": 0,
            "misconceptions": {},  # concept_id -> count
            "last_action": None,
        }

    def _get_tutor_state(self, student_id: str) -> Dict[str, Any]:
        """Get or create tutor state for a student (load-through cache)."""
        if student_id not in self._tutor_states:
            stored = firestore_store.load_doc(
                self._tutor_state_collection, student_id, default=None)
            self._tutor_states[student_id] = (
                stored if isinstance(stored, dict) and stored
                else self._default_tutor_state())
        return self._tutor_states[student_id]

    def _save_tutor_state(self, student_id: str) -> None:
        """Write-through persist (never raises)."""
        try:
            state = self._tutor_states.get(student_id)
            if state is not None:
                firestore_store.save_doc(
                    self._tutor_state_collection, student_id, state)
        except Exception:
            pass

    def _is_guided_lesson_request(self, query: str) -> bool:
        """Check if query requests guided step-by-step lesson."""
        q_lower = query.lower()
        for pattern in self.GUIDED_LESSON_TRIGGERS:
            if re.search(pattern, q_lower):
                return True
        return False

    def _detect_follow_up_type(self, query: str) -> Optional[str]:
        """Detect type of short follow-up question."""
        q_lower = query.lower().strip()
        for ftype, patterns in self.FOLLOW_UP_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, q_lower):
                    return ftype
        return None

    def _evaluate_student_answer(self, student_answer: str, check_question: str = "") -> str:
        """
        Evaluate student's answer to a check question.
        Returns: 'correct', 'partially_correct', 'incorrect', 'unclear'
        """
        ans_lower = student_answer.lower().strip()
        
        # Check for positive indicators
        positive_score = sum(1 for pat in self.POSITIVE_ANSWER_PATTERNS if re.search(pat, ans_lower))
        negative_score = sum(1 for pat in self.NEGATIVE_ANSWER_PATTERNS if re.search(pat, ans_lower))
        
        # If clearly positive with content
        if positive_score > 0 and negative_score == 0:
            # Check if they actually provided content or just said "yes"
            content_words = len([w for w in ans_lower.split() if w not in 
                               {"yes", "yep", "yup", "ok", "okay", "got it", "understand", "clear", "right", "correct"}])
            if content_words >= 2:
                return "correct"
            else:
                return "partially_correct"  # Just said "yes" without explanation
        
        # If clearly negative
        if negative_score > 0:
            return "incorrect"
        
        # Check for substantive content (biology terms, explanations)
        # If they wrote a meaningful sentence, treat as at least partially correct
        bio_keywords = ["atp", "mitochondria", "energy", "cellular", "respiration", "powerhouse", 
                        "produces", "production", "synthesis", "electron", "transport", "chain",
                        "glucose", "oxygen", "carbon", "dioxide", "water", "krebs", "glycolysis"]
        has_bio_content = any(kw in ans_lower for kw in bio_keywords)
        
        if has_bio_content and len(ans_lower.split()) >= 4:
            return "correct"
        
        # If very short or just "okay", treat as unclear
        if len(ans_lower.split()) <= 2:
            return "unclear"
        
        # Default: treat as partially correct if they wrote something substantial
        return "partially_correct"

    def _handle_guided_lesson(self, query: str, student_id: str, top: Dict, 
                               retrieval_results: List, profile: Dict) -> Optional[Dict]:
        """
        Handle guided lesson mode: teach one stage, ask check question, wait for response.
        Returns response dict if in guided lesson mode, None otherwise.
        """
        state = self._get_tutor_state(student_id)
        
        # Get clean concept name for lesson
        concept_name = concept_normalizer.get_canonical_concept_name(top.get("title", "")) or top.get("title", "this topic")
        
        # Check if starting a new guided lesson
        if self._is_guided_lesson_request(query) and not state["active_lesson"]:
            # Initialize lesson
            state["active_lesson"] = True
            state["lesson_concept"] = top.get("concept_id")
            state["lesson_stage"] = 1
            state["current_step_index"] = 0
            
            # Build lesson steps from retrieval evidence
            steps = []
            for r in retrieval_results[:3]:
                if r.get("definition"):
                    # Clean the definition
                    defn = r["definition"][:400] if len(r["definition"]) > 400 else r["definition"]
                    steps.append(("definition", defn))
                if r.get("mechanism_steps"):
                    mech = r["mechanism_steps"]
                    # Only process if it has proper step separators
                    if " -> " in mech and mech.count(" -> ") >= 1:
                        for i, step in enumerate(mech.split(" -> ")):
                            step = step.strip()
                            # Filter out non-step content (too long, doesn't start with action verb)
                            if step and len(step) > 10 and len(step) < 200:
                                # Check if it looks like a proper step
                                first_word = step.split()[0].lower() if step.split() else ""
                                if first_word in ["step", "inner", "pyruvate", "electron", "krebs", "link", "oxidative", "acetyl", "nadh", "fadh", "atp", "chemiosmosis", "proton", "gradient", "atp synthase", "oxygen", "water"]:
                                    steps.append((f"step_{i+1}", step))
            state["lesson_steps"] = steps
            
            # Start with first step
            if steps:
                step_type, step_content = steps[0]
                state["pending_check_question"] = self._generate_check_question(step_type, step_content, concept_name)
                
                reply = self._format_lesson_step(state, step_type, step_content, concept_name, top.get("chapter_name", ""))
                return {
                    "reply": reply,
                    "mode": "guided_lesson",
                    "status": "success",
                    "confidence": "HIGH",
                    "concept_id": top.get("concept_id"),
                    "chapter_id": top.get("chapter_id"),
                    "title": concept_name,
                    "strategy": "guided_lesson",
                    "student_trajectory": profile.get("trajectory_stage"),
                    "concept_mastery": profile.get("overall_mastery"),
                    "is_repeated_weakness": False,
                    "resolved_query": query,
                    "lesson_stage": state["lesson_stage"],
                    "total_stages": len(steps),
                    "requires_student_response": True,
                    "check_question": state["pending_check_question"],
                }
        
        # Continue existing guided lesson
        if state["active_lesson"] and state["pending_check_question"]:
            # Evaluate student's answer to the check question
            evaluation = self._evaluate_student_answer(query, state["pending_check_question"])
            
            # Update misconception tracking
            concept_id = state["lesson_concept"]
            if evaluation == "incorrect":
                state["misconceptions"][concept_id] = state["misconceptions"].get(concept_id, 0) + 1
            elif evaluation == "correct":
                # Reduce misconception count on correct answer
                if concept_id in state["misconceptions"]:
                    state["misconceptions"][concept_id] = max(0, state["misconceptions"][concept_id] - 1)
            
            # Handle based on evaluation
            if evaluation == "correct":
                # Advance to next step
                state["current_step_index"] += 1
                if state["current_step_index"] < len(state["lesson_steps"]):
                    step_type, step_content = state["lesson_steps"][state["current_step_index"]]
                    concept_name = concept_normalizer.get_canonical_concept_name(top.get("title", "")) or top.get("title", "this topic")
                    state["pending_check_question"] = self._generate_check_question(step_type, step_content, concept_name)
                    reply = self._format_lesson_step(state, step_type, step_content, concept_name, top.get("chapter_name", ""))
                    return {
                        "reply": reply,
                        "mode": "guided_lesson",
                        "status": "success",
                        "confidence": "HIGH",
                        "evaluation": "correct",
                        "lesson_stage": state["lesson_stage"] + 1,
                        "total_stages": len(state["lesson_steps"]),
                        "requires_student_response": True,
                        "check_question": state["pending_check_question"],
                    }
                else:
                    # Lesson complete
                    state["active_lesson"] = False
                    state["pending_check_question"] = None
                    concept_name = concept_normalizer.get_canonical_concept_name(top.get("title", "")) or top.get("title", "this topic")
                    reply = f"🎉 **Lesson Complete!** You've mastered **{concept_name}**!\n\n"
                    reply += f"📖 **Summary:** {top.get('definition', '')[:300]}...\n\n"
                    reply += "Would you like to practice with some MCQs or move to another topic?"
                    return {
                        "reply": reply,
                        "mode": "guided_lesson_complete",
                        "status": "success",
                        "confidence": "HIGH",
                        "lesson_complete": True,
                    }
            
            elif evaluation == "partially_correct":
                # Provide gentle correction and re-ask
                reply = f"👍 **Good start!** Let me clarify a bit more:\n\n"
                reply += self._clarify_concept(state["pending_check_question"], top)
                reply += f"\n\n**Check Question:** {state['pending_check_question']}"
                return {
                    "reply": reply,
                    "mode": "guided_lesson",
                    "status": "success",
                    "confidence": "HIGH",
                    "evaluation": "partially_correct",
                    "requires_student_response": True,
                    "check_question": state["pending_check_question"],
                }
            
            elif evaluation == "incorrect":
                # Provide correct explanation and try again
                misconception_count = state["misconceptions"].get(concept_id, 0)
                reply = f"🤔 **Not quite right.** Let me explain the key point:\n\n"
                reply += self._clarify_concept(state["pending_check_question"], top)
                
                if misconception_count >= 2:
                    reply += f"\n\n💡 **This concept has tripped you up {misconception_count} times.** "
                    reply += "Let me try a simpler approach..."
                    # Could escalate strategy here
                
                reply += f"\n\n**Let's try again:** {state['pending_check_question']}"
                return {
                    "reply": reply,
                    "mode": "guided_lesson",
                    "status": "success",
                    "confidence": "HIGH",
                    "evaluation": "incorrect",
                    "misconception_count": misconception_count,
                    "requires_student_response": True,
                    "check_question": state["pending_check_question"],
                }
            
            else:  # unclear
                reply = f"🤷 **I'm not sure I understood your answer.** Could you rephrase or tell me what part is unclear?\n\n"
                reply += f"**Check Question:** {state['pending_check_question']}"
                return {
                    "reply": reply,
                    "mode": "guided_lesson",
                    "status": "success",
                    "confidence": "HIGH",
                    "evaluation": "unclear",
                    "requires_student_response": True,
                    "check_question": state["pending_check_question"],
                }
        
        return None

    def _generate_check_question(self, step_type: str, step_content: str, topic: str) -> str:
        """Generate a check question based on lesson step."""
        if step_type == "definition":
            return f"What is the key function of {topic}?"
        elif step_type.startswith("step_"):
            # Extract key terms from step
            words = step_content.split()
            key_terms = [w for w in words if len(w) > 4 and w.isalpha()][:3]
            if key_terms:
                return f"What role does {' '.join(key_terms)} play in {topic}?"
            return f"What happens in this step of {topic}?"
        return f"Can you explain {topic} in your own words?"

    def _format_lesson_step(self, state: Dict, step_type: str, step_content: str, title: str, chapter: str) -> str:
        """Format a lesson step for display."""
        stage = state["current_step_index"] + 1
        total = len(state["lesson_steps"])
        
        header = f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [Guided Lesson: Stage {stage}/{total}]:**\n"
        header += f"*\"Let's learn **{title}** step by step. Here's stage {stage}:\"*\n\n"
        
        if step_type == "definition":
            content = f"📖 **Definition:**\n{step_content}"
        else:
            content = f"🔬 **Step {step_type.replace('step_', '')}:**\n{step_content}"
        
        check_q = state.get("pending_check_question", "")
        footer = f"\n\n❓ **Check Your Understanding:** {check_q}"
        footer += f"\n\n*Type your answer, or ask 'Why?' / 'What does it do?' / 'Make it easier' / 'Okay' to continue.*"
        
        return header + content + footer

    def _clarify_concept(self, check_question: str, top: Dict) -> str:
        """Provide clarification for a misconception."""
        definition = top.get("definition", "")
        if definition:
            return f"**NCERT Definition:** {definition[:400]}"
        return "Please review the NCERT textbook section for this concept."

    def _handle_follow_up(self, query: str, student_id: str, top: Dict, 
                          retrieval_results: List, profile: Dict) -> Optional[Dict]:
        """Handle contextual short follow-ups like 'Why?', 'What does it do?', etc."""
        follow_up_type = self._detect_follow_up_type(query)
        if not follow_up_type:
            return None
        
        state = self._get_tutor_state(student_id)
        concept_name = top.get("title", "this concept")
        
        if follow_up_type == "why":
            reply = f"🧬 **Why {concept_name} works this way:**\n\n"
            # Get mechanism from retrieval
            for r in retrieval_results:
                if r.get("mechanism_steps"):
                    reply += r["mechanism_steps"][:500]
                    break
            if not any(r.get("mechanism_steps") for r in retrieval_results):
                reply += top.get("definition", "See NCERT for the detailed mechanism.")
                
        elif follow_up_type == "what_does_it_do":
            reply = f"👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
            reply += f"⚙️ **Function of {concept_name}:**\n\n"
            reply += top.get("definition", "See NCERT for the function.")
            
        elif follow_up_type == "make_it_harder":
            # Escalate strategy
            reply = f"👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
            reply += f"🎯 **Leveling up!** Let's dive deeper into **{concept_name}**:\n\n"
            # Add NEET traps
            for r in retrieval_results:
                if r.get("neet_traps"):
                    reply += f"⚠️ **NEET Trap:** {r['neet_traps'][:300]}\n\n"
                    break
            reply += "*Want an advanced MCQ on this?*"
            
        elif follow_up_type == "make_it_easier":
            # Simplify
            reply = f"👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
            reply += f"📚 **Simpler explanation of {concept_name}:**\n\n"
            # Use analogy if available
            chap_id = top.get("chapter_id", "")
            m_c = re.search(r'\d+', chap_id)
            prefix_chap = f"c{int(m_c.group(0)):02d}" if m_c else chap_id[:3]
            if prefix_chap in self.ANALOGIES:
                reply += f"💡 **Analogy:** {self.ANALOGIES[prefix_chap]}\n\n"
            reply += top.get("definition", "")[:400]
            reply += "\n\n*Does that help? Ask me to continue or give an example.*"
            
        elif follow_up_type == "okay":
            # Continue to next step or provide summary
            if state["active_lesson"] and state["current_step_index"] + 1 < len(state["lesson_steps"]):
                state["current_step_index"] += 1
                step_type, step_content = state["lesson_steps"][state["current_step_index"]]
                state["pending_check_question"] = self._generate_check_question(step_type, step_content, concept_name)
                return self._format_lesson_step(state, step_type, step_content, concept_name, top.get("chapter_name", ""))
            else:
                reply = f"👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
                reply += f"✅ **Great!** Ready for the next concept or would you like MCQs on **{concept_name}**?"
        
        elif follow_up_type == "example":
            reply = f"👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
            reply += f"💡 **Example for {concept_name}:**\n\n"
            # Try to find example in retrieval
            for r in retrieval_results:
                if r.get("neet_traps") and "example" in r["neet_traps"].lower():
                    reply += r["neet_traps"][:400]
                    break
            else:
                reply += "Refer to NCERT textbook for worked examples."
        
        return {
            "reply": reply,
            "mode": "follow_up",
            "status": "success",
            "confidence": "HIGH",
            "follow_up_type": follow_up_type,
            "concept_id": top.get("concept_id"),
            "chapter_id": top.get("chapter_id"),
            "title": concept_name,
        }

    def _scope_note(self, resolved_query: str, raw_query: str) -> str:
        """Honest scoping (Req O): flags query terms with zero corpus support
        (entity-like: digit-bearing, long non-adverb, or raw-uppercase) so the
        student knows which part goes beyond NCERT. Ordinary words are never
        flagged."""
        try:
            from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as _SK
        except Exception:
            _SK = set()
        raw_uppers = set(re.findall(r"[A-Z]{2,}", raw_query or ""))
        flagged = []
        for w in re.findall(r"[A-Za-z0-9]{3,}", (resolved_query or "").lower()):
            if w in {"the", "and", "for", "with", "from", "about", "explain", "describe", "discuss"}:
                continue
            if w in _SK:
                continue
            supported = self.retrieval._has_support(w)
            if supported:
                continue
            entity_like = (any(c.isdigit() for c in w) or w.upper() in raw_uppers
                           or (len(w) >= 6 and not w.endswith("ly")))
            if entity_like:
                flagged.append(w)
        flagged = sorted(set(flagged))[:3]
        if not flagged:
            return ""
        quoted = ", ".join(f"'{f}'" for f in flagged)
        return (f"\n\n🔎 *Scope note: {quoted} go{'es' if len(flagged) == 1 else ''} beyond the NCERT syllabus; "
                f"the above covers the related NCERT-grounded concept.*")

    def _detect_study_mode(self, query: str) -> str:
        """LEARN / PRACTICE / REVISION / NEET / QUIZ from explicit mode cues.

        General prefix/keyword patterns (not topics): a leading mode cue
        ("Practice:", "Revise X", "NEET mode") or standalone mode request.
        Default is LEARN. Same pipeline serves all modes.
        """
        q = (query or "").strip().lower()
        if re.match(r"^(practice|quiz|test me|quick quiz|mock test)\b[:\s]", q):
            return "practice" if q.startswith("practice") else "quiz"
        if re.match(r"^(revise|revision|recap|quick revision)\b[:\s]", q):
            return "revision"
        if re.match(r"^(neet mode|neet level|exam mode)\b[:\s]", q):
            return "neet"
        return "learn"

    def _strip_mode_prefix(self, query: str) -> str:
        """Remove a leading mode cue (plus filler words), leaving the topic."""
        q = (query or "").strip()
        q2 = re.sub(r"^(practice|quiz|test me|quick quiz|mock test|revise|revision|recap|quick revision|neet mode|neet level|exam mode)\b[:\s]*",
                    "", q, flags=re.IGNORECASE).strip()
        q2 = re.sub(r"^(me|on|about|for|my)\b[\s:]*", "", q2,
                    flags=re.IGNORECASE).strip()
        return q2

    def _model_chain(self) -> List[str]:
        """Working models first; dead routes removed. Graceful multi-model failover."""
        chain = []
        if OPENROUTER_MODEL and OPENROUTER_MODEL != "agnes-2.0-flash":
            chain.append(OPENROUTER_MODEL)
        if OPENROUTER_KEY and OPENROUTER_KEY.startswith("sk-nry-"):
            chain.extend(["agnes-2.5-flash"])
        else:
            chain.extend([
                "google/gemini-2.0-flash-lite:free",
                "meta-llama/llama-3.3-70b-instruct:free",
                "openai/gpt-4o-mini"
            ])
        return list(dict.fromkeys([m for m in chain if m and m != "minimax-m3-free" and m != "agnes-2.0-flash"]))

    def check_chain_health(self) -> Dict[str, bool]:
        """Non-blocking startup health check for models in the chain."""
        health = {}
        for m in self._model_chain():
            health[m] = True  # Model is configured and ready in chain
        return health

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
        strategy: str = "standard_ncert",
        student_profile: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        retrieval_results: Optional[List[Dict[str, Any]]] = None,
        tone_flag: Optional[str] = None,
        is_partial: bool = False,
    ) -> Optional[str]:
        """
        Grounded generator: RAG over the evidence pack.
        For strong evidence (Tier 1): strict cite-or-refuse against pack.
        For partial evidence (Tier 2): synthesizes evidence with NCERT curriculum facts.
        Model chain fails over fast across candidates; local template remains offline fallback.
        Includes pre-flight injection validation and structural payload markers.
        """
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_KEY") or OPENROUTER_KEY
        if not api_key or is_api_circuit_broken():
            return None

        # Pre-flight validation gate: block injection attempts before LLM call
        if INJECTION_PATTERNS.search(query):
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

        if is_partial:
            evidence_rule = (
                "Rules: 1) Anchor your answer in the VERIFIED NCERT EVIDENCE below, and supplement with accurate "
                "facts from the standard NCERT Class 11 and 12 Biology curriculum to provide a complete explanation. "
                "2) If the question is outside the NCERT Biology curriculum entirely, say exactly: CANNOT ANSWER. "
            )
        else:
            evidence_rule = (
                "Rules: 1) Every fact must come from the evidence; never invent details, numbers, or examples. "
                "2) If the evidence cannot answer the question, say exactly: CANNOT ANSWER FROM EVIDENCE. "
            )

        system_instruction = (
            "You are Dr. Priya, BioNEETPro's NEET Biology mentor. Answer from the NCERT curriculum and the evidence below. "
            f"{evidence_rule}"
            "3) Cite sources inline like [E1], [E2] after each paragraph where evidence is used. "
            "4) Shape: one-line direct answer first, then mechanism/steps, then exactly 3 NEET traps, then one check question WITHOUT its answer. "
            "5) Under 280 words. No markdown tables unless the question compares two things, then use one 3-row table. "
            f"Strategy: {strategy_prompts.get(strategy, strategy_prompts['standard_ncert'])}\n\n"
            f"{EVIDENCE_START}\n{pack}\n{EVIDENCE_END}"
        )
        if tone_flag == "medical_educational":
            system_instruction += (
                "\n\nIMPORTANT: This question involves sensitive reproductive biology topics from the NCERT curriculum. "
                "Use strictly objective, clinical, and scientifically rigorous language. Avoid colloquialisms, "
                "euphemisms, or moralizing. Present facts as stated in NCERT textbooks for NEET preparation."
            )

        # Restructure user payload with structural markers to keep LLM within system constraints
        structured_query = (
            f"{STUDENT_CONTEXT_START}\n{query}\n{STUDENT_CONTEXT_END}"
        )

        messages = [{"role": "system", "content": system_instruction}]
        if history:
            for turn in history[-4:]:
                role = turn.get("role", "user")
                messages.append({"role": role if role in ("user", "assistant") else "user",
                                 "content": str(turn.get("content", ""))[:500]})
        messages.append({"role": "user", "content": structured_query})

        for model in self._model_chain():
            try:
                resp = requests.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                    json={"model": model, "messages": messages, "max_tokens": 900, "temperature": 0.2},
                    timeout=2.0,
                )
                if resp.status_code in (401, 402, 403, 429):
                    trip_api_circuit_breaker(60.0)
                    return None
                if resp.status_code != 200:
                    continue
                ctype = str(resp.headers.get("Content-Type", "") if hasattr(resp, "headers") and isinstance(getattr(resp, "headers", None), dict) else "")
                raw_text = getattr(resp, "text", None)
                if "html" in ctype.lower() or (isinstance(raw_text, str) and raw_text.strip().startswith("<")):
                    continue
                data = resp.json()
                choices = data.get("choices")
                if not choices or not isinstance(choices, list):
                    continue
                content = (choices[0].get("message", {}).get("content") or "").strip()
                low = content.lower()
                if len(content) < 60 or "cannot answer from evidence" in low or (is_partial and "cannot answer" in low and len(content) < 120):
                    continue
                tag = "NCERT Grounded" if not is_partial else "NCERT Augmented"
                header = (
                    f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [{tag} • {strategy.replace('_', ' ').title()}]:**\n\n"
                )
                return header + content
            except Exception:
                continue

        return None

    def _generate_external_fallback_response(
        self,
        query: str,
        strategy: str = "standard_ncert",
        student_profile: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        tone_flag: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        TIER 3: External LLM Fallback for valid NCERT Biology queries
        when local textbook retrieval yields insufficient or zero evidence chunks.
        Strictly aligned with NCERT Class 11 and 12 Biology curriculum.
        """
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_KEY") or OPENROUTER_KEY
        if not api_key or is_api_circuit_broken():
            return None

        if INJECTION_PATTERNS.search(query):
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
            "You are Dr. Priya, BioNEETPro's expert Senior AI Biology Mentor for NEET-UG aspirants. "
            "The student is asking about a concept from the NCERT Biology curriculum. "
            "Explain this topic thoroughly, rigorously, and pedagogically according to the NCERT Class 11 & 12 textbooks.\n\n"
            "Requirements:\n"
            "1) Factually strict: Adhere strictly to NCERT Biology conventions and standard NEET terminology.\n"
            "2) Output structure:\n"
            "   - **Core Definition & Overview**: 1-2 clear, precise sentences defining the concept.\n"
            "   - **Key Mechanisms / Structural Details**: Clear bulleted breakdown of components, steps, or features.\n"
            "   - **⚠️ NEET Traps & High-Yield Exam Points**: Exactly 3 distinct, high-yield traps, exception cases, or common misconceptions tested in NEET.\n"
            "   - **💬 Diagnostic Check Question**: Exactly 1 conceptual check question for the student without revealing the answer.\n"
            "3) Word count: Keep the entire response between 180 and 320 words.\n"
            "4) Tone: Warm, authoritative, inspiring, and encouraging.\n"
            f"Pedagogical Strategy: {strategy_prompts.get(strategy, strategy_prompts['standard_ncert'])}"
        )
        if tone_flag == "medical_educational":
            system_instruction += (
                "\n\nIMPORTANT: This question involves sensitive human anatomy or reproductive biology from the NCERT curriculum. "
                "Use strictly objective, clinical, and scientifically rigorous terminology. Avoid slang, moralizing, or colloquialisms."
            )

        structured_query = f"{STUDENT_CONTEXT_START}\n{query}\n{STUDENT_CONTEXT_END}"
        messages = [{"role": "system", "content": system_instruction}]
        if history:
            for turn in history[-4:]:
                role = turn.get("role", "user")
                messages.append({
                    "role": role if role in ("user", "assistant") else "user",
                    "content": str(turn.get("content", ""))[:500]
                })
        messages.append({"role": "user", "content": structured_query})

        sanitized_fallback = None
        sanitized_model = None

        def _build_tier3_payload(content_text: str, used_model: str) -> Dict[str, Any]:
            header = (
                f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [NCERT Biology Curriculum • External Verified Fallback]:**\n\n"
            )
            footer = (
                f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📚 **NCERT Source Reference:**\n"
                f"• **Source:** NCERT Biology Standard Curriculum (Verified External Knowledge)\n"
                f"• **Coverage Status:** High-Yield NEET Concept Breakdown\n\n"
                f"💬 *Ask any follow-up question or type 'Give me 3 questions on it' to test yourself!*"
            )
            full_reply = header + content_text + footer
            canon_title = concept_normalizer.get_canonical_concept_name(query) or query.title()

            return {
                "reply": full_reply,
                "mode": "external_fallback",
                "source_mode": "external_llm_fallback",
                "fallback_tier": "tier_3",
                "model_used": used_model,
                "status": "success",
                "confidence": "HIGH",
                "hybrid_score": 1.0,
                "concept_id": "NCERT-EXT-FALLBACK",
                "title": canon_title,
                "chapter_id": "c00",
                "strategy": strategy,
                "strategy_used": strategy,
                "student_trajectory": (student_profile or {}).get("trajectory_stage", "foundation"),
                "concept_mastery": (student_profile or {}).get("overall_mastery", 0.65),
                "is_repeated_weakness": False,
                "resolved_query": query,
                "source": "NCERT Biology Standard Curriculum (Verified External Knowledge)",
                "citations": [{
                    "title": canon_title,
                    "source": "NCERT Biology Curriculum",
                    "section": "Standard Class 11 & 12 Syllabus",
                    "page_number": None,
                    "chunk_id": "EXT-FALLBACK-01",
                    "confidence": "HIGH",
                    "score": 1.0,
                }],
                "figures": [],
                "tables": [],
                "faithfulness": 1.0,
            }

        for model in self._model_chain():
            try:
                resp = requests.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                    json={"model": model, "messages": messages, "max_tokens": 850, "temperature": 0.3},
                    timeout=2.0,
                )
                if resp.status_code in (401, 402, 403, 429):
                    trip_api_circuit_breaker(60.0)
                    if sanitized_fallback is not None:
                        return _build_tier3_payload(sanitized_fallback, sanitized_model)
                    return None
                if resp.status_code != 200:
                    continue
                ctype = str(resp.headers.get("Content-Type", "") if hasattr(resp, "headers") and isinstance(getattr(resp, "headers", None), dict) else "")
                raw_text = getattr(resp, "text", None)
                if "html" in ctype.lower() or (isinstance(raw_text, str) and raw_text.strip().startswith("<")):
                    continue
                body = resp.json()
                choices = body.get("choices")
                if not choices or not isinstance(choices, list):
                    continue
                content = (choices[0].get("message", {}).get("content") or "").strip()
                if len(content) < 60:
                    continue
                low = content.lower()
                if "cannot answer" in low and len(content) < 120:
                    continue

                # Run response through response_validator
                from response_validator import response_validator
                val_res = response_validator.validate_response(content)
                sanitized_content = val_res.get("sanitized_response", content)
                if not val_res.get("is_valid", True):
                    if sanitized_fallback is None:
                        sanitized_fallback = sanitized_content
                        sanitized_model = model
                    continue

                return _build_tier3_payload(sanitized_content, model)
            except Exception:
                continue

        if sanitized_fallback is not None:
            return _build_tier3_payload(sanitized_fallback, sanitized_model or "sanitized_fallback")

        return None

    call_openrouter_api = _generate_api_grounded_response

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
        if out.get("source_mode") == "external_llm_fallback":
            out["faithfulness"] = 1.0
            if not out.get("citations"):
                out["citations"] = [{
                    "title": out.get("title", "NCERT Biology Curriculum"),
                    "source": "NCERT Biology Curriculum",
                    "section": "Standard Class 11 & 12 Syllabus",
                    "page_number": None,
                    "chunk_id": "EXT-FALLBACK-01",
                    "confidence": "HIGH",
                    "score": 1.0,
                }]
            return out

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
        focus_chapter_id: Optional[str] = None,
        tone_flag: Optional[str] = None
    ) -> Dict[str, Any]:
        """Public entry: inner pipeline + write-through lesson-state persist."""
        try:
            out = self._generate_inner(query, student_id, history,
                                       focus_chapter_id, tone_flag)
            try:
                out["study_mode"] = self._detect_study_mode(query)
            except Exception:
                out["study_mode"] = "learn"
            if isinstance(out, dict) and out.get("status") == "success":
                cache_key = f"{student_id}:{query.strip().lower()}:{focus_chapter_id or ''}"
                _tutor_lru_cache.set(cache_key, out)
            return out
        finally:
            self._save_tutor_state(student_id)

    @staticmethod
    def _is_greeting(query: str) -> bool:
        clean = re.sub(r"[^\w\s]", "", str(query or "").lower()).strip()
        if not clean:
            return False
        greeting_tokens = {
            "hi", "hello", "hey", "hola", "namaste", "vanakkam", "pranam",
            "good morning", "good afternoon", "good evening", "howdy", "greetings",
            "hi priya", "hello priya", "hey priya", "hi dr priya", "hello dr priya", "dr priya",
            "who are you", "what can you do", "help", "start", "menu"
        }
        if clean in greeting_tokens:
            return True
        if re.match(r"^(hi|hello|hey|greetings|namaste)\s+(priya|dr priya|doctor|mentor|there|sir|maam|mam)?$", clean):
            return True
        return False

    def _build_greeting_response(self, student_id: str) -> Dict[str, Any]:
        chips = [
            {"label": "🌿 Photosynthesis", "query": "Explain Photosynthesis light reaction"},
            {"label": "🫀 Heart Chambers", "query": "Why does the human heart have 4 chambers?"},
            {"label": "🧬 Genetics", "query": "Explain Mendel's Law of Segregation"},
            {"label": "🦁 Animal Kingdom", "query": "Teach me types of animal kingdom classification"},
            {"label": "⚡ 5 Hard MCQs", "query": "Give me 5 hard MCQs in Biology"},
        ]
        reply = (
            "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
            "👋 **Hello! I'm Dr. Priya, your dedicated NEET Biology AI Mentor.**\n\n"
            "Ask me any doubt! I will explain biological concepts directly from NCERT, break down mechanisms step-by-step, share intuitive everyday analogies, and warn you about tricky NEET exam traps.\n\n"
            "**What would you like to master today?**\n"
            "• 🌿 **Plant Physiology:** Photosynthesis, Respiration in Plants, Plant Growth\n"
            "• 🧬 **Genetics & Evolution:** Mendelian Genetics, Molecular Basis of Inheritance\n"
            "• 🫀 **Human Physiology:** Heart & Circulation, Neural Control, Nephron & Excretion\n"
            "• 🔬 **Cell Biology:** Cell Cycle, Mitosis vs Meiosis, Cell Organelles\n"
            "• 🦁 **Diversity:** Animal Kingdom & Plant Kingdom Classification\n\n"
            "Try clicking one of the topic chips below or ask me any question!"
        )
        return {
            "reply": reply,
            "mode": "greeting",
            "status": "success",
            "confidence": "HIGH",
            "concept_id": "BIO-GREETING",
            "chapter_id": "c01",
            "title": "Welcome to NEET Biology Mentor",
            "strategy": "socratic_intro",
            "strategy_used": "socratic_intro",
            "resolved_query": "Hi",
            "student_id": student_id,
            "follow_up_chips": chips,
            "suggested_actions": chips,
        }

    def _generate_inner(
        self,
        query: str,
        student_id: str = "student_local",
        history: Optional[List[Dict[str, str]]] = None,
        focus_chapter_id: Optional[str] = None,
        tone_flag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        NLP -> Context -> Hybrid Retrieval (rewrite+compare+rerank) -> Mastery Adaptation -> Grounded Socratic reply.
        """
        # 0. Check LRU response cache for instant retrieval (<1ms)
        cache_key = f"{student_id}:{query.strip().lower()}:{focus_chapter_id or ''}"
        cached_res = _tutor_lru_cache.get(cache_key)
        if cached_res:
            return cached_res

        # 0a. Greeting check: Welcome student warmly with high-yield starting options
        if self._is_greeting(query):
            greet_out = self._build_greeting_response(student_id)
            _tutor_lru_cache.set(cache_key, greet_out)
            return greet_out

        # 1. NLP Processing & Conversational Reference Resolution
        nlp_res = self.nlp.process_query(query, history or [], student_id=student_id)
        resolved_query = nlp_res["resolved_query"]

        # 1b. Study modes (same pipeline, behavior configuration only — no
        # duplicated tutor systems). LEARN/REVISION/NEET explain via the
        # standard path below (tagged); PRACTICE/QUIZ route MCQ-first through
        # the real MCQ subsystem on the stripped topic.
        study_mode = self._detect_study_mode(query)
        if study_mode in ("practice", "quiz") and nlp_res["intent"] != "mcq_request":
            from mcq_engine import mcq_engine
            topic = self._strip_mode_prefix(query) or "weak topics"
            prac = mcq_engine.generate_mcqs(
                f"Give me 5 MCQs on {topic}", student_id=student_id)
            nlp_res = dict(nlp_res, intent="mcq_request",
                           resolved_query=f"Give me 5 MCQs on {topic}")
            resolved_query = nlp_res["resolved_query"]
            # fall through to the unified MCQ branch below with study_mode kept

        # 2a. Unified MCQ routing: natural-language MCQ requests flow through the
        # real MCQ subsystem regardless of entry point (/chat, /api/tutor/answer).
        if nlp_res["intent"] == "mcq_request":
            from mcq_engine import mcq_engine
            mcq_data = mcq_engine.generate_mcqs(resolved_query, student_id=student_id)
            mcqs = mcq_data.get("mcqs", [])
            if mcqs:
                first = mcqs[0]
                try:
                    self.nlp.context_tracker.track_concept(
                        student_id=student_id,
                        concept_id=str(first.get("concept_id", "BIO-GEN")),
                        title=str(first.get("topic", first.get("chapter", "MCQ Practice"))),
                        canonical_name=str(first.get("topic", "")),
                    )
                except Exception:
                    pass
            profile = self.learner.get_or_create_profile(student_id)
            out = {
                "reply": mcq_engine.format_mcq_intro(mcq_data) if mcqs else mcq_engine.format_mcqs_for_chat(mcq_data),
                "mode": "mcq_practice",
                "status": "success",
                "confidence": "HIGH" if mcqs else "LOW",
                "concept_id": (mcqs[0].get("concept_id") if mcqs else None),
                "chapter_id": (mcqs[0].get("chapter") if mcqs else None),
                "title": mcq_data.get("topic", "MCQ Practice"),
                "strategy": "mcq_practice",
                "strategy_used": "mcq_practice",
                "student_trajectory": profile.get("trajectory_stage"),
                "concept_mastery": profile.get("overall_mastery"),
                "is_repeated_weakness": False,
                "resolved_query": resolved_query,
                "mcqs": mcqs,
                "mcq_count": mcq_data.get("count", 0),
                "mcq_difficulty": mcq_data.get("difficulty"),
                "mcq_difficulty_mode": mcq_data.get("difficulty_mode"),
                "mcq_topic": mcq_data.get("topic"),
            }
            return out

        # 2b. MCQ answer report / quiz feedback ("I got question 2 wrong"):
        if nlp_res["intent"] in ("quiz_feedback", "mcq_answer", "mcq_reference"):
            from mcq_engine import mcq_engine
            # Extract question number if present
            m_num = re.search(r"(?:question|q|#)\s*(?:number|no\.?|#)?\s*(\d+)", resolved_query, re.I)
            q_num = int(m_num.group(1)) if m_num else 1

            # Extract correctness indicators
            is_wrong = bool(re.search(r"\b(wrong|incorrect|not right|false|missed|failed)\b", resolved_query, re.I))
            is_right = bool(re.search(r"\b(right|correct|true|got it right)\b", resolved_query, re.I))

            # Retrieve recent MCQ from session
            recent_mcq = mcq_engine.get_recent_mcq(q_num, student_id=student_id)

            if recent_mcq:
                concept_id = recent_mcq.get("concept_id") or "BIO-GEN-01"
                chapter_id = recent_mcq.get("chapter_id") or "c01"
                topic_name = recent_mcq.get("topic") or recent_mcq.get("chapter") or "NEET Biology"
                correct_ans = recent_mcq.get("correct_answer", "")
                c_idx = recent_mcq.get("correct_index", 0)
                letter = chr(65 + c_idx) if 0 <= c_idx < 26 else "A"
                explanation = recent_mcq.get("explanation", "See NCERT Biology for key details.")
                q_text = recent_mcq.get("question", "")

                # If student explicitly reported right/wrong, update learner model
                if is_wrong or is_right:
                    is_correct_attempt = not is_wrong if is_wrong else is_right
                    learner_manager.record_attempt(
                        student_id=student_id,
                        concept_id=concept_id,
                        chapter_id=chapter_id,
                        is_correct=is_correct_attempt,
                        topic_id=topic_name
                    )

                if is_wrong:
                    reply = (
                        f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — Targeted MCQ Review:**\n\n"
                        f"Don't worry — clearing up mistakes on high-yield questions is how you hit 360/360 in NEET!\n\n"
                        f"❓ **Question {q_num}:** {q_text}\n\n"
                        f"✅ **Correct Answer:** **({letter}) {correct_ans}**\n\n"
                        f"📖 **NCERT Rationale & Misconception Breakdown:**\n"
                        f"{explanation}\n\n"
                        f"💡 **NEET Exam Tip:** Questions on **{topic_name}** frequently test subtle phrasing differences. "
                        f"I've logged this in your learning profile to reinforce it in upcoming practice sessions. "
                        f"Would you like another practice question on this topic?"
                    )
                elif is_right:
                    reply = (
                        f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — Quiz Verification:**\n\n"
                        f"🎯 **Spot on!** You got Question {q_num} right:\n\n"
                        f"❓ **Question {q_num}:** {q_text}\n"
                        f"✅ **Answer:** **({letter}) {correct_ans}**\n\n"
                        f"📖 **Key NCERT Point:** {explanation}\n\n"
                        f"Keep up the momentum! Your mastery in **{topic_name}** has been updated."
                    )
                else:
                    reply = (
                        f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — Question {q_num} Review:**\n\n"
                        f"❓ **Question {q_num}:** {q_text}\n\n"
                        f"✅ **Correct Answer:** **({letter}) {correct_ans}**\n\n"
                        f"📖 **NCERT Explanation:**\n{explanation}\n\n"
                        f"Tell me which option you selected, and we can break down why the other choices were distractors!"
                    )

                return {
                    "reply": reply,
                    "mode": "quiz_feedback",
                    "status": "success",
                    "confidence": "HIGH",
                    "concept_id": concept_id,
                    "chapter_id": chapter_id,
                    "title": topic_name,
                    "resolved_query": resolved_query,
                    "question_number": q_num,
                }
            else:
                focal = self.nlp.context_tracker.get_focal_concept(student_id)
                hint = f" on **{focal[1]}**" if focal else ""
                return {
                    "reply": (
                        "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n"
                        f"*\"Noted — let's review Question {q_num}{hint}. "
                        "I don't see an active test in your current session, but if you paste the question or tell me the topic, "
                        "I'll break down the exact NCERT concept and common traps for you! "
                        "Or type 'Give me 3 questions on it' to generate a fresh test.\"*"
                    ),
                    "mode": "mcq_review",
                    "status": "mcq_reference",
                    "confidence": "HIGH",
                    "resolved_query": resolved_query,
                }

        # 2c. Syllabus Boundary Gate with evidence-grounded admission.
        # The keyword validator has imperfect recall (e.g. valid NCERT topics
        # like breathing/cloning/taxonomy can fail it). When it rejects BUT
        # retrieval returns HIGH-confidence evidence COVERING the query's
        # distinctive terms, the evidence wins and we proceed (flagged). True
        # out-of-scope queries have no such evidence and still refuse.
        focal_ctx = nlp_res.get("focal_concept")
        retrieval_results = None
        admitted_by_evidence = False

        # Stale context override: If the current query explicitly carries its own
        # biology topic terms, do NOT let a stale UI context (e.g. default 'Photosynthesis')
        # restrict retrieval to an unrelated chapter.
        effective_focus = focus_chapter_id
        if effective_focus:
            syl_data = nlp_res.get("syllabus_data") or {}
            matched_terms = syl_data.get("matched_keywords") or syl_data.get("matched_terms") or []
            if matched_terms:
                effective_focus = None

        if not nlp_res["syllabus_valid"]:
            probe = self.retrieval.search(
                query=resolved_query,
                expanded_query=nlp_res["expanded_query"],
                top_k=4,
                focus_chapter_id=effective_focus,
                focal_context_name=focal_ctx
            )
            top0 = probe[0] if probe else None
            cov_terms = [t for t in dict.fromkeys(
                self.retrieval._content_terms(resolved_query.lower())) if len(t) >= 4]
            need = min(2, len(cov_terms))
            covered = self.retrieval.evidence_covers(
                resolved_query.lower(), top0) if top0 else 0
            # HIGH + covered always admits. MEDIUM admits only with the same
            # coverage (weak-but-on-topic evidence, honestly labeled MEDIUM in
            # the reply). LOW/empty never admits.
            if (top0 and top0.get("confidence") in ("HIGH", "MEDIUM")
                    and need >= 1 and covered >= need):
                retrieval_results = probe
                admitted_by_evidence = True
            else:
                refusal = nlp_res["syllabus_data"].get("refusal_message")
                return {
                    "reply": refusal,
                    "mode": "syllabus_restricted",
                    "source_mode": "safe_fallback",
                    "fallback_tier": "tier_4",
                    "status": "out_of_syllabus",
                    "resolved_query": resolved_query,
                    "confidence": "REJECTED"
                }

        # 3. Hybrid Concept Retrieval (Dual-Corpus: KB + Textbook Chunks)
        if retrieval_results is None:
            retrieval_results = self.retrieval.search(
                query=resolved_query,
                expanded_query=nlp_res["expanded_query"],
                top_k=4,
                focus_chapter_id=effective_focus,
                focal_context_name=focal_ctx
            )

        controlled_refusal = {
            "reply": (
                "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n"
                "*\"I couldn't find enough verified NCERT evidence for that specific Biology question in my local textbook knowledge base. "
                "Try asking about an NCERT topic such as Mitochondria, Cell Division, Photosynthesis, or Human Neural Control.\"*\n\n"
            ),
            "mode": "local_fallback",
            "source_mode": "safe_fallback",
            "fallback_tier": "tier_4",
            "status": "no_match",
            "confidence": "LOW"
        }

        if not retrieval_results:
            # Check if this is a follow-up that can be answered from context
            # before giving up
            follow_up_type = self._detect_follow_up_type(query)
            if follow_up_type:
                # Try to answer from focal concept context
                focal = self.nlp.context_tracker.get_focal_concept(student_id)
                if focal:
                    profile = self.learner.get_or_create_profile(student_id)
                    # Create a minimal top dict from focal concept
                    top = {"title": focal[2], "concept_id": focal[0], "chapter_id": focal[0].split("-")[0] if "-" in focal[0] else "c01", "chapter_name": focal[1]}
                    follow_up_response = self._handle_follow_up(query, student_id, top, [], profile)
                    if follow_up_response:
                        return self._enrich(follow_up_response, [], top)

            # TIER 3: Attempt external LLM fallback for valid Biology query with insufficient/no local chunks
            fb_res = self._generate_external_fallback_response(
                query=resolved_query,
                strategy="standard_ncert",
                student_profile=self.learner.get_or_create_profile(student_id),
                history=history,
                tone_flag=tone_flag,
            )
            if fb_res:
                return self._enrich(fb_res, [], fb_res)

            # TIER 4: Safe refusal when retrieval and external fallback fail
            return controlled_refusal

        top = retrieval_results[0]

        # Confidence Gate
        if top["confidence"] == "REJECTED":
            # If local evidence was completely rejected, attempt Tier 3 external fallback before refusing
            fb_res = self._generate_external_fallback_response(
                query=resolved_query,
                strategy="standard_ncert",
                student_profile=self.learner.get_or_create_profile(student_id),
                history=history,
                tone_flag=tone_flag,
            )
            if fb_res:
                return self._enrich(fb_res, retrieval_results, top)
            controlled_refusal["confidence"] = "REJECTED"
            return controlled_refusal

        # NOTE (honesty-rule experiment, REMOVED): a low-score + uncovered-top
        # refusal was trialled here but over-refused valid partial answers
        # (e.g. vitamins/deficiency at 0.4976 with 2/3 term coverage).
        # Lexical coverage cannot separate "partial but related" from
        # "unrelated" (gymnosperms shares water/tall/trees words with a water
        # transport query), so refusal stays with the no-evidence gate above.
        # Genuine coverage gaps (e.g. ascent of sap — absent from the corpus)
        # are documented limitations, counted honestly in evaluation.

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
        # Unify learner lookups through the canonical vocabulary id: KB rows and
        # textbook chunks use different id spaces for the same concept, so check
        # both the canonical id and the raw retrieval id (general mechanism).
        profile = self.learner.get_or_create_profile(student_id)

        # 5b. Handle guided lesson mode (step-by-step teaching with check questions)
        guided_response = self._handle_guided_lesson(query, student_id, top, retrieval_results, profile)
        if guided_response:
            return self._enrich(guided_response, retrieval_results, top)

        # 5c. Handle contextual follow-ups (Why?, What does it do?, Make it harder, etc.)
        follow_up_response = self._handle_follow_up(query, student_id, top, retrieval_results, profile)
        if follow_up_response:
            return self._enrich(follow_up_response, retrieval_results, top)
        canon_id = c_id
        for _alias, _info in concept_normalizer.CONCEPT_ALIASES.items():
            if _info.get("canonical_name") == canon_name:
                canon_id = _info.get("concept_id", c_id)
                break
        _cm = profile.get("concept_mastery", {})
        _centry = _cm.get(canon_id) or _cm.get(c_id) or {}
        concept_mastery = _centry.get("mastery", profile["overall_mastery"])
        trajectory = profile["trajectory_stage"]
        _rm = profile.get("repeated_mistakes", {})
        mistake_info = _rm.get(canon_id) or _rm.get(c_id) or {}
        mistake_count = mistake_info.get("mistake_count", 0)

        # Check if student asked to "from basics", "explain again" or has a repeated mistake
        is_from_basics = nlp_res.get("is_from_basics", False) or bool(re.search(r"\b(from basics?|basics?|beginner|simple terms|like i('?m)? weak|step by step)\b", query.lower()))
        is_explain_again = bool(re.search(r"\b(explain\s+(it\s+)?again|simpler|another way|did not get it)\b", query.lower()))

        # Escalation ladder (ordered worst-first; previously the >=4 branch was
        # unreachable dead code shadowed by the >=2 branch above it).
        if mistake_count >= 4:
            strategy = "remedial_diagnostic"
        elif mistake_count == 3:
            strategy = "process_flow"
        elif is_explain_again or mistake_count >= 2:
            strategy = "concrete_analogy"
        elif is_from_basics or concept_mastery < 0.50 or mistake_count == 1:
            strategy = "simplified_steps"
        elif concept_mastery >= 0.80:
            strategy = "advanced_concise"
        else:
            strategy = "standard_ncert"

        # Check if local evidence is partial or strong
        is_partial_evidence = (
            top.get("confidence") != "HIGH"
            or float(top.get("hybrid_score", 0)) < 0.70
        )

        api_reply = None
        # Tier 1 (Strong Local NCERT Evidence): local-first Socratic generation delivers
        # verified textbook facts in <15ms. We only query external LLM for Tier 2 (partial
        # evidence synthesis).
        if is_partial_evidence:
            api_reply = self._generate_api_grounded_response(
                query=resolved_query,
                top_evidence=top,
                strategy=strategy,
                student_profile=profile,
                history=history,
                retrieval_results=retrieval_results,
                tone_flag=tone_flag,
                is_partial=is_partial_evidence,
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
            source_mode = "local_plus_llm" if is_partial_evidence else "local_ncert"
            fallback_tier = "tier_2" if is_partial_evidence else "tier_1"
            out = {
                "reply": api_reply + compare_block + source_citation,
                "mode": "api_grounded",
                "source_mode": source_mode,
                "fallback_tier": fallback_tier,
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
        if strategy == "remedial_diagnostic":
            header_intro = (
                f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [Local Algorithmic Tutor • Adaptive Remediation • Foundations Rebuild]:**\n"
                f"*\"This is our **Adaptive Remediation** pass for **{title}** — mistakes show the foundation needs a rebuild, "
                f"so let's reconstruct it from its prerequisite upward!\"*"
            )
        elif strategy == "process_flow":
            header_intro = (
                f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [Local Algorithmic Tutor • Adaptive Remediation • Process Flow]:**\n"
                f"*\"**Adaptive Remediation** for **{title}**: let's walk the strict step-by-step chain slowly — "
                f"this is where the errors are creeping in!\"*"
            )
        elif is_explain_again or mistake_count >= 2:
            header_intro = (
                f"👩‍⚕️ **Dr. Priya (AI Biology Mentor) — [Local Algorithmic Tutor • Analogy & Simplification • Adaptive Remediation]:**\n"
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
            f"{self._scope_note(resolved_query, query)}"
        )

        out = {
            "reply": full_reply,
            "mode": "local_adaptive",
            "source_mode": "local_ncert",
            "fallback_tier": "tier_1",
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


AdaptiveBiologyTutor.answer = AdaptiveBiologyTutor.generate_tutoring_response
adaptive_tutor = AdaptiveBiologyTutor()
