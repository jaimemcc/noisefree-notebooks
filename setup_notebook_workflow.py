#!/usr/bin/env python
"""
Automated setup script for Pixi + Jupytext notebook workflow.

Usage:
    python setup_notebook_workflow.py                    # Default: notebooks/ and notebooks/text/
    python setup_notebook_workflow.py --notebook-dir notebooks --tracked-dir text
    python setup_notebook_workflow.py --notebook-dir analysis --tracked-dir .tracked
"""

from __future__ import annotations

import argparse
import sys
import subprocess
from pathlib import Path
from textwrap import dedent


def create_pyproject_toml(root: Path, notebook_dir: str, tracked_dir: str) -> None:
    """Generate pyproject.toml with Pixi and Jupytext configuration."""
    content = f'''\
[tool.jupytext]
formats = "ipynb,py:percent"

[tool.pixi.workspace]
name = "notebook-project"
channels = ["conda-forge"]
platforms = ["win-64"]

[tool.pixi.pypi-dependencies]
jupytext = ">=1.16"
pre-commit = ">=3.7"

[tool.pixi.tasks]
bootstrap = "pre-commit install"
check-notebook-policy = "python scripts/check_notebook_policy.py"
check-notebook-sync = "python scripts/check_notebook_sync.py"
check-notebooks = {{ depends-on = ["check-notebook-policy", "check-notebook-sync"] }}
sync-notebooks = "python scripts/sync_notebooks.py"
regenerate-notebooks = "python scripts/regenerate_notebooks.py"
# Aliases for convenience
sync = {{ depends-on = ["sync-notebooks"] }}
regen = {{ depends-on = ["regenerate-notebooks"] }}
check = {{ depends-on = ["check-notebooks"] }}
'''
    (root / "pyproject.toml").write_text(content)
    print("✓ Created pyproject.toml")


def create_gitignore(root: Path, notebook_dir: str) -> None:
    """Generate .gitignore that ignores .ipynb but tracks .py."""
    content = f'''\
{notebook_dir}/*.ipynb
.pytest_cache/
.ruff_cache/
# pixi environments
.pixi/*
!.pixi/config.toml
'''
    (root / ".gitignore").write_text(content)
    print("✓ Created .gitignore")


def create_precommit_config(root: Path) -> None:
    """Generate .pre-commit-config.yaml with Pixi-routed hooks."""
    content = '''\
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
'''
    (root / ".pre-commit-config.yaml").write_text(content)
    print("✓ Created .pre-commit-config.yaml")


def create_github_workflow(root: Path) -> None:
    """Generate GitHub Actions workflow for CI."""
    workflow_dir = root / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)

    content = '''\
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
'''
    (workflow_dir / "notebook-policy.yml").write_text(content)
    print("✓ Created .github/workflows/notebook-policy.yml")


def create_scripts(root: Path, notebook_dir: str, tracked_dir: str) -> None:
    """Generate all four Python scripts with proper path configuration."""
    scripts_dir = root / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # Script 1: sync_notebooks.py
    sync_script = f'''\
from __future__ import annotations

from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "{notebook_dir}"
TRACKED_NOTEBOOK_DIR = ROOT / "{notebook_dir}" / "{tracked_dir}"


def source_notebooks() -> list[Path]:
    return sorted(path for path in NOTEBOOK_DIR.glob("*.ipynb") if path.is_file())


def main() -> int:
    notebooks = source_notebooks()
    if not notebooks:
        print("No source notebooks found under {notebook_dir}/.")
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
'''
    (scripts_dir / "sync_notebooks.py").write_text(sync_script)

    # Script 2: check_notebook_sync.py
    check_sync_script = f'''\
from __future__ import annotations

import sys
from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "{notebook_dir}"
TRACKED_NOTEBOOK_DIR = ROOT / "{notebook_dir}" / "{tracked_dir}"


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
                f"Notebook sync check failed for {{source_notebook.relative_to(ROOT)}}. Regenerate it with: pixi run sync",
                file=sys.stderr,
            )
            return 1

        regenerated_text = jupytext.writes(jupytext.read(source_notebook), fmt="py:percent")
        current_text = target_notebook.read_text(encoding="utf-8")

        if regenerated_text != current_text:
            print(
                f"Notebook sync check failed for {{source_notebook.relative_to(ROOT)}}. Regenerate it with: pixi run sync",
                file=sys.stderr,
            )
            return 1

    print("Notebook sync check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    (scripts_dir / "check_notebook_sync.py").write_text(check_sync_script)

    # Script 3: regenerate_notebooks.py
    regen_script = f'''\
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "{notebook_dir}"
TRACKED_NOTEBOOK_DIR = ROOT / "{notebook_dir}" / "{tracked_dir}"


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
            print(f"Notebook not found: {{tracked_notebook}}", file=sys.stderr)
            return 1
        notebooks = [tracked_notebook]
    else:
        notebooks = tracked_notebooks()
        if not notebooks:
            print("No tracked notebooks found under {notebook_dir}/{tracked_dir}/.")
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
'''
    (scripts_dir / "regenerate_notebooks.py").write_text(regen_script)

    # Script 4: check_notebook_policy.py
    policy_script = f'''\
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANAGED_NOTEBOOK_DIR = ROOT / "{notebook_dir}"


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
        print("Notebook policy violation: .ipynb files should stay in {notebook_dir}/ and not be tracked in git.", file=sys.stderr)
        for violation in violations:
            print(f"  - {{violation}}", file=sys.stderr)
        print(
            "Fix: keep the source notebook local, then run pixi run sync to refresh the tracked .py copy.",
            file=sys.stderr,
        )
        return 1

    print("Notebook policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    (scripts_dir / "check_notebook_policy.py").write_text(policy_script)

    print("✓ Created 4 scripts in scripts/")


def create_directories(root: Path, notebook_dir: str, tracked_dir: str) -> None:
    """Create the notebook directory structure."""
    (root / notebook_dir / tracked_dir).mkdir(parents=True, exist_ok=True)
    print(f"✓ Created directory structure: {notebook_dir}/ and {notebook_dir}/{tracked_dir}/")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Set up Pixi + Jupytext notebook workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
            Examples:
              python setup_notebook_workflow.py
              python setup_notebook_workflow.py --notebook-dir analysis --tracked-dir .tracked
        """),
    )
    parser.add_argument(
        "--notebook-dir",
        default="notebooks",
        help="Directory for source .ipynb files (default: notebooks)",
    )
    parser.add_argument(
        "--tracked-dir",
        default="text",
        help="Subdirectory within notebook-dir for tracked .py files (default: text)",
    )
    parser.add_argument(
        "--skip-pixi",
        action="store_true",
        help="Skip pixi install and bootstrap (useful for testing)",
    )
    args = parser.parse_args(argv)

    root = Path.cwd()

    print("\n📋 Setting up notebook workflow...")
    print(f"   Notebook directory: {args.notebook_dir}/")
    print(f"   Tracked directory: {args.notebook_dir}/{args.tracked_dir}/\n")

    # Create configuration files
    create_directories(root, args.notebook_dir, args.tracked_dir)
    create_pyproject_toml(root, args.notebook_dir, args.tracked_dir)
    create_gitignore(root, args.notebook_dir)
    create_precommit_config(root)
    create_github_workflow(root)
    create_scripts(root, args.notebook_dir, args.tracked_dir)

    print("\n✅ Setup complete!\n")

    # Install and bootstrap
    if not args.skip_pixi:
        print("🔧 Installing Pixi environment...")
        result = subprocess.run(["pixi", "install"], cwd=root)
        if result.returncode != 0:
            print("⚠️  pixi install failed. Install Pixi from https://pixi.sh and try again.", file=sys.stderr)
            return 1

        print("\n🚀 Bootstrapping pre-commit hooks...")
        result = subprocess.run(["pixi", "run", "bootstrap"], cwd=root)
        if result.returncode != 0:
            print("⚠️  bootstrap failed. Run 'pixi run bootstrap' manually.", file=sys.stderr)
            return 1

    print("\n" + "=" * 60)
    print("🎉 Notebook workflow is ready!\n")
    print("Next steps:")
    print(f"  1. Create your first notebook in {args.notebook_dir}/<name>.ipynb")
    print(f"  2. Run: pixi run sync")
    print(f"  3. Commit: git add {args.notebook_dir}/{args.tracked_dir}/")
    print("  4. For more info, see SETUP_INSTRUCTIONS.md or NOTEBOOK_WORKFLOW.md")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
