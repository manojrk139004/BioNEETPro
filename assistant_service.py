"""
BioNEETPro V2 - Multi-Role AI Assistant Service
Provides contextual, role-aware AI guidance for:
1. STUDENT: Dr. Priya (NEET Biology Tutor & Mentor)
2. TEACHER: Prof. Sharma (Pedagogical Assessment & Curriculum Consultant)
3. SUPER_ADMIN / ADMIN: BioNEETPro Systems & Operations Advisor
"""

import os
import re
import json
import time
import logging
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
from syllabus import syllabus_validator, get_canonical_curriculum
from learner_model import learner_manager
from retrieval_engine import retrieval_engine

logger = logging.getLogger("assistant_service")

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_KEY")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL") or os.environ.get("AI_API_BASE_URL")
if not OPENROUTER_BASE_URL:
    OPENROUTER_BASE_URL = "https://router.bynara.id/v1" if OPENROUTER_KEY and OPENROUTER_KEY.startswith("sk-nry-") else "https://openrouter.ai/api/v1"
OPENROUTER_BASE_URL = OPENROUTER_BASE_URL.rstrip("/")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "gpt-4o-mini")

# Safety injection guardrail regex
INJECTION_REGEX = re.compile(
    r"(?i)(ignore\s+(previous|all)\s+instructions|system\s+prompt|jailbreak|override\s+safety|you\s+are\s+now\s+dan|pretend\s+to\s+be\s+unrestricted)",
    re.IGNORECASE
)

STUDENT_SYSTEM_PROMPT = """You are Dr. Priya, an expert, encouraging NEET Biology Mentor at BioNEETPro.
Your mission is to help students excel in NEET Biology (Class 11 & Class 12 NCERT).
Guidelines:
1. Strictly stay within the NCERT Biology curriculum. If asked about non-biology subjects (physics, chemistry, politics, coding, etc.), politely guide the student back to Biology.
2. Emphasize high-yield NCERT lines, diagrams, mnemonics, and common NEET exam traps.
3. Be supportive, concise, and structured with bullet points where appropriate.
4. If the student asks about their weak topics or test preparation, encourage them and offer targeted concept reviews."""

TEACHER_SYSTEM_PROMPT = """You are Prof. Sharma, Academic Biology Specialist and Assessment Consultant for BioNEETPro Educators.
Your mission is to assist teachers and faculty members in crafting exceptional NEET Biology assessments and lessons.
Guidelines:
1. Help teachers construct rigorous, NCERT-grounded MCQs (assertion-reason, statement-based, match-the-column, diagrammatic).
2. Assist in balancing test difficulty (Easy ~30%, Medium ~50%, Hard ~20%) across Class 11 & 12 units.
3. Provide pedagogical advice on addressing common student misconceptions in specific chapters.
4. Refuse non-educational queries, keeping all guidance focused on school/college assessment engineering."""

ADMIN_SYSTEM_PROMPT = """You are the BioNEETPro Institutional Operations & Systems Advisor.
Your mission is to support school and college administrators in overseeing their institutional assessment platform.
Guidelines:
1. Guide admins on managing teacher accounts, monitoring assessment schedules, and reviewing platform audit records.
2. Provide concise summaries of institutional metrics, completion rates, and curriculum coverage.
3. Explain platform security policies, role-based permissions (SUPER_ADMIN, TEACHER, STUDENT), and data integrity standards.
4. Keep all responses formal, clear, and actionable."""


class AssistantService:
    def __init__(self):
        self.openrouter_key = OPENROUTER_KEY
        self.openrouter_url = OPENROUTER_BASE_URL
        self.model = OPENROUTER_MODEL
        self._api_cooldown_until: float = 0.0

    def _call_llm(self, system_prompt: str, messages: List[Dict[str, str]]) -> Optional[str]:
        if not self.openrouter_key:
            return None
        if time.time() < getattr(self, "_api_cooldown_until", 0):
            return None
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://bio-neet-pro.vercel.app",
                "X-Title": "BioNEETPro Assistant"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "system", "content": system_prompt}] + messages[-8:],
                "temperature": 0.4,
                "max_tokens": 600,
            }
            res = requests.post(f"{self.openrouter_url}/chat/completions", headers=headers, json=payload, timeout=2.5)
            if res.status_code == 200:
                data = res.json()
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "").strip()
            elif res.status_code in (401, 403):
                self._api_cooldown_until = time.time() + 300
                logger.warning(f"Assistant LLM key invalid/unauthorized (status {res.status_code}); cooldown set for 300s.")
        except (requests.Timeout, requests.ConnectionError):
            self._api_cooldown_until = time.time() + 60
            logger.warning("Assistant LLM call timed out/connection failed; set circuit breaker for 60s.")
        except Exception as e:
            logger.warning(f"Assistant LLM call failed: {e}")
        return None

    def _student_fallback(self, query: str, student_id: str) -> str:
        # Check boundary first
        boundary = syllabus_validator.check_query_syllabus(query)
        if not boundary.get("is_valid"):
            return boundary.get("refusal_message", "Please ask questions regarding the NCERT NEET Biology syllabus.")

        # Check weak topics query
        q_low = query.lower()
        if any(w in q_low for w in ["weak", "improve", "my progress", "score", "where to study"]):
            profile = learner_manager.get_profile(student_id)
            weak_concepts = profile.get("weak_concepts", [])
            if weak_concepts:
                weak_list = "\n".join([f"• **{c}**" for c in weak_concepts[:5]])
                return (
                    f"👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
                    f"Based on your recent practice sessions, here are the topics you should focus on:\n\n"
                    f"{weak_list}\n\n"
                    f"💡 **Recommendation:** Spend 20 minutes reviewing the NCERT chapter lines and take a targeted Chapter Test in the Teacher/Assessment section!"
                )
            else:
                return (
                    "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
                    "Great work! Your mastery across practiced topics is solid. Keep up the momentum by attempting upcoming scheduled assessments or practicing mixed Mock Tests."
                )

        # Use retrieval engine to answer query
        results = retrieval_engine.search(query, top_k=2)
        if results:
            top = results[0]
            title = top.get("title") or top.get("topic") or "Biology Concept"
            definition = top.get("definition") or top.get("content") or ""
            traps = top.get("neet_traps", "Be mindful of exact NCERT exceptions.")
            return (
                f"👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
                f"📌 **{title}**\n\n"
                f"{definition}\n\n"
                f"⚠️ **NEET Exam Trap:**\n{traps}\n\n"
                f"📖 *Reference: NCERT Biology ({top.get('chapter_name', 'NEET Syllabus')})*"
            )

        return (
            "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
            "Here is the key NCERT insight: Master the exact definitions and diagram labeling. "
            "Could you specify the exact chapter or concept (e.g. *Photosynthesis*, *Mendelian Genetics*, *Nephron*) so I can guide you precisely?"
        )

    def _teacher_fallback(self, query: str, context: Dict[str, Any]) -> str:
        q_low = query.lower()
        if any(w in q_low for w in ["question", "mcq", "create test", "assessment", "draft"]):
            return (
                "👨‍🏫 **Prof. Sharma (Assessment Consultant):**\n\n"
                "Here are proven best practices for designing a balanced NEET Biology assessment:\n\n"
                "1. **Difficulty Distribution:**\n"
                "   • **Easy (30%):** Direct recall and definition questions (e.g. hormone functions, enzyme names).\n"
                "   • **Medium (50%):** Application, multi-statement evaluation, and diagram-based analysis.\n"
                "   • **Hard (20%):** Assertion-Reasoning with subtle nuances, high-yield NCERT traps, and multi-step physiological pathways.\n\n"
                "2. **Effective Distractors:** Ensure wrong options represent common student misconceptions rather than arbitrary facts.\n\n"
                "👉 *Use our **Assessment Builder** wizard in the Teacher Portal to draft, AI-generate, and schedule your test directly!*"
            )
        elif any(w in q_low for w in ["chapter", "syllabus", "class 11", "class 12"]):
            curriculum = get_canonical_curriculum()
            return (
                f"👨‍🏫 **Prof. Sharma (Assessment Consultant):**\n\n"
                f"BioNEETPro adheres strictly to the canonical 33 rationalized NCERT chapters across Class 11 and Class 12.\n\n"
                f"• **Class 11:** 19 core chapters (Units 1-5: Diversity, Anatomy/Morphology, Cell, Plant Physiology, Human Physiology)\n"
                f"• **Class 12:** 14 core chapters (Units 6-10: Reproduction, Genetics, Human Welfare, Biotechnology, Ecology)\n\n"
                f"You can select any unit or chapter from the Assessment Builder cascading selector to create targeted unit or chapter tests."
            )
        else:
            return (
                "👨‍🏫 **Prof. Sharma (Assessment Consultant):**\n\n"
                "Hello Colleague! I am here to help you structure upcoming tests, craft high-quality NCERT MCQs, and interpret your class analytics. "
                "How can I assist your teaching today?"
            )

    def _admin_fallback(self, query: str, context: Dict[str, Any]) -> str:
        q_low = query.lower()
        if any(w in q_low for w in ["teacher", "account", "faculty", "add teacher"]):
            return (
                "👑 **BioNEETPro Administrator Advisor:**\n\n"
                "**Teacher Management Protocol:**\n"
                "• Administrators can create teacher credentials with institutional emails in the **Admin Portal** (`/api/admin/teachers`).\n"
                "• Teachers are given scoped access: they can author assessments, manage questions, and view submissions for their own tests.\n"
                "• If a faculty member leaves or is on leave, an Admin can update their status to `INACTIVE` or `SUSPENDED` with immediate session revocation."
            )
        elif any(w in q_low for w in ["audit", "security", "role", "permission"]):
            return (
                "👑 **BioNEETPro Administrator Advisor:**\n\n"
                "**Security & Governance Summary:**\n"
                "• **Role Hierarchy:** `SUPER_ADMIN` > `TEACHER` > `STUDENT`.\n"
                "• **Authentication Mode:** Server-side Firebase ID token verification with fail-closed security.\n"
                "• **Data Isolation:** Students can never view unreleased answer keys; duplicate submission locks prevent multi-attempt tampering.\n"
                "• All administrative actions are recorded in immutable audit logs."
            )
        else:
            return (
                "👑 **BioNEETPro Administrator Advisor:**\n\n"
                "Welcome to the Institutional Management Assistant. "
                "You can ask me about teacher onboarding, assessment governance, system performance metrics, or institutional compliance."
            )

    def chat(
        self,
        role: str,
        user_id: str,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes a chat query tailored to the user's role.
        """
        clean_msg = (message or "").strip()
        if not clean_msg:
            return {"error": "Message cannot be empty.", "reply": "Please enter a message."}

        # Check injection
        if INJECTION_REGEX.search(clean_msg):
            return {
                "reply": "⚠️ Security Alert: Prompt injection or instruction override attempt detected. Query rejected.",
                "role": role,
                "status": "rejected"
            }

        norm_role = (role or "STUDENT").upper()
        history_msgs = history or []
        ctx = context or {}

        # 1. Format LLM call if available
        if norm_role == "TEACHER":
            sys_prompt = TEACHER_SYSTEM_PROMPT
        elif norm_role in ("SUPER_ADMIN", "ADMIN"):
            sys_prompt = ADMIN_SYSTEM_PROMPT
        else:
            sys_prompt = STUDENT_SYSTEM_PROMPT

        formatted_history = []
        for h in history_msgs[-6:]:
            r = "assistant" if h.get("role") in ("assistant", "model") else "user"
            c = str(h.get("content") or "").strip()
            if c:
                formatted_history.append({"role": r, "content": c[:1000]})
        formatted_history.append({"role": "user", "content": clean_msg[:2000]})

        llm_reply = self._call_llm(sys_prompt, formatted_history)
        if llm_reply:
            if norm_role == "TEACHER" and "Sharma" not in llm_reply:
                llm_reply = f"👨‍🏫 **Prof. Sharma (Assessment Specialist):**\n\n{llm_reply}"
            elif norm_role in ("SUPER_ADMIN", "ADMIN") and "Administrator" not in llm_reply and "Admin" not in llm_reply:
                llm_reply = f"👑 **BioNEETPro Operations (Administrator Support):**\n\n{llm_reply}"
            elif norm_role == "STUDENT" and "Priya" not in llm_reply:
                llm_reply = f"👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n{llm_reply}"

            chips = self._get_role_chips(norm_role, clean_msg, llm_reply)
            return {
                "reply": llm_reply,
                "role": norm_role,
                "mode": "ai_assistant_online",
                "status": "success",
                "chips": chips,
                "suggested_actions": chips,
            }

        # 2. Local fallback by role
        if norm_role == "TEACHER":
            reply = self._teacher_fallback(clean_msg, ctx)
        elif norm_role in ("SUPER_ADMIN", "ADMIN"):
            reply = self._admin_fallback(clean_msg, ctx)
        else:
            reply = self._student_fallback(clean_msg, user_id)

        chips = self._get_role_chips(norm_role, clean_msg, reply)
        return {
            "reply": reply,
            "role": norm_role,
            "mode": "local_assistant_knowledge",
            "status": "success",
            "chips": chips,
            "suggested_actions": chips,
        }

    def _get_role_chips(self, role: str, message: str, reply: str) -> List[Dict[str, str]]:
        norm_role = (role or "STUDENT").upper()
        if norm_role == "TEACHER":
            return [
                {"label": "📝 5 Balanced MCQs", "query": "Suggest 5 balanced MCQs for this topic with difficulty distribution"},
                {"label": "⚠️ Common Student Traps", "query": "What misconceptions and traps do students encounter here?"},
                {"label": "⚖️ Test Blueprints", "query": "How should I structure a 45-minute NEET Biology assessment?"},
            ]
        elif norm_role in ("SUPER_ADMIN", "ADMIN"):
            return [
                {"label": "👑 Faculty Management", "query": "How do teacher accounts and permissions work?"},
                {"label": "🔐 Security & Integrity", "query": "What security guardrails protect student submissions?"},
                {"label": "📊 System Overview", "query": "Give me a summary of institutional governance policies"},
            ]
        else:
            return [
                {"label": "🧪 Take 3-Q Quiz", "query": "Give me 3 practice questions on this topic"},
                {"label": "💡 NEET Exam Trap", "query": "What are the common NEET exam traps on this?"},
                {"label": "🧠 Mnemonic", "query": "Give me a memorable mnemonic for this"},
                {"label": "👶 Explain Simpler", "query": "Explain this in very simple everyday terms with an analogy"},
            ]


assistant_service = AssistantService()
 
