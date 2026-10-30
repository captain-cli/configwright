import unittest
from copy import deepcopy
from configwright.core import build
from configwright.dockhand_adapter import normalize_servicewright

MANIFEST = {"schemaVersion": 1, "applications": {
    "auth-api": {"port": "${dockhand.ports.auth-api}"},
    "media-api": {"port": "${dockhand.ports.media-api}", "authUrl": "http://localhost:${dockhand.ports.auth-api}/"}}}
RESOLVED = {"services": [
    {"name": "auth-api", "runtime": {"port": 6751}},
    {"name": "media-api", "runtime": {"port": 6752}}]}

class AdapterTests(unittest.TestCase):
    def test_uses_real_allocations(self):
        result = build(MANIFEST, normalize_servicewright(RESOLVED, MANIFEST))
        self.assertEqual(result['applications']['auth-api']['port'], 6751)
        self.assertEqual(result['applications']['media-api']['authUrl'], 'http://localhost:6751/')

    def test_missing_service_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unresolved Dockhand'):
            normalize_servicewright({'services': RESOLVED['services'][:1]}, MANIFEST)

    def test_duplicate_ports_rejected(self):
        bad = deepcopy(RESOLVED)
        bad['services'][1]['runtime']['port'] = 6751
        with self.assertRaisesRegex(ValueError, 'Duplicate resolved ports'):
            normalize_servicewright(bad, MANIFEST)

    def test_literal_port_conflict_rejected(self):
        bad = deepcopy(MANIFEST)
        bad['applications']['auth-api']['port'] = 4310
        with self.assertRaisesRegex(ValueError, 'Port mismatch'):
            normalize_servicewright(RESOLVED, bad)

    def test_duplicate_service_rejected(self):
        bad = deepcopy(RESOLVED)
        bad['services'].append(deepcopy(bad['services'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate Dockhand service'):
            normalize_servicewright(bad, MANIFEST)

if __name__ == '__main__': unittest.main()
