# SPDX-License-Identifier: MIT

"""Documentation release checks; no Go toolchain or private scrub policy required."""

from pathlib import Path
import runpy
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
        for path in self.root.rglob("*.md"):
            if path.name != "README.md" or path.parent != self.root:
                self.assertIn(f"]({path.relative_to(self.root).as_posix()})", readme)


if __name__ == "__main__":
    unittest.main()
