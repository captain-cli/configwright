import unittest
from configwright.credentials import validate_credential_references

MASTER = {"applications": {"api": {"jwtSecretRef": "env:JWT_SECRET"}}, "databases": {"appdb": {"passwordRef": "env:APP_DB_PASSWORD"}}}
SPEC = {"credentials": {"JWT_SECRET": {"bytes": 64}, "APP_DB_PASSWORD": {"bytes": 32}}}

class CredentialContractsTest(unittest.TestCase):
    def test_declared_refs(self):
        self.assertEqual(validate_credential_references(MASTER, SPEC)["references"], 2)
    def test_missing_ref(self):
        with self.assertRaisesRegex(ValueError, "not declared"):
            validate_credential_references(MASTER, {"credentials": {"JWT_SECRET": {}}})
    def test_invalid_ref(self):
        with self.assertRaisesRegex(ValueError, "Invalid or unsupported"):
            validate_credential_references({"jwtSecretRef":"plaintext"}, SPEC)
