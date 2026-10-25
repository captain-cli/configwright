import json
import tempfile
import unittest
from pathlib import Path
from configwright.core import build, render

class ConfigTests(unittest.TestCase):
    def test_render_references_and_contracts(self):
        src = {"schemaVersion": 1, "project": "demo", "applications": {"api": {"port": "${dockhand.ports.api}", "secretRef": "env:JWT_SECRET"}}, "databases": {"x": {"passwordRef": "env:PASSWORD"}}}
        doc = build(src, {"ports": {"api": 4321}})
        self.assertEqual(doc["applications"]["api"]["port"], 4321)
        with tempfile.TemporaryDirectory() as t:
            paths = render(doc, t)
            self.assertEqual(len(paths), 4)
            self.assertEqual(json.loads((Path(t)/"applications/api.json").read_text())["secretRef"], "env:JWT_SECRET")
    def test_unresolved_reference_fails(self):
        with self.assertRaises(ValueError):
            build({"schemaVersion": 1, "applications": {"api": {"port": "${dockhand.ports.missing}"}}}, {})
    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as t:
            render(build({"schemaVersion": 1, "applications": {}}), Path(t)/"out", True)
            self.assertFalse((Path(t)/"out").exists())

if __name__ == "__main__": unittest.main()
