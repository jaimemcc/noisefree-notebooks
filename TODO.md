# Roadmap and TODO

## Workflow Distribution and Updates

Status: planned

Goal:
Create an elegant, low-risk way to update the notebook workflow package across repositories when features are added or bugs are fixed.

Why this matters:
- Repositories should adopt fixes and improvements without manual script copying.
- Workflow internals should stay isolated from project code.
- Update steps should be predictable and easy to roll back.

Initial design tasks:
- Define distribution approach: Git-tag install, internal package index, or PyPI package.
- Add workflow version metadata and expose a `--version` CLI output.
- Add update command design (for example `nfw update`) with dry-run and apply modes.
- Define compatibility policy for config/schema changes.
- Add migration hooks for breaking changes with clear upgrade notes.
- Add test matrix across at least 2-3 sample repos before publishing.
- Document release and update playbook (release checklist, changelog, rollback plan).

Success criteria:
- Existing repos can upgrade in a single documented command.
- Upgrade reports what will change before applying changes.
- CI verifies workflow version and upgrade compatibility.
