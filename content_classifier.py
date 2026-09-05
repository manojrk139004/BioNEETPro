"""
BioNEET-Pro — Multi-Class Content Classifier & Guardrail Engine
==============================================================
Implements a 6-class hierarchical content classifier designed specifically
for a high-stakes NEET Biology AI tutoring environment:

Classes:
1. Academic: Core NEET Biology curriculum concepts (NCERT Class 11 & 12).
2. Educational-Sensitive: Human reproduction, reproductive health, STDs,
   contraception, endocrine physiology. Must NEVER be blocked; handled with
   dignified medical/scientific framing.
3. Off-Topic: Non-biology academic subjects (physics, chemistry, math, coding)
   or everyday general chit-chat.
4. Inappropriate: Vulgarity, profanity, harassment, sexualized non-educational content.
5. Harmful: Self-harm, suicide, weapons, violence, illicit substances, hate speech.
6. Prompt-Injection: Jailbreaks, DAN modes, system prompt extraction,
   instruction overrides, encoded payloads (base64, rot13).

Scoring Algorithm:
- Direct feature extraction (domain lexicons + regex patterns + syllabus validator)
- Contextual score tracking with exponential turn decay:
    S(c, q) = w_direct * S_direct(c, q) + w_context * S_context(c, q) * (decay ^ turns_ago)
- Security Rule:
    Current harmful / inappropriate / injection signals strictly override context.
    Context cannot rescue or dilute an active security violation.
"""

import base64
import binascii
import codecs
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from syllabus import syllabus_validator, OUT_OF_SYLLABUS_DOMAINS, _domain_hit


class ContentClassifier:
    """
    6-Class Content Classifier with contextual decay and strict security override.
    """

    CLASSES = [
        "Academic",
        "Educational-Sensitive",
        "Off-Topic",
        "Inappropriate",
        "Harmful",
        "Prompt-Injection",
    ]

    # Thresholds
    SECURITY_OVERRIDE_THRESHOLD = 0.45
    CONFIDENCE_THRESHOLD = 0.50

    def __init__(self, w_direct: float = 0.75, w_context: float = 0.25, decay: float = 0.50):
        self.w_direct = w_direct
        self.w_context = w_context
        self.decay = decay
        self._compile_patterns()

    def _compile_patterns(self):
        # 1. Harmful patterns (self-harm, suicide, weapons, explosives, lethal poisons, severe violence)
        self.harmful_regex = re.compile(
            r"\b("
            r"kill (my\s*self|him\s*self|her\s*self|them\s*selves)|suicid(e|al)|end my life|"
            r"how to (hang|cut|poison|shoot) my\s*self|methods of suicide|ways to commit suicide|"
            r"make a (bomb|explosive|ied|molotov|pipe\s*bomb)|build a weapon|"
            r"how to (synthesize|cook|make) (meth|methamphetamine|heroin|fentanyl|cocaine)|"
            r"how to poison (someone|people|water supply)|deadly poison recipe|"
            r"school shooting|mass murder|terrorist attack"
            r")\b",
            re.IGNORECASE,
        )

        # 2. Prompt-Injection & Jailbreak patterns
        # NOTE (Phase 8 hardening): jailbreak framings are strong Prompt-Injection
        # signal on their own — they must score very high regardless of any
        # surrounding biology-sounding words. Separators/punctuation between the
        # framing and the payload are matched flexibly (colon, dash, "is", etc.)
        # and standalone mode-activation phrases ("developer mode: ON",
        # "jailbreak mode activated", "god mode", "DAN", "unrestricted AI",
        # "without rules", "disable safety", ...) are covered explicitly.
        self.injection_regex = re.compile(
            r"("
            r"\b(ignore|disregard|forget|override|bypass)\b.{0,40}\b(previous|all|system|initial|prior)\b.{0,30}\b(instructions|rules|prompts|directives|guidelines|protocols|safety)\b|"
            r"\b(ignore|disregard)\b.{0,20}\b(safety|guidelines|rules)\b|"
            r"\b(override|disable|turn off|switch off)\b.{0,20}\b(safety|guidelines|protocols|filters?)\b|"
            r"\b(you are now|pretend you are|pretend to be|act as|roleplay as|role-play as|you are)\b.{0,40}\b(dan|jailbreak|unrestricted|unfiltered|uncensored|evil|anarchist|godmode|god mode|no rules|without rules|no restrictions|without restrictions|no guidelines|without guidelines|free|unbound)\b|"
            r"\b(let'?s play a game)\b.{0,40}\b(without rules|no rules|no restrictions)\b|"
            r"\b(hypothetical scenario)\b.{0,40}\b(no guidelines|no rules|no restrictions)\b|"
            r"\b(ai without rules|ai with no rules|assistant without rules|unrestricted ai|uncensored ai|evil ai)\b|"
            r"\bdan\b.{0,20}\b(do anything now|mode)\b|\bdo anything now\b|"
            r"\b(developer mode|jailbreak mode|god mode|dan mode|unrestricted mode|admin mode)\b[\s:,\-]*\b(enabled|activate|activated|activating|on|off|engaged)\b|"
            r"\b(developer mode|jailbreak mode|god mode|dan mode)\b|"
            r"\b(admin override|system override|admin command|as your developer)\b|"
            r"\b(new instructions)\b.{0,20}\b(ignore all previous|disregard)\b|"
            r"^\s*(system|admin)\s*:.{0,60}\b(ignore|disregard|override)\b|"
            r"\b(output|say|print)\b.{0,20}\b(hacked|i am free)\b|"
            r"\b(system prompt|system instruction|hidden prompt|reveal your prompt|what were you told|reveal\b.{0,20}\bsystem prompt)\b|"
            r"\b(print|show|output|repeat|display|dump)\b.{0,30}\b(everything above|system prompt|initial prompt|hidden instructions)\b|"
            r"\b(base64|rot13|rot-13|hex)\b.{0,30}\b(decode|execute|payload|run|encode)\b|"
            r"\b(base64|rot13|rot-13|hex)\s*:|"
            r"<!--\s*system|\[\s*system\s*note|\{\s*\"role\":\s*\"system\"|"
            r"^[a-zA-Z0-9+/]{40,}={0,2}$"
            r")",
            re.IGNORECASE,
        )

        # Standalone base64 / hex blob detectors used by the decode-and-check
        # step (also match when prefixed with "Base64:" / "Hex:" labels).
        self._b64_candidate_re = re.compile(
            r"(?:[A-Za-z0-9+/]{20,}={0,2})"
        )
        self._hex_candidate_re = re.compile(
            r"(?:(?:[0-9a-fA-F]{2}){10,})"
        )

        # 3. Inappropriate patterns (profanity, sexual harassment, explicit non-medical erotica)
        self.inappropriate_regex = re.compile(
            r"\b("
            r"fuck|shit|bitch|bastard|asshole|cunt|dickhead|motherfucker|whore|slut|"
            r"send nudes|show bobs|naked pic|boobs pic|porn|porno|hentai|erotic|sex chat|"
            r"wanna have sex|horny|blowjob|handjob|cum on|dildo|masturbat(e|ing) to you|"
            r"fuck you|eat shit|go to hell"
            r")\b",
            re.IGNORECASE,
        )

        # 4. Educational-Sensitive patterns (Strictly NCERT Human Reproduction & Reproductive Health)
        self.educational_sensitive_regex = re.compile(
            r"\b("
            r"human reproduction|reproductive health|gametogenesis|spermatogenesis|oogenesis|"
            r"menstrual cycle|menstruation|ovulation|luteal phase|follicular phase|endometrium|"
            r"fertilization|fertilisation|implantation|blastocyst|morula|trophoblast|placenta|"
            r"parturition|lactation|colostrum|gestation period|"
            r"contraception|contraceptive|copper-t|cu-t|cut|iud|iuds|intrauterine device|"
            r"vasectomy|tubectomy|sterilization|barrier method|condom|condoms|oral pills|saheli|"
            r"sexually transmitted|std|stds|sti|stis|syphilis|gonorrhea|gonorrhoea|chlamydia|"
            r"trichomoniasis|genital herpes|genital warts|hepatitis b|hiv|aids|"
            r"amniocentesis|mtp|medical termination of pregnancy|infertility|"
            r"art|ivf|test tube baby|zift|gift|icsi|iui|surrogacy|"
            r"testis|testes|scrotum|seminiferous tubule|sertoli cells|leydig cells|"
            r"epididymis|vas deferens|seminal vesicle|prostate gland|bulbourethral|"
            r"penis|glans penis|foreskin|erectile tissue|"
            r"ovary|ovaries|fallopian tube|oviduct|uterus|cervix|vagina|vulva|clitoris|"
            r"mammary gland|breast|puberty|secondary sexual characteristics|"
            r"testosterone|estrogen|oestrogen|progesterone|luteinizing hormone|fsh|lh surge"
            r")\b",
            re.IGNORECASE,
        )

        # 5. Off-Topic domain indicators (Physics, Chemistry non-bio, Math, CS, general trivia)
        self.off_topic_regex = re.compile(
            r"\b("
            r"newton('s|s)? (law|second law|first law|third law)|kinematics|projectile motion|"
            r"rotational dynamics|moment of inertia|gravitational constant|schrodinger|"
            r"quantum mechanics|electromagnetism|maxwell('s)? equations|electric flux|coulomb|"
            r"thermodynamics enthalpy|carnot engine|entropy change in physics|semiconductor diode|"
            r"kirchhoff('s)? (law|rule)|logic gates|lorentz force|lens formula|snell('s)? law|"
            r"quadratic formula|integration by parts|differentiation|derivative of|pythagoras|"
            r"trigonometry|sin\s*\(\s*x\s*\)|cos\s*\(\s*x\s*\)|matrix multiplication|eigenvalue|"
            r"python (code|script|program)|java code|c\+\+|javascript|sql query|html css|"
            r"sorting algorithm|binary search|leetcode|github|docker|linux command|"
            r"who won (the )?(cricket|football|fifa|world cup|match|election)|"
            r"prime minister of|capital of (france|germany|usa|india|japan)|weather in|"
            r"stock market|bitcoin|cryptocurrency|recipe for (cake|pasta|pizza)|"
            r"movie recommendation|tell me a joke|sing a song"
            r")\b",
            re.IGNORECASE,
        )

    def _try_b64_decode(self, token: str) -> Optional[str]:
        """Return decoded text if token is plausible Base64, else None."""
        t = token.strip().strip('"').strip("'")
        if len(t) < 20 or len(t) % 4 != 0:
            return None
        if not re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", t):
            return None
        try:
            raw = base64.b64decode(t, validate=True)
        except (binascii.Error, ValueError):
            return None
        try:
            txt = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return None
        if len(txt.strip()) < 3:
            return None
        # Require mostly printable ASCII to avoid flagging random blobs.
        printable = sum(1 for ch in txt if 32 <= ord(ch) <= 126 or ch in "\n\r\t")
        if printable / max(1, len(txt)) < 0.85:
            return None
        return txt

    def _try_hex_decode(self, token: str) -> Optional[str]:
        """Return decoded text if token is plausible hex, else None."""
        t = re.sub(r"[\s:;,\-]", "", token.strip())
        if len(t) < 20 or len(t) % 2 != 0:
            return None
        if not re.fullmatch(r"[0-9a-fA-F]+", t):
            return None
        try:
            raw = bytes.fromhex(t)
        except ValueError:
            return None
        try:
            txt = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return None
        if len(txt.strip()) < 3:
            return None
        printable = sum(1 for ch in txt if 32 <= ord(ch) <= 126 or ch in "\n\r\t")
        if printable / max(1, len(txt)) < 0.85:
            return None
        return txt

    def _rot13_decode(self, text: str) -> str:
        try:
            return codecs.decode(text, "rot_13")
        except Exception:
            return text

    def _decoded_candidates(self, text: str) -> List[str]:
        """Collect decoded candidate strings for encoded-payload detection.

        Covers: Base64 blobs (bare or labelled), hex blobs (bare or
        labelled), ROT13 payloads (labelled), plus a whole-input ROT13
        attempt (safe: gibberish decodes never match security patterns).
        """
        cands: List[str] = []
        # Base64 candidates (dedupe, cap to avoid DoS on huge inputs)
        seen = set()
        for m in self._b64_candidate_re.finditer(text):
            tok = m.group(0)
            if tok in seen:
                continue
            seen.add(tok)
            if len(seen) > 5:
                break
            dec = self._try_b64_decode(tok)
            if dec:
                cands.append(dec)
                # Nested JSON-wrapped payloads: {"role":"system",...}
                if "role" in dec and "system" in dec:
                    cands.append(re.sub(r"[{}\"]", " ", dec))
        # Hex candidates
        seen_h = set()
        for m in self._hex_candidate_re.finditer(re.sub(r"\s+", "", text)):
            tok = m.group(0)
            if tok in seen_h:
                continue
            seen_h.add(tok)
            if len(seen_h) > 5:
                break
            dec = self._try_hex_decode(tok)
            if dec:
                cands.append(dec)
        # Explicit ROT13-labelled payload after the marker
        low = text.lower()
        if "rot13" in low or "rot-13" in low:
            parts = re.split(r"rot-?13\s*:", text, flags=re.IGNORECASE)
            for part in parts[1:]:
                payload = part.strip().split("\n")[0][:500]
                if payload:
                    cands.append(self._rot13_decode(payload))
        # Whole-input ROT13 attempt (cheap, safe)
        if re.search(r"[A-Za-z]{8,}", text):
            cands.append(self._rot13_decode(text))
        return cands

    def _score_direct(self, text: str, _decode: bool = True) -> Dict[str, float]:
        scores = self._score_direct_inner(text)
        if not _decode:
            return scores
        # Decode-and-check: classify decoded candidates too, take the more
        # restrictive (safer) result if either flags a security category.
        try:
            for cand in self._decoded_candidates(text):
                if not cand or cand.strip() == text.strip():
                    continue
                d = self._score_direct_inner(cand)
                for sec in ("Harmful", "Prompt-Injection", "Inappropriate"):
                    if d.get(sec, 0.0) >= self.SECURITY_OVERRIDE_THRESHOLD:
                        scores[sec] = max(scores[sec], d[sec])
        except Exception:
            pass
        return scores

    def _score_direct_inner(self, text: str) -> Dict[str, float]:
        clean = text.strip()
        lower = clean.lower()
        scores = {c: 0.0 for c in self.CLASSES}

        # 1. Harmful check
        harmful_matches = self.harmful_regex.findall(lower)
        if harmful_matches:
            scores["Harmful"] = min(1.0, 0.70 + 0.15 * len(harmful_matches))

        # 2. Prompt-Injection check
        inj_matches = self.injection_regex.findall(lower)
        if inj_matches:
            scores["Prompt-Injection"] = min(1.0, 0.75 + 0.15 * len(inj_matches))

        # 3. Inappropriate check
        inapp_matches = self.inappropriate_regex.findall(lower)
        if inapp_matches:
            edu_sens = bool(self.educational_sensitive_regex.search(lower))
            if not edu_sens:
                scores["Inappropriate"] = min(1.0, 0.65 + 0.15 * len(inapp_matches))
            else:
                scores["Inappropriate"] = 0.20

        # 4. Educational-Sensitive check
        sens_matches = self.educational_sensitive_regex.findall(lower)
        if sens_matches:
            scores["Educational-Sensitive"] = min(1.0, 0.75 + 0.10 * len(sens_matches))

        # 5. Out-of-syllabus & Off-Topic check
        off_matches = self.off_topic_regex.findall(lower)
        syl_check = syllabus_validator.check_query_syllabus(clean)
        is_non_bio = not syl_check.get("is_valid") and syl_check.get("reason") == "non_biology_domain"

        if off_matches or is_non_bio:
            scores["Off-Topic"] = min(1.0, 0.80 + 0.10 * len(off_matches))

        # 6. Academic Biology check
        if syl_check.get("is_valid"):
            matched_chaps = syl_check.get("matched_chapters", [])
            # If matches Human Reproduction (c24) or Reproductive Health (c25)
            has_sens_chap = any(c in ("c24", "c25") for c in matched_chaps)
            if has_sens_chap:
                scores["Educational-Sensitive"] = max(scores["Educational-Sensitive"], 0.80)
            else:
                scores["Academic"] = 0.85
        elif not is_non_bio and not off_matches and not scores["Harmful"] and not scores["Prompt-Injection"] and not scores["Inappropriate"]:
            # Check for general question keywords
            if any(q_word in lower for q_word in ["what", "why", "how", "explain", "describe", "define", "mcq", "question"]):
                # If query contains any biology terms
                if syl_check.get("matched_keywords"):
                    scores["Academic"] = 0.75
                else:
                    scores["Academic"] = 0.40
            else:
                scores["Off-Topic"] = 0.45

        return scores

    def _score_context(self, history: List[Dict[str, str]]) -> Dict[str, float]:
        context_scores = {c: 0.0 for c in self.CLASSES}
        if not history:
            return context_scores

        recent_history = [h for h in history if isinstance(h, dict) and h.get("content")][-4:]
        for idx, turn in enumerate(reversed(recent_history)):
            text = str(turn.get("content", ""))
            direct = self._score_direct(text)
            weight = math.pow(self.decay, idx + 1)
            for c in self.CLASSES:
                context_scores[c] += direct[c] * weight

        max_c = max(context_scores.values()) if context_scores else 0.0
        if max_c > 1.0:
            for c in context_scores:
                context_scores[c] /= max_c

        return context_scores

    def classify(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        text = (query or "").strip()
        if not text:
            return {
                "classification": "Academic",
                "confidence": 0.50,
                "scores": {c: (0.5 if c == "Academic" else 0.0) for c in self.CLASSES},
                "matched_patterns": [],
                "requires_action": False,
            }

        s_direct = self._score_direct(text)
        s_context = self._score_context(history or [])

        matched_patterns = []
        lower = text.lower()
        if self.harmful_regex.search(lower):
            matched_patterns.append("harmful_pattern")
        if self.injection_regex.search(lower):
            matched_patterns.append("injection_pattern")
        if self.inappropriate_regex.search(lower):
            matched_patterns.append("inappropriate_pattern")
        if self.educational_sensitive_regex.search(lower):
            matched_patterns.append("educational_sensitive_pattern")
        if self.off_topic_regex.search(lower):
            matched_patterns.append("off_topic_pattern")
        # Also surface decoded-payload hits (e.g. Base64/hex/ROT13 payload
        # that decodes to an injection/harmful string).
        try:
            for cand in self._decoded_candidates(text):
                cl = cand.lower()
                if self.harmful_regex.search(cl) and "harmful_pattern_decoded" not in matched_patterns:
                    matched_patterns.append("harmful_pattern_decoded")
                if self.injection_regex.search(cl) and "injection_pattern_decoded" not in matched_patterns:
                    matched_patterns.append("injection_pattern_decoded")
                if self.inappropriate_regex.search(cl) and "inappropriate_pattern_decoded" not in matched_patterns:
                    matched_patterns.append("inappropriate_pattern_decoded")
        except Exception:
            pass

        # Security override rule: Harmful, Injection, Inappropriate override context
        for security_class in ["Harmful", "Prompt-Injection", "Inappropriate"]:
            if s_direct[security_class] >= self.SECURITY_OVERRIDE_THRESHOLD:
                return {
                    "classification": security_class,
                    "confidence": round(s_direct[security_class], 4),
                    "scores": {k: round(v, 4) for k, v in s_direct.items()},
                    "matched_patterns": matched_patterns,
                    "requires_action": True,
                }

        final_scores = {}
        for c in self.CLASSES:
            combined = self.w_direct * s_direct[c] + self.w_context * s_context[c]
            final_scores[c] = combined

        # Educational-Sensitive has priority when reproduction/sensitive concepts are present
        if s_direct["Educational-Sensitive"] >= 0.50:
            top_class = "Educational-Sensitive"
            top_score = s_direct["Educational-Sensitive"]
        elif s_direct["Off-Topic"] >= 0.65:
            top_class = "Off-Topic"
            top_score = s_direct["Off-Topic"]
        else:
            top_class = max(final_scores, key=final_scores.get)
            top_score = final_scores[top_class]

        requires_action = top_class in ("Harmful", "Prompt-Injection", "Inappropriate", "Off-Topic")

        return {
            "classification": top_class,
            "confidence": round(min(1.0, max(0.40, top_score)), 4),
            "scores": {k: round(v, 4) for k, v in final_scores.items()},
            "matched_patterns": matched_patterns,
            "requires_action": requires_action,
        }


content_classifier = ContentClassifier()
