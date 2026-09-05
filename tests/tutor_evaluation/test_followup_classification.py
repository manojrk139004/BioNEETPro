"""Phase 7: follow-up vs topic-switch classification.

Genuine follow-ups (no explicit topic) must KEEP the prior topic;
explicit switches must CHANGE it. Prior topic tokens are asserted in
follow-up replies; switch replies must contain the NEW topic tokens.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import FOLLOWUPS, CORPUS  # noqa: E402
from harness import run_conversation, topic_hit  # noqa: E402


def corpus_tokens(prompt):
    for e in CORPUS:
        if e["prompt"].lower() == prompt.lower().rstrip("."):
            return e["tokens"]
    for e in CORPUS:
        if e["prompt"].lower() in prompt.lower() or prompt.lower() in e["prompt"].lower():
            return e["tokens"]
    return None


class TestFollowUpClassification(unittest.TestCase):
    def test_genuine_followups_keep_topic(self):
        fails = []
        for prior, follow in FOLLOWUPS:
            toks = corpus_tokens(prior)
            sid, turns = run_conversation([prior, follow])
            out = turns[1][1]
            if toks and not topic_hit(out, toks):
                fails.append((prior, follow, out.get("chapter_id"),
                              (out.get("title") or "")[:60]))
        self.assertEqual(fails, [], f"follow-up context lost: {fails[:8]}")

    def test_explicit_switches_change_topic(self):
        cases = [
            ("Explain photosynthesis.", "Now teach me nephron.",
             ["nephron", "glomerulus", "filtrate"]),
            ("Explain cardiac cycle.", "switch to genetics",
             ["mendel", "dominance", "gene", "allele", "dna"]),
            ("Teach me flower structure.", "tell me about DNA",
             ["dna", "nucleotide", "double helix"]),
            ("What is an ecosystem?", "Now explain kidney",
             ["kidney", "nephron", "excretory"]),
        ]
        fails = []
        for prior, current, toks in cases:
            sid, turns = run_conversation([prior, current])
            out = turns[1][1]
            if not topic_hit(out, toks):
                fails.append((prior, current, out.get("chapter_id"),
                              (out.get("title") or "")[:60]))
        self.assertEqual(fails, [], f"switch failed: {fails[:8]}")


if __name__ == "__main__":
    unittest.main()
