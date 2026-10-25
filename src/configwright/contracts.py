"""Versioned JSON Schema validation against a local Captain Contracts checkout."""
from pathlib import Path


def validate_document(document, contracts, schema_name):
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        from jsonschema.exceptions import ValidationError, SchemaError
    except ImportError as exc:
        raise ValueError("Contract validation requires: pip install jsonschema>=4") from exc
    schema_dir = Path(contracts)
    if not (schema_dir / schema_name).exists():
        schema_dir = schema_dir / "v0.1.0"
    schema_path = schema_dir / schema_name
    if not schema_path.is_file():
        raise ValueError(f"Cannot find contract schema: {schema_path}")
    import json
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema.setdefault("$id", schema_path.resolve().as_uri())
    Draft202012Validator.check_schema(schema)
    # Register local sibling schemas; no network fetches needed for shipped contracts.
    registry = Registry()
    for other in schema_dir.glob("*.schema.json"):
        uri = other.resolve().as_uri()
        other_schema = json.loads(other.read_text(encoding="utf-8"))
        other_schema.setdefault("$id", uri)
        resource = Resource.from_contents(other_schema)
        registry = registry.with_resource(uri, resource)
    validator = Draft202012Validator(schema, registry=registry)
    errors = sorted(validator.iter_errors(document), key=lambda e: tuple(str(x) for x in e.absolute_path))
    if errors:
        error = errors[0]
        location = "/" + "/".join(str(p) for p in error.absolute_path)
        raise ValueError(f"{schema_name} validation failed at {location}: {error.message}")
    return True
