#!/usr/bin/env python3
"""Extract inline JavaScript from the static frontend and syntax-check it with Node."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import tempfile


class InlineScripts(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.scripts: list[tuple[str, bool]] = []
        self._current: list[str] | None = None
        self._is_module = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        attributes = dict(attrs)
        if attributes.get("src"):
            self._current = None
            return
        self._current = []
        self._is_module = (attributes.get("type") or "").lower() == "module"

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._current is not None:
            source = "".join(self._current)
            if source.strip():
                self.scripts.append((source, self._is_module))
            self._current = None


def check_file(html_path: Path, temp_dir: Path) -> bool:
    parser = InlineScripts()
    parser.feed(html_path.read_text(encoding="utf-8-sig"))
    ok = True
    for index, (source, is_module) in enumerate(parser.scripts, start=1):
        suffix = ".mjs" if is_module else ".js"
        source_path = temp_dir / f"{html_path.stem}-{index}{suffix}"
        source_path.write_text(source, encoding="utf-8")
        result = subprocess.run(
            ["node", "--check", str(source_path)],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if result.returncode:
            ok = False
            print(f"FAIL {html_path} inline script {index}:")
            print((result.stderr or result.stdout).strip())
        else:
            print(f"PASS {html_path} inline script {index}")
    if not parser.scripts:
        print(f"FAIL {html_path}: no inline JavaScript found")
        return False
    return ok


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    root = Path(__file__).resolve().parents[1]
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("files", nargs="*", type=Path, help="HTML files to check (defaults to both app entrypoints)")
    args = cli.parse_args()
    files = args.files or [root / "index.html", root / "BioNeet-Pro.html"]
    with tempfile.TemporaryDirectory(prefix="bioneet-js-check-") as temp:
        temp_dir = Path(temp)
        results = [check_file(path, temp_dir) for path in files]
        return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
