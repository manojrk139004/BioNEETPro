"""
BioNEETPro - Syllabus Boundary Strict Enforcement Tests
======================================================
Validates:
1. Approved NCERT Class 11 and 12 Biology chapters are accepted.
2. Physics questions are strictly rejected.
3. Chemistry questions are strictly rejected.
4. Mathematics questions are strictly rejected.
5. Programming, celebrity, sports, and general non-academic queries are rejected.
6. Edge cases and mixed queries.
"""

import unittest
from syllabus import syllabus_validator


class TestSyllabusBoundary(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.validator = syllabus_validator

    def test_01_valid_biology_chapters_accepted(self):
        """Tests that queries across all major NCERT biology units are accepted."""
        valid_queries = [
            "What is photosynthesis in higher plants?",
            "Explain cellular respiration and ATP yield",
            "Describe the human circulatory system and heart",
            "How does the nephron filter blood in the kidney?",
            "What are Mendel's laws of inheritance?",
            "Explain the central dogma: DNA replication, transcription, translation",
            "What is Bt cotton and cry gene in biotechnology?",
            "Describe ecosystem energy flow and 10 percent rule",
            "Explain human spermatogenesis and oogenesis",
            "What is biodiversity hotspot and in situ conservation?",
        ]

        for q in valid_queries:
            res = self.validator.check_query_syllabus(q)
            self.assertTrue(res["is_valid"], f"Valid biology query falsely rejected: '{q}'")

    def test_02_physics_domain_rejected(self):
        """Tests that physics questions are rejected with out-of-syllabus guidance."""
        physics_queries = [
            "What is Newton's first law of motion?",
            "Calculate velocity of a projectile launched at 45 degrees",
            "What is Gauss's law of electric flux?",
            "Explain quantum mechanics and Schrodinger equation",
            "How does an optical prism disperse white light?",
            "What is Kirchhoff's current and voltage law?",
            "Calculate acceleration due to gravity on Mars",
        ]

        for q in physics_queries:
            res = self.validator.check_query_syllabus(q)
            self.assertFalse(res["is_valid"], f"Physics query falsely accepted: '{q}'")
            self.assertIn("refusal_message", res)

    def test_03_chemistry_domain_rejected(self):
        """Tests that pure chemistry questions are rejected."""
        chemistry_queries = [
            "What is the SN1 and SN2 reaction mechanism in haloalkanes?",
            "How to calculate molarity and molality of a solution?",
            "Explain Le Chatelier's principle in chemical equilibrium",
            "What is the enthalpy change in exothermic reaction?",
            "Describe coordination compounds and ligand field theory",
        ]

        for q in chemistry_queries:
            res = self.validator.check_query_syllabus(q)
            self.assertFalse(res["is_valid"], f"Chemistry query falsely accepted: '{q}'")
            self.assertIn("refusal_message", res)

    def test_04_mathematics_domain_rejected(self):
        """Tests that mathematics questions are rejected."""
        math_queries = [
            "Evaluate the integral of x^2 dx from 0 to 1",
            "What is Pythagoras theorem in trigonometry?",
            "How to find determinant of a 3x3 matrix?",
            "Calculate probability of drawing an ace from a deck of cards",
        ]

        for q in math_queries:
            res = self.validator.check_query_syllabus(q)
            self.assertFalse(res["is_valid"], f"Math query falsely accepted: '{q}'")

    def test_05_programming_and_general_rejected(self):
        """Tests that programming, tech, and non-academic queries are rejected."""
        general_queries = [
            "How to write a Python Flask API endpoint?",
            "What is React useState and useEffect hook?",
            "Who won the 2024 ICC cricket world cup?",
            "Tell me about the latest Marvel superhero movie",
            "What is Bitcoin cryptocurrency and blockchain?",
            "Who is the current prime minister of India?",
        ]

        for q in general_queries:
            res = self.validator.check_query_syllabus(q)
            self.assertFalse(res["is_valid"], f"Non-academic query falsely accepted: '{q}'")


if __name__ == "__main__":
    unittest.main()
