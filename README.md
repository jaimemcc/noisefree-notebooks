# noisefree-notebooks

Set up a text-first Jupyter workflow in a repository using Pixi + Jupytext.

## What most users come here for

Use [setup_notebook_workflow.py](setup_notebook_workflow.py) to install the workflow files, tasks, and checks.

By default, setup is safe for established repositories:
- Existing managed files are preserved (`--on-existing skip`).
- Managed files can be previewed without changes (`--dry-run`).
- The script runs `pixi install` and `pixi run bootstrap` unless `--skip-pixi` is used.

## Tooling layout

Workflow implementation files are isolated under `tooling/notebook_workflow/` so they are clearly infrastructure, not project code.

- Daily commands (`pixi run sync`, `pixi run check`, `pixi run regen`) stay the same.
- `scripts/` contains compatibility wrappers only.
- New repositories created with `setup_notebook_workflow.py` now generate workflow scripts under `tooling/notebook_workflow/`.

## Roadmap

Planned future work is tracked in [TODO.md](TODO.md), including the workflow/package update strategy across repositories.

## Setup options

### Option A: default setup (recommended)

```powershell
python setup_notebook_workflow.py
```

### Option B: safe setup for an existing repo (recommended for migration)

```powershell
python setup_notebook_workflow.py --on-existing skip
```

### Option C: preview setup changes first

```powershell
python setup_notebook_workflow.py --on-existing skip --dry-run
```

### Option D: custom notebook and tracked directories

```powershell
python setup_notebook_workflow.py --notebook-dir analysis --tracked-dir text
```

### Option E: select Pixi Python version

```powershell
python setup_notebook_workflow.py --python-version 3.12.*
```

Short aliases are also available:
- `-n` for `--notebook-dir`
- `-t` for `--tracked-dir`
- `-p` for `--python-version`
- `-s` for `--skip-pixi`
- `-o` for `--on-existing`
- `-d` for `--dry-run`

Behavior when `--python-version` is omitted:
- If `pyproject.toml` already has `[tool.pixi.dependencies] python = ...`, that pin is reused.
- Otherwise the setup default is `3.11.*`.

Validation:
- Setup now fails fast if the Python spec is malformed.
- Valid examples: `3.11.*`, `3.12.*`, `>=3.11,<3.13`.

Important distinction:
- The Python interpreter used to run `setup_notebook_workflow.py` does not control your project runtime.
- Your project/runtime Python comes from the Pixi environment pin in `pyproject.toml`.

## Existing repository migration

If your repo previously tracked managed `.ipynb` files under the notebook directory, run:

```powershell
python setup_notebook_workflow.py --on-existing skip
pixi run migrate-existing-notebooks-preview
pixi run migrate-existing-notebooks
```

This migration flow:
1. Previews tracked managed `.ipynb` files.
2. Optionally untracks them from git.
3. Syncs notebooks.
4. Verifies sync and policy checks.

## Multiple notebook roots (supported)

Yes. You can manage more than one notebook source folder in the same repository.

Edit [notebook_workflow_config.json](notebook_workflow_config.json):

```json
{
	"managed_roots": [
		{
			"source_dir": "feature1/notebooks",
			"tracked_subdir": "text"
		},
		{
			"source_dir": "feature2/notebooks",
			"tracked_subdir": "text"
		}
	]
}
```

Notes:
- `source_dir` is repository-relative.
- `tracked_subdir` is created under each `source_dir`.
- You can also use `tracked_dir` if you want a repository-relative tracked location.
- All workflow commands (`sync`, `regen`, `check`, policy, untrack, migration) use this config.

If you add new notebook roots, also update `.gitignore` so managed `.ipynb` files stay untracked.

## After setup (daily use)

1. Edit `notebooks/<name>.ipynb`.
2. Sync to tracked text notebooks:

```powershell
pixi run sync
```

3. Validate before commit:

```powershell
pixi run check
```

4. Commit updates in `notebooks/text/`.

## Command reference

- `pixi run sync`: convert managed `.ipynb` to tracked `.py`
- `pixi run regen`: regenerate `.ipynb` from tracked `.py`
- `pixi run regen <notebook.py>`: regenerate one notebook
- `pixi run check`: run policy + sync checks
- `pixi run migrate-existing-notebooks-preview`: preview migration impact
- `pixi run migrate-existing-notebooks`: apply untrack + sync + checks
- `pixi run preview-untrack-managed-notebooks`: preview tracked managed `.ipynb`
- `pixi run untrack-managed-notebooks`: untrack managed `.ipynb` (`--apply --yes`)
