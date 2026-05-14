from __future__ import annotations

from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[1]
SOURCE_NOTEBOOK_DIR = ROOT / "notebooks" / "source"
TRACKED_NOTEBOOK_DIR = ROOT / "notebooks" / "text"


def source_notebooks() -> list[Path]:
    return sorted(path for path in SOURCE_NOTEBOOK_DIR.rglob("*.ipynb") if path.is_file())


def main() -> int:
    notebooks = source_notebooks()
    if not notebooks:
        print("No source notebooks found under notebooks/source/.")
        return 0

    for source_notebook in notebooks:
        relative_path = source_notebook.relative_to(SOURCE_NOTEBOOK_DIR).with_suffix(".py")
        target_notebook = TRACKED_NOTEBOOK_DIR / relative_path
        target_notebook.parent.mkdir(parents=True, exist_ok=True)

        notebook_object = jupytext.read(source_notebook)
        jupytext.write(notebook_object, target_notebook, fmt="py:percent")

    print("Notebook sync complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
