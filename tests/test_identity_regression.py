"""
BioNEET-Pro — Tutor Identity Regression Suite
============================================
Verifies that the canonical AI Biology Mentor persona is consistently
"Dr. Arya" across all tutoring modes, greetings, Socratic fallbacks,
and MCQ chat formatting, and that no stale "Dr. Priya" identity leaks.
"""

import unittest
from adaptive_tutor import adaptive_tutor
from mcq_engine import mcq_engine
from app import build_unified_answer


class TestTutorIdentityRegression(unittest.TestCase):

    def test_01_greeting_identity(self):
        """Verify greeting response introduces Dr. Arya."""
        res = adaptive_tutor.generate_tutoring_response("Hello Dr")
        self.assertEqual(res.get("mode"), "greeting")
        self.assertIn("Dr. Arya", res.get("reply", ""))
        self.assertNotIn("Dr. Priya", res.get("reply", ""))

    def test_02_grounded_tutoring_identity(self):
        """Verify grounded tutoring response uses Dr. Arya."""
        res = adaptive_tutor.generate_tutoring_response("Explain photosynthesis")
        self.assertIn(res.get("status"), ("success", "local_adaptive"))
        self.assertIn("Dr. Arya", res.get("reply", ""))
        self.assertNotIn("Dr. Priya", res.get("reply", ""))

    def test_03_socratic_fallback_identity(self):
        """Verify out-of-syllabus refusal uses Dr. Arya."""
        res = adaptive_tutor.generate_tutoring_response("Explain Newton's laws")
        self.assertEqual(res.get("status"), "out_of_syllabus")
        self.assertIn("Dr. Arya", res.get("reply", ""))
        self.assertNotIn("Dr. Priya", res.get("reply", ""))

    def test_04_mcq_chat_formatting_identity(self):
        """Verify MCQ markdown formatting uses Dr. Arya."""
        mcq_data = mcq_engine.generate_mcqs("Give me 2 MCQs on Genetics")
        formatted = mcq_engine.format_mcqs_for_chat(mcq_data)
        self.assertIn("Dr. Arya", formatted)
        self.assertNotIn("Dr. Priya", formatted)

    def test_05_unified_answer_identity(self):
        """Verify build_unified_answer entry point uses Dr. Arya."""
        out = build_unified_answer("What is mitochondria?")
        self.assertEqual(out.get("status"), "success")
        self.assertIn("Dr. Arya", out.get("reply", ""))
        self.assertNotIn("Dr. Priya", out.get("reply", ""))


if __name__ == "__main__":
    unittest.main()
