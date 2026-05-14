# nbtest

This repository is set up for a text-first Jupyter workflow.

## First setup

Run:

```powershell
pixi install
pixi run bootstrap
```

If you are not using Pixi, use:

```powershell
python scripts/bootstrap_notebook_workflow.py
```

## Notebook policy

- Keep notebook source in `notebooks/` as `py:percent` text notebooks.
- Treat `.ipynb` files in managed notebook paths as generated local artifacts.
- Run `pixi run check-notebook-policy` before committing if you want a manual check.
- Run `pixi run check-notebook-sync` to verify tracked text notebooks still round-trip cleanly.
- Run `pixi run sync-notebooks` to regenerate paired notebook JSON when you want the interactive artifact locally.

## Starter notebook

The repository includes [notebooks/starter_notebook.py](notebooks/starter_notebook.py) as a working example of the text-first notebook format.
