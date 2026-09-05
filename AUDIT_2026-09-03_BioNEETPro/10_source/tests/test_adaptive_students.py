"""
BioNEETPro - Adaptive Student Modeling & Pedagogical Strategy Tests
==================================================================
Validates:
1. Bayesian Knowledge Tracing (BKT) probability updates across sequences of attempts.
2. Trajectory stage classifications (Novice -> Learning -> Developing -> Competent -> Strong -> NEET Ready).
3. Repeated mistake detection and escalation (mild -> warning -> critical).
4. Socratic pedagogical strategy switching in AdaptiveBiologyTutor based on mastery & error history.
5. Response time and cognitive level tracking.
"""

import unittest
import uuid
from learner_model import learner_manager, BayesianKnowledgeTracer
from adaptive_tutor import adaptive_tutor


class TestAdaptiveStudents(unittest.TestCase):

    def setUp(self):
        self.student_id = f"test_student_{uuid.uuid4().hex[:8]}"
        self.manager = learner_manager
        self.tutor = adaptive_tutor
        self.bkt = BayesianKnowledgeTracer()

    def test_01_bkt_mathematical_updates(self):
        """Verifies BKT increases on correct answers and decreases on errors."""
        prior = 0.50

        # Correct answer
        after_correct = self.bkt.update_mastery(prior, is_correct=True)
        self.assertGreater(after_correct, prior, "BKT mastery must increase after a correct answer")

        # Incorrect answer
        after_incorrect = self.bkt.update_mastery(prior, is_correct=False)
        self.assertLess(after_incorrect, prior, "BKT mastery must decrease after an incorrect answer")

        # Consecutive correct streak approaches 0.99
        p = 0.50
        for _ in range(5):
            p = self.bkt.update_mastery(p, is_correct=True)
        self.assertGreaterEqual(p, 0.85, "Consecutive correct answers must drive mastery towards mastery ceiling")

        print(f"\n[PASS] BKT Mathematics: Correct (0.50 -> {after_correct}) and Incorrect (0.50 -> {after_incorrect}).")

    def test_02_trajectory_stage_progression(self):
        """Verifies student moves up through trajectory stages as mastery builds."""
        p1 = self.manager.get_or_create_profile(self.student_id)
        self.assertEqual(p1["trajectory_stage"], "Learning")  # 0.50 default baseline

        # Simulate strong student answering 6 questions correctly
        for i in range(6):
            self.manager.record_attempt(
                student_id=self.student_id,
                concept_id=f"BIO-TEST-{i}",
                chapter_id="c13",
                is_correct=True,
                response_time_sec=12.0
            )

        updated = self.manager.get_or_create_profile(self.student_id)
        self.assertIn(updated["trajectory_stage"], ["Strong", "NEET Ready"])
        self.assertGreater(updated["overall_mastery"], 0.70)

        print(f"[PASS] Trajectory Progression: Baseline -> {updated['trajectory_stage']} (Mastery: {updated['overall_mastery']}).")

    def test_03_repeated_mistakes_escalation(self):
        """Verifies repeated error counts escalate severity: warning (2 errors) -> critical (4 errors)."""
        concept = "BIO-C08-01"

        # 1st mistake -> mild
        res1 = self.manager.record_attempt(self.student_id, concept, "c08", is_correct=False)
        prof1 = self.manager.get_or_create_profile(self.student_id)
        self.assertEqual(prof1["repeated_mistakes"][concept]["mistake_count"], 1)

        # 2nd mistake -> warning
        res2 = self.manager.record_attempt(self.student_id, concept, "c08", is_correct=False)
        prof2 = self.manager.get_or_create_profile(self.student_id)
        self.assertEqual(prof2["repeated_mistakes"][concept]["severity"], "warning")

        # 4th mistake -> critical
        self.manager.record_attempt(self.student_id, concept, "c08", is_correct=False)
        self.manager.record_attempt(self.student_id, concept, "c08", is_correct=False)
        prof4 = self.manager.get_or_create_profile(self.student_id)
        self.assertEqual(prof4["repeated_mistakes"][concept]["severity"], "critical")
        self.assertEqual(prof4["repeated_mistakes"][concept]["mistake_count"], 4)

        print(f"[PASS] Repeated Mistake Escalation: 1 error (mild) -> 2 errors (warning) -> 4 errors (critical).")

    def test_04_pedagogical_strategy_adaptation(self):
        """Verifies tutor changes teaching strategy based on student profile and repeated mistakes."""
        # Case A: Repeated mistakes on Mitochondria (2 errors) -> switches to concrete_analogy
        self.manager.record_attempt(self.student_id, "BIO-C08-01", "c08", is_correct=False)
        self.manager.record_attempt(self.student_id, "BIO-C08-01", "c08", is_correct=False)

        resp_analogy = self.tutor.generate_tutoring_response("What is mitochondria?", student_id=self.student_id)
        self.assertEqual(resp_analogy["strategy_used"], "concrete_analogy")
        self.assertTrue(resp_analogy["is_repeated_weakness"])
        self.assertIn("Adaptive Remediation", resp_analogy["reply"])

        # Case B: Remedial Diagnostic (4 errors)
        self.manager.record_attempt(self.student_id, "BIO-C08-01", "c08", is_correct=False)
        self.manager.record_attempt(self.student_id, "BIO-C08-01", "c08", is_correct=False)
        resp_remedial = self.tutor.generate_tutoring_response("What is mitochondria?", student_id=self.student_id)
        self.assertEqual(resp_remedial["strategy_used"], "remedial_diagnostic")

        print(f"[PASS] Pedagogical Strategy Adaptation: Successfully shifted to concrete_analogy and remedial_diagnostic.")

    def test_05_speed_categorization(self):
        """Verifies speed analysis correctly classifies fast/slow attempts."""
        r_fast = self.manager.record_attempt(self.student_id, "BIO-C01-01", "c01", is_correct=True, response_time_sec=8.0)
        self.assertEqual(r_fast.get("speed_category"), "fast_correct")

        r_slow = self.manager.record_attempt(self.student_id, "BIO-C01-02", "c01", is_correct=True, response_time_sec=42.0)
        self.assertEqual(r_slow.get("speed_category"), "slow_correct")

        r_guess = self.manager.record_attempt(self.student_id, "BIO-C01-03", "c01", is_correct=False, response_time_sec=5.0)
        self.assertEqual(r_guess.get("speed_category"), "fast_incorrect")

        print(f"[PASS] Speed Categorization: fast_correct (<15s), slow_correct (>30s), fast_incorrect (<10s).")


if __name__ == "__main__":
    unittest.main()
