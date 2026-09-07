"""
BioNEETPro - Comprehensive Master Verification Test Suite
Tests all 8 Architectural Pillars:
1. Syllabus Constraint & Boundary Validation
2. Biology Concept Graph Traversal
3. NLP Anaphora Resolution & Intent Classification
4. Hybrid Retrieval & Relevance Scoring
5. Adaptive Tutor Pedagogy & Strategy Switching
6. On-Demand Local MCQ Engine
7. Bayesian Knowledge Tracing & Learner Profile
8. Emergency Fallback Controller Isolation
"""

import unittest
from syllabus import syllabus_validator
from concept_graph import concept_graph
from nlp_pipeline import nlp_pipeline
from retrieval_engine import retrieval_engine
from adaptive_tutor import adaptive_tutor
from mcq_engine import mcq_engine
from learner_model import learner_manager
from fallback_controller import fallback_controller


class TestSyllabusValidation(unittest.TestCase):
    def test_in_syllabus_queries(self):
        valid_queries = [
            "Why is blood red?",
            "Explain Calvin cycle in photosynthesis",
            "How does lac operon repressor work?",
            "Explain 206 bones in human body",
            "Why leaf is green?",
            "Give me 5 MCQs on Genetics"
        ]
        for q in valid_queries:
            res = syllabus_validator.check_query_syllabus(q)
            self.assertTrue(res["is_valid"], f"Query should be valid: {q}")

    def test_out_of_syllabus_queries(self):
        invalid_queries = [
            "What is projectile motion in physics?",
            "Write a python script to sort an array",
            "Who won the cricket world cup?",
            "How does quantum superposition work?",
            "Explain SN1 reaction mechanism in organic chemistry"
        ]
        for q in invalid_queries:
            res = syllabus_validator.check_query_syllabus(q)
            self.assertFalse(res["is_valid"], f"Query should be rejected: {q}")
            self.assertIn("refusal_message", res)


class TestConceptGraph(unittest.TestCase):
    def test_graph_nodes_and_edges(self):
        self.assertGreater(len(concept_graph.nodes), 30)
        self.assertGreater(len(concept_graph.adj_out), 20)

    def test_insulin_causal_chain(self):
        chain = concept_graph.get_causal_chain("BIO-C22-01")
        self.assertGreaterEqual(len(chain), 2)
        rels = [step["relationship"] for step in chain]
        self.assertIn("CAUSES", rels)
        self.assertIn("RESULTS_IN", rels)

    def test_calvin_cycle_contrasts(self):
        contrasts = concept_graph.get_contrasting_concepts("BIO-C13-02")
        self.assertTrue(any("Kranz" in c["title"] or "C4" in c["title"] or "Hatch" in c["title"] for c in contrasts))

    def test_prerequisite_tracing(self):
        prereqs = concept_graph.get_prerequisites("BIO-C27-01")
        self.assertTrue(len(prereqs) > 0)


class TestNLPPipeline(unittest.TestCase):
    def test_anaphora_resolution(self):
        history = [
            {"role": "user", "content": "Can you explain mitochondria?"},
            {"role": "assistant", "content": "Mitochondria are double-membraned organelles that generate ATP."}
        ]
        res = nlp_pipeline.process_query("Why does it have folds?", history)
        self.assertIn("mitochondria", res["resolved_query"].lower())

    def test_intent_classification(self):
        self.assertEqual(nlp_pipeline.classify_intent("Why is blood red?")[0], "why")
        self.assertEqual(nlp_pipeline.classify_intent("What is the difference between C3 and C4 plants?")[0], "difference_comparison")
        self.assertEqual(nlp_pipeline.classify_intent("Give me 5 hard MCQs on Genetics")[0], "mcq_request")
        self.assertEqual(nlp_pipeline.classify_intent("What is the Central Dogma?")[0], "definition")

    def test_blooms_cognitive_level(self):
        cog1 = nlp_pipeline.identify_cognitive_level("Define photosynthesis")
        self.assertEqual(cog1["level_code"], "BT1")

        cog2 = nlp_pipeline.identify_cognitive_level("Explain the mechanism of sliding filament theory")
        self.assertEqual(cog2["level_code"], "BT2")

        cog4 = nlp_pipeline.identify_cognitive_level("Distinguish between mitosis and meiosis")
        self.assertEqual(cog4["level_code"], "BT4")


class TestHybridRetrieval(unittest.TestCase):
    def test_high_confidence_matches(self):
        tests = [
            ("why leaf is green", "Why Leaves Are Green"),
            ("why is human excretion yellow", "Why Human Excretion"),
            ("206 bones in human body", "206 Bones"),
            ("semi conservative replication", "Semi-Conservative DNA Replication")
        ]
        for query, expected_phrase in tests:
            res = retrieval_engine.search(query, top_k=1)
            self.assertTrue(len(res) > 0)
            top = res[0]
            self.assertIn(expected_phrase.lower(), top["title"].lower())
            self.assertIn(top["confidence"], ["HIGH", "MEDIUM"])


class TestAdaptiveTutor(unittest.TestCase):
    def test_adaptive_socratic_response(self):
        res = adaptive_tutor.generate_tutoring_response("why leaf is green?", student_id="unit_test_student")
        self.assertEqual(res["status"], "success")
        self.assertIn("Chlorophyll", res["reply"])
        self.assertTrue("Dr. Arya" in res["reply"] or "Dr. Arya" in res["reply"])

    def test_out_of_syllabus_refusal(self):
        res = adaptive_tutor.generate_tutoring_response("Explain quantum electrodynamics", student_id="unit_test_student")
        self.assertEqual(res["status"], "out_of_syllabus")
        self.assertIn("Syllabus Boundary Notice", res["reply"])


class TestMCQEngine(unittest.TestCase):
    def test_mcq_quantity_and_difficulty_parsing(self):
        req1 = mcq_engine.parse_mcq_request("Give me 3 hard MCQs")
        self.assertEqual(req1["requested_count"], 3)
        self.assertEqual(req1["explicit_difficulty"], "hard")

        req2 = mcq_engine.parse_mcq_request("Give me 10 easy questions on Photosynthesis")
        self.assertEqual(req2["requested_count"], 10)
        self.assertEqual(req2["explicit_difficulty"], "easy")
        self.assertEqual(req2["target_topic"], "photosynthesis")

    def test_mcq_generation_structure(self):
        # NOTE (2026-09-04 isolation fix): use a fresh student id. The old
        # "unit_test_student" id is shared with tutor tests above that leave a
        # stale focal concept ("Chloroplasts") in the context tracker, so a
        # bare "Give me 2 MCQs" resolved to that 1-question topic instead of
        # the mixed pool this structure test intends. Intent unchanged.
        gen = mcq_engine.generate_mcqs("Give me 2 MCQs", student_id="unit_test_struct")
        self.assertEqual(gen["status"], "success")
        self.assertEqual(len(gen["mcqs"]), 2)
        for mcq in gen["mcqs"]:
            self.assertEqual(len(mcq["options"]), 4)
            self.assertIn("correct_answer", mcq)
            self.assertIn("explanation", mcq)


class TestLearnerModelBKT(unittest.TestCase):
    def test_bkt_mastery_update(self):
        bkt = learner_manager.bkt
        prior = 0.50
        # Correct answer should increase mastery
        p_correct = bkt.update_mastery(prior, is_correct=True)
        self.assertGreater(p_correct, prior)

        # Incorrect answer should decrease mastery
        p_incorrect = bkt.update_mastery(prior, is_correct=False)
        self.assertLess(p_incorrect, prior)

    def test_repeated_mistake_tracking(self):
        import uuid
        student_id = f"test_mistake_{uuid.uuid4().hex[:8]}"
        c_id = "BIO-C13-01"

        # Record 2 errors
        learner_manager.record_attempt(student_id, c_id, "c13", is_correct=False)
        res = learner_manager.record_attempt(student_id, c_id, "c13", is_correct=False)

        self.assertTrue(res["is_repeated_weakness"])
        self.assertEqual(res["mistake_severity"], "warning")


class TestFallbackController(unittest.TestCase):
    def test_fallback_disabled_by_default(self):
        self.assertFalse(fallback_controller.should_trigger_fallback("LOW"))


if __name__ == "__main__":
    unittest.main()
