from __future__ import annotations

import tempfile
import sys
from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"


def tracked_text_notebooks() -> list[Path]:
    return sorted(path for path in NOTEBOOK_DIR.rglob("*.py") if path.is_file())


def main() -> int:
    notebooks = tracked_text_notebooks()
    if not notebooks:
        print("Notebook sync check passed: no tracked text notebooks found.")
        return 0

    for notebook in notebooks:
        original_text = notebook.read_text(encoding="utf-8")
        notebook_object = jupytext.read(notebook, fmt="py:percent")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_ipynb = Path(temp_dir) / f"{notebook.stem}.ipynb"
            jupytext.write(notebook_object, temp_ipynb, fmt="ipynb")
            roundtrip_text = jupytext.writes(jupytext.read(temp_ipynb), fmt="py:percent")

        if roundtrip_text != original_text:
            print(
                f"Notebook sync check failed for {notebook.relative_to(ROOT)}. Regenerate it with: pixi run sync-notebooks",
                file=sys.stderr,
            )
            return 1

    print("Notebook sync check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
