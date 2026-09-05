"""Firestore-sync regression: every per-student backend store persists and
reloads (Firestore-first, file fallback), lesson state survives a restart,
chat threads round-trip via API.
unittest style (no pytest).
"""
import unittest

import os as _os
_os.environ.setdefault("DEV_AUTH_MODE", "true")  # functional suite runs in documented dev auth mode
import firestore_store


class TestStoreFallback(unittest.TestCase):
    def test_status_honest(self):
        import os
        from pathlib import Path
        st = firestore_store.status()
        self.assertIn("firestore_enabled", st)
        # Honest either way: enabled iff Admin SDK + key are actually present.
        key_here = Path("serviceAccount.json").exists() or bool(
            os.environ.get("FIREBASE_SERVICE_ACCOUNT") or
            os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON"))
        try:
            import firebase_admin  # noqa
            sdk = True
        except ImportError:
            sdk = False
        self.assertEqual(st["firestore_enabled"], sdk and key_here)
        if not st["firestore_enabled"]:
            self.assertTrue(st["reason"])

    def test_roundtrip(self):
        firestore_store.save_doc("flashcards", "sync_probe", {"cards": {"a": 1}})
        back = firestore_store.load_doc("flashcards", "sync_probe")
        self.assertEqual(back["cards"], {"a": 1})
        firestore_store.delete_doc("flashcards", "sync_probe")
        self.assertIsNone(firestore_store.load_doc("flashcards", "sync_probe"))


class TestLearnerProfileSync(unittest.TestCase):
    def test_profile_roundtrip(self):
        from learner_model import learner_manager
        p = learner_manager.get_or_create_profile("sync_probe_learner")
        p["overall_mastery"] = 0.77
        learner_manager.save_profile("sync_probe_learner", p)
        p2 = learner_manager.get_or_create_profile("sync_probe_learner")
        self.assertEqual(p2["overall_mastery"], 0.77)


class TestDialogueSync(unittest.TestCase):
    def test_record_and_load(self):
        import dialogue_state as ds
        ds.record_turn("sync_probe_dialogue", "BIO-C08-01", "Cell", "socratic", 0.6)
        st = ds.load("sync_probe_dialogue")
        self.assertGreaterEqual(st["turns"], 1)
        self.assertEqual(st["focal"]["concept_id"], "BIO-C08-01")


class TestLessonStateSurvivesRestart(unittest.TestCase):
    def test_state_file_written_and_reloaded(self):
        from adaptive_tutor import AdaptiveBiologyTutor
        t1 = AdaptiveBiologyTutor()
        st = t1._get_tutor_state("sync_probe_lesson")
        st["active_lesson"] = "Cell"
        st["current_step_index"] = 2
        t1._save_tutor_state("sync_probe_lesson")
        t2 = AdaptiveBiologyTutor()
        st2 = t2._get_tutor_state("sync_probe_lesson")
        self.assertEqual(st2["active_lesson"], "Cell")
        self.assertEqual(st2["current_step_index"], 2)


class TestFlashcardSync(unittest.TestCase):
    def test_create_review_persists(self):
        from flashcard_backend import (create_flashcard, review_flashcard,
                                       get_due_flashcards)
        card = create_flashcard("sync_probe_fc", "Q?", "A.", "", "c08", [])
        res = review_flashcard("sync_probe_fc", card["card_id"], True)
        self.assertIn("new_box", res)
        # Fresh load still sees it (persisted, not just in-memory).
        from flashcard_backend import _load_flashcards
        self.assertIn(card["card_id"], _load_flashcards("sync_probe_fc")["cards"])


class TestChatThreadApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app as appmod
        cls.client = appmod.app.test_client()

    def test_thread_roundtrip(self):
        c = self.client
        r = c.post("/chat", json={"message": "What is mitochondria?",
                                  "student_id": "sync_probe_chat"})
        self.assertEqual(r.status_code, 200)
        t = c.get("/api/chat/thread?student_id=sync_probe_chat").get_json()
        self.assertGreaterEqual(len(t["turns"]), 1)
        self.assertIn("mitochondria", t["turns"][-1]["user"].lower())
        c.delete("/api/chat/thread?student_id=sync_probe_chat")
        t2 = c.get("/api/chat/thread?student_id=sync_probe_chat").get_json()
        self.assertEqual(t2["turns"], [])

    def test_score_history_roundtrip(self):
        c = self.client
        r = c.get("/api/score/predict?student_id=sync_probe_chat")
        self.assertEqual(r.status_code, 200)
        h = c.get("/api/score/history?student_id=sync_probe_chat").get_json()
        self.assertIn("predictions", h)


if __name__ == "__main__":
    unittest.main()
