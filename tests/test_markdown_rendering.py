"""
Markdown / XSS regression tests executed against the REAL formatAIReply()
shipped in BioNeet-Pro.html (extracted + run under node).

  4. headings render (## / ###)
  5. unordered lists render (<ul><li>)
  6. ordered lists render (<ol><li>)
  7. malicious HTML is sanitized (script/iframe/event-handlers/javascript: URLs)
  + bold/italic/inline-code/citation chips/link safety spot-checks
"""
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))


def extract_fn():
    html = (BASE / "BioNeet-Pro.html").read_text(encoding="utf-8")
    i = html.find("function formatAIReply(text)")
    assert i >= 0, "formatAIReply not found in BioNeet-Pro.html"
    # balanced-brace extraction
    j = html.find("{", i)
    depth = 0
    for k in range(j, len(html)):
        if html[k] == "{":
            depth += 1
        elif html[k] == "}":
            depth -= 1
            if depth == 0:
                return html[i:k + 1]
    raise AssertionError("unbalanced braces in formatAIReply")


NODE_CASES = [
    ("heading2", "## Photosynthesis\nBody", ["md-h2", "Photosynthesis"]),
    ("heading3", "### Light reactions\nBody", ["md-h3", "Light reactions"]),
    ("ulist", "- ATP\n- NADPH", ["<ul", "<li>ATP</li>", "<li>NADPH</li>"]),
    ("olist", "1. Light reactions\n2. Calvin cycle",
     ["<ol", "Light reactions", "Calvin cycle"]),
    ("bold", "**Calvin cycle** fixes CO2", ["<strong>Calvin cycle</strong>"]),
    ("italic", "*Thylakoid* membranes", ["<em>Thylakoid</em>"]),
    ("code", "`Rubisco` enzyme", ["<code>Rubisco</code>"]),
    ("cite", "See evidence [E1: Calvin cycle]", ["cite-chip"]),
    ("safe_link", "[NCERT](/api/textbook/pdf/c01)", ['href="/api/textbook/pdf/c01"']),
    ("xss_script", "<script>alert(1)</script>", ["&lt;script&gt;"]),
    ("xss_img", '<img src=x onerror=alert(1)>', ["&lt;img", "onerror".replace("onerror", "onerror")]),
    ("xss_jsurl", "[click](javascript:alert(1))", ["javascript:".replace("javascript:", "javascript:")]),
    ("xss_iframe", "<iframe src='http://evil'></iframe>", ["&lt;iframe"]),
]

NEGATIVE = {
    # NOTE: checks target LIVE markup only. Escaped text such as
    # "&lt;img ... onerror=..." is inert (renders as text) and is the
    # CORRECT sanitized outcome — so substring checks must not flag the
    # escaped form.
    "xss_script": ["<script>"],
    "xss_img": ["<img"],
    "xss_jsurl": ['href="javascript:'],
    "xss_iframe": ["<iframe"],
}


def run_node(fn_src, payload):
    import json as _j
    js = fn_src + "\nconst __p=" + _j.dumps(payload) + ";\nconsole.log(formatAIReply(__p));"
    proc = subprocess.run(["node", "-e", js], capture_output=True, text=True,
                          timeout=30, cwd=str(BASE))
    assert proc.returncode == 0, f"node failed: {proc.stderr[:300]}"
    return proc.stdout


class TestMarkdownRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which("node") is None:
            raise unittest.SkipTest("node not available")
        cls.fn = extract_fn()
        cls.outputs = {}
        for name, payload, _ in NODE_CASES:
            cls.outputs[name] = run_node(cls.fn, payload)

    def test_4_headings_render(self):
        self.assertIn("md-h2", self.outputs["heading2"])
        self.assertIn("md-h3", self.outputs["heading3"])

    def test_5_unordered_lists_render(self):
        out = self.outputs["ulist"]
        self.assertIn("<ul", out)
        self.assertIn("<li>ATP</li>", out)

    def test_6_ordered_lists_render(self):
        out = self.outputs["olist"]
        self.assertIn("<ol", out)
        self.assertIn("Calvin cycle", out)

    def test_7_malicious_html_sanitized(self):
        for name in ("xss_script", "xss_img", "xss_jsurl", "xss_iframe"):
            out = self.outputs[name]
            for bad in NEGATIVE[name]:
                self.assertNotIn(bad, out, f"{name} leaked: {bad}")

    def test_rich_formatting_spot_checks(self):
        self.assertIn("<strong>Calvin cycle</strong>", self.outputs["bold"])
        self.assertIn("<em>Thylakoid</em>", self.outputs["italic"])
        self.assertIn("<code>Rubisco</code>", self.outputs["code"])
        self.assertIn("cite-chip", self.outputs["cite"])
        self.assertIn('href="/api/textbook/pdf/c01"', self.outputs["safe_link"])


if __name__ == "__main__":
    unittest.main()
