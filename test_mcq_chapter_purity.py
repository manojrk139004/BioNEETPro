"""Phase 4 regression: chapter-wise purity + Phase 2 bank sanity + Phase 5 endpoints.

- generate_chapter_mcqs returns ONLY the requested chapter (5 chapters).
- generate_mcqs reports honest padded flag (no silent off-chapter padding).
- /api/coach/tip never returns fallback/error text.
- /api/textbook/pdf serves real PDFs; unknown chapter -> honest 404.
unittest style (no pytest).
"""
import unittest

import os as _os
_os.environ.setdefault("DEV_AUTH_MODE", "true")  # functional suite runs in documented dev auth mode
from mcq_engine import LocalMCQEngine
import app as appmod


CHAPTERS_5 = [
    "Cell: The Unit of Life",
    "Human Reproduction",
    "Photosynthesis in Higher Plants",
    "Biotechnology and Its Applications",
    "Cell Cycle and Cell Division",
]


class TestChapterPurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng = LocalMCQEngine()

    def test_five_chapters_pure(self):
        for ch in CHAPTERS_5:
            with self.subTest(chapter=ch):
                r = self.eng.generate_chapter_mcqs(ch, 10)
                self.assertGreater(r["count"], 0, ch)
                for m in r["mcqs"]:
                    self.assertEqual(m["chapter"], ch)

    def test_no_silent_padding_flag(self):
        r = self.eng.generate_mcqs("Give me 5 MCQs on xyzzy_nonexistent_topic_qqq",
                                   student_id="purity_probe")
        # Unknown topic -> honest mixed pool with the flag present and a
        # Mixed/Diagnostic label (never mislabelled as the requested chapter).
        self.assertIn("padded", r)
        self.assertIn(r["topic"].lower(), ("mixed ncert biology",
                                           "diagnostic mixed syllabus (no weak topics yet)"))
        # Strict chapter fetch for unknown chapter: zero, with shortfall.
        r2 = self.eng.generate_chapter_mcqs("Xyzzy No Such Chapter", 5)
        self.assertEqual(r2["count"], 0)
        self.assertEqual(r2["shortfall"], 5)


class TestBankSanity(unittest.TestCase):
    def test_all_validated(self):
        eng = LocalMCQEngine()
        bad = [m for m in eng.mcq_pool if not eng.validate_mcq(m)]
        self.assertEqual(bad, [])
        self.assertGreaterEqual(len(eng.mcq_pool), 500)


class TestCoachPdfEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = appmod.app.test_client()

    def test_coach_tip_clean(self):
        r = self.client.get("/api/coach/tip?student_id=purity_probe")
        self.assertEqual(r.status_code, 200)
        tip = r.get_json().get("tip", "")
        for bad in ["couldn't find enough verified", "insufficient evidence",
                    "Server not running"]:
            self.assertNotIn(bad, tip)

    def test_pdf_serves_and_404s(self):
        r = self.client.get("/api/textbook/pdf/c08")
        self.assertEqual(r.status_code, 200)
        self.assertIn("pdf", r.content_type)
        r2 = self.client.get("/api/textbook/pdf/c16")
        self.assertEqual(r2.status_code, 404)

    def test_pdf_intent(self):
        r = self.client.post("/api/tutor/answer",
                             json={"query": "give me the PDF for Human Reproduction",
                                   "student_id": "purity_probe"})
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertEqual(j.get("mode"), "pdf_request")
        self.assertEqual(j.get("chapter_id"), "c24")


if __name__ == "__main__":
    unittest.main()
