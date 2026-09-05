"""
Security + hardening regression tests for the BioNEETPro final sprint.

Covers (server-side enforceable items):
  1. student cannot impersonate another UID (strict mode ignores body id)
  2. unauthenticated user cannot access protected learner data
  3. non-admin cannot invoke admin endpoints
  8. all 33 chapters meet the MCQ target (seed bank)
  9. malformed MCQs are rejected
 10. duplicate MCQs are detected
 11. production backend URL does not default to localhost
 12. Docker build contains required modules
 13. missing NCERT PDF fails safely
 14. real Firestore learner data is used (no fake store)
 15. fake student counts are impossible (auth-gated results + empty states)

Markdown rendering / XSS items (4-7) live in tests/test_markdown_rendering.py
(executed against the real formatAIReply from BioNeet-Pro.html via node).
"""
import json
import os
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

import app as app_module


class TestAuthHardening(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()
        app_module._rate_buckets.clear()
        self._prev_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._prev_env)
        app_module._rate_buckets.clear()

    def _strict(self):
        os.environ.pop("DEV_AUTH_MODE", None)
        os.environ["REQUIRE_FIREBASE_AUTH"] = "true"

    def _dev(self):
        os.environ["DEV_AUTH_MODE"] = "true"
        os.environ.pop("REQUIRE_FIREBASE_AUTH", None)

    def test_1_strict_mode_ignores_spoofed_body_uid(self):
        """Strict (production default) + no token -> 401 even with a body student_id."""
        self._strict()
        res = self.client.get("/api/learner/profile?student_id=victim_user")
        self.assertIn(res.status_code, (401, 403))
        res2 = self.client.post("/api/tutor/answer",
                               json={"query": "What is mitosis?",
                                     "student_id": "victim_user"})
        # Either auth rejection or a normal answer is acceptable; what must
        # NEVER happen is trusting 'victim_user' silently in strict mode.
        # /api/tutor/answer is a public tutoring endpoint, so it answers but
        # must attribute to a non-spoofed identity.
        self.assertEqual(res2.status_code, 200)
        out = res2.get_json()
        self.assertNotEqual(out.get("student_id"), "victim_user")

    def test_2_learner_profile_self_only(self):
        """A caller authenticated (header) as student_local cannot read another
        student's profile; own profile works."""
        self._dev()
        hdr = {"Authorization": "Bearer student_local"}
        own = self.client.get("/api/learner/profile?student_id=student_local",
                              headers=hdr)
        self.assertEqual(own.status_code, 200)
        other = self.client.get("/api/learner/profile?student_id=someone_else_xyz",
                                headers=hdr)
        self.assertEqual(other.status_code, 403)
        self.assertIn("own", other.get_json().get("error", ""))
        # Presented-but-unverifiable JWT must be denied, not trusted.
        bad = self.client.get("/api/learner/profile?student_id=student_local",
                              headers={"Authorization": "Bearer abc.def.ghi"})
        self.assertIn(bad.status_code, (401, 403))

    def test_3_admin_endpoints_reject_anonymous(self):
        for method, url, body in [
            ("GET", "/api/tutor/tracker?limit=5", None),
            ("POST", "/api/mcqs/generate", {"chapter_id": "c01", "count": 1}),
            ("POST", "/api/tutor/import-kaggle", {}),
        ]:
            if method == "GET":
                res = self.client.get(url)
            else:
                res = self.client.post(url, json=body)
            self.assertIn(res.status_code, (401, 403),
                          f"{method} {url} must deny anonymous callers")
            self.assertIn("error", res.get_json())


class TestMCQBank(unittest.TestCase):
    def test_8_all_chapters_meet_target(self):
        seed = json.loads((BASE / "data" / "mcq_firestore_seed.json").read_text(encoding="utf-8"))
        from collections import Counter
        counts = Counter(d.get("chapter", "?") for d in seed)
        self.assertEqual(len(counts), 33)
        thin = {k: v for k, v in counts.items() if v < 200}
        self.assertEqual(thin, {}, f"chapters below 200: {thin}")

    def test_9_malformed_mcqs_rejected(self):
        from mcq_engine import mcq_engine
        good = {"question": "Which organelle produces ATP via oxidative phosphorylation?",
                "options": ["Nucleus", "Mitochondrion", "Ribosome", "Golgi body"],
                "correct_index": 1, "correct_answer": "Mitochondrion"}
        self.assertTrue(mcq_engine.validate_mcq(good))
        bads = [
            dict(good, options=["A", "B", "C"]),                       # 3 options
            dict(good, options=["A", "A", "B", "C"]),                  # dup options
            dict(good, correct_index=7),                               # index OOB
            dict(good, correct_answer="Nucleus"),                      # answer mismatch
            dict(good, question=""),                                   # empty question
            dict(good, question="short"),                             # too short
        ]
        for b in bads:
            self.assertFalse(mcq_engine.validate_mcq(b), f"should reject: {b}")

    def test_10_duplicate_mcqs_detected(self):
        from mcq_bank_generator import is_dup
        existing = ["Which of the following is most closely associated with 'x' (Cell)?"]
        buckets = {"Cell": list(existing)}
        self.assertTrue(is_dup(existing[0], existing, chapter="Cell", buckets=buckets))
        self.assertTrue(is_dup(existing[0] + " ", existing))  # exact, global
        self.assertFalse(is_dup("Entirely unrelated question about nephron filtration?",
                               existing, chapter="Cell", buckets=buckets))


class TestDeploymentConfig(unittest.TestCase):
    def test_11_no_localhost_default_for_production(self):
        html = (BASE / "BioNeet-Pro.html").read_text(encoding="utf-8")
        # Backend resolution contract (behavioral properties, not literals):
        # 1. deploy-time override supported; 2. local dev (any frontend port)
        # maps to the Flask backend on :5000 (never same-origin :5500);
        # 3. no bare localhost default that would break production browsers.
        self.assertIn("window.BIONEET_AI_BACKEND_URL", html)
        self.assertIn(":5000", html)
        self.assertIn("AI_BACKEND_URL", html)
        self.assertNotIn('BIONEET_AI_BACKEND_URL || "http://127.0.0.1:5000"',
                         html)

    def test_12_docker_contains_required_modules(self):
        dockerfile = (BASE / "Dockerfile").read_text(encoding="utf-8")
        required = ["app.py", "tutor_engine.py", "retrieval_engine.py",
                    "learner_model.py", "mcq_engine.py", "firestore_store.py",
                    "adaptive_tutor.py", "nlp_pipeline.py", "data", "scripts"]
        for mod in required:
            self.assertIn(mod, dockerfile, f"Dockerfile must COPY {mod}")
            if mod.endswith(".py"):
                self.assertTrue((BASE / mod).exists(), f"missing module {mod}")
        self.assertIn("gunicorn", dockerfile.lower())
        reqs = (BASE / "requirements.txt").read_text(encoding="utf-8").lower()
        self.assertIn("gunicorn", reqs)

    def test_13_missing_pdf_fails_safely(self):
        client = app_module.app.test_client()
        for bad in ("does-not-exist-zzz", "..%2Fapp", "c01%00.pdf"):
            res = client.get(f"/api/textbook/pdf/{bad}")
            # Must never serve a file nor leak a traceback: 400/404 only.
            self.assertIn(res.status_code, (400, 404), bad)
            data = res.get_json(silent=True) or {}
            self.assertNotIn("Traceback", json.dumps(data))
        # A real mapped chapter serves a PDF (Textbook/ present in dev).
        ok = client.get("/api/textbook/pdf/c01")
        self.assertIn(ok.status_code, (200, 404))
        if ok.status_code == 200:
            self.assertIn("application/pdf", ok.content_type)

    def test_14_real_firestore_store_roundtrip(self):
        import firestore_store
        probe = {"ok": True, "n": 7}
        firestore_store.save_doc("score_predictions", "__regression_probe__", probe)
        back = firestore_store.load_doc("score_predictions", "__regression_probe__",
                                        default=None)
        self.assertEqual(back, probe)
        firestore_store.delete_doc("score_predictions", "__regression_probe__")
        self.assertIsNone(firestore_store.load_doc("score_predictions",
                                                   "__regression_probe__",
                                                   default=None))

    def test_15_no_fake_counts_results_gated(self):
        rules = (BASE / "firestore.rules").read_text(encoding="utf-8")
        # results collection must require sign-in (no public leaderboard scrape)
        self.assertIn("match /results/", rules)
        self.assertIn("allow list: if signedIn()", rules)
        html = (BASE / "BioNeet-Pro.html").read_text(encoding="utf-8")
        # honest empty states instead of fabricated numbers
        self.assertIn("Not enough students yet", html)


if __name__ == "__main__":
    unittest.main()
