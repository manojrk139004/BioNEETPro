"""
BioNEETPro - MCQ Engine & Validation Unit Tests
==============================================
Validates:
1. Every generated MCQ satisfies strict canonical criteria (4 unique options, valid correct_index 0-3).
2. On-demand quantity parsing supports 1, 5, 10, 20 questions.
3. Difficulty overrides work (easy, medium, hard) vs adaptive default.
4. Topic filtering respects NCERT biology domain.
5. Socratic chat formatting generates clean Markdown with collapsible explanations.
"""

import unittest
import json
from pathlib import Path
from mcq_engine import mcq_engine, LocalMCQEngine


class TestMCQValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = mcq_engine

    def test_01_mcq_pool_integrity(self):
        """Verifies every question in the pool is strictly valid."""
        self.assertGreater(len(self.engine.mcq_pool), 50, "MCQ pool should contain at least 50 validated questions")

        for idx, q in enumerate(self.engine.mcq_pool):
            self.assertTrue(self.engine.validate_mcq(q), f"MCQ at index {idx} failed validation: {q}")
            self.assertEqual(len(q["options"]), 4, f"MCQ {q['id']} does not have 4 options")
            self.assertEqual(len(set(q["options"])), 4, f"MCQ {q['id']} has duplicate options")
            self.assertIn(q["correct_index"], [0, 1, 2, 3], f"MCQ {q['id']} has invalid correct_index")
            self.assertEqual(q["correct_answer"], q["options"][q["correct_index"]])
            self.assertTrue(len(q["question"]) > 10, f"MCQ {q['id']} has question text too short")

        print(f"\n[PASS] MCQ Pool Integrity: {len(self.engine.mcq_pool)}/{len(self.engine.mcq_pool)} MCQs 100% valid.")

    def test_02_dynamic_quantity_generation(self):
        """Tests on-demand quantity parsing for different counts."""
        test_counts = [1, 3, 5, 10]
        for c in test_counts:
            result = self.engine.generate_mcqs(f"Give me {c} questions on Biology")
            self.assertEqual(result["status"], "success")
            self.assertEqual(len(result["mcqs"]), c, f"Expected {c} questions, got {len(result['mcqs'])}")

        print(f"[PASS] Dynamic Quantity Parsing: {test_counts} successfully generated.")

    def test_03_difficulty_override(self):
        """Tests that user difficulty overrides take precedence."""
        diff_cases = [
            ("Give me 3 easy questions", "easy"),
            ("Give me 3 medium questions", "medium"),
            ("Give me 3 hard questions", "hard"),
        ]

        for query, expected_diff in diff_cases:
            result = self.engine.generate_mcqs(query)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["difficulty"], expected_diff)
            self.assertEqual(result["difficulty_mode"], "user_override")

        print(f"[PASS] Difficulty Override: Easy/Medium/Hard user overrides respected.")

    def test_04_topic_filtering(self):
        """Tests that topic filters target relevant biology chapters."""
        topics = ["photosynthesis", "genetics", "circulation", "respiration"]
        for t in topics:
            result = self.engine.generate_mcqs(f"Give me 2 questions on {t}")
            self.assertEqual(result["status"], "success")
            self.assertGreaterEqual(len(result["mcqs"]), 1)

        print(f"[PASS] Topic Filtering: Verified across {topics}.")

    def test_05_chat_formatting_structure(self):
        """Tests that Markdown formatting includes Dr. Arya header and collapsible answers."""
        result = self.engine.generate_mcqs("Give me 2 MCQs on Genetics")
        formatted = self.engine.format_mcqs_for_chat(result)

        self.assertIn("Dr. Arya", formatted)
        self.assertIn("<details>", formatted)
        self.assertIn("</details>", formatted)
        self.assertIn("Correct Answer:", formatted)
        self.assertIn("NCERT Explanation:", formatted)

        print(f"[PASS] Socratic Chat Formatting: Proper Markdown generated with interactive tags.")

    def test_06_shipped_seed_has_unique_ids_and_correct_translation(self):
        """The deployable Firestore seed keeps identifiers unique and the known bad item corrected."""
        seed_path = Path(__file__).resolve().parents[1] / "data" / "mcq_firestore_seed.json"
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        ids = [str(item.get("id", "")) for item in seed]
        self.assertEqual(len(ids), len(set(ids)), "MCQ IDs must be unique for cloud sync")

        matches = [item for item in seed if item.get("id") == "mbi-translation-definition"]
        self.assertEqual(len(matches), 1, "The corrected translation MCQ must appear exactly once")
        item = matches[0]
        self.assertEqual(item["options"][item["correct"]], "Synthesis of protein from an mRNA template")
        self.assertEqual(len(item["options"]), 4)


if __name__ == "__main__":
    unittest.main()
