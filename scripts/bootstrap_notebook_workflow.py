from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements-dev.txt"


def ensure_python_package(package_name: str) -> None:
    if importlib.util.find_spec(package_name) is not None:
        return

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)])


def main() -> int:
    ensure_python_package("jupytext")
    ensure_python_package("pre_commit")

    print("Notebook workflow bootstrap is ready.")
    print("Next: run 'pre-commit install' once, then use 'pixi run sync-notebooks' after editing notebooks/source/*.ipynb.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
