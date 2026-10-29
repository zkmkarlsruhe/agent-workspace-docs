# SPDX-License-Identifier: MIT

"""Documentation release checks; no Go toolchain or private scrub policy required."""

import importlib.util
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class DocsTest(runpy.run_path(str(HERE / "document_checks.py"))["DocumentChecks"],
               runpy.run_path(str(HERE / "semantic_checks.py"))["SemanticChecks"], unittest.TestCase):
    root = HERE.parents[1]
    documents_only = True

    def test_notice_and_index(self):
        readme = (self.root / "README.md").read_text()
        self.assertIn("Prototype for evaluation only. Not production software, no support, "
                      "no guarantees. Do not make it reachable from the internet; run it only in an "
                      "internal network. Use at your own risk.", readme)
        for path in (self.root / "docs").rglob("*.md"):
            if path != self.root / "docs/README.md":
                self.assertIn(f"]({path.relative_to(self.root).as_posix()})", readme)

    def test_pages_navigation(self):
        config = (self.root / "mkdocs.yml").read_text()
        nav = json.loads(config.split("\nnav: ", 1)[1])
        pages = sorted(p.relative_to(self.root / "docs").as_posix()
                       for p in (self.root / "docs").rglob("*.md")
                       if p != self.root / "docs/README.md")
        self.assertEqual(nav, [{"Home": "README.md"}, {"Whitepaper": "whitepaper.md"}]
                         + [p for p in pages if not p.startswith("adr/") and p != "whitepaper.md"]
                         + [{"ADRs": [p for p in pages if p.startswith("adr/")]}])
        self.assertIn("https://zkmkarlsruhe.github.io/agent-workspace-docs/", config)
        self.assertIn("https://zkmkarlsruhe.github.io/agent-workspace-docs/",
                      (self.root / "README.md").read_text())

    def test_mkdocs_build(self):
        if importlib.util.find_spec("mkdocs") is None:
            reason = "mkdocs unavailable; install mkdocs-material==9.6.14 to check Pages"
            print("SKIP: " + reason, flush=True)
            self.skipTest(reason)
        with tempfile.TemporaryDirectory(prefix="docs-site-") as site:
            subprocess.run([sys.executable, "-I", "-B", "-m", "mkdocs", "build", "--strict",
                            "--site-dir", site], cwd=self.root, check=True)


if __name__ == "__main__":
    unittest.main()
