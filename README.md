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

- Author notebooks in `notebooks/source/` as `.ipynb` files.
- Run `pixi run sync-notebooks` to generate the tracked `.py` copies in `notebooks/text/`.
- Run `pixi run regenerate-notebooks` to restore all `.ipynb` files from the tracked `.py` copies.
- Run `pixi run regenerate-notebooks <notebook_name.py>` to restore a single notebook (e.g., `pixi run regenerate-notebooks starter_notebook.py`).
- Run `pixi run check-notebook-sync` before committing to confirm the tracked `.py` files match the source notebooks.
- Run `pixi run check-notebook-policy` if you want a manual check that no `.ipynb` files are being tracked.

## Starter notebook

The repository includes [notebooks/source/starter_notebook.ipynb](notebooks/source/starter_notebook.ipynb) as the source notebook and [notebooks/text/starter_notebook.py](notebooks/text/starter_notebook.py) as the tracked sync target.
