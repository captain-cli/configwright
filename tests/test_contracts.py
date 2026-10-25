import copy
import tempfile
import unittest
from pathlib import Path
from configwright.core import load, build
from configwright.contracts import validate_document
from configwright.cli import main

SCHEMAS = Path(__file__).resolve().parents[2] / "captain-contracts" / "schemas"
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"

class ContractTests(unittest.TestCase):
    def test_valid_manifest_and_resolved(self):
        manifest = load(EXAMPLES / "project.json")
        self.assertTrue(validate_document(manifest, SCHEMAS, "project.schema.json"))
        master = build(manifest, load(EXAMPLES / "dockhand-resolved.json"))
        self.assertTrue(validate_document(master, SCHEMAS, "resolved-config.schema.json"))
    def test_reject_bad_manifest(self):
        manifest = load(EXAMPLES / "project.json")
        manifest["applications"] = []
        with self.assertRaisesRegex(ValueError, "applications"):
            validate_document(manifest, SCHEMAS, "project.schema.json")
    def test_reject_bad_resolved_database_port(self):
        master = build(load(EXAMPLES / "project.json"), load(EXAMPLES / "dockhand-resolved.json"))
        master["databases"]["appdb"]["port"] = 70000
        with self.assertRaisesRegex(ValueError, "port"):
            validate_document(master, SCHEMAS, "resolved-config.schema.json")
    def test_cli_validate_and_build(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(main(["validate", "--manifest", str(EXAMPLES / "project.json"), "--contracts", str(SCHEMAS)]), 0)
            self.assertEqual(main(["validate", "--manifest", str(EXAMPLES / "project.json"), "--dockhand", str(EXAMPLES / "dockhand-resolved.json"), "--contracts", str(SCHEMAS)]), 0)
            self.assertEqual(main(["build", "--manifest", str(EXAMPLES / "project.json"), "--dockhand", str(EXAMPLES / "dockhand-resolved.json"), "--contracts", str(SCHEMAS), "--output", d]), 0)
            self.assertTrue((Path(d) / "master_config.json").exists())

if __name__ == "__main__": unittest.main()
