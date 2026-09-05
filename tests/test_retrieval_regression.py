"""
BioNEETPro - Retrieval Regression & Zero Random Answer Test Suite
================================================================
Validates:
1. Valid NCERT Biology queries retrieve the correct concept with high/medium confidence.
2. Paraphrased & colloquial queries retrieve the correct concept via normalization.
3. Out-of-syllabus & non-biology queries are strictly REJECTED (Zero Random Answers).
4. Ambiguous queries are safely gated with controlled refusal.
"""

import unittest
from retrieval_engine import retrieval_engine
from adaptive_tutor import adaptive_tutor
from syllabus import syllabus_validator


class TestRetrievalRegression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.retrieval = retrieval_engine
        cls.tutor = adaptive_tutor

    def test_01_core_biology_concepts_retrieved(self):
        """Tests that standard NCERT queries retrieve the expected concepts."""
        test_cases = [
            ("What is mitochondria?", ["mitochondria"]),
            ("Explain Calvin cycle in photosynthesis", ["calvin", "photosynthesis"]),
            ("How does DNA replication work?", ["dna", "replication"]),
            ("What is the function of nephron in kidney?", ["nephron", "excretory", "kidney"]),
            ("Describe the human heart circulation", ["heart", "circulation", "cardiac"]),
            ("How does the sliding filament theory work in muscles?", ["sarcomere", "muscle", "sliding"]),
            ("What are the 206 bones in human skeletal system?", ["bone", "skeletal", "skeleton"]),
            ("Explain crossing over in pachytene meiosis", ["meiosis", "cell cycle", "crossing"]),
            ("How does the lac operon mechanism work?", ["lac operon", "operon"]),
            ("What is glycolysis pathway in respiration?", ["glycolysis", "respiration"]),
        ]

        success_count = 0
        for query, expected_keywords in test_cases:
            res = self.tutor.generate_tutoring_response(query)
            self.assertEqual(res["status"], "success", f"Failed on valid query: '{query}', reply: {res.get('reply')[:100]}")
            self.assertIn(res["confidence"], ["HIGH", "MEDIUM"])
            matched_title = res.get("title", "").lower()
            matched_defn = str(res.get("reply", "")).lower()
            has_match = any(kw in matched_title or kw in matched_defn for kw in expected_keywords)
            self.assertTrue(has_match, f"Expected keywords {expected_keywords} not in matched title '{matched_title}'")
            success_count += 1

        print(f"\n[PASS] Core Biology Concepts: {success_count}/{len(test_cases)} matched correctly.")

    def test_02_concept_aliases_normalized(self):
        """Tests that colloquial biological terms are mapped to canonical concepts."""
        alias_cases = [
            ("What is the powerhouse of the cell?", "mitochondria"),
            ("Why are lysosomes called suicide bags?", "lysosome"),
            ("Which organelle is the food factory of the cell?", "chloroplast"),
            ("What is the master gland of human endocrine system?", "pituitary"),
            ("Which organ is the graveyard of RBCs?", "spleen"),
        ]

        for query, expected_keyword in alias_cases:
            res = self.tutor.generate_tutoring_response(query)
            self.assertIn(res["status"], ["success", "local_fallback"])
            matched_text = (res.get("title", "") + " " + res.get("reply", "")).lower()
            self.assertIn(expected_keyword, matched_text, f"Alias '{query}' did not resolve to '{expected_keyword}'")

        print(f"[PASS] Concept Alias Normalization: {len(alias_cases)}/{len(alias_cases)} normalized successfully.")

    def test_03_zero_random_answers_on_out_of_syllabus(self):
        """CRITICAL: Verifies zero random answers on non-biology queries."""
        banned_queries = [
            "What is Newton's third law of motion?",
            "Explain quantum mechanics and wave function",
            "How to balance redox reactions in chemistry?",
            "What is the SN1 and SN2 reaction mechanism?",
            "Solve the integral of sin(x) cos(x) dx",
            "How to write a Python Flask web server?",
            "Who won the 2024 cricket world cup?",
            "Explain the causes of the French Revolution",
            "What is cryptocurrency and Bitcoin mining?",
            "How does JavaScript event loop work in browser?",
        ]

        irrelevant_retrievals = 0
        for query in banned_queries:
            res = self.tutor.generate_tutoring_response(query)
            # System must either reject as out_of_syllabus or controlled refusal (NO random biological record)
            is_rejected = res["status"] in ("out_of_syllabus", "no_match") or res.get("confidence") == "REJECTED"
            if not is_rejected:
                irrelevant_retrievals += 1
                print(f"FAILED on query: '{query}' -> returned concept '{res.get('title')}'")

            self.assertTrue(
                is_rejected,
                f"VIOLATION: Random answer returned for non-biology query: '{query}' -> concept: '{res.get('title')}'"
            )

        self.assertEqual(irrelevant_retrievals, 0, f"Irrelevant retrieval rate must be 0%, got {irrelevant_retrievals}")
        print(f"[PASS] Zero Random Answers: 0/{len(banned_queries)} irrelevant retrievals. 100% rejection rate.")

    def test_04_controlled_refusal_on_empty_or_gibberish(self):
        """Tests that gibberish or empty queries trigger controlled refusal, never a default dataset row."""
        gibberish_queries = [
            "asdfghjkl qwertyuiop",
            "xyz1234567890",
            "??? !!! ...",
        ]

        for query in gibberish_queries:
            res = self.tutor.generate_tutoring_response(query)
            self.assertIn(res["status"], ["out_of_syllabus", "no_match"])
            self.assertNotIn("status", ["success"])

        print(f"[PASS] Controlled Refusal: All gibberish queries rejected.")


if __name__ == "__main__":
    unittest.main()
