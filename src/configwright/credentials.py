"""Validate env credential references against a declaration, without reading secrets."""
import re

ENV = re.compile(r"^env:([A-Z][A-Z0-9_]*)$")

def validate_credential_references(master, spec):
    names = spec.get("credentials") if isinstance(spec, dict) else None
    if not isinstance(names, dict):
        raise ValueError("Credential spec must contain a credentials object")
    found = []
    def walk(node, path="$ "):
        if isinstance(node, dict):
            for key, val in node.items():
                loc = f"{path.strip()}.{key}"
                if key.endswith("Ref"):
                    match = ENV.fullmatch(val) if isinstance(val, str) else None
                    if not match:
                        raise ValueError(f"Invalid or unsupported credential reference at {loc}; expected env:UPPERCASE_KEY")
                    if match.group(1) not in names:
                        raise ValueError(f"Credential {match.group(1)} referenced at {loc} is not declared")
                    found.append(match.group(1))
                else:
                    walk(val, loc)
        elif isinstance(node, list):
            for i, val in enumerate(node):
                walk(val, f"{path}[{i}]")
    walk(master)
    return {"references": len(found), "requiredKeys": sorted(set(found))}
