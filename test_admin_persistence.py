"""Phase 7 regression: admin CRUD reliability guard (static + endpoint checks).

Acceptance (Part K 1-3): student-delete, MCQ-edit, MCQ-delete, update-post must
all hit Firestore (source of truth) with localStorage only as cache, and a
fresh reload path (reloadFromFirestore) must exist. Dead-UI guards: bell wired,
no mock-student padding, coach fallback filter, chart clamp.

unittest style (no pytest).
"""
import os as _os
_os.environ.setdefault("DEV_AUTH_MODE", "true")  # functional suite runs in documented dev auth mode
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = (ROOT / "BioNeet-Pro.html").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")


class TestAdminFirestoreWiring(unittest.TestCase):
    def test_student_delete_hits_firestore(self):
        self.assertIn('deleteDoc(doc(db, "users"', HTML)
        self.assertIn("renderStudentTable", HTML)

    def test_mcq_edit_hits_firestore(self):
        self.assertIn('setDoc(mcqRef', HTML)
        self.assertIn('addDoc(collection(db, "mcqs")', HTML)

    def test_mcq_delete_hits_firestore(self):
        self.assertIn('deleteDoc(doc(db, "mcqs"', HTML)

    def test_update_post_and_delete_hit_firestore(self):
        self.assertIn('setDoc(doc(db, "updates"', HTML)
        self.assertIn('deleteDoc(doc(db, "updates"', HTML)

    def test_fresh_reload_path_exists(self):
        self.assertIn("reloadFromFirestore", HTML)
        self.assertIn("getDocs", HTML)

    def test_sync_degrades_per_collection(self):
        # Live bug: one denied read (users list) aborted the whole syncData.
        # Users/admin-check sections must be individually isolated now.
        self.assertIn("Users list not permitted for this account", HTML)
        self.assertIn("Admin check not permitted for this account", HTML)

    def test_save_is_cache_plus_sync(self):
        self.assertIn("queueFirestoreSync", HTML)
        self.assertIn("localStorage is only an optimistic cache", HTML)


class TestDeadUiGuards(unittest.TestCase):
    def test_no_mock_student_padding(self):
        self.assertNotIn("baseMockNames", HTML)
        self.assertNotIn("150 - cohort.length", HTML)

    def test_admin_buttons_quote_ids(self):
        # String Firestore doc ids rendered unquoted into onclick() throw
        # ReferenceError and silently kill Edit/Del (live bug, 2026-09-04).
        self.assertIn("editMCQ(\\'' + m.id", HTML)
        self.assertIn("deleteMCQ(\\'' + m.id", HTML)
        self.assertIn("deleteVideo(\\'' + v.id", HTML)
        self.assertIn("deleteUpdate(\\'' + u.id", HTML)
        self.assertIn('doc(db, "mcqs", String(editMCQId))', HTML)
        self.assertIn('deleteDoc(doc(db, "mcqs", String(id)))', HTML)

    def test_videos_firestore_crud(self):
        self.assertIn('setDoc(doc(db, "videos", String(vid.id)), vid)', HTML)
        self.assertIn('deleteDoc(doc(db, "videos", String(id)))', HTML)

    def test_bank_sync_wiring(self):
        self.assertIn("syncFullBank", HTML)
        self.assertIn("/api/mcqs/seed", HTML)
        self.assertIn("generateMoreMCQs", HTML)
        self.assertIn("/api/mcqs/generate", HTML)

    def test_all_onclick_handlers_exported(self):
        # Live bug: module-scope functions are invisible to inline onclick
        # unless assigned to window (syncFullBank was not defined).
        import re as _re
        handlers = set(_re.findall(r'onclick="([A-Za-z_]+)\(', HTML))
        exported = set(_re.findall(r'window\.([A-Za-z_]+)\s*=', HTML))
        funcs = set(_re.findall(r'function ([A-Za-z_]+)\(', HTML))
        missing = sorted(h for h in handlers if h in funcs and h not in exported)
        self.assertEqual(missing, [], f"unexposed handlers: {missing}")

    def test_flashcards_empty_guard(self):
        self.assertIn("paintFlashcards", HTML)
        # Live bug 2026-09-04: block-scoped `l` was referenced outside its
        # try block (ReferenceError) killing every flashcards render.
        self.assertIn("_renderFlashcardsInner", HTML)
        self.assertIn("Could not load flashcards", HTML)

    def test_pooled_accuracy_math(self):
        # Mean-of-ratios lied (1/2 + 4/38 showed 30% instead of pooled 13%).
        self.assertIn("POOLED correct/total", HTML)
        self.assertNotIn("r.correct / r.total * 100), 0) / cr.length", HTML)
        self.assertNotIn("a + (r.correct/r.total*100),0)/myR.length", HTML)

    def test_exam_integrity_mode(self):
        self.assertIn("enterExamMode", HTML)
        self.assertIn("examViolationAutoSubmit", HTML)
        self.assertIn("visibilitychange", HTML)
        self.assertIn("exam-mode", HTML)
        self.assertIn("integrity: ts.integrity", HTML)
        # Killer bug 2026-09-05: module-scope vars are NOT window props, so
        # `window.testState` was always undefined and testIsLive() never true.
        self.assertNotIn("window.testState", HTML)

    def test_review_mark_visible(self):
        self.assertIn("qMarkBadge", HTML)
        self.assertIn("reviewToggleBtn", HTML)

    def test_coach_interactive(self):
        self.assertIn("coachPracticeWeakest", HTML)
        self.assertIn("refreshCoachTip", HTML)
        self.assertIn("weakestChapterStats", HTML)
        self.assertIn("/api/coach/tip", HTML)

    def test_student_sort_and_detail(self):
        self.assertIn('id="sSort"', HTML)
        self.assertIn("openStudentDetail", HTML)
        self.assertIn("exportStudentsCSV", HTML)
        self.assertIn('id="sRecentReg"', HTML)
        self.assertIn('id="aRecentLogins"', HTML)
        self.assertIn("lastLoginAt", HTML)

    def test_honest_rank_empty_state(self):
        self.assertIn("Not enough students yet for a ranking", HTML)

    def test_bell_wired(self):
        self.assertIn("toggleNotifPanel", HTML)
        self.assertNotIn("toast('3 new NEET updates!'", HTML)

    def test_coach_guard(self):
        self.assertIn("FALLBACK_PATTERNS", HTML)
        self.assertIn("/api/coach/tip", HTML)

    def test_chart_clamp(self):
        self.assertIn("Math.min(100", HTML)
        self.assertIn("max-height:104px", HTML)


class TestBackendRoutes(unittest.TestCase):
    def test_routes_present(self):
        for route in ["/api/coach/tip", "/api/textbook/chapters",
                      "/api/textbook/pdf/", "/api/mcqs/generate",
                      "/api/mcqs/seed", "/api/mcq/submit-batch",
                      "/api/score/predict", "/api/flashcards",
                      "/api/chat/thread"]:
            self.assertIn(route, APP, route)

    def test_seed_endpoint_live(self):
        import app as appmod
        client = appmod.app.test_client()
        r = client.get("/api/mcqs/seed?offset=0&limit=5")
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertGreater(j["total"], 1000)
        self.assertEqual(len(j["mcqs"]), 5)
        for m in j["mcqs"]:
            self.assertIn("q", m)
            self.assertEqual(len(m["opts"]), 4)
            self.assertIn(m["correct"], [0, 1, 2, 3])

    def test_pdf_intent(self):
        self.assertIn("request_chapter_pdf", (ROOT / "nlp_pipeline.py").read_text(
            encoding="utf-8"))


class TestFrontendWiring(unittest.TestCase):
    def test_score_predictor_wired(self):
        self.assertIn("/api/score/predict", HTML)
        self.assertIn("scorePredBox", HTML)

    def test_markdown_citations(self):
        self.assertIn("cite-chip", HTML)
        self.assertIn("md-list", HTML)

    def test_flashcards_server_backed(self):
        self.assertIn("/api/flashcards/review", HTML)
        self.assertIn("fc-flip", HTML)

    def test_lessons_pdf_buttons(self):
        self.assertIn("/api/textbook/chapters", HTML)
        self.assertIn("Download NCERT PDF", HTML)


if __name__ == "__main__":
    unittest.main()
