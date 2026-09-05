"""Regression: fuzzy typo-correction must never turn pedagogy framing into
biology terms (2026-09-04 root cause: "teach" -> "teeth" hijacked every
"teach me ..." query into Digestion and Absorption).
unittest style (no pytest).
"""
import unittest

from concept_normalizer import concept_normalizer as cn
from retrieval_engine import retrieval_engine


class TestFuzzyGuard(unittest.TestCase):
    def test_teach_not_teeth(self):
        self.assertEqual(cn.correct_typos("teach me about cell"),
                         "teach me about cell")

    def test_no_digestion_hijack(self):
        for q in ["teach me about cell", "teach me abt cell",
                  "teach me about brain"]:
            with self.subTest(query=q):
                names = [v.get("canonical_name")
                         for v in cn.normalize(q).values()]
                self.assertNotIn("Digestion and Absorption", names)

    def test_rewrite_clean(self):
        for q in ["teach me about cell", "teach me about brain"]:
            with self.subTest(query=q):
                self.assertNotIn("Digestion",
                                 retrieval_engine.rewrite_query(q))

    def test_real_typos_still_fixed(self):
        self.assertIn("mitochondria", cn.correct_typos("explain mitocondria"))
        self.assertIn("xylem", cn.correct_typos("xyelm"))

    def test_broad_queries_retrieve_right_chapter(self):
        top = retrieval_engine.search("teach me about cell")[0]
        self.assertIn("cell", top.get("title", "").lower())
        top2 = retrieval_engine.search("teach me about brain")[0]
        hay = (top2.get("title", "") + " " +
               top2.get("chapter_name", "")).lower()
        self.assertTrue("brain" in hay or "neural" in hay,
                        f"brain query misrouted: {hay[:100]}")


if __name__ == "__main__":
    unittest.main()
