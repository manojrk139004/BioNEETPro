"""Mastery-sync regression: finishing a test must move the learner model
(stuck-at-403 bug — endTest never recorded attempts, so the predictor sat at
the 0.50-mastery default forever).
unittest style (no pytest).
"""
import unittest

import os as _os
_os.environ.setdefault("DEV_AUTH_MODE", "true")  # functional suite runs in documented dev auth mode


class TestSubmitBatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app as appmod
        cls.client = appmod.app.test_client()

    def test_batch_moves_mastery_and_prediction(self):
        c = self.client
        sid = "mastery_sync_probe"
        before = c.get(f"/api/score/predict?student_id={sid}").get_json()
        self.assertEqual(before["predicted_total_score"], 403)
        r = c.post("/api/mcq/submit-batch", json={
            "student_id": sid,
            "attempts": [
                {"concept_id": "X", "chapter_id": "c08", "is_correct": True},
                {"concept_id": "X", "chapter_id": "c08", "is_correct": False},
            ]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["recorded"], 2)
        prof = c.get(f"/api/learner/profile?student_id={sid}").get_json()
        self.assertNotEqual(prof["overall_mastery"], 0.50)
        after = c.get(f"/api/score/predict?student_id={sid}").get_json()
        self.assertNotEqual(after["predicted_total_score"], 403)

    @classmethod
    def tearDownClass(cls):
        import firestore_store as fs
        for col in ("learner_profiles", "flashcards", "dialogue_states",
                    "score_predictions", "tutor_states", "chat_threads"):
            fs.delete_doc(col, "mastery_sync_probe")


if __name__ == "__main__":
    unittest.main()
