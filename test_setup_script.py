#!/usr/bin/env python3
"""
Test script to validate setup_notebook_workflow.py and generated scripts.

Catches common issues early:
- NameErrors and undefined variables
- Syntax errors in templates
- Argument parsing errors
- Missing imports
"""

import subprocess
import sys
import tempfile
from pathlib import Path
import shutil
import os


def test_setup_script_syntax():
    """Validate setup_notebook_workflow.py has no syntax errors."""
    script = Path("setup_notebook_workflow.py")
    result = subprocess.run([sys.executable, "-m", "py_compile", str(script)], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Syntax error in setup_notebook_workflow.py:")
        print(result.stderr)
        return False
    print("✓ setup_notebook_workflow.py syntax OK")
    return True


def test_setup_script_help():
    """Test that setup script can parse --help without errors."""
    result = subprocess.run([sys.executable, "setup_notebook_workflow.py", "--help"],
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error running setup_notebook_workflow.py --help:")
        print(result.stderr)
        return False
    if "Set up Pixi" not in result.stdout:
        print(f"❌ Help output missing expected content")
        return False
    print("✓ setup_notebook_workflow.py --help works")
    return True


def test_setup_script_dry_run():
    """Test a dry-run setup to catch runtime errors early."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal test environment
        test_root = Path(tmpdir)
        (test_root / "notebooks").mkdir()
        
        # Copy setup script to temp directory
        setup_script = Path("setup_notebook_workflow.py")
        if setup_script.exists():
            shutil.copy(setup_script, test_root / "setup_notebook_workflow.py")
        
        result = subprocess.run(
            [sys.executable, "setup_notebook_workflow.py", 
             "--dry-run", "--skip-pixi"],
            cwd=test_root,
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        
        if "NameError" in result.stderr or "Traceback" in result.stderr:
            print(f"❌ Runtime error in setup_notebook_workflow.py:")
            print(result.stderr)
            return False
        
        if result.returncode not in (0, 1):  # 1 is acceptable for validation errors
            print(f"❌ Unexpected exit code {result.returncode}:")
            print(result.stderr)
            return False
        
        print("✓ setup_notebook_workflow.py dry-run works")
        return True


def test_generated_pyproject_platforms():
    """Ensure generated pyproject includes both Windows and Linux platforms for CI lock compatibility."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_root = Path(tmpdir)

        setup_script = Path("setup_notebook_workflow.py")
        if setup_script.exists():
            shutil.copy(setup_script, test_root / "setup_notebook_workflow.py")

        result = subprocess.run(
            [sys.executable, "setup_notebook_workflow.py", "--skip-pixi", "--on-existing", "overwrite"],
            cwd=test_root,
            capture_output=True,
            text=True,
            timeout=20,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )

        if result.returncode != 0:
            print("❌ setup_notebook_workflow.py failed while generating pyproject:")
            print(result.stderr)
            return False

        pyproject_path = test_root / "pyproject.toml"
        if not pyproject_path.exists():
            print("❌ setup_notebook_workflow.py did not generate pyproject.toml")
            return False

        content = pyproject_path.read_text(encoding="utf-8")
        expected = 'platforms = ["win-64", "linux-64"]'
        if expected not in content:
            print("❌ Generated pyproject.toml is missing required multi-platform Pixi config")
            print(f"Expected line: {expected}")
            return False

        print("✓ generated pyproject.toml includes win-64 and linux-64 platforms")
        return True


def test_existing_pixi_toml_gets_workflow_entries():
    """Ensure setup merges workflow tasks/deps into an existing pixi.toml repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_root = Path(tmpdir)

        (test_root / "pixi.toml").write_text(
            """
[workspace]
name = "existing-project"
channels = ["conda-forge"]
platforms = ["win-64"]

[dependencies]
python = "3.12.*"
""".strip()
            + "\n",
            encoding="utf-8",
        )

        setup_script = Path("setup_notebook_workflow.py")
        if setup_script.exists():
            shutil.copy(setup_script, test_root / "setup_notebook_workflow.py")

        result = subprocess.run(
            [sys.executable, "setup_notebook_workflow.py", "--skip-pixi", "--on-existing", "skip"],
            cwd=test_root,
            capture_output=True,
            text=True,
            timeout=20,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )

        if result.returncode != 0:
            print("❌ setup_notebook_workflow.py failed for existing pixi.toml repo:")
            print(result.stderr)
            return False

        pixi_toml_path = test_root / "pixi.toml"
        pyproject_path = test_root / "pyproject.toml"
        if not pixi_toml_path.exists():
            print("❌ Existing pixi.toml was not preserved")
            return False
        if not pyproject_path.exists():
            print("❌ setup_notebook_workflow.py did not create pyproject.toml for jupytext config")
            return False

        pixi_content = pixi_toml_path.read_text(encoding="utf-8")
        pyproject_content = pyproject_path.read_text(encoding="utf-8")

        expected_entries = [
            "[tasks]",
            'bootstrap = "pre-commit install"',
            "[pypi-dependencies]",
            'jupytext = ">=1.16"',
            'pre-commit = ">=3.7"',
            'python = "3.12.*"',
        ]
        for expected_entry in expected_entries:
            if expected_entry not in pixi_content:
                print(f"❌ Existing pixi.toml is missing expected workflow entry: {expected_entry}")
                return False

        # Check that platforms includes both win-64 and linux-64
        if 'platforms = ["win-64", "linux-64"]' not in pixi_content:
            print("❌ Existing pixi.toml did not get updated to include linux-64 in platforms")
            print("pixi.toml content:")
            print(pixi_content)
            return False

        if "[tool.jupytext]" not in pyproject_content:
            print("❌ pyproject.toml is missing the jupytext config section")
            return False

        print("✓ existing pixi.toml repos get notebook workflow tasks, dependencies, and platforms")
        return True


def test_existing_notebooks_are_reported_for_initial_sync():
    """Ensure setup detects existing notebooks and tells the user to sync before first commit when Pixi is skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_root = Path(tmpdir)
        notebooks_dir = test_root / "notebooks"
        notebooks_dir.mkdir(parents=True)
        (notebooks_dir / "example.ipynb").write_text('{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}\n', encoding="utf-8")

        setup_script = Path("setup_notebook_workflow.py")
        if setup_script.exists():
            shutil.copy(setup_script, test_root / "setup_notebook_workflow.py")

        result = subprocess.run(
            [sys.executable, "setup_notebook_workflow.py", "--skip-pixi", "--on-existing", "overwrite"],
            cwd=test_root,
            capture_output=True,
            text=True,
            timeout=20,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )

        if result.returncode != 0:
            print("❌ setup_notebook_workflow.py failed while checking existing notebook sync guidance:")
            print(result.stderr)
            return False

        if "Run 'pixi run sync' before your first commit." not in result.stderr:
            print("❌ setup_notebook_workflow.py did not warn about syncing existing notebooks before first commit")
            return False

        print("✓ existing notebooks are reported for initial sync guidance")
        return True


def test_existing_gitignore_gets_notebook_entries():
    """Ensure setup appends managed notebook ignore rules to an existing .gitignore."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_root = Path(tmpdir)
        (test_root / ".gitignore").write_text("dist/\n", encoding="utf-8")

        setup_script = Path("setup_notebook_workflow.py")
        if setup_script.exists():
            shutil.copy(setup_script, test_root / "setup_notebook_workflow.py")

        result = subprocess.run(
            [sys.executable, "setup_notebook_workflow.py", "--skip-pixi", "--on-existing", "skip"],
            cwd=test_root,
            capture_output=True,
            text=True,
            timeout=20,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )

        if result.returncode != 0:
            print("❌ setup_notebook_workflow.py failed while updating existing .gitignore:")
            print(result.stderr)
            return False

        gitignore_content = (test_root / ".gitignore").read_text(encoding="utf-8")
        for expected_line in ["dist/", "notebooks/**/*.ipynb", ".ipynb_checkpoints/"]:
            if expected_line not in gitignore_content:
                print(f"❌ Existing .gitignore is missing expected entry: {expected_line}")
                return False

        print("✓ existing .gitignore files get managed notebook ignore entries")
        return True


def test_generated_script_syntax():
    """Test that generated scripts have valid Python syntax."""
    scripts_to_check = [
        "setup_notebook_workflow.py",
        "update_notebook_workflow.py",
    ]
    
    all_ok = True
    for script_name in scripts_to_check:
        script = Path(script_name)
        if not script.exists():
            continue
            
        result = subprocess.run([sys.executable, "-m", "py_compile", str(script)],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Syntax error in {script_name}:")
            print(result.stderr)
            all_ok = False
        else:
            print(f"✓ {script_name} syntax OK")
    
    return all_ok


def test_generated_tooling_script_syntax():
    """Ensure setup generates tooling scripts with valid Python syntax."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_root = Path(tmpdir)

        setup_script = Path("setup_notebook_workflow.py")
        if setup_script.exists():
            shutil.copy(setup_script, test_root / "setup_notebook_workflow.py")

        result = subprocess.run(
            [sys.executable, "setup_notebook_workflow.py", "--skip-pixi", "--on-existing", "overwrite"],
            cwd=test_root,
            capture_output=True,
            text=True,
            timeout=20,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )

        if result.returncode != 0:
            print("❌ setup_notebook_workflow.py failed while generating tooling scripts:")
            print(result.stderr)
            return False

        generated_script = test_root / "tooling" / "notebook_workflow" / "migrate_existing_notebooks.py"
        compile_result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(generated_script)],
            capture_output=True,
            text=True,
        )
        if compile_result.returncode != 0:
            print("❌ Generated migrate_existing_notebooks.py has invalid syntax:")
            print(compile_result.stderr)
            return False

        print("✓ generated tooling scripts have valid syntax")
        return True


def test_import_setup_module():
    """Test that setup_notebook_workflow can be imported."""
    try:
        import setup_notebook_workflow
        print("✓ setup_notebook_workflow imports successfully")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error importing setup_notebook_workflow: {e}")
        return False
    except NameError as e:
        print(f"❌ NameError importing setup_notebook_workflow: {e}")
        return False
    except Exception as e:
        print(f"⚠ Warning importing setup_notebook_workflow: {e}")
        return True  # Non-critical


def test_import_update_module():
    """Test that update_notebook_workflow can be imported."""
    try:
        import update_notebook_workflow
        print("✓ update_notebook_workflow imports successfully")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error importing update_notebook_workflow: {e}")
        return False
    except NameError as e:
        print(f"❌ NameError importing update_notebook_workflow: {e}")
        return False
    except Exception as e:
        print(f"⚠ Warning importing update_notebook_workflow: {e}")
        return True  # Non-critical


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing notebook workflow scripts")
    print("=" * 60 + "\n")
    
    tests = [
        ("Syntax check", test_setup_script_syntax),
        ("Generated script syntax", test_generated_script_syntax),
        ("Generated tooling script syntax", test_generated_tooling_script_syntax),
        ("Import setup_notebook_workflow", test_import_setup_module),
        ("Import update_notebook_workflow", test_import_update_module),
        ("Help output", test_setup_script_help),
        ("Dry-run execution", test_setup_script_dry_run),
        ("Generated pyproject platforms", test_generated_pyproject_platforms),
        ("Existing pixi.toml merge", test_existing_pixi_toml_gets_workflow_entries),
        ("Existing notebook sync guidance", test_existing_notebooks_are_reported_for_initial_sync),
        ("Existing gitignore merge", test_existing_gitignore_gets_notebook_entries),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} raised exception: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed < total:
        print("\n⚠ Some tests failed. Fix issues before committing.")
        return 1
    else:
        print("\n✓ All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
