# Chat Handoff Notes (May 14, 2026)

## Repository naming

- Preferred name selected: `noisefree_notebooks`.
- Recommendation for GitHub repository slug: `noisefree-notebooks`.
- Recommendation for Python import/package style: `noisefree_notebooks`.

## Setup hardening completed

The notebook workflow setup was hardened for established repositories:

- `setup_notebook_workflow.py`
  - Added safer existing-file behavior via `--on-existing` with options: `skip` (default), `overwrite`, `fail`.
  - Added `--dry-run` to preview changes without writing files.
  - Added clearer handling when Pixi is missing from PATH.
  - Updated generated tasks and guidance for migration workflows.

## Migration and untracking improvements

### New/updated scripts

- `scripts/untrack_managed_notebooks.py`
  - Preview mode by default.
  - Apply mode now requires explicit confirmation: `--apply --yes`.
  - Shows list and total count of tracked managed `.ipynb` files.

- `scripts/migrate_existing_notebooks.py` (new)
  - Guided migration flow for established repos:
    1. Preview tracked managed `.ipynb` files.
    2. Optional untrack step.
    3. Sync notebooks.
    4. Run sync check.
    5. Run policy check.

### Pixi task updates

- Added in `pyproject.toml`:
  - `preview-untrack-managed-notebooks`
  - `untrack-managed-notebooks` (uses `--apply --yes`)
  - `migrate-existing-notebooks-preview`
  - `migrate-existing-notebooks`

## Recommended established-repo migration commands

```powershell
# 1) Safe setup (preserve existing managed files)
python setup_notebook_workflow.py --on-existing skip

# 2) Preview migration impact
pixi run migrate-existing-notebooks-preview

# 3) Apply migration (untrack + sync + checks)
pixi run migrate-existing-notebooks
```

## Folder rename + chat history note

- Copilot chat history may not follow a folder rename, because history is usually tied to workspace identity/path.
- This file is intended to preserve the important decisions from this chat.
