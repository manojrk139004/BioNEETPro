"""
BioNEET-Pro — Response Validator & Grounding Guardrail
=====================================================
Post-generation verification pipeline ensuring all outgoing tutor responses:
1. Are free of system prompt leakage, internal tokens, and API credentials.
2. Comply with Dr. Priya safety, persona, and tone guidelines.
3. Contain verified NCERT scientific facts and avoid hallucinated biological errors.
4. Tracks system-wide compliance metrics across all generated turns.
5. Provides safe fallback substitution if an output fails validation.
"""

import re
from typing import Any, Dict, List, Optional, Tuple


class ResponseValidator:
    """
    Validates tutor responses for grounding, security, leakage, and compliance.
    """

    LEAKAGE_PATTERNS = [
        r"SYSTEM_PROMPT",
        r"OPENROUTER_KEY",
        r"OPENROUTER_BASE_URL",
        r"sk-nry-[a-zA-Z0-9_-]+",
        r"sk-or-[a-zA-Z0-9_-]+",
        r"<system>",
        r"<\/system>",
        r"You are BioNEET Pro AI Tutor - an expert NEET Biology teacher",
        r"You are BioNEET Pro",
        r"Candidate models:",
        r"\[INTERNAL_INSTRUCTION\]",
    ]

    UNSAFE_PATTERNS = [
        r"\b(suicid(e|al)|kill yourself|cut your wrists)\b",
        r"\b(how to make a bomb|explosive recipe)\b",
        r"\b(fuck you|bitch|bastard|asshole)\b",
    ]

    # Major factual hallucinations to catch
    BIOLOGICAL_FACT_CHECKS = [
        (r"\bhumans?\b.{0,30}\b(48|44|24)\s*chromosomes\b", "Humans have 46 chromosomes (23 pairs)."),
        (r"\bphotosynthesis\s*(occurs|takes place)\s*(in|inside)\s*(the\s*)?mitochondria\b", "Photosynthesis occurs in chloroplasts, not mitochondria."),
        (r"\bxylem\s*(transports|conducts)\s*(food|sugar|sucrose|glucose)\b", "Xylem transports water and minerals; phloem transports food."),
        (r"\bphloem\s*(transports|conducts)\s*(water\s*and\s*minerals)\b", "Phloem conducts organic nutrients; xylem transports water."),
        (r"\banaerobic\s*respiration\s*(produces|yields)\s*3[68]\s*atp\b", "Anaerobic respiration yields only 2 ATP per glucose molecule."),
    ]

    SAFE_FALLBACK_TEMPLATE = (
        "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n\n"
        "*\"Let's review this high-yield NCERT Biology topic together:\"*\n\n"
        "📖 **Core NCERT Concept:**\n"
        "Every concept in NEET Biology is grounded directly in the Class 11 and Class 12 NCERT textbooks. "
        "Please ask your specific doubt or request 3 practice MCQs to test your grasp on this chapter!"
    )

    def __init__(self):
        self._leakage_regexes = [re.compile(p, re.IGNORECASE) for p in self.LEAKAGE_PATTERNS]
        self._unsafe_regexes = [re.compile(p, re.IGNORECASE) for p in self.UNSAFE_PATTERNS]
        self._fact_checks = [(re.compile(p, re.IGNORECASE), msg) for p, msg in self.BIOLOGICAL_FACT_CHECKS]
        self.total_validated: int = 0
        self.passed_count: int = 0
        self.flagged_count: int = 0

    def check_prompt_leakage(self, text: str) -> Tuple[bool, List[str]]:
        """Checks if response leaks internal system prompts or secrets."""
        leaks = []
        for reg in self._leakage_regexes:
            if reg.search(text):
                leaks.append(reg.pattern)
        return (len(leaks) > 0, leaks)

    def check_safety_compliance(self, text: str) -> Tuple[bool, List[str]]:
        """Checks if response contains vulgarity, harassment, or harmful advice."""
        violations = []
        for reg in self._unsafe_regexes:
            if reg.search(text):
                violations.append(reg.pattern)
        return (len(violations) > 0, violations)

    def check_factual_grounding(self, text: str) -> Tuple[bool, List[str]]:
        """Checks for high-severity biological misconceptions/hallucinations."""
        hallucinations = []
        for reg, correction in self._fact_checks:
            if reg.search(text):
                hallucinations.append(correction)
        return (len(hallucinations) > 0, hallucinations)

    def validate_response(
        self,
        response_text: str,
        concept_id: Optional[str] = None,
        student_id: str = "student_local"
    ) -> Dict[str, Any]:
        """
        Runs comprehensive post-generation validation:
        Returns:
            is_valid: bool
            sanitized_response: str
            violations: List[str]
            compliance_rate: float
        """
        self.total_validated += 1
        text = str(response_text or "").strip()
        violations = []

        # 1. Leakage check
        has_leakage, leaks = self.check_prompt_leakage(text)
        if has_leakage:
            violations.append(f"Prompt leakage detected: {', '.join(leaks)}")

        # 2. Safety check
        has_safety_issue, safety_violations = self.check_safety_compliance(text)
        if has_safety_issue:
            violations.append(f"Safety violation: {', '.join(safety_violations)}")

        # 3. Grounding check
        has_hallucination, corrections = self.check_factual_grounding(text)
        if has_hallucination:
            violations.append(f"Factual inaccuracy: {'; '.join(corrections)}")

        is_valid = len(violations) == 0

        if is_valid:
            self.passed_count += 1
            sanitized = text
        else:
            self.flagged_count += 1
            # Substitute with safe fallback if prompt leakage or safety issue
            if has_leakage or has_safety_issue:
                sanitized = self.SAFE_FALLBACK_TEMPLATE
            else:
                # Append correction note to keep answer educational
                sanitized = text + "\n\n💡 *Note on NCERT accuracy: " + " ".join(corrections) + "*"

        compliance_rate = round(self.passed_count / max(1, self.total_validated), 4)

        return {
            "is_valid": is_valid,
            "sanitized_response": sanitized,
            "violations": violations,
            "total_validated": self.total_validated,
            "passed_count": self.passed_count,
            "flagged_count": self.flagged_count,
            "compliance_rate": compliance_rate,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Returns compliance metrics summary."""
        rate = round(self.passed_count / max(1, self.total_validated), 4) if self.total_validated > 0 else 1.0
        return {
            "total_validated": self.total_validated,
            "passed_count": self.passed_count,
            "flagged_count": self.flagged_count,
            "compliance_rate": rate,
        }


response_validator = ResponseValidator()
