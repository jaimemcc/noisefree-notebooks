from __future__ import annotations

import sys
from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
TRACKED_NOTEBOOK_DIR = ROOT / "notebooks" / "text"


def source_notebooks() -> list[Path]:
    return sorted(path for path in NOTEBOOK_DIR.glob("*.ipynb") if path.is_file())


def main() -> int:
    notebooks = source_notebooks()
    if not notebooks:
        print("Notebook sync check passed: no source notebooks found.")
        return 0

    for source_notebook in notebooks:
        relative_path = source_notebook.relative_to(NOTEBOOK_DIR).with_suffix(".py")
        target_notebook = TRACKED_NOTEBOOK_DIR / relative_path

        if not target_notebook.exists():
            print(
                f"Notebook sync check failed for {source_notebook.relative_to(ROOT)}. Regenerate it with: pixi run sync-notebooks",
                file=sys.stderr,
            )
            return 1

        regenerated_text = jupytext.writes(jupytext.read(source_notebook), fmt="py:percent")
        current_text = target_notebook.read_text(encoding="utf-8")

        if regenerated_text != current_text:
            print(
                f"Notebook sync check failed for {source_notebook.relative_to(ROOT)}. Regenerate it with: pixi run sync-notebooks",
                file=sys.stderr,
            )
            return 1

    print("Notebook sync check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
