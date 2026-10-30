"""Strict adapter for Dockhand's resolved ServiceWright collection.

Only infrastructure allocations cross this boundary. No credential values.
"""
import re

_PORT_REF = re.compile(r'\$\{dockhand\.ports\.([A-Za-z0-9_.-]+)\}')
_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]*$')


def normalize_servicewright(resolved, manifest):
    if not isinstance(resolved, dict) or not isinstance(resolved.get('services'), list):
        raise ValueError('Dockhand resolved configuration requires a services array')
    if not isinstance(manifest, dict) or not isinstance(manifest.get('applications'), dict):
        raise ValueError('ConfigWright manifest requires applications object')
    ports = {}
    for service in resolved['services']:
        if not isinstance(service, dict):
            raise ValueError('Invalid Dockhand service entry')
        name = service.get('name')
        runtime = service.get('runtime')
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise ValueError('Invalid Dockhand service name')
        if name in ports:
            raise ValueError(f'Duplicate Dockhand service name: {name}')
        if not isinstance(runtime, dict) or not isinstance(runtime.get('port'), int) or isinstance(runtime['port'], bool) or not 1 <= runtime['port'] <= 65535:
            raise ValueError(f'Invalid resolved port for {name}')
        ports[name] = runtime['port']
    if len(set(ports.values())) != len(ports):
        raise ValueError('Duplicate resolved ports across services')
    refs = set(_PORT_REF.findall(str_values(manifest)))
    missing = refs - ports.keys()
    if missing:
        raise ValueError(f'Unresolved Dockhand service references: {", ".join(sorted(missing))}')
    # A service port must not be silently overridden by an unrelated literal.
    for name, app in manifest['applications'].items():
        if name in ports and isinstance(app, dict) and 'port' in app:
            value = app['port']
            expected = '${dockhand.ports.' + name + '}'
            if value != expected and value != ports[name]:
                raise ValueError(f'Port mismatch for application {name}: expected Dockhand port {ports[name]}')
    return {'ports': ports}


def str_values(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return '\n'.join(map(str_values, value))
    if isinstance(value, dict):
        return '\n'.join(map(str_values, value.values()))
    return ''
