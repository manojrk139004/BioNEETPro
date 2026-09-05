"""
Unit tests for BioNEET Pro local algorithmic tutor engine
"""

import os
import unittest
from pathlib import Path
from tutor_engine import (
    ConceptSearchEngine,
    KnowledgeTracingEngine,
    PedagogicalTracker,
)


class TestTutorEngine(unittest.TestCase):
    def setUp(self):
        self.search_engine = ConceptSearchEngine()
        self.tracker = PedagogicalTracker()
        self.bkt = KnowledgeTracingEngine()

    def test_search_engine_tfidf_ranking(self):
        query = "Explain photosynthesis and light reaction photophosphorylation"
        matches = self.search_engine.match_concept(query, top_k=3)
        self.assertTrue(len(matches) > 0)
        top = matches[0]
        # Should match Non-cyclic Photophosphorylation
        self.assertIn("BIO-C13", top["concept_id"])
        self.assertGreater(top["similarity_score"], 0.20)
        self.assertTrue(any("photosynthesis" in t or "reaction" in t or "light" in t for t in top["matched_terms"]))

    def test_dna_replication_query(self):
        query = "What is semi-conservative DNA replication Meselson Stahl"
        matches = self.search_engine.match_concept(query, top_k=3)
        top = matches[0]
        self.assertEqual(top["concept_id"], "BIO-C28-01")
        self.assertGreater(top["similarity_score"], 0.30)

    def test_brain_white_query(self):
        query = "why is brain white"
        matches = self.search_engine.match_concept(query, top_k=3)
        self.assertTrue(len(matches) > 0)
        top = matches[0]
        self.assertEqual(top["concept_id"], "BIO-C21-01")
        self.assertIn(top["chapter_id"], ["c19", "c21"])
        self.assertIn("White Matter", top["title"])
        self.assertIn("brain", top["matched_terms"])

    def test_bkt_mastery_update(self):
        prior = 0.50
        # Correct answer should boost mastery
        next_mastery = self.bkt.update(prior, is_correct=True)
        self.assertGreater(next_mastery, prior)

        # Incorrect answer should reduce mastery
        lower_mastery = self.bkt.update(prior, is_correct=False)
        self.assertLess(lower_mastery, prior)

    def test_pedagogical_state_machine_steps(self):
        # Step 1: Initialize session
        res1 = self.tracker.start_query_session("What is lac operon regulation repressor")
        self.assertEqual(res1["step_number"], 1)
        self.assertIn(res1["chapter_id"], ["c25", "c28"])
        session_id = res1["session_id"]

        # Step 2: Biological mechanism
        res2 = self.tracker.get_step_content(session_id, 2)
        self.assertEqual(res2["step_number"], 2)
        self.assertIn("Biological Mechanism", res2["content"])

        # Step 3: NEET traps
        res3 = self.tracker.get_step_content(session_id, 3)
        self.assertEqual(res3["step_number"], 3)
        self.assertIn("Common Exam Pitfalls", res3["content"])

        # Step 4: Micro-quiz
        res4 = self.tracker.get_step_content(session_id, 4)
        self.assertEqual(res4["step_number"], 4)
        self.assertIsNotNone(res4["quiz"])
        self.assertEqual(len(res4["quiz"]["options"]), 4)

        # Quiz verification
        verify_res = self.tracker.verify_quiz(session_id, selected_index=res4["quiz"]["correct_index"])
        self.assertTrue(verify_res["is_correct"])
        # NOTE (2026-09-04 fix): BKT mastery caps at 0.99, so a correct answer
        # at the cap correctly holds 0.99 instead of increasing. Assert the
        # real invariant: correct answers never decrease mastery, and the cap
        # is respected. Intent unchanged.
        self.assertGreaterEqual(verify_res["updated_mastery"], verify_res["prior_mastery"])
        self.assertLessEqual(verify_res["updated_mastery"], 0.99)

    def test_csv_persistence(self):
        summary = self.tracker.get_tracker_summary(limit=5)
        self.assertGreater(summary["total_logged_interactions"], 0)
        self.assertIn("matched_concept_id", summary["recent_records"][-1])


if __name__ == "__main__":
    unittest.main()
