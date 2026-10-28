"""ConfigWright CLI."""
import argparse
import json
from .core import build, load, render
from .contracts import validate_document
from .credentials import validate_credential_references


def main(argv=None):
    parser = argparse.ArgumentParser(prog="configwright")

    parser.add_argument(
        "--version",
        action="version",
        version="configwright 0.3.0",
    )

    subs = parser.add_subparsers(dest="command", required=True)
    cmd = subs.add_parser("build", help="Resolve and render configuration")
    cmd.add_argument("--manifest", required=True)
    cmd.add_argument("--dockhand")
    cmd.add_argument("--contracts", help="Contracts schemas directory (or its v0.1.0 parent)")
    cmd.add_argument("--credential-spec", help="CredentialWright declaration file (never secret values)")
    cmd.add_argument("--output", required=True)
    cmd.add_argument("--dry-run", action="store_true")
    check = subs.add_parser("validate", help="Validate manifest and optionally resolved output")
    check.add_argument("--manifest", required=True)
    check.add_argument("--dockhand")
    check.add_argument("--contracts", required=True)
    check.add_argument("--credential-spec", help="CredentialWright declaration file")
    args = parser.parse_args(argv)
    try:
        manifest = load(args.manifest)
        if args.contracts:
            validate_document(manifest, args.contracts, "project.schema.json")
        # Manifests without an available Dockhand resolution can still be validated as input.
        if args.command == "validate" and not args.dockhand and not args.credential_spec:
            print(json.dumps({"valid": True, "stage": "manifest"}, indent=2))
            return 0
        master = build(manifest, load(args.dockhand) if args.dockhand else None)
        if args.contracts:
            validate_document(master, args.contracts, "resolved-config.schema.json")
        credential_summary = None
        if args.credential_spec:
            spec = load(args.credential_spec)
            if args.contracts:
                validate_document(spec, args.contracts, "credential-spec.schema.json")
            credential_summary = validate_credential_references(master, spec)
        if args.command == "validate":
            print(json.dumps({"valid": True, "stage": "resolved", "credentials": credential_summary}, indent=2))
            return 0
        paths = render(master, args.output, args.dry_run)
        print(json.dumps({"dryRun": args.dry_run, "paths": paths, "credentials": credential_summary}, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        parser.exit(2, f"configwright: {exc}\n")


if __name__ == "__main__":
    main()
