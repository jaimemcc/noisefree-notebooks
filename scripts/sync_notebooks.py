from __future__ import annotations

from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
TRACKED_NOTEBOOK_DIR = ROOT / "notebooks" / "text"


def source_notebooks() -> list[Path]:
    notebooks: list[Path] = []
    for path in NOTEBOOK_DIR.rglob("*.ipynb"):
        if not path.is_file():
            continue
        if TRACKED_NOTEBOOK_DIR in path.parents:
            continue
        notebooks.append(path)
    return sorted(notebooks)


def main() -> int:
    notebooks = source_notebooks()
    if not notebooks:
        print("No source notebooks found under notebooks/.")
        return 0

    for source_notebook in notebooks:
        relative_path = source_notebook.relative_to(NOTEBOOK_DIR).with_suffix(".py")
        target_notebook = TRACKED_NOTEBOOK_DIR / relative_path
        target_notebook.parent.mkdir(parents=True, exist_ok=True)

        notebook_object = jupytext.read(source_notebook)
        jupytext.write(notebook_object, target_notebook, fmt="py:percent")

    print("Notebook sync complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
