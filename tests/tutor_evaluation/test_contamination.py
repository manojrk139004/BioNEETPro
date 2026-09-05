"""Phase 8/9: retrieval + learner-model contamination.

- 10-turn single-topic histories then an explicit switch: EVIDENCE (top
  titles/chapters) and reply must reflect the CURRENT query.
- Extreme learner profiles (weak/strong) must change depth, never topic.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import CORPUS  # noqa: E402
from harness import run_conversation, topic_hit  # noqa: E402
from learner_model import learner_manager  # noqa: E402

LONG_CONTEXT = [
    "Explain cardiac cycle.",
    "What are the phases of cardiac cycle?",
    "Tell me more about systole.",
    "What about diastole?",
    "Give me an example of cardiac output.",
    "Explain cardiac cycle simply.",
    "What is the role of valves?",
    "How is cardiac output regulated?",
    "Why does the heart have 4 chambers?",
    "Give me 3 questions on it",
]

CARDIAC_TOKS = ["cardiac", "systole", "diastole", "ventricle", "atrium"]


class TestRetrievalContamination(unittest.TestCase):
    def test_long_context_then_switch(self):
        pairs = [
            ("can u teach me flower and its parts",
             ["flower", "sepal", "petal", "stamen", "carpel"]),
            ("Now teach me nephron.",
             ["nephron", "glomerulus", "filtrate"]),
            ("Explain DNA replication.",
             ["replicat", "semiconservative", "helicase"]),
        ]
        fails = []
        for current, toks in pairs:
            sid, turns = run_conversation(LONG_CONTEXT + [current])
            out = turns[-1][1]
            if not topic_hit(out, toks):
                fails.append((current, out.get("chapter_id"),
                              (out.get("title") or "")[:60]))
            # evidence itself must not be cardiac
            if topic_hit(out, CARDIAC_TOKS) and not topic_hit(out, toks):
                fails.append((current, "STALE-CARDIAC-EVIDENCE",
                              out.get("chapter_id"), ""))
        self.assertEqual(fails, [], f"contamination: {fails[:8]}")


class TestLearnerContamination(unittest.TestCase):
    def _profile(self, sid, weak=(), strong=()):
        for c in weak:
            for _ in range(6):
                learner_manager.record_attempt(
                    student_id=sid, concept_id=c, chapter_id="general",
                    is_correct=False, difficulty="medium",
                    cognitive_level="BT2", response_time_sec=10.0, topic_id="t")
        for c in strong:
            for _ in range(6):
                learner_manager.record_attempt(
                    student_id=sid, concept_id=c, chapter_id="general",
                    is_correct=True, difficulty="hard",
                    cognitive_level="BT4", response_time_sec=8.0, topic_id="t")

    def test_weak_profile_does_not_hijack_topic(self):
        import uuid
        sid = f"weakprof_{uuid.uuid4().hex[:8]}"
        self._profile(sid, weak=("BIO-CIRC",), strong=("BIO-FLOWER",))
        _, turns = run_conversation(["Teach me flower."], sid=sid)
        out = turns[0][1]
        self.assertTrue(
            topic_hit(out, ["flower", "sepal", "petal", "stamen", "carpel"]),
            f"weak-profile hijack: {out.get('chapter_id')} {(out.get('title') or '')[:60]}")

    def test_weak_genetics_profile_still_teaches_genetics(self):
        import uuid
        sid = f"weakgen_{uuid.uuid4().hex[:8]}"
        self._profile(sid, weak=("BIO-GEN",), strong=("BIO-FLOWER",))
        _, turns = run_conversation(["Teach me genetics."], sid=sid)
        out = turns[0][1]
        self.assertTrue(
            topic_hit(out, ["mendel", "gene", "allele", "dna", "inheritance"]),
            f"weak-profile hijack: {out.get('chapter_id')} {(out.get('title') or '')[:60]}")


if __name__ == "__main__":
    unittest.main()
