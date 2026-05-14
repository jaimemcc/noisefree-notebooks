# Setting up a notebook-first Pixi workflow

This document describes two scenarios:
1. Setting up the notebook workflow in a **new fresh repository**
2. Adding the notebook workflow to an **existing repository**

## Quick Start: Automated Setup (Recommended)

The fastest way to set up the workflow is using the automated setup script:

```powershell
# Copy setup_notebook_workflow.py to your repo, then run:
python setup_notebook_workflow.py

# Or with custom directories:
python setup_notebook_workflow.py --notebook-dir analysis --tracked-dir .tracked
```

This script automatically creates:
- ✅ Directory structure
- ✅ All config files (pyproject.toml, .gitignore, .pre-commit-config.yaml)
- ✅ All scripts (sync, check, regen, bootstrap)
- ✅ GitHub Actions workflow
- ✅ Runs `pixi install` and `pixi run bootstrap`

**Then you're done.** Just create your first notebook and run `pixi run sync`.

---

## Scenario 1: Fresh Repository Setup (Manual)

If you prefer manual setup instead of using the script, follow these steps:

### Step 1: Create repository structure

```powershell
mkdir my-repo
cd my-repo
git init
```

### Step 2: Create the base files

Create these files in the root directory:

**`pyproject.toml`** — Pixi config with notebook tasks:
```toml
[tool.jupytext]
formats = "ipynb,py:percent"

[tool.pixi.workspace]
name = "my-repo"
channels = ["conda-forge"]
platforms = ["win-64"]

[tool.pixi.pypi-dependencies]
jupytext = ">=1.16"
pre-commit = ">=3.7"

[tool.pixi.tasks]
bootstrap = "pre-commit install"
check-notebook-policy = "python scripts/check_notebook_policy.py"
check-notebook-sync = "python scripts/check_notebook_sync.py"
check-notebooks = { depends-on = ["check-notebook-policy", "check-notebook-sync"] }
sync-notebooks = "python scripts/sync_notebooks.py"
regenerate-notebooks = "python scripts/regenerate_notebooks.py"
# Aliases for convenience
sync = { depends-on = ["sync-notebooks"] }
regen = { depends-on = ["regenerate-notebooks"] }
check = { depends-on = ["check-notebooks"] }
```

**`.gitignore`**:
```
notebooks/*.ipynb
.pytest_cache/
.ruff_cache/
# pixi environments
.pixi/*
!.pixi/config.toml
```

⚠️ **Important**: Only ignore `.ipynb` files, NOT `notebooks/text/`. The `.py` files in `notebooks/text/` must be tracked in git.
```

**`.pre-commit-config.yaml`**:
```yaml
repos:
  - repo: local
    hooks:
      - id: notebook-policy
        name: notebook-policy
        entry: pixi run python scripts/check_notebook_policy.py --staged
        language: system
        pass_filenames: false
      - id: notebook-sync
        name: notebook-sync
        entry: pixi run python scripts/check_notebook_sync.py
        language: system
        pass_filenames: false
```

**`.github/workflows/notebook-policy.yml`** (if using GitHub):
```yaml
name: notebook-policy

on:
  pull_request:
  push:
    branches:
      - main
      - master

jobs:
  policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: prefix-dev/setup-pixi@v0
        with:
          cache: true

      - name: Install notebook tooling
        run: pixi install --locked

      - name: Check notebook workflow
        run: pixi run check-notebooks
```

### Step 3: Create scripts directory and add check/sync scripts

Create `scripts/` directory and add these files:

**`scripts/bootstrap_notebook_workflow.py`**:
```python
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
    print("Next: run 'pre-commit install' once, then use 'pixi run sync' after editing notebooks/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**`scripts/check_notebook_policy.py`**:
```python
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANAGED_NOTEBOOK_DIR = ROOT / "notebooks"


def git_list_files(*, staged: bool) -> list[str]:
    command = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"] if staged else ["git", "ls-files"]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def find_managed_notebook_violations(paths: list[str]) -> list[str]:
    violations: list[str] = []
    for relative_path in paths:
        candidate = ROOT / relative_path
        if candidate.suffix.lower() == ".ipynb" and MANAGED_NOTEBOOK_DIR in candidate.parents:
            violations.append(relative_path)
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check repository notebook policy.")
    parser.add_argument("--staged", action="store_true", help="Check staged files instead of tracked files.")
    args = parser.parse_args(argv)

    violations = find_managed_notebook_violations(git_list_files(staged=args.staged))
    if violations:
        print("Notebook policy violation: .ipynb files should stay in notebooks/ and not be tracked in git.", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        print(
            "Fix: keep the source notebook local, then run pixi run sync to refresh the tracked .py copy.",
            file=sys.stderr,
        )
        return 1

    print("Notebook policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**`scripts/check_notebook_sync.py`**:
```python
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
                f"Notebook sync check failed for {source_notebook.relative_to(ROOT)}. Regenerate it with: pixi run sync",
                file=sys.stderr,
            )
            return 1

        regenerated_text = jupytext.writes(jupytext.read(source_notebook), fmt="py:percent")
        current_text = target_notebook.read_text(encoding="utf-8")

        if regenerated_text != current_text:
            print(
                f"Notebook sync check failed for {source_notebook.relative_to(ROOT)}. Regenerate it with: pixi run sync",
                file=sys.stderr,
            )
            return 1

    print("Notebook sync check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**`scripts/sync_notebooks.py`**:
```python
from __future__ import annotations

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
```

**`scripts/regenerate_notebooks.py`**:
```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
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
        source_notebook = NOTEBOOK_DIR / relative_path
        source_notebook.parent.mkdir(parents=True, exist_ok=True)

        notebook_object = jupytext.read(tracked_notebook, fmt="py:percent")
        jupytext.write(notebook_object, source_notebook, fmt="ipynb")

    print("Notebook regeneration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Step 4: Initialize Pixi and bootstrap

```powershell
pixi install
pixi run bootstrap
```

### Step 5: Create your first notebook

Create `notebooks/example.ipynb` using VS Code Jupyter or any notebook editor, write some code, then sync it:

```powershell
pixi run sync
```

This creates `notebooks/text/example.py` as the tracked version.

### Step 6: Commit

```powershell
git add pyproject.toml .gitignore .pre-commit-config.yaml .github/ scripts/
git add notebooks/text/
git commit -m "initial notebook workflow setup"
```

---

## Scenario 2: Adding Notebook Workflow to Existing Repository
### Option A: Using Automated Setup (Recommended)

```powershell
# Copy setup_notebook_workflow.py to your repo root, then:
python setup_notebook_workflow.py
```

This sets up all the workflow files automatically. Then continue with Step 3 below to migrate your existing notebooks.

### Option B: Manual Setup

#### Step 1: Back up your existing notebooks (Manual)


If you already have `.ipynb` files you want to keep, back them up:

```powershell
mkdir notebooks_backup
Copy-Item notebooks/*.ipynb notebooks_backup/ -Recurse
```

#### Step 2: Add the workflow files (Manual)

Add all the files from **Scenario 1 Steps 2–3** to your repo. If you already have a `pyproject.toml`, add the `[tool.jupytext]`, `[tool.pixi.workspace]`, etc. sections to it.

Create the `scripts/` directory and add all four Python scripts.

### Step 3: Migrate Your Existing Notebooks

For each `.ipynb` file you want to keep:

1. Move it to `notebooks/<name>.ipynb`
2. Run `pixi run sync` to generate `notebooks/text/<name>.py`
3. Verify the `.py` file looks correct
4. Delete the `notebooks/<name>.ipynb` (keep only the `.py` for git tracking)
5. Or run `pixi run regen <name>.py` to restore it when you need to edit it

Example:
```powershell
Move-Item notebooks/analysis.ipynb notebooks/
pixi install
pixi run sync
# Check notebooks/text/analysis.py
Remove-Item notebooks/analysis.ipynb  # Keep only the .py tracked
```

#### Step 4: Initialize Pixi and bootstrap (Manual Setup Only)

```powershell
pixi install
pixi run bootstrap
```

### Step 5: Test the workflow

```powershell
# Regenerate a notebook to edit
pixi run regen analysis.py

# Edit it in VS Code, then sync back
pixi run sync

# Check before committing
pixi run check
```

### Step 6: Update .gitignore and commit

Make sure `.gitignore` includes `notebooks/*.ipynb` and `notebooks/text/` as shown above, then commit the new workflow files and the `notebooks/text/*.py` files.

---

## Daily Workflow

1. **Edit notebooks**: Open `notebooks/<name>.ipynb` in VS Code and edit normally.
2. **Sync before commit**: Run `pixi run sync` to update `notebooks/text/<name>.py`.
3. **Check before committing**: Run `pixi run check` to verify sync and policy.
4. **Commit**: Commit only `notebooks/text/` changes (`.ipynb` files stay local).
5. **Restore on new machine**: After cloning, run `pixi run regen` to rebuild all `.ipynb` files.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `.ipynb` files not syncing to `.py` | Run `pixi run sync` after editing |
| `.py` file changes not showing in notebook | Run `pixi run regen <notebook.py>` |
| Pre-commit hook failing | Run `pixi run check` to see the exact issue |
| Sync check fails after editing | Run `pixi run sync` to regenerate the `.py` |
| "Notebook does not appear to be JSON" | Delete the empty `.ipynb` file and regenerate it |

---

## Customizing Directory Names

The setup script makes it easy to use different directory names for your notebooks. Just pass options when running the setup:

```powershell
# Use "analysis" instead of "notebooks"
python setup_notebook_workflow.py --notebook-dir analysis

# Use ".tracked" instead of "text"
python setup_notebook_workflow.py --tracked-dir .tracked

# Combine both
python setup_notebook_workflow.py --notebook-dir analysis --tracked-dir .tracked
```

The script updates **all** configuration files and Python scripts automatically—no manual editing needed. This is much faster than trying to modify paths in multiple files.

### Supported Setup Script Options

| Option | Default | Purpose |
|--------|---------|---------|
| `--notebook-dir` | `notebooks` | Directory for source `.ipynb` files |
| `--tracked-dir` | `text` | Subdirectory within notebook-dir for tracked `.py` files |
| `--skip-pixi` | — | Skip `pixi install` and bootstrap (useful for testing/CI) |

### Example: Multi-project Setup

If you have multiple project folders with different naming conventions, the setup script adapts:

```powershell
# Project 1: use "notebooks/text"
cd project1
python ../setup_notebook_workflow.py

# Project 2: use "analysis/.tracked"
cd ../project2
python ../setup_notebook_workflow.py --notebook-dir analysis --tracked-dir .tracked
```

Each project gets properly configured files tailored to its chosen directory structure.

---

## File Structure After Setup

The setup script creates the following structure (default paths):

```
my-repo/
├── .github/workflows/
│   └── notebook-policy.yml          (GitHub Actions CI)
├── scripts/
│   ├── sync_notebooks.py            (convert .ipynb → .py)
│   ├── check_notebook_sync.py       (validate sync)
│   ├── check_notebook_policy.py     (enforce policy)
│   └── regenerate_notebooks.py      (convert .py → .ipynb)
├── notebooks/                       (configurable with --notebook-dir)
│   ├── analysis.ipynb               (local, never committed)
│   ├── exploration.ipynb            (local, never committed)
│   └── text/                        (configurable with --tracked-dir)
│       ├── analysis.py              (tracked in git)
│       └── exploration.py           (tracked in git)
├── pyproject.toml                   (Pixi + Jupytext config)
├── .gitignore                       (ignores .ipynb, tracks .py)
├── .pre-commit-config.yaml          (git hooks config)
├── setup_notebook_workflow.py       (the setup script itself)
└── README.md                        (your project docs)
```

If you used different directory names, the structure adapts accordingly:

```
my-repo/
├── analysis/                        (if --notebook-dir analysis)
│   ├── report.ipynb
│   └── .tracked/                    (if --tracked-dir .tracked)
│       └── report.py
└── ...
```

