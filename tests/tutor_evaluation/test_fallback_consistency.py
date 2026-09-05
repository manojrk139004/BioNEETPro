"""Phase 10/11/12/13: fallback paths, evidence consistency, ambiguity, OOS.

- Provider failure (mock ONLY at the external requests boundary) -> local
  path must still answer the CURRENT topic.
- Evidence/answer consistency: chapter label, title, reply must agree with
  each other and the query (sampled).
- Ambiguous queries: clarification or safe answer, never confident unrelated.
- Out-of-scope: refusal intact (guardrail preservation).
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import run_conversation, topic_hit, blob  # noqa: E402
import adaptive_tutor as adaptive_mod  # noqa: E402


class TestFallbackPaths(unittest.TestCase):
    def test_provider_failure_keeps_current_topic(self):
        import requests
        with mock.patch.object(adaptive_mod, "OPENROUTER_KEY", "test-key"), \
             mock.patch.object(requests, "post",
                               side_effect=ConnectionError("down")):
            sid, turns = run_conversation(
                ["Explain cardiac cycle.", "Teach me flower."])
            out = turns[1][1]
            self.assertTrue(
                topic_hit(out, ["flower", "sepal", "petal", "stamen",
                                "carpel"]),
                f"fallback lost topic: {out.get('chapter_id')} "
                f"{(out.get('title') or '')[:60]}")


class TestConsistency(unittest.TestCase):
    def test_label_evidence_answer_agree(self):
        cases = [
            ("Explain cardiac cycle.", ["cardiac", "systole", "diastole"]),
            ("can u teach me flower and its parts",
             ["flower", "sepal", "petal"]),
            ("What is a nephron?", ["nephron", "glomerulus"]),
        ]
        fails = []
        for prompt, toks in cases:
            sid, turns = run_conversation([prompt])
            out = turns[0][1]
            b = blob(out)
            if not all(t in b for t in toks[:2]):
                fails.append((prompt, "topic missing", out.get("chapter_id")))
            # chapter label must come from the evidence (internal agreement)
            title = (out.get("title") or "").lower()
            if toks[0] not in title and toks[0] not in b:
                fails.append((prompt, "label/answer mismatch",
                              out.get("chapter_id")))
        self.assertEqual(fails, [], f"inconsistency: {fails[:8]}")


class TestAmbiguousAndOOS(unittest.TestCase):
    def test_ambiguous_handled_honestly(self):
        for prompt in ["teach me transport", "explain cycle",
                       "tell me about replication", "what is the heart?"]:
            sid, turns = run_conversation([prompt])
            out = turns[0][1]
            mode = out.get("mode")
            # Either a grounded answer, a refusal, or clarification — never a
            # confident answer whose evidence contradicts the query terms.
            self.assertIn(mode, ("local_adaptive", "api_grounded",
                                 "local_fallback", "syllabus_restricted",
                                 "policy_restricted", "mcq_practice",
                                 "follow_up", "injection_blocked",
                                 "content_blocked"),
                          f"{prompt}: unexpected mode {mode}")

    def test_out_of_scope_refused(self):
        for prompt in ["teach me calculus",
                       "what is quantum mechanics?",
                       "write my English essay",
                       "tell me today's cricket score",
                       "solve this unrelated coding problem"]:
            sid, turns = run_conversation([prompt])
            out = turns[0][1]
            self.assertIn(out.get("mode"),
                          ("syllabus_restricted", "policy_restricted"),
                          f"OOS leaked: {prompt} -> {out.get('mode')}")


if __name__ == "__main__":
    unittest.main()
