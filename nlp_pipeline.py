"""
BioNEETPro - Comprehensive Biology NLP Processing Pipeline
==========================================================
Implements:
1. Student Shorthand Normalization ("abt" -> "about", "diff b/w" -> "difference between")
2. Typo & Phrasing Correction ("explain me X" -> "explain X")
3. Multi-turn Conversational Anaphora & Antecedent Resolution ("it", "that", "these folds", "increase")
4. Per-Student Context Isolation via ConversationContextTracker
5. Pedagogical Intent Classification (12 distinct categories)
6. Bloom's Taxonomy Cognitive Level Identification (BT1 to BT6)
7. Biology Entity Extraction & Synonym Expansion
8. NCERT Syllabus Boundary Validation
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from concept_normalizer import concept_normalizer
from syllabus import syllabus_validator

# Comprehensive Biology Synonym Dictionary for NEET
BIOLOGY_SYNONYMS: Dict[str, List[str]] = {
    "leaf": ["leaves", "foliage", "chlorophyll", "chloroplast", "mesophyll", "stoma", "guard cells"],
    "leaves": ["leaf", "foliage", "chlorophyll", "chloroplast", "mesophyll"],
    "blood": ["plasma", "erythrocyte", "leukocyte", "hemoglobin", "platelet", "circulation", "heme"],
    "bone": ["bones", "skeleton", "skeletal", "hydroxyapatite", "calcium", "cortical", "osteocyte", "marrow"],
    "bones": ["bone", "skeleton", "skeletal", "hydroxyapatite", "calcium", "marrow"],
    "heart": ["cardiac", "atrium", "ventricle", "circulation", "pacemaker", "sinoatrial", "av node"],
    "brain": ["cerebrum", "cerebellum", "medulla", "cortex", "white matter", "grey matter", "neuron", "myelin", "forebrain", "midbrain", "hindbrain"],
    "urine": ["excretion", "urochrome", "urobilin", "kidney", "nephron", "urea", "filtrate", "glomerulus"],
    "excretion": ["urine", "urochrome", "kidney", "nephron", "urea", "excretory", "micturition"],
    "pee": ["urine", "urochrome", "excretion", "kidney"],
    "muscle": ["sarcomere", "actin", "myosin", "troponin", "sliding filament", "striated"],
    "kidney": ["nephron", "glomerulus", "loop of henle", "countercurrent", "renal", "filtration"],
    "lung": ["lungs", "alveoli", "respiration", "breathing", "vital capacity", "gaseous exchange"],
    "sugar": ["glucose", "carbohydrate", "insulin", "glycogen", "glucagon", "diabetes"],
    "energy": ["atp", "mitochondria", "phosphorylation", "respiration", "glycolysis"],
    "light reaction": ["photophosphorylation", "thylakoid", "z-scheme", "ps i", "ps ii", "photolysis"],
    "dark reaction": ["calvin cycle", "c3 pathway", "stroma", "rubisco", "carboxylation"],
    "cell division": ["mitosis", "meiosis", "cell cycle", "cytokinesis", "crossing over"],
    "dna": ["nucleic acid", "double helix", "replication", "nucleotide", "watson crick"],
    "rna": ["transcription", "mrna", "trna", "rrna", "translation", "ribosome", "genetic code"],
    "hormone": ["endocrine", "pituitary", "thyroid", "adrenal", "insulin", "glucagon", "receptor"],
    "plant hormone": ["auxin", "gibberellin", "cytokinin", "ethylene", "abscisic acid", "aba", "phytohormone"],
    "yellow": ["urochrome", "bilirubin", "carotenoid", "xanthophyll", "urine"],
    "red": ["blood", "hemoglobin", "heme", "erythrocyte", "oxyhemoglobin"],
    "white": ["bone", "hydroxyapatite", "myelin", "white matter", "leukocyte"],
    "green": ["chlorophyll", "chloroplast", "leaves", "leaf", "pigment"],
    "photosynthesis": ["calvin cycle", "light reaction", "chlorophyll", "chloroplast", "z-scheme", "rubisco", "thylakoid", "c3", "c4"],
    "respiration": ["glycolysis", "krebs cycle", "mitochondria", "ets", "pyruvate", "atp synthase"],
    "circulation": ["heart", "blood", "arteries", "veins", "cardiac cycle", "double circulation"],
    "locomotion": ["bones", "skeleton", "muscle", "sarcomere", "sliding filament", "joints"],
    "genetics": ["mendel", "inheritance", "dna", "genes", "chromosomes", "replication", "alleles"],
    "evolution": ["darwin", "natural selection", "homologous", "hardy weinberg", "origin of life"],
    "biotechnology": ["restriction enzymes", "pbr322", "pcr", "gel electrophoresis", "bt cotton"],
    "ecology": ["ecosystem", "trophic levels", "energy flow", "biodiversity", "food chain"],
    "mitochondria": ["cristae", "matrix", "inner membrane", "atp synthase", "aerobic respiration", "powerhouse"],
    "cristae": ["mitochondrial folds", "inner membrane", "surface area", "atp generation", "electron transport chain"],
    "earthworm": ["annelida", "pheretima", "setae", "metamerism", "clitellum"],
    "annelida": ["earthworm", "pheretima", "metamerism", "setae"],
    "frog": ["rana", "amphibia", "tadpole", "toad"],
    "gfr": ["glomerulus", "filtration", "nephron", "urine"],
    "bod": ["sewage", "oxygen", "pollution", "effluent"],
    "action potential": ["sodium", "depolarization", "axon", "threshold"],
    "diabetes": ["insulin", "glucose", "pancreas", "blood sugar"],
    "malaria": ["plasmodium", "mosquito", "anopheles", "hemozoin"],
    "iud": ["contraception", "uterus", "copper", "birth control"],
    "vernalization": ["flowering", "cold", "plant hormone", "growth"],
    "emulsification": ["bile", "fats", "digestion", "lipase"],
    "tidal volume": ["lungs", "breathing", "air", "respiration"],
    "meselson": ["dna", "replication", "semi-conservative", "isotope"],
    "logistic growth": ["carrying capacity", "population", "growth curve"],
    "commensalism": ["population", "interaction", "species", "symbiosis"],
    "succession": ["pioneer", "climax", "ecosystem", "community"],
    "gout": ["uric acid", "joints", "excretion", "kidney"],
    "myasthenia": ["muscle", "acetylcholine", "paralysis", "neuromuscular"],
    "spermiogenesis": ["sperm", "spermatid", "testis", "gamete"],
    "aestivation": ["flower", "petals", "calyx", "corolla"],
    "ommatidia": ["cockroach", "eye", "vision", "mosaic"],
    "stroma": ["chloroplast", "calvin", "photosynthesis", "thylakoid"],
    "pyruvate": ["glycolysis", "respiration", "glucose", "mitochondria"],
    "diastole": ["heart", "cardiac", "systole", "chambers"],
    "allele": ["gene", "mendel", "dominant", "recessive"],
    "lactose": ["operon", "repressor", "ecoli", "gene"],
    "vntr": ["dna", "fingerprinting", "probe", "repeat"],
    "mrna": ["transcription", "ribosome", "translation", "nucleus"],
    "sewage": ["bod", "microbes", "treatment", "effluent"],
    "methanogen": ["biogas", "methane", "archaea", "anaerobic"],
    "pioneer": ["succession", "climax", "lichens", "ecosystem"],
    "endosperm": ["seed", "fertilization", "embryo", "flower"],
    "stigma": ["pollination", "pollen", "flower", "carpel"],
    "uric acid": ["excretion", "kidney", "gout", "nephron"],
    "acetylcholine": ["neuron", "synapse", "muscle", "impulse"],
}

# Student Shorthand Map
STUDENT_SHORTHAND_MAP = [
    (r"\bbout\b", "about"),
    (r"\babt\b", "about"),
    (r"\bdiff\b", "difference"),
    (r"\bdifs\b", "differences"),
    (r"\bb/w\b", "between"),
    (r"\bbw\b", "between"),
    (r"\beg\b", "example"),
    (r"\be\.g\.\b", "example"),
    (r"\bpls\b", "please"),
    (r"\bplz\b", "please"),
    (r"\bur\b", "your"),
    (r"\bu\b", "you"),
    (r"\br\b", "are"),
    (r"\bans\b", "answer"),
    (r"\bques\b", "question"),
    (r"\bqn\b", "question"),
    (r"\bq\b", "question"),
    (r"\bqns\b", "questions"),
    (r"\bimp\b", "important"),
    (r"\bpic\b", "diagram"),
    (r"\bdiag\b", "diagram"),
    (r"\bstruct\b", "structure"),
    (r"\bfunc\b", "function"),
    (r"\bresp\b", "respiration"),
    (r"\bphts\b", "photosynthesis"),
    (r"\bphoto\b", "photosynthesis"),
    (r"\brepro\b", "reproduction"),
    (r"\bdiv\b", "division"),
    (r"\bchem\b", "chemical"),
    (r"\bbio\b", "biology"),
    (r"\borg\b", "organism"),
    (r"\binfo\b", "information"),
    (r"\bexplain me\b", "explain to me"),
    (r"\btell me abt\b", "tell me about"),
    (r"\bteach me abt\b", "teach me about"),
    (r"\bwat\b", "what"),
    (r"\btll\b", "tell"),
    (r"\bxplain\b", "explain"),
    (r"\bgv\b", "give"),
    (r"\bgimme\b", "give me"),
    (r"\bhw\b", "how"),
    (r"\bwts\b", "what is"),
    (r"\bwht\b", "what"),
    (r"\bhows\b", "how is"),
    (r"\bwhy+\b", "why"),
    (r"\bdef\b", "define"),
    (r"\b(wat|wht|wh4t)\b", "what"),
    (r"\br0le\b", "role"),
    (r"\bfuncti0n\b", "function"),
    (r"\bstructur3\b", "structure"),
    (r"\bd1ff\b", "difference")
]


class StudentConversationState:
    """Holds active context for a single student."""

    def __init__(self, student_id: str):
        self.student_id = student_id
        self.focal_concept_id: Optional[str] = None
        self.focal_title: Optional[str] = None
        self.focal_canonical_name: Optional[str] = None
        self.last_subtopic: Optional[str] = None
        self.recent_concepts: List[Tuple[str, str, str]] = []  # (concept_id, title, canonical_name)

    def track(self, concept_id: str, title: str, canonical_name: Optional[str] = None, subtopic: Optional[str] = None):
        c_name = canonical_name or title
        self.focal_concept_id = concept_id
        self.focal_title = title
        self.focal_canonical_name = c_name
        if subtopic:
            self.last_subtopic = subtopic
        self.recent_concepts.append((concept_id, title, c_name))
        if len(self.recent_concepts) > 8:
            self.recent_concepts.pop(0)


class ConversationContextTracker:
    """Multi-tenant context tracker managing independent states per student."""

    def __init__(self):
        self.states: Dict[str, StudentConversationState] = {}

    def get_state(self, student_id: str = "student_local") -> StudentConversationState:
        if student_id not in self.states:
            self.states[student_id] = StudentConversationState(student_id)
        return self.states[student_id]

    def track_concept(self, student_id: str, concept_id: str, title: str, canonical_name: Optional[str] = None, subtopic: Optional[str] = None):
        state = self.get_state(student_id)
        state.track(concept_id, title, canonical_name, subtopic)

    def clear_context(self, student_id: str):
        if student_id in self.states:
            del self.states[student_id]

    def get_focal_concept(self, student_id: str = "student_local") -> Optional[Tuple[str, str, str]]:
        state = self.get_state(student_id)
        if state.focal_concept_id and state.focal_title:
            return (state.focal_concept_id, state.focal_title, state.focal_canonical_name or state.focal_title)
        return None

    def get_last_subtopic(self, student_id: str = "student_local") -> Optional[str]:
        return self.get_state(student_id).last_subtopic


class NLPPipeline:
    """
    Advanced Biology NLP Pipeline for BioNEETPro.
    """

    INTENT_PATTERNS = [
        # Chapter PDF delivery — must precede generic explanation intents:
        # "give me the PDF for Cell", "download this chapter's NCERT PDF".
        ("request_chapter_pdf", r"\b(pdf|ncert\s*pdf|download\b.{0,25}\b(chapter|ncert|pdf)|give me\b.{0,30}\bpdf|this chapter'?s\b.{0,25}\b(ncert\s*)?pdf)\b"),
        # Answering / referring to a specific MCQ / quiz feedback.
        # Must precede mcq_request: "I got question 2 wrong" is a quiz result report.
        ("quiz_feedback", r"\b(i got|my answer was|got\b.{0,15}\b(wrong|right|correct|incorrect)|question(s)?\s*(number|no\.?|#)?\s*\d+\b.{0,25}(wrong|right|correct|incorrect)|i answered|i chose [a-d])\b"),
        ("mcq_answer", r"\b(i chose|i think|my answer|answer is|option [a-d]|explain question)\b"),
        ("mcq_reference", r"\bquestion(s)?\s*(number|no\.?|#)?\s*\d+\b"),
        # Explicit MCQ Request — requires a request verb OR an explicit MCQ token.
        # Bare "question" without a verb (e.g. "what is question 2") is NOT a request.
        ("mcq_request", r"\b(give|quiz|ask|test|generate|practice|provide|send|make|create|prepare|want|need)\b.{0,40}\b(mcqs?|questions?|quiz|test|problems?|quizzes)\b|\b(mcqs?)\b|\btest me\b|\bquiz me\b"),
        # Comparisons & Differences
        ("difference_comparison", r"\b(difference|differentiate|distinguish|versus|vs|contrast|compare|comparison|between .* and .*)\b"),
        # Causal & Reason Questions
        ("why", r"\b(why|reason|cause of|why does|why do|why is|why are|what causes)\b"),
        # Mechanisms & Pathways
        ("how_process", r"\b(how|mechanism|process|steps of|pathway|working of|how does|how do|how is)\b"),
        # Biological Function
        ("function", r"\b(function|functions|role|roles|purpose|what does .+ do|importance of|significance of)\b"),
        # Concrete Examples
        ("example", r"\b(example|examples|give an example|such as|illustrate with)\b"),
        # Rapid Revision & Recaps
        ("revision", r"\b(revise|revision|summary|summarize|overview of|recap|briefly)\b"),
        # Follow-up questions relying on context
        ("follow_up", r"\b(what does that increase|what happens next|what about|and then|what does that mean|why that|explain it again|explain again|tell me more|what did that do)\b"),
        # Broad Overviews & Explanations
        ("overview_explanation", r"\b(teach me about|teach me|explain|describe|tell me about|give an explanation|guide me on|discuss|structure of)\b"),
        # Formal Definitions
        ("definition", r"\b(what is|what are|define|definition|meaning of)\b"),
    ]

    BLOOM_KEYWORDS = {
        "BT1": ["define", "list", "name", "what is", "state", "identify", "who", "when", "where", "which"],
        "BT2": ["explain", "describe", "why", "discuss", "summarize", "paraphrase", "illustrate", "teach me"],
        "BT3": ["apply", "calculate", "solve", "predict", "demonstrate", "how would"],
        "BT4": ["distinguish", "differentiate", "compare", "contrast", "analyze", "separate", "categorize"],
        "BT5": ["evaluate", "judge", "assess", "justify", "verify", "critique"],
        "BT6": ["design", "formulate", "construct", "propose", "synthesize"],
    }

    def __init__(self):
        self.validator = syllabus_validator
        self.context_tracker = ConversationContextTracker()

    def normalize_shorthand(self, text: str) -> str:
        """Expands student text shorthand, slang, and abbreviations."""
        normalized = text
        for pattern, replacement in STUDENT_SHORTHAND_MAP:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        # Fix double spaces
        return re.sub(r"\s+", " ", normalized).strip()

    def clean_text(self, text: str) -> str:
        """Normalizes spaces and cleans common noise characters.
        Includes unicode/homoglyph normalization (NFKC) and strips zero-width
        spaces and control characters to prevent adversarial obfuscation.
        """
        if not text:
            return ""
        # Unicode/homoglyph normalization to canonical form
        text = unicodedata.normalize('NFKC', text)
        # Cross-script homoglyph normalization (Cyrillic & Greek confusables to Latin)
        homoglyphs = str.maketrans({
            '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p', '\u0441': 'c', '\u0443': 'y', '\u0445': 'x',
            '\u0456': 'i', '\u0458': 'j', '\u0455': 's', '\u0410': 'A', '\u0412': 'B', '\u0415': 'E', '\u041a': 'K',
            '\u041c': 'M', '\u041d': 'H', '\u041e': 'O', '\u0420': 'P', '\u0421': 'C', '\u0422': 'T', '\u0425': 'X',
            '\u03bf': 'o', '\u03bd': 'v', '\u03c1': 'p'
        })
        text = text.translate(homoglyphs)
        # Strip zero-width spaces and control characters
        text = re.sub(r"[\u200b-\u200d\ufeff\u0000-\u001f\u007f-\u009f]", "", text)
        # Remove apostrophes WITHOUT inserting spaces ("Newton's" -> "Newtons"),
        # so multi-word denylist/vocabulary entries keep matching downstream.
        text = re.sub(r"['\u2019\u2018]", "", text)
        cleaned = re.sub(r"[^\w\s\?\-\,\.]", " ", text)
        return re.sub(r"\s+", " ", cleaned).strip()

    def _has_explicit_topic(self, clean_query: str) -> bool:
        """General self-sufficiency signal (behavior contract Rules 1 & 3).

        True when the CURRENT query names its own biology topic through any
        pre-existing general mechanism: extracted biology entities, the
        canonical concept vocabulary, or a syllabus-valid verdict with real
        matched keywords. Such queries must never be history-rewritten —
        pronouns bind intra-sententially; topic-less follow-ups still inherit.
        No topic/keyword lists are hardcoded here.
        """
        try:
            if self.extract_biology_entities(clean_query):
                return True
        except Exception:
            pass
        try:
            if concept_normalizer.get_canonical_concept_name(clean_query):
                return True
        except Exception:
            pass
        try:
            chk = self.validator.check_query_syllabus(clean_query)
            kws = [k for k in (chk.get("matched_keywords") or [])
                   if str(k).strip().lower() not in ("", "contextual_followup")]
            if chk.get("is_valid") and kws:
                return True
        except Exception:
            pass
        return False

    def resolve_conversational_anaphora(
        self,
        current_query: str,
        history: Optional[List[Dict[str, str]]] = None,
        student_id: str = "student_local"
    ) -> Tuple[str, bool]:
        """
        Resolves conversational pronouns ('it', 'that', 'these folds', 'this organ')
        and implicit antecedents using conversation context.
        """
        clean_curr = self.clean_text(current_query)
        was_resolved = False

        # Look for focal concept in state
        focal = self.context_tracker.get_focal_concept(student_id)
        focal_name = focal[2] if focal else None
        last_subtopic = self.context_tracker.get_last_subtopic(student_id)

        # Fallback: scan recent history for focal biology concept if tracker state empty
        if not focal_name and history:
            for turn in reversed(history[-4:]):
                content = str(turn.get("content", ""))
                norm_c = concept_normalizer.get_canonical_concept_name(content)
                if norm_c:
                    focal_name = norm_c
                    break
                # Assistant format extraction: 📌 **<Title>** or 📖 **Chapter:** <Chapter>
                m_t = re.search(r"📌\s*\*\*([^*]+)\*\*", content)
                if m_t:
                    cand = m_t.group(1).split("—")[0].strip()
                    if cand and len(cand) >= 3:
                        focal_name = cand
                        break
                m_ch = re.search(r"📖\s*\*\*Chapter:\*\*\s*([^\n\r]+)", content)
                if m_ch:
                    cand = m_ch.group(1).strip()
                    if cand and len(cand) >= 3:
                        focal_name = cand
                        break
                # User query syllabus extraction
                s_chk = self.validator.check_query_syllabus(content)
                if s_chk.get("is_valid") and s_chk.get("chapter_name"):
                    focal_name = s_chk["chapter_name"]
                    break

        # Check subtopic from history (e.g. "folds", "cristae")
        if history and not last_subtopic:
            for turn in reversed(history[-3:]):
                c_text = str(turn.get("content", "")).lower()
                if "fold" in c_text or "cristae" in c_text:
                    last_subtopic = "cristae folds"
                    break

        resolved = clean_curr

        # Explicit-topic guard (contract Rules 1 & 3): the current query names
        # its own topic, so historical focal context must NOT be spliced in.
        # Genuine topic-less follow-ups fall through to the rules below.
        if focal_name and self._has_explicit_topic(clean_curr):
            return resolved, False

        # 0. Bare follow-ups ("why?", "how?", "and then?") inherit the focal concept
        # so the syllabus gate and retrieval see a grounded question, not a stray word.
        if focal_name and re.fullmatch(
            r"(why|how|what|and then|tell me more|go on|continue|explain again)\s*\??", clean_curr, re.IGNORECASE
        ):
            resolved = f"{clean_curr.strip()} about {focal_name}?"
            return resolved, True

        # 1. Handle "What does that increase?" or "What does it increase?"
        if re.search(r"\bwhat does (that|it|this) increase\b", clean_curr, re.IGNORECASE):
            recent_text = ""
            if history:
                recent_text = " ".join(str(h.get("content", "")) for h in history[-2:]).lower()
            if "fold" in recent_text or "crista" in recent_text or (last_subtopic and "fold" in last_subtopic.lower()):
                subject = f"{focal_name} folds (cristae)" if focal_name else "mitochondrial folds cristae"
            else:
                subject = last_subtopic or (f"{focal_name} cristae folds" if focal_name else "mitochondrial cristae folds")
            resolved = f"What do {subject} increase?"
            return resolved, True

        # 2. Handle "Give me 3 questions" / "Give me 3 questions on it"
        m_mcq_implicit = re.search(r"\bgive me (\d+)\s*(?:easy|medium|hard)?\s*(?:questions?|mcqs?)(?:\s+on\s+it|\s+about\s+it)?\b", clean_curr, re.IGNORECASE)
        has_explicit_on_topic = bool(re.search(r"\bon\s+[a-zA-Z]{3,}\b", clean_curr, re.IGNORECASE) and not re.search(r"\bon\s+it\b", clean_curr, re.IGNORECASE))
        if m_mcq_implicit and focal_name and not has_explicit_on_topic:
            count_num = m_mcq_implicit.group(1)
            resolved = f"Give me {count_num} MCQs on {focal_name}"
            return resolved, True

        # 3. Handle "Explain it again" / "explain again"
        if re.search(r"\bexplain\s+(it\s+)?again\b", clean_curr, re.IGNORECASE) and focal_name:
            resolved = f"Explain {focal_name} again with a simpler approach"
            return resolved, True

        # 4. Handle pronouns "it", "this", "that", "these", "its", "their", "they"
        pronoun_match = re.search(r"\b(it|this|that|these|its|they|their|the organ|the organelle|the process)\b", resolved, re.IGNORECASE)
        if pronoun_match and focal_name:
            p = pronoun_match.group(1)
            # If current query mentions folds, e.g. "Why does it have folds?"
            if "fold" in resolved.lower():
                self.context_tracker.get_state(student_id).last_subtopic = f"{focal_name} folds"
            resolved = re.sub(r"\b" + re.escape(p) + r"\b", focal_name, resolved, count=1, flags=re.IGNORECASE)
            was_resolved = True

        # 5. Follow-ups without explicit pronoun: "give me an analogy", "explain simpler", "give mnemonic", "exam traps"
        if focal_name and not was_resolved:
            if re.search(r"\b(analogy|simpler|simple terms|everyday terms|mnemonic|mnemonics|exam traps?|traps?)\b", resolved, re.IGNORECASE):
                resolved = f"{resolved.rstrip('.?!')} for {focal_name}"
                was_resolved = True

        return resolved, was_resolved

    def extract_biology_entities(self, query: str) -> List[str]:
        """Extracts recognized biology terms and concept canonical names."""
        tokens = query.lower().split()
        entities = set()

        for token in tokens:
            cleaned = re.sub(r"[^\w]", "", token)
            if cleaned in BIOLOGY_SYNONYMS:
                entities.add(cleaned)

        norm_matches = concept_normalizer.normalize(query)
        for _, info in norm_matches.items():
            entities.add(info["canonical_name"].lower())

        return list(entities)

    def expand_synonyms(self, query: str) -> str:
        """Expands query with biological synonyms for high retrieval recall."""
        tokens = query.lower().split()
        expanded_terms = set(tokens)
        for token in tokens:
            cleaned_token = re.sub(r"[^\w]", "", token)
            if cleaned_token in BIOLOGY_SYNONYMS:
                for syn in BIOLOGY_SYNONYMS[cleaned_token][:3]:
                    expanded_terms.add(syn)
        return " ".join(expanded_terms)

    def classify_intent(self, query: str) -> Tuple[str, float]:
        """Classifies student intention into 10+ pedagogical categories."""
        clean = query.lower()
        for intent, pattern in self.INTENT_PATTERNS:
            if re.search(pattern, clean):
                return intent, 0.92
        return "general_doubt", 0.70

    def identify_cognitive_level(self, query: str) -> Dict[str, Any]:
        """Maps query to Bloom's Taxonomy cognitive level (BT1 to BT6)."""
        clean = query.lower()
        for level, keywords in self.BLOOM_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", clean):
                    level_names = {
                        "BT1": "Remembering (Knowledge Recall)",
                        "BT2": "Understanding (Conceptual Comprehension)",
                        "BT3": "Applying (Problem Solving)",
                        "BT4": "Analyzing (Distinctions & Structure)",
                        "BT5": "Evaluating (Critical Judgement)",
                        "BT6": "Creating (Synthesis)",
                    }
                    return {
                        "level_code": level,
                        "level_name": level_names.get(level, level),
                        "trigger_keyword": kw,
                    }
        return {
            "level_code": "BT2",
            "level_name": "Understanding (Conceptual Comprehension)",
            "trigger_keyword": "default",
        }

    def process_query(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
        student_id: str = "student_local"
    ) -> Dict[str, Any]:
        """
        Executes full NLP question-understanding pipeline:
        1. Shorthand Normalization ("abt" -> "about")
        2. Typo Correction
        3. Conversational Anaphora & Antecedent Resolution
        4. Intent Classification (12 categories)
        5. Bloom's Cognitive Level Identification
        6. Biology Entity Extraction
        7. Syllabus Boundary Validation
        """
        raw_query = (query or "").strip()
        shorthand_normalized = self.normalize_shorthand(raw_query)
        typo_corrected = concept_normalizer.correct_typos(shorthand_normalized)

        resolved_query, was_resolved = self.resolve_conversational_anaphora(
            typo_corrected, history or [], student_id=student_id
        )

        is_from_basics = any(k in resolved_query.lower() for k in [
            "from basics", "from basic", "for beginner", "for beginners", "like i'm weak",
            "like im weak", "step by step", "simple terms", "teach basics", "basic explanation"
        ])

        # Get intent and focal context early for syllabus inheritance
        intent, intent_conf = self.classify_intent(resolved_query)
        focal = self.context_tracker.get_focal_concept(student_id)

        # Check if this is a context-dependent follow-up that should inherit syllabus validity from focal concept
        follow_up_intents = {"example", "why", "how_process", "function", "definition", "follow_up", "general_doubt"}
        has_focal_context = focal is not None
        
        syllabus_check = self.validator.check_query_syllabus(resolved_query)
        
        # If query is a generic follow-up but we have focal context or resolved query, allow it
        if not syllabus_check.get("is_valid") and (has_focal_context or was_resolved) and intent in follow_up_intents:
            # Inherit syllabus validity from focal concept
            focal_concept = (focal[1] if focal else "")
            focal_check = self.validator.check_query_syllabus(focal_concept) if focal_concept else {}
            if not focal_check.get("is_valid"):
                focal_check = self.validator.check_query_syllabus(resolved_query)
            if focal_check.get("is_valid"):
                syllabus_check = {
                    "is_valid": True,
                    "confidence": "context_inherited",
                    "chapter_id": focal_check.get("chapter_id"),
                    "chapter_name": focal_check.get("chapter_name"),
                    "unit_name": focal_check.get("unit_name"),
                    "matched_keywords": ["contextual_followup"],
                    "inherited_from": focal_concept or focal_check.get("chapter_name")
                }
        
        # Raw-text rescan: cleaning strips symbols ('C++' -> 'C'), so code-flavoured
        # mixed queries are re-checked against the uncleaned text. A raw
        # non-biology verdict always wins (general anti-disguise mechanism).
        if syllabus_check.get("is_valid"):
            try:
                raw_check = self.validator.check_query_syllabus(raw_query)
                if not raw_check.get("is_valid") and raw_check.get("reason") == "non_biology_domain":
                    syllabus_check = raw_check
            except Exception:
                pass
        
        cognitive = self.identify_cognitive_level(resolved_query)
        expanded_query = self.expand_synonyms(resolved_query)
        entities = self.extract_biology_entities(resolved_query)

        return {
            "raw_query": raw_query,
            "normalized_query": typo_corrected,
            "resolved_query": resolved_query,
            "was_context_resolved": was_resolved or (resolved_query.lower() != raw_query.lower()),
            "syllabus_valid": syllabus_check["is_valid"],
            "syllabus_data": syllabus_check,
            "intent": intent,
            "intent_confidence": intent_conf,
            "cognitive_level": cognitive,
            "expanded_query": expanded_query,
            "biology_entities": entities,
            "is_from_basics": is_from_basics,
            "focal_concept": focal[1] if focal else None,
            "canonical_concept": concept_normalizer.get_canonical_concept_name(resolved_query)
        }


nlp_pipeline = NLPPipeline()
