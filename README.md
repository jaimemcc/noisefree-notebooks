# noisefree-notebooks

Text-first Jupyter workflow using Pixi + Jupytext.

## What this repo does

- Edit notebooks locally as `.ipynb` in `notebooks/`.
- Track only synced `.py` files in `notebooks/text/`.
- Keep notebook policy and sync checks enforced locally and in CI.

## Quick start

```powershell
pixi install
pixi run bootstrap
```

Then restore any generated notebooks from tracked text files:

```powershell
pixi run regen
```

## Daily workflow

1. Edit `notebooks/<name>.ipynb`.
2. Sync notebook sources to tracked text files:

```powershell
pixi run sync
```

3. Validate before commit:

```powershell
pixi run check
```

4. Commit changes in `notebooks/text/`.

## Core commands

- `pixi run sync`: convert managed `.ipynb` to `.py` (tracked)
- `pixi run regen`: regenerate `.ipynb` from tracked `.py`
- `pixi run regen <notebook.py>`: regenerate one notebook
- `pixi run check`: run sync + policy checks
- `pixi run check-notebook-sync`: verify `.py` files match source notebooks
- `pixi run check-notebook-policy`: ensure managed `.ipynb` files are not tracked

## Existing repo migration

Safe migration path for repos that previously tracked managed `.ipynb` files:

```powershell
python setup_notebook_workflow.py --on-existing skip
pixi run migrate-existing-notebooks-preview
pixi run migrate-existing-notebooks
```

Related tasks:

- `pixi run preview-untrack-managed-notebooks`
- `pixi run untrack-managed-notebooks`

## Notes

- Current default branch: `main`.
- Remote repository: `https://github.com/jaimemcc/noisefree-notebooks`.
