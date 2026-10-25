"""ConfigWright: manifest resolution without runtime infrastructure side effects."""
import json
import os
import re
import tempfile
from pathlib import Path

TOKEN = re.compile(r"\$\{([^}]+)\}")


def load(path):
    path = Path(path)
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise ValueError("YAML support requires: pip install PyYAML") from exc
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    return json.loads(path.read_text(encoding="utf-8"))


def lookup(root, dotted):
    obj = root
    for part in dotted.split("."):
        if not isinstance(obj, dict) or part not in obj:
            raise ValueError(f"Unresolved configuration reference: {dotted}")
        obj = obj[part]
    return obj


def resolve(value, context):
    if isinstance(value, dict):
        return {k: resolve(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, context) for v in value]
    if not isinstance(value, str):
        return value
    match = TOKEN.fullmatch(value)
    if match:
        return lookup(context, match.group(1))
    def replace(match):
        result = lookup(context, match.group(1))
        if isinstance(result, (dict, list)):
            raise ValueError("Cannot interpolate complex values into a string")
        return str(result)
    return TOKEN.sub(replace, value)


def build(manifest, dockhand=None):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("applications"), dict):
        raise ValueError("Manifest must contain an 'applications' object")
    if manifest.get("schemaVersion") != 1:
        raise ValueError("Supported manifest schemaVersion is 1")
    context = {"dockhand": dockhand or {}, "project": {"name": manifest.get("project", "unnamed")}}
    # Secrets are intentionally opaque references. Never load credential values.
    resolved = resolve(manifest, context)
    return {"schemaVersion": 1, "project": resolved.get("project"),
            "environment": resolved.get("environment", "development"),
            "databases": resolved.get("databases", {}),
            "services": resolved.get("services", {}),
            "applications": resolved["applications"]}


def _write_json(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".configwright-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(content, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def render(master, output, dry_run=False):
    output = Path(output)
    destinations = [output / "master_config.json"]
    for name in master["applications"]:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
            raise ValueError(f"Invalid application identifier: {name!r}")
        destinations.append(output / "applications" / f"{name}.json")
    destinations.extend([output / "schemawright" / "databases.json",
                         output / "servicewright" / "services.json"])
    if not dry_run:
        _write_json(destinations[0], master)
        for name, dest in zip(master["applications"], destinations[1:1 + len(master["applications"])]):
            _write_json(dest, master["applications"][name])
        _write_json(destinations[-2], master["databases"])
        _write_json(destinations[-1], master["services"])
    return [str(p) for p in destinations]
