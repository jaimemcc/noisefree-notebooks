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
import re
from pathlib import Path
from textwrap import dedent


DEFAULT_PYTHON_SPEC = "3.11.*"
PYTHON_SPEC_ALLOWED_PATTERN = re.compile(r"^[0-9A-Za-z.*<>=!,|^~+\-]+$")


def write_text_file(path: Path, content: str, *, on_existing: str, dry_run: bool) -> str:
    """Write file content with configurable behavior for existing files."""
    existed_before = path.exists()

    if existed_before:
        if on_existing == "skip":
            return "skipped"
        if on_existing == "fail":
            raise FileExistsError(f"Refusing to overwrite existing file: {path}")

    if dry_run:
        return "would-overwrite" if existed_before else "would-create"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "overwritten" if existed_before else "created"


def report_write(path: Path, status: str) -> None:
    labels = {
        "created": "✓ Created",
        "overwritten": "✓ Updated",
        "skipped": "• Skipped existing",
        "would-create": "• Dry run would create",
        "would-overwrite": "• Dry run would update",
    }
    print(f"{labels.get(status, '•')} {path}")


def infer_existing_pixi_python(root: Path) -> str | None:
    """Read existing [tool.pixi.dependencies].python pin from pyproject.toml if present."""
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    in_pixi_dependencies = False
    for raw_line in pyproject_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            in_pixi_dependencies = line == "[tool.pixi.dependencies]"
            continue

        if in_pixi_dependencies and line.startswith("python"):
            match = re.match(r'python\s*=\s*["\']([^"\']+)["\']', line)
            if match:
                return match.group(1)
    return None


def validate_python_spec(python_spec: str) -> str:
    """Validate a Pixi-compatible Python version spec and normalize whitespace."""
    normalized = python_spec.strip()
    if not normalized:
        raise ValueError(
            "Invalid Python version spec: value is empty. Use examples like '3.11.*', '3.12.*', or '>=3.11,<3.13'."
        )

    if any(ch.isspace() for ch in normalized):
        raise ValueError(
            "Invalid Python version spec: whitespace is not allowed. Use examples like '3.11.*' or '>=3.11,<3.13'."
        )

    if not PYTHON_SPEC_ALLOWED_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Invalid Python version spec: contains unsupported characters. "
            "Use examples like '3.11.*', '3.12.*', or '>=3.11,<3.13'."
        )

    if not any(ch.isdigit() for ch in normalized):
        raise ValueError(
            "Invalid Python version spec: must contain at least one digit. "
            "Use examples like '3.11.*' or '>=3.11,<3.13'."
        )

    return normalized


def resolve_python_spec(root: Path, requested_python_spec: str | None) -> tuple[str, str]:
    """Choose python spec from CLI, existing pyproject, or default."""
    if requested_python_spec:
        return validate_python_spec(requested_python_spec), "--python-version"

    existing_python_spec = infer_existing_pixi_python(root)
    if existing_python_spec:
        return validate_python_spec(existing_python_spec), "existing pyproject.toml"

    return validate_python_spec(DEFAULT_PYTHON_SPEC), "default"


def create_pyproject_toml(
    root: Path,
    notebook_dir: str,
    tracked_dir: str,
    python_spec: str,
    *,
    on_existing: str,
    dry_run: bool,
) -> None:
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
check-notebook-policy = "python tooling/notebook_workflow/check_notebook_policy.py"
check-notebook-sync = "python tooling/notebook_workflow/check_notebook_sync.py"
check-notebooks = {{ depends-on = ["check-notebook-policy", "check-notebook-sync"] }}
sync-notebooks = "python tooling/notebook_workflow/sync_notebooks.py"
regenerate-notebooks = "python tooling/notebook_workflow/regenerate_notebooks.py"
untrack-managed-notebooks = "python tooling/notebook_workflow/untrack_managed_notebooks.py --apply --yes"
preview-untrack-managed-notebooks = "python tooling/notebook_workflow/untrack_managed_notebooks.py"
migrate-existing-notebooks-preview = "python tooling/notebook_workflow/migrate_existing_notebooks.py"
migrate-existing-notebooks = "python tooling/notebook_workflow/migrate_existing_notebooks.py --apply-untrack --yes"
# Aliases for convenience
sync = {{ depends-on = ["sync-notebooks"] }}
regen = {{ depends-on = ["regenerate-notebooks"] }}
check = {{ depends-on = ["check-notebooks"] }}

[tool.pixi.dependencies]
python = "{python_spec}"
'''
    target = root / "pyproject.toml"
    status = write_text_file(target, content, on_existing=on_existing, dry_run=dry_run)
    report_write(target, status)


def create_gitignore(root: Path, notebook_dir: str, *, on_existing: str, dry_run: bool) -> None:
    """Generate .gitignore that ignores .ipynb but tracks .py."""
    content = f'''\
{notebook_dir}/*.ipynb
.pytest_cache/
.ruff_cache/
# pixi environments
.pixi/*
!.pixi/config.toml
'''
    target = root / ".gitignore"
    status = write_text_file(target, content, on_existing=on_existing, dry_run=dry_run)
    report_write(target, status)


def create_precommit_config(root: Path, *, on_existing: str, dry_run: bool) -> None:
    """Generate .pre-commit-config.yaml with Pixi-routed hooks."""
    content = '''\
repos:
  - repo: local
    hooks:
      - id: notebook-policy
        name: notebook-policy
        entry: pixi run python tooling/notebook_workflow/check_notebook_policy.py --staged
        language: system
        pass_filenames: false
      - id: notebook-sync
        name: notebook-sync
        entry: pixi run python tooling/notebook_workflow/check_notebook_sync.py
        language: system
        pass_filenames: false
'''
    target = root / ".pre-commit-config.yaml"
    status = write_text_file(target, content, on_existing=on_existing, dry_run=dry_run)
    report_write(target, status)


def create_github_workflow(root: Path, *, on_existing: str, dry_run: bool) -> None:
    """Generate GitHub Actions workflow for CI."""
    workflow_dir = root / ".github" / "workflows"
    if not dry_run:
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
    target = workflow_dir / "notebook-policy.yml"
    status = write_text_file(target, content, on_existing=on_existing, dry_run=dry_run)
    report_write(target, status)


def create_scripts(root: Path, notebook_dir: str, tracked_dir: str, *, on_existing: str, dry_run: bool) -> None:
    """Generate workflow scripts with proper path configuration."""
    scripts_dir = root / "tooling" / "notebook_workflow"
    if not dry_run:
        scripts_dir.mkdir(parents=True, exist_ok=True)

    # Script 1: sync_notebooks.py
    sync_script = f'''\
from __future__ import annotations

from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = ROOT / "{notebook_dir}"
TRACKED_NOTEBOOK_DIR = ROOT / "{notebook_dir}" / "{tracked_dir}"


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
    sync_target = scripts_dir / "sync_notebooks.py"
    sync_status = write_text_file(sync_target, sync_script, on_existing=on_existing, dry_run=dry_run)
    report_write(sync_target, sync_status)

    # Script 2: check_notebook_sync.py
    check_sync_script = f'''\
from __future__ import annotations

import sys
from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = ROOT / "{notebook_dir}"
TRACKED_NOTEBOOK_DIR = ROOT / "{notebook_dir}" / "{tracked_dir}"


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
    check_sync_target = scripts_dir / "check_notebook_sync.py"
    check_sync_status = write_text_file(check_sync_target, check_sync_script, on_existing=on_existing, dry_run=dry_run)
    report_write(check_sync_target, check_sync_status)

    # Script 3: regenerate_notebooks.py
    regen_script = f'''\
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import jupytext


ROOT = Path(__file__).resolve().parents[2]
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
    regen_target = scripts_dir / "regenerate_notebooks.py"
    regen_status = write_text_file(regen_target, regen_script, on_existing=on_existing, dry_run=dry_run)
    report_write(regen_target, regen_status)

    # Script 4: check_notebook_policy.py
    policy_script = f'''\
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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
    policy_target = scripts_dir / "check_notebook_policy.py"
    policy_status = write_text_file(policy_target, policy_script, on_existing=on_existing, dry_run=dry_run)
    report_write(policy_target, policy_status)

    untrack_script = f'''\
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANAGED_NOTEBOOK_DIR = ROOT / "{notebook_dir}"


def tracked_managed_notebooks() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    tracked: list[str] = []
    for line in completed.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        candidate = ROOT / path
        if candidate.suffix.lower() == ".ipynb" and MANAGED_NOTEBOOK_DIR in candidate.parents:
            tracked.append(path)
    return sorted(tracked)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List or untrack managed .ipynb files currently tracked by git.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Run git rm --cached on matched files. Without this flag, only preview changes.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required with --apply to confirm untracking changes in git index.",
    )
    args = parser.parse_args(argv)

    tracked = tracked_managed_notebooks()
    if not tracked:
        print("No tracked managed .ipynb files found.")
        return 0

    print("Managed .ipynb files currently tracked by git:")
    for path in tracked:
        print(f"  - {{path}}")
    print(f"\\nTotal tracked managed notebooks: {{len(tracked)}}")

    if not args.apply:
        print("\nPreview mode only. Re-run with --apply to untrack these files.")
        return 0

    if not args.yes:
        print("\\nRefusing to apply without explicit confirmation.", file=sys.stderr)
        print("Re-run with: --apply --yes", file=sys.stderr)
        return 2

    command = ["git", "rm", "--cached", "--", *tracked]
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        print("Failed to untrack one or more files.", file=sys.stderr)
        return completed.returncode

    print("\nUntracked managed .ipynb files from git index.")
    print("Run 'pixi run sync' and commit the updated tracked .py files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    untrack_target = scripts_dir / "untrack_managed_notebooks.py"
    untrack_status = write_text_file(untrack_target, untrack_script, on_existing=on_existing, dry_run=dry_run)
    report_write(untrack_target, untrack_status)

    migrate_script = '''\
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from untrack_managed_notebooks import tracked_managed_notebooks


ROOT = Path(__file__).resolve().parents[2]


def run_step(command: list[str], *, step_name: str) -> int:
    print(f"\\n[{step_name}] {' '.join(command)}")
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        print(f"Step failed: {step_name}", file=sys.stderr)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate existing repositories to the notebook text-first workflow: "
            "preview/untrack tracked managed .ipynb files, then sync and validate."
        ),
    )
    parser.add_argument(
        "--apply-untrack",
        action="store_true",
        help="Apply git rm --cached to tracked managed .ipynb files. Without this flag, preview only.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required with --apply-untrack to confirm index changes.",
    )
    args = parser.parse_args(argv)

    tracked = tracked_managed_notebooks()
    if tracked:
        print("Managed .ipynb files currently tracked by git:")
        for path in tracked:
            print(f"  - {path}")
        print(f"\\nTotal tracked managed notebooks: {len(tracked)}")

        if not args.apply_untrack:
            print("\\nPreview mode only. Re-run with --apply-untrack --yes to untrack these files.")
            return 0

        if not args.yes:
            print("\\nRefusing to apply without explicit confirmation.", file=sys.stderr)
            print("Re-run with: --apply-untrack --yes", file=sys.stderr)
            return 2

        untrack_rc = run_step(
            [sys.executable, "tooling/notebook_workflow/untrack_managed_notebooks.py", "--apply", "--yes"],
            step_name="untrack",
        )
        if untrack_rc != 0:
            return untrack_rc
    else:
        print("No tracked managed .ipynb files found.")

    sync_rc = run_step([sys.executable, "tooling/notebook_workflow/sync_notebooks.py"], step_name="sync")
    if sync_rc != 0:
        return sync_rc

    check_sync_rc = run_step([sys.executable, "tooling/notebook_workflow/check_notebook_sync.py"], step_name="check-sync")
    if check_sync_rc != 0:
        return check_sync_rc

    check_policy_rc = run_step([sys.executable, "tooling/notebook_workflow/check_notebook_policy.py"], step_name="check-policy")
    if check_policy_rc != 0:
        return check_policy_rc

    print("\\nMigration checks passed.")
    print("Next: review git status, then commit the staged/untracked changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    migrate_target = scripts_dir / "migrate_existing_notebooks.py"
    migrate_status = write_text_file(migrate_target, migrate_script, on_existing=on_existing, dry_run=dry_run)
    report_write(migrate_target, migrate_status)

    print("✓ Script generation completed in tooling/notebook_workflow/")


def create_directories(root: Path, notebook_dir: str, tracked_dir: str, *, dry_run: bool) -> None:
    """Create the notebook directory structure."""
    notebook_path = root / notebook_dir
    tracked_path = root / notebook_dir / tracked_dir

    if dry_run:
        print(f"• Dry run would ensure directory: {notebook_path}")
        print(f"• Dry run would ensure directory: {tracked_path}")
        return

    tracked_path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Ensured directory structure: {notebook_dir}/ and {notebook_dir}/{tracked_dir}/")


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
    parser.add_argument(
        "--python-version",
        help=(
            "Python version/spec for [tool.pixi.dependencies].python "
            f"(example: 3.11.*). Defaults to existing pyproject pin when present, otherwise {DEFAULT_PYTHON_SPEC}."
        ),
    )
    parser.add_argument(
        "--on-existing",
        choices=["skip", "overwrite", "fail"],
        default="skip",
        help="How to handle existing generated files (default: skip)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files or running pixi commands",
    )
    args = parser.parse_args(argv)

    root = Path.cwd()
    try:
        python_spec, python_spec_source = resolve_python_spec(root, args.python_version)
    except ValueError as exc:
        print(f"⚠️  {exc}", file=sys.stderr)
        return 2

    print("\n📋 Setting up notebook workflow...")
    print(f"   Notebook directory: {args.notebook_dir}/")
    print(f"   Tracked directory: {args.notebook_dir}/{args.tracked_dir}/\n")
    print(f"   Pixi Python: {python_spec} (from {python_spec_source})\n")

    # Create configuration files
    create_directories(root, args.notebook_dir, args.tracked_dir, dry_run=args.dry_run)

    try:
        create_pyproject_toml(
            root,
            args.notebook_dir,
            args.tracked_dir,
            python_spec,
            on_existing=args.on_existing,
            dry_run=args.dry_run,
        )
        create_gitignore(root, args.notebook_dir, on_existing=args.on_existing, dry_run=args.dry_run)
        create_precommit_config(root, on_existing=args.on_existing, dry_run=args.dry_run)
        create_github_workflow(root, on_existing=args.on_existing, dry_run=args.dry_run)
        create_scripts(
            root,
            args.notebook_dir,
            args.tracked_dir,
            on_existing=args.on_existing,
            dry_run=args.dry_run,
        )
    except FileExistsError as exc:
        print(f"⚠️  {exc}", file=sys.stderr)
        print("Use --on-existing overwrite to replace managed files, or --on-existing skip to keep them.", file=sys.stderr)
        return 1

    print("\n✅ Setup complete!\n")

    # Install and bootstrap
    if args.dry_run:
        print("Dry run complete. No files were changed and no commands were executed.")
    elif not args.skip_pixi:
        print("🔧 Installing Pixi environment...")
        try:
            result = subprocess.run(["pixi", "install"], cwd=root)
        except FileNotFoundError:
            print("⚠️  Pixi executable was not found on PATH.", file=sys.stderr)
            print("Install Pixi from https://pixi.sh, then run 'pixi install' and 'pixi run bootstrap'.", file=sys.stderr)
            return 1

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
    print(f"  3. If migrating existing repos: pixi run preview-untrack-managed-notebooks")
    print(f"  4. Or run full migration: pixi run migrate-existing-notebooks")
    print(f"  5. Commit: git add {args.notebook_dir}/{args.tracked_dir}/")
    print("  6. For more info, see README.md")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
