"""
Test suite for Flask app endpoints including local algorithmic tutor routes.
"""

import json
import os as _os
_os.environ.setdefault("DEV_AUTH_MODE", "true")  # functional suite runs in documented dev auth mode
import unittest
from app import app


class TestAppEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["local_algorithm_active"])
        self.assertEqual(data["dataset_file"], "neet_knowledge_base.csv")
        self.assertGreater(data["dataset_records"], 0)

    def test_dataset_info_endpoint(self):
        res = self.client.get("/api/tutor/dataset-info")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["filename"], "neet_knowledge_base.csv")
        self.assertIn("columns", data)
        self.assertGreater(data["total_records"], 10)

    def test_tutor_query_step_verify_flow(self):
        # 1. Query Step 1
        res = self.client.post(
            "/api/tutor/query",
            json={"query": "Explain Calvin cycle steps in photosynthesis"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("session_id", data)
        self.assertEqual(data["step_number"], 1)
        self.assertIn("Calvin Cycle", data["title"])
        session_id = data["session_id"]

        # 2. Step 2 (Mechanism)
        res_step2 = self.client.post(
            "/api/tutor/step",
            json={"session_id": session_id, "step_number": 2}
        )
        self.assertEqual(res_step2.status_code, 200)
        s2_data = res_step2.get_json()
        self.assertEqual(s2_data["step_number"], 2)
        self.assertIn("Mechanism", s2_data["content"])

        # 3. Step 3 (Traps)
        res_step3 = self.client.post(
            "/api/tutor/step",
            json={"session_id": session_id, "step_number": 3}
        )
        self.assertEqual(res_step3.status_code, 200)
        s3_data = res_step3.get_json()
        self.assertEqual(s3_data["step_number"], 3)
        self.assertIn("NEET Traps", s3_data["content"])

        # 4. Step 4 (Quiz)
        res_step4 = self.client.post(
            "/api/tutor/step",
            json={"session_id": session_id, "step_number": 4}
        )
        self.assertEqual(res_step4.status_code, 200)
        s4_data = res_step4.get_json()
        self.assertEqual(s4_data["step_number"], 4)
        self.assertIsNotNone(s4_data["quiz"])
        correct_idx = s4_data["quiz"]["correct_index"]

        # 5. Verify Quiz + BKT Update
        res_verify = self.client.post(
            "/api/tutor/verify",
            json={"session_id": session_id, "selected_index": correct_idx}
        )
        self.assertEqual(res_verify.status_code, 200)
        v_data = res_verify.get_json()
        self.assertTrue(v_data["is_correct"])
        self.assertGreater(v_data["updated_mastery"], 0)

    def test_tracker_endpoint(self):
        # /api/tutor/tracker is ADMIN ONLY (hardened): anonymous callers must
        # be denied. (Previous version asserted public 200 access — obsolete
        # after the auth-hardening sprint; replaced with this equivalent
        # protection test. Admin happy-path is covered in
        # tests/test_security_regression.py via role logic.)
        res = self.client.get("/api/tutor/tracker?limit=10")
        self.assertIn(res.status_code, (401, 403))
        data = res.get_json()
        self.assertIn("error", data)

    def test_legacy_ask_fallback_to_local_algorithm(self):
        res = self.client.post("/ask", json={"question": "What is semi-conservative DNA replication?", "prefer_local": True})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("answer", data)
        # One-brain RAG: grounded API answer preferred; local template is the offline fallback.
        # Either way the answer must be Dr. Priya's with NCERT grounding.
        self.assertIn("Dr. Priya", data["answer"])
        self.assertTrue(
            "Local Algorithmic Tutor" in data["answer"] or "NCERT Grounded" in data["answer"],
            "Answer must come from the grounded pipeline (API) or the local fallback",
        )


if __name__ == "__main__":
    unittest.main()
