from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def tracked_text_notebooks() -> list[Path]:
    notebooks_root = ROOT / "notebooks"
    return sorted(path for path in notebooks_root.rglob("*.py") if path.is_file())


def main() -> int:
    notebooks = tracked_text_notebooks()
    if not notebooks:
        print("No tracked text notebooks found under notebooks/.")
        return 0

    for notebook in notebooks:
        subprocess.run(["jupytext", "--sync", str(notebook)], cwd=ROOT, check=True)

    print("Notebook sync complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
