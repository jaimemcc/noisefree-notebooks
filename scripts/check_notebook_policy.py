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
        print("Notebook policy violation: generated .ipynb files are not tracked in managed notebook paths.", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        print(
            "Fix: regenerate the paired text notebook, or remove the staged/generated .ipynb file from notebooks/.",
            file=sys.stderr,
        )
        return 1

    print("Notebook policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
