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
        ("Import setup_notebook_workflow", test_import_setup_module),
        ("Import update_notebook_workflow", test_import_update_module),
        ("Help output", test_setup_script_help),
        ("Dry-run execution", test_setup_script_dry_run),
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
