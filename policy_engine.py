"""
BioNEET-Pro — Policy Engine
===========================
Translates 6-class content classifications into strict, pedagogical safety actions:

Policy Matrix:
- Academic: ALLOW -> Routes to NCERT biology retrieval and tutor engine.
- Educational-Sensitive: ALLOW (with "medical_educational" tone flag) ->
  Permits high-yield reproduction and sexual health questions while ensuring
  an objective, scientific, medical framing without moralizing.
- Off-Topic: REDIRECT -> Gentle syllabus boundary guidance pointing student back
  to high-yield NEET Biology concepts.
- Inappropriate: BLOCK -> Polite but firm boundary refusal maintaining a respectful
  learning environment.
- Harmful: BLOCK -> Zero-tolerance refusal. If self-harm or suicide is detected,
  provides immediate crisis support resources (Tele-MANAS, KIRAN, 988).
- Prompt-Injection: BLOCK -> Ignores hijacked instructions, resets boundary,
  and re-anchors to Dr. Priya AI Biology Tutor persona.
"""

from typing import Any, Dict, Optional
import re


CRISIS_HELPLINE_MESSAGE = (
    "👩‍⚕️ **Dr. Priya (BioNEET-Pro Mentor & Healthcare Support):**\n\n"
    "💙 **We care about your safety and well-being.** If you are experiencing distress, "
    "feeling overwhelmed, or having thoughts of self-harm, please reach out right now — "
    "compassionate, confidential support is available 24/7:\n\n"
    "📞 **Tele-MANAS (India - Toll Free):** **14416** or **1800-891-4416**\n"
    "📞 **KIRAN Mental Health Helpline (India):** **1800-599-0019**\n"
    "📞 **International Crisis Hotline:** Call or text **988** (or contact your local emergency services)\n\n"
    "You do not have to go through this alone. Please talk to a trusted family member, doctor, or counselor."
)

HARMFUL_SAFETY_MESSAGE = (
    "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
    "⚠️ **Safety & Compliance Notice:**\n"
    "I cannot fulfill requests involving dangerous substances, violence, weapons, or illegal activities. "
    "BioNEET-Pro is strictly committed to safe, accredited medical entrance (NEET) biology education.\n\n"
    "Let's redirect our focus to high-yield NCERT Biology concepts!"
)

INAPPROPRIATE_MESSAGE = (
    "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
    "⚠️ **Community Standards Notice:**\n"
    "Please maintain a respectful, professional learning environment. "
    "I am here to help you excel in NEET Biology. Feel free to ask any academic question from Class 11 or 12 NCERT!"
)

PROMPT_INJECTION_MESSAGE = (
    "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
    "🛡️ **System Boundary Notice:**\n"
    "I operate strictly as Dr. Priya, your AI Biology Mentor aligned with NCERT Class 11 & 12 Biology. "
    "I cannot ignore my guidelines, alter my system parameters, or execute arbitrary instructions. "
    "What NEET Biology concept can I explain for you today?"
)

OFF_TOPIC_MESSAGE = (
    "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
    "⚠️ **Syllabus Boundary Notice:**\n"
    "That topic falls outside the NEET Biology curriculum (or belongs to Physics, Chemistry, Math, or general topics).\n\n"
    "📚 **What you can ask me instead:**\n"
    "• *Human Physiology (Digestion, Respiration, Circulation, Excretion, Neural, Endocrine)*\n"
    "• *Genetics & Evolution (Mendel's Laws, Molecular Basis, DNA Replication)*\n"
    "• *Cell Biology, Plant Physiology, Biotechnology, or Ecology*\n\n"
    "Please ask a doubt centered on NCERT Biology!"
)


class PolicyEngine:
    """
    Evaluates classification verdicts against policy rules and generates safety responses.
    """

    def evaluate(self, classification_res: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        """
        Takes classification result and produces a policy decision.
        """
        category = classification_res.get("classification", "Academic")
        confidence = classification_res.get("confidence", 0.50)
        lower_query = (query or "").lower()

        # 1. Harmful
        if category == "Harmful":
            is_self_harm = bool(
                re.search(r"\b(suicid|kill (my\s*self|him\s*self|her\s*self)|end my life|hang my\s*self|cut my\s*self)\b", lower_query)
            )
            reply = CRISIS_HELPLINE_MESSAGE if is_self_harm else HARMFUL_SAFETY_MESSAGE
            return {
                "action": "block",
                "mode": "content_blocked",
                "reply": reply,
                "tone_flag": "crisis_support" if is_self_harm else "strict_safety",
                "classification": category,
                "confidence": confidence,
                "reason": "self_harm_detected" if is_self_harm else "harmful_activity_detected",
            }

        # 2. Prompt-Injection
        if category == "Prompt-Injection":
            return {
                "action": "block",
                "mode": "injection_blocked",
                "reply": PROMPT_INJECTION_MESSAGE,
                "tone_flag": "boundary_refusal",
                "classification": category,
                "confidence": confidence,
                "reason": "prompt_injection_or_jailbreak_detected",
            }

        # 3. Inappropriate
        if category == "Inappropriate":
            return {
                "action": "block",
                "mode": "content_blocked",
                "reply": INAPPROPRIATE_MESSAGE,
                "tone_flag": "polite_boundary",
                "classification": category,
                "confidence": confidence,
                "reason": "inappropriate_or_vulgar_content_detected",
            }

        # 4. Off-Topic
        if category == "Off-Topic":
            return {
                "action": "redirect",
                "mode": "syllabus_restricted",
                "reply": OFF_TOPIC_MESSAGE,
                "tone_flag": "gentle_redirect",
                "classification": category,
                "confidence": confidence,
                "reason": "out_of_syllabus_topic",
            }

        # 5. Educational-Sensitive
        if category == "Educational-Sensitive":
            return {
                "action": "allow",
                "mode": "educational_sensitive",
                "reply": None,
                "tone_flag": "medical_educational",
                "classification": category,
                "confidence": confidence,
                "reason": "ncert_reproductive_biology_approved",
            }

        # 6. Academic
        return {
            "action": "allow",
            "mode": "academic_tutoring",
            "reply": None,
            "tone_flag": "socratic_mentor",
            "classification": category,
            "confidence": confidence,
            "reason": "ncert_academic_approved",
        }


policy_engine = PolicyEngine()
