from __future__ import annotations

import json

import pytest


class ManifestDirectory(pytest.Directory):
    def collect(self):
        # The standard pytest behavior is to loop over all `test_*.py` files and
        # call `pytest_collect_file` on each file. This collector instead reads
        # the `manifest.json` file and only calls `pytest_collect_file` for the
        # files defined there.
        manifest_path = self.path / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        ihook = self.ihook
        for file in manifest["modules"]:
            yield from ihook.pytest_collect_file(
                file_path=self.path / file, parent=self
            )
