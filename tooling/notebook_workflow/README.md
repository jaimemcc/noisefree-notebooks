# Notebook Workflow Tooling

This folder contains infrastructure-only scripts for notebook sync and policy checks.

Most users should run these via Pixi tasks from the repository root:

- `pixi run sync`
- `pixi run regen`
- `pixi run check`
- `pixi run migrate-existing-notebooks`

Compatibility wrappers remain in `scripts/` so older references still work.
