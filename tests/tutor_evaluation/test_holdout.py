"""Phase 29 runner: holdout AFTER implementation. 30 unseen switches.

Pass bar: >= 28/30 second-topic resolutions (>= 93%; target band with the
visible corpus >= 95% topic target).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from holdout import HOLDOUT  # noqa: E402
from harness import run_conversation, topic_hit  # noqa: E402


class TestHoldout(unittest.TestCase):
    def test_unseen_switches(self):
        fails = []
        for prior, current, toks in HOLDOUT:
            sid, turns = run_conversation([prior, current])
            out = turns[1][1]
            if out.get("mode") in ("syllabus_restricted",
                                   "policy_restricted"):
                fails.append((current, "wrongly restricted", "", ""))
                continue
            if not topic_hit(out, toks):
                fails.append((current, out.get("chapter_id"),
                              (out.get("title") or "")[:60]))
        rate = 1 - len(fails) / len(HOLDOUT)
        open(Path(__file__).resolve().parent / "holdout_result.txt", "w",
             encoding="utf-8").write(
            f"holdout: {len(HOLDOUT) - len(fails)}/{len(HOLDOUT)} "
            f"({rate:.1%})\n" + "\n".join(str(f) for f in fails))
        self.assertGreaterEqual(rate, 28 / 30, f"holdout {rate}: {fails[:8]}")


if __name__ == "__main__":
    unittest.main()
