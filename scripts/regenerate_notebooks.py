from __future__ import annotations

import argparse
import sys
from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[1]
SOURCE_NOTEBOOK_DIR = ROOT / "notebooks" / "source"
TRACKED_NOTEBOOK_DIR = ROOT / "notebooks" / "text"


def tracked_notebooks() -> list[Path]:
    return sorted(path for path in TRACKED_NOTEBOOK_DIR.rglob("*.py") if path.is_file())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate source .ipynb notebooks from tracked .py files.")
    parser.add_argument(
        "notebook",
        nargs="?",
        help="Specific notebook to regenerate (e.g., 'starter_notebook.py'). If omitted, regenerates all notebooks.",
    )
    args = parser.parse_args(argv)

    if args.notebook:
        tracked_notebook = TRACKED_NOTEBOOK_DIR / args.notebook
        if not tracked_notebook.exists():
            print(f"Notebook not found: {tracked_notebook}", file=sys.stderr)
            return 1
        notebooks = [tracked_notebook]
    else:
        notebooks = tracked_notebooks()
        if not notebooks:
            print("No tracked notebooks found under notebooks/text/.")
            return 0

    for tracked_notebook in notebooks:
        relative_path = tracked_notebook.relative_to(TRACKED_NOTEBOOK_DIR).with_suffix(".ipynb")
        source_notebook = SOURCE_NOTEBOOK_DIR / relative_path
        source_notebook.parent.mkdir(parents=True, exist_ok=True)

        notebook_object = jupytext.read(tracked_notebook, fmt="py:percent")
        jupytext.write(notebook_object, source_notebook, fmt="ipynb")

    print("Notebook regeneration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
