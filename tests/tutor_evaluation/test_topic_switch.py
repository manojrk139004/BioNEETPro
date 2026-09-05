"""Phase 4/6/28: single-turn topic accuracy + topic-switch torture.

- test_single_turn_corpus: all 110 prompts, fresh conversation each.
- test_scripted_switches: SWITCH_PAIRS — second topic must win.
- test_randomized_switch_sequences: seeded random 6-turn chains across groups.
"""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import CORPUS, SWITCH_PAIRS  # noqa: E402
from harness import run_conversation, topic_hit, chapter_hit  # noqa: E402


class TestSingleTurnCorpus(unittest.TestCase):
    def test_all_corpus_prompts_resolve(self):
        fails = []
        for i, entry in enumerate(CORPUS):
            sid, turns = run_conversation([entry["prompt"]])
            out = turns[0][1]
            if entry.get("expect_refusal"):
                # Documented coverage gap: must refuse/clarify honestly,
                # never answer an unrelated topic confidently.
                if out.get("mode") in ("local_fallback", "syllabus_restricted",
                                       "policy_restricted"):
                    continue
                fails.append((entry["prompt"], "expected honest refusal",
                              out.get("chapter_id"),
                              (out.get("title") or "")[:60]))
                continue
            if out.get("mode") in ("syllabus_restricted", "policy_restricted"):
                fails.append((entry["prompt"], "wrongly restricted"))
                continue
            if not topic_hit(out, entry["tokens"]):
                fails.append((entry["prompt"],
                              f"no topic token in chapter={out.get('chapter_id')} "
                              f"title={(out.get('title') or '')[:60]}"))
                continue
            ch = chapter_hit(out, entry.get("chapter"))
            if ch is False:
                fails.append((entry["prompt"],
                              f"chapter hint {entry.get('chapter')!r} missing "
                              f"(got {out.get('chapter_id')})"))
        self.assertEqual(fails, [], f"{len(fails)} corpus failures: {fails[:8]}")


class TestTopicSwitch(unittest.TestCase):
    def test_scripted_switch_pairs(self):
        fails = []
        for prior, current in SWITCH_PAIRS:
            cur_entry = next(
                (e for e in CORPUS if e["prompt"].lower() in current.lower()
                 or current.lower() in e["prompt"].lower()), None)
            sid, turns = run_conversation([prior, current])
            out = turns[1][1]
            prior_tok = prior.lower().split()
            if cur_entry:
                if not topic_hit(out, cur_entry["tokens"]):
                    fails.append((prior, current, out.get("chapter_id"),
                                  (out.get("title") or "")[:60]))
            else:
                # fall back: current query's own content words must appear
                content = [w for w in current.lower().split()
                           if len(w) > 4 and w not in ("teach", "explain", "about")]
                if not any(w.strip("?.") in str(out.get("reply") or "").lower()
                           for w in content):
                    fails.append((prior, current, "no-content-match", ""))
        self.assertEqual(fails, [], f"switch failures: {fails[:8]}")

    def test_randomized_switch_sequences(self):
        rng = random.Random(20260905)
        topics = [e for e in CORPUS]
        fails = []
        for chain in range(12):
            seq = rng.sample(topics, 5)
            sid, turns = run_conversation([e["prompt"] for e in seq])
            for entry, (prompt, out) in zip(seq, turns):
                if not topic_hit(out, entry["tokens"]):
                    fails.append((prompt, out.get("chapter_id"),
                                  (out.get("title") or "")[:60]))
        rate = 1 - len(fails) / 60
        self.assertGreaterEqual(rate, 0.95, f"switch accuracy {rate}: {fails[:8]}")


if __name__ == "__main__":
    unittest.main()
