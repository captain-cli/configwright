# ConfigWright v0.2.0

Standalone config compiler. Reads JSON or YAML manifests, interpolates Dockhand outputs, retains credential references, and renders a master plus per-tool projection files.

```bash
pip install -e .
configwright validate --manifest examples/project.json --contracts ../captain-contracts/schemas
configwright validate --manifest examples/project.json --dockhand examples/dockhand-resolved.json --contracts ../captain-contracts/schemas
configwright build --manifest examples/project.json --dockhand examples/dockhand-resolved.json --contracts ../captain-contracts/schemas --output .local/generated
python -m unittest discover -s tests -v
```

`validate` without `--dockhand` checks **only the input manifest**; supply `--dockhand` to validate the resolved master. `build` remains usable without `--contracts` for backward compatibility. Contracts validate shape, not availability of actual referenced secrets. Do not commit generated deployment secrets.
