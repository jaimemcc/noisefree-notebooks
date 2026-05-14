Use this as a handoff prompt to your new repo assistant:

Implementation Brief: Jupyter + Git Noise-Free Workflow

Goal
Set up a repository-specific notebook workflow so that only source changes are tracked in git. Execution counts, outputs, and volatile metadata must not appear as meaningful changes across machines.

Chosen Strategy
Use a text-first notebook workflow with Jupytext pairing.

1. Track text notebooks as the canonical source.
2. Treat notebook JSON files as generated local artifacts by default.
3. Ensure notebook JSON can be recreated easily from text.
4. Add local and CI guardrails so setup is consistent across clones.

Why this strategy
1. It is robust against cross-machine notebook noise.
2. Diffs and code reviews are cleaner.
3. Regeneration is straightforward, so notebook interactivity is preserved.
4. It avoids the dirtying behavior that can still occur with incomplete metadata stripping.

Requirements
1. Repository-scoped behavior first.
2. Simple first-time setup per clone.
3. Clear prompt or failure if setup is missing.
4. Deterministic behavior on Windows and non-Windows environments.
5. No history rewrite unless explicitly requested.

Implementation Plan

Phase 1: Notebook policy
1. Choose one canonical text format for notebooks.
2. Define managed notebook paths.
3. Define exception paths where notebook JSON may still be tracked, if any.

Phase 2: Pairing and ignore policy
1. Configure automatic pairing between notebook JSON and text representation.
2. Ignore generated notebook JSON in managed paths.
3. Keep the policy explicit and minimal.

Phase 3: Bootstrap setup
1. Provide one command that installs required tooling.
2. Validate tooling installation.
3. Print clear success and remediation messages.

Phase 4: Local guardrails
1. Add commit-time checks that fail when notebook pairs are out of sync.
2. Block accidental commits of generated notebook JSON in managed paths.
3. Keep errors actionable with exact fix commands.

Phase 5: CI enforcement
1. Run notebook sync and policy checks in pull requests.
2. Fail with clear instructions if notebooks are unsynced or policy is violated.
3. Keep CI checks aligned with local checks.

Phase 6: Onboarding docs
1. Add a short setup section with first-run command.
2. Add daily workflow examples.
3. Add troubleshooting for regeneration and sync issues.

Validation Checklist
1. Fresh clone, bootstrap once, execute notebook, confirm clean status when only outputs changed.
2. Edit source cell, sync, confirm only text notebook diff.
3. Delete local notebook JSON, regenerate, confirm expected clean status.
4. Repeat on second machine, confirm same behavior.
5. Intentionally break sync, confirm local check and CI both fail with helpful guidance.

Daily Workflow Expectations
1. Open and run notebooks normally.
2. Sync pair before commit if not automatic.
3. Commit text notebook changes.
4. Regenerate notebook JSON as needed for interactive use.

Migration Notes
1. For existing notebooks, convert to paired text form.
2. Remove tracked notebook JSON in managed paths after conversion.
3. Do not rewrite git history unless explicitly requested.

Definition of Done
1. Notebook execution on different machines does not create git noise unless source changed.
2. New contributors can set up with one documented command.
3. Policy is enforced both locally and in CI.
4. Workflow is documented and reproducible.

If you want, I can also generate a second version of this brief that is command-oriented, with exact shell and PowerShell commands and expected outputs.