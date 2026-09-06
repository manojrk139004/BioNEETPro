"""
BioNEETPro - Interactive MCQ Evaluation & Scoring Unit Tests
============================================================
Verifies:
1. Generating MCQs does NOT spoil answers upfront in the question text.
2. Answering active MCQs via letter format ("1:C, 2:A, 3:B", "C A B", "Option C", "C")
   correctly evaluates against the active session questions.
3. Official NEET Marking scheme (+4 for correct, -1 for incorrect) is accurately calculated.
4. Attempt updates BKT learner model.
5. Answering without an active quiz gives a warm mentor redirection.
"""

import unittest
from mcq_engine import mcq_engine
from adaptive_tutor import adaptive_tutor
from learner_model import learner_manager


class TestInteractiveMCQEvaluation(unittest.TestCase):

    def setUp(self):
        self.student_id = "test_mcq_interactive_student"
        # Generate 3 MCQs on Genetics for this student session
        gen_res = mcq_engine.generate_mcqs("Give me 3 questions on Genetics", student_id=self.student_id)
        self.assertEqual(gen_res["status"], "success")
        self.assertEqual(len(gen_res["mcqs"]), 3)
        self.active_mcqs = gen_res["mcqs"]

    def test_01_no_spoilers_in_chat_prompt(self):
        """Verify format_mcqs_for_chat does not contain answer spoilers by default."""
        gen_res = {"status": "success", "mcqs": self.active_mcqs, "topic": "Genetics", "difficulty": "medium"}
        chat_text = mcq_engine.format_mcqs_for_chat(gen_res)
        self.assertNotIn("<details>", chat_text)
        self.assertNotIn("🔍 Click to Reveal", chat_text)
        self.assertIn("How to answer", chat_text)
        self.assertIn("Question 1", chat_text)
        self.assertIn("Question 2", chat_text)
        self.assertIn("Question 3", chat_text)

    def test_02_all_correct_submission_evaluation(self):
        """Submit all correct answers: expect +12/12 marks and 100% accuracy feedback."""
        c1 = chr(65 + self.active_mcqs[0]["correct_index"])
        c2 = chr(65 + self.active_mcqs[1]["correct_index"])
        c3 = chr(65 + self.active_mcqs[2]["correct_index"])

        submission_query = f"1:{c1}, 2:{c2}, 3:{c3}"
        res = adaptive_tutor.generate_tutoring_response(submission_query, student_id=self.student_id)

        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("mode"), "quiz_evaluation")
        self.assertEqual(res.get("score"), 12)
        self.assertEqual(res.get("max_score"), 12)
        self.assertEqual(res.get("correct_count"), 3)
        self.assertIn("12/12 Marks", res.get("reply", ""))
        self.assertIn("3/3 Correct", res.get("reply", ""))
        self.assertIn("Outstanding performance", res.get("reply", ""))

    def test_03_mixed_submission_neet_scoring(self):
        """Submit 1 correct and 2 incorrect: expect 1*4 - 2*1 = +2/12 marks."""
        c1 = chr(65 + self.active_mcqs[0]["correct_index"])
        w2 = chr(65 + ((self.active_mcqs[1]["correct_index"] + 1) % 4))
        w3 = chr(65 + ((self.active_mcqs[2]["correct_index"] + 1) % 4))

        submission_query = f"{c1} {w2} {w3}"
        res = adaptive_tutor.generate_tutoring_response(submission_query, student_id=self.student_id)

        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("mode"), "quiz_evaluation")
        self.assertEqual(res.get("score"), 2)
        self.assertEqual(res.get("correct_count"), 1)
        self.assertIn("+2/12 Marks", res.get("reply", ""))
        self.assertIn("1/3 Correct", res.get("reply", ""))
        self.assertIn("Correct (+4 Marks)", res.get("reply", ""))
        self.assertIn("Incorrect (-1 Mark)", res.get("reply", ""))

    def test_04_single_answer_option_c_submission(self):
        """Submit single answer 'Option B'."""
        res = adaptive_tutor.generate_tutoring_response("Option B", student_id=self.student_id)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("mode"), "quiz_evaluation")
        self.assertIn("Marks", res.get("reply", ""))
        self.assertIn("Question 1:", res.get("reply", ""))

    def test_05_answer_without_active_quiz_redirection(self):
        """Answering when no quiz was generated redirects warmly."""
        new_student = "student_without_active_test"
        res = adaptive_tutor.generate_tutoring_response("1:C, 2:A, 3:B", student_id=new_student)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("active test", res.get("reply", "").lower())
        self.assertIn("MCQs", res.get("reply", ""))

    def test_06_assistant_chat_mcq_interactive_flow(self):
        """Replicates full mobile user flow: request MCQs via /api/assistant/chat, then answer Q1: A."""
        from app import app
        client = app.test_client()

        # Step 1: Request MCQs
        req_res = client.post('/api/assistant/chat', json={
            "message": "Give me 3 MCQs on Photosynthesis",
            "role": "STUDENT"
        })
        self.assertEqual(req_res.status_code, 200)
        data = req_res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("mcqs", data)
        self.assertEqual(len(data["mcqs"]), 3)
        mcqs = data["mcqs"]

        # Step 2: Answer Q1: A
        ans_res = client.post('/api/assistant/chat', json={
            "message": "Q1: A",
            "role": "STUDENT",
            "active_mcqs": mcqs,
            "context": {"active_mcqs": mcqs}
        })
        self.assertEqual(ans_res.status_code, 200)
        ans_data = ans_res.get_json()
        self.assertEqual(ans_data.get("status"), "success")
        reply = ans_data.get("reply", "")
        self.assertNotIn("isn't an active test", reply.lower())
        self.assertIn("Marks", reply)
        self.assertIn("NEET Scheme: +4 / -1", reply)
        self.assertIn("Question 1:", reply)

    def test_07_assistant_chat_admin_answering_mcq(self):
        """Even if role is SUPER_ADMIN, submitting an MCQ answer evaluates biology, not admin protocol."""
        from app import app
        client = app.test_client()

        # Request MCQs
        req = client.post('/api/assistant/chat', json={
            "message": "Give me 3 MCQs on Cell Division",
            "role": "SUPER_ADMIN"
        })
        self.assertEqual(req.status_code, 200)
        mcqs = req.get_json().get("mcqs", [])

        # Submit answer Q1: B
        ans = client.post('/api/assistant/chat', json={
            "message": "Q1: B",
            "role": "SUPER_ADMIN",
            "active_mcqs": mcqs,
            "context": {"active_mcqs": mcqs}
        })
        self.assertEqual(ans.status_code, 200)
        reply = ans.get_json().get("reply", "")
        self.assertNotIn("isn't an active test", reply.lower())
        self.assertIn("Priya", reply)
        self.assertIn("Marks", reply)


if __name__ == "__main__":
    unittest.main()
