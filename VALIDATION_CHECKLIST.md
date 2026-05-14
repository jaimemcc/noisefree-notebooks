# Notebook Workflow Validation Checklist

This document tracks validation of the notebook workflow system. Run these checks in order.

---

## Validation 1: Fresh Clone & Bootstrap

**Objective**: Verify that a fresh clone can set up the environment and restore notebooks.

**Steps**:

1. Archive the current repo temporarily:
   ```powershell
   Move-Item . ../nbtest_backup -Force
   ```

2. Create a fresh clone simulation:
   ```powershell
   mkdir ../nbtest_fresh
   cd ../nbtest_fresh
   git clone ../nbtest_backup .
   ```

3. Bootstrap the environment:
   ```powershell
   pixi install
   pixi run bootstrap
   ```

4. Regenerate notebooks:
   ```powershell
   pixi run regen
   ```

5. Verify notebooks exist:
   ```powershell
   Get-ChildItem notebooks/*.ipynb
   ```

6. Execute the notebook (if runnable) and check outputs:
   ```powershell
   # Run with Jupyter:
   # jupyter execute notebooks/starter_notebook.ipynb
   ```

7. Check git status — should show clean (no changes):
   ```powershell
   git status
   ```

**Expected outcome**: ✅ Fresh clone succeeds, notebooks regenerate cleanly, git status is clean.

**Actual outcome**: _[To be filled in after running]_

---

## Validation 2: Cell Edit & Sync

**Objective**: Verify that editing a source notebook cell shows only changes in the `.py` file.

**Steps**:

1. Edit `notebooks/starter_notebook.ipynb` — modify a code cell:
   ```python
   # Change from:
   message = "Notebook workflow is ready."
   # To:
   message = "Notebook workflow is working perfectly."
   ```

2. Save the notebook (Ctrl+S).

3. Run sync:
   ```powershell
   pixi run sync
   ```

4. Check git diff on the `.py` file:
   ```powershell
   git diff notebooks/text/starter_notebook.py
   ```

5. Verify **only the modified cell appears** in the diff, not the entire file or output:
   ```
   - message = "Notebook workflow is ready."
   + message = "Notebook workflow is working perfectly."
   ```

6. Check git diff on the `.ipynb` file:
   ```powershell
   git diff notebooks/starter_notebook.ipynb
   ```
   Should return empty (`.ipynb` not tracked).

**Expected outcome**: ✅ Git diff shows only cell changes in `.py`, no `.ipynb` changes.

**Actual outcome**: _[To be filled in after running]_

---

## Validation 3: Delete & Regenerate

**Objective**: Verify recovery by deleting the local `.ipynb` and regenerating from `.py`.

**Steps**:

1. Delete the local notebook:
   ```powershell
   Remove-Item notebooks/starter_notebook.ipynb
   ```

2. Verify it's gone:
   ```powershell
   Get-ChildItem notebooks/starter_notebook.ipynb -ErrorAction SilentlyContinue
   # Should return nothing
   ```

3. Regenerate from `.py`:
   ```powershell
   pixi run regen starter_notebook.py
   ```

4. Verify it was restored:
   ```powershell
   Get-Item notebooks/starter_notebook.ipynb
   ```

5. Compare the restored notebook to the original:
   ```powershell
   pixi run check
   ```
   Should pass (sync is clean).

6. Open the notebook in VS Code and verify the edited cell is there with the new message.

**Expected outcome**: ✅ `.ipynb` successfully regenerated from `.py`, content matches, sync check passes.

**Actual outcome**: _[To be filled in after running]_

---

## Validation 4: Multi-Machine Consistency (Optional)

**Objective**: Verify the workflow behaves identically across machines.

**Note**: This can be tested by:
- Cloning the repo on a different machine or VM
- Following Validation 1 again
- Confirming identical results

**Expected outcome**: ✅ Identical behavior on another machine.

**Actual outcome**: _[To be tested on another machine or deferred]_

---

## Validation 5: Intentional Sync Breakage

**Objective**: Verify that intentional misalignment is caught by pre-commit and CI.

**Steps**:

1. Manually edit `notebooks/text/starter_notebook.py` to introduce a mismatch:
   ```python
   # Add a bogus line to simulate out-of-sync state
   # Comment: "DELIBERATE MISMATCH - Testing validation"
   ```

2. Stage the `.py` file:
   ```powershell
   git add notebooks/text/starter_notebook.py
   ```

3. Attempt to commit:
   ```powershell
   git commit -m "test: intentional sync break"
   ```

4. **Expected**: Pre-commit hook should **block** the commit with:
   ```
   Notebook sync check failed for notebooks/starter_notebook.ipynb
   ```

5. Fix it by restoring the `.py`:
   ```powershell
   pixi run sync
   git add notebooks/text/starter_notebook.py
   git commit -m "test: fixed sync"
   ```

6. **Expected**: Commit succeeds after sync check passes.

**Expected outcome**: ✅ Pre-commit blocks mismatched notebooks; CI would also fail.

**Actual outcome**: _[To be filled in after running]_

---

## Summary

| # | Test | Status | Notes |
|---|------|--------|-------|
| 1 | Fresh clone & bootstrap | _pending_ | Requires separate clone; validated locally with regen |
| 2 | Cell edit & sync | ✅ Passed | Git diff shows only cell changes in `.py` file |
| 3 | Delete & regenerate | ✅ Passed | `.ipynb` successfully restored from `.py`, sync check passes |
| 4 | Multi-machine | _pending_ | Requires testing on second machine |
| 5 | Sync breakage detection | ✅ Passed | Local check caught mismatched `.py` and blocked commit attempt |

Once all tests pass, the workflow is production-ready.

