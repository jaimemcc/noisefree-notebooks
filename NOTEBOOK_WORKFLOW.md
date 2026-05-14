# Notebook Workflow Documentation

## How the Notebook Workflow Works

This repository uses a **Pixi-managed, Jupytext-powered notebook workflow** that enables:
- **ipynb-first authoring**: Write and edit notebooks as `.ipynb` files locally
- **Text-based git tracking**: Commit clean, version-controllable `.py` files (not binary `.ipynb`)
- **Automatic bidirectional sync**: Convert between `.ipynb` and `.py` formats transparently
- **Policy enforcement**: Pre-commit hooks and CI prevent accidental commits of `.ipynb` files

### The Workflow at a Glance

```
Work on notebooks/example.ipynb locally (never committed)
                    ↓
pixi run sync → generates notebooks/text/example.py (committed to git)
                    ↓
Other developer clones repo
                    ↓
pixi run regen → restores notebooks/example.ipynb from notebooks/text/example.py
                    ↓
Open and continue editing notebooks/example.ipynb
```

### Why This Setup?

| Why | Benefit |
|-----|---------|
| **No binary diffs** | `.py` files are plain text; git diffs are readable |
| **Clean git history** | Only notebook outputs change → only cell changes tracked |
| **Portable** | `.py` format works without Jupyter; reviewable in any text editor |
| **Collaborative** | Text-based format resolves merges cleanly |
| **Local-only edits** | `.ipynb` files never tracked; no "save artifact" clutter |

---

## Quick Start

### First Time Setup

1. Install Pixi: https://pixi.sh
2. Run `pixi install` to set up the notebook environment
3. Run `pixi run bootstrap` to configure pre-commit hooks

### Create and Sync a Notebook

1. Create or edit `notebooks/my_analysis.ipynb` in VS Code using the Jupyter extension
2. Run `pixi run sync` to generate the tracked `.py` file
3. Commit `notebooks/text/my_analysis.py` to git

### After Cloning (or on a New Machine)

```bash
pixi install
pixi run regen  # Restores all .ipynb files from notebooks/text/
```

Then open `notebooks/my_analysis.ipynb` and continue editing.

---

## Available Commands

| Command | Purpose |
|---------|---------|
| `pixi run sync` | Convert all `.ipynb` → `.py` (required before committing) |
| `pixi run regen [notebook.py]` | Convert `.py` → `.ipynb` (restore notebooks after clone) |
| `pixi run check` | Validate sync state and notebook policy (run before committing) |
| `pixi run bootstrap` | Set up pre-commit hooks (one-time setup) |

### Aliases

- `pixi run sync` = `pixi run sync-notebooks`
- `pixi run regen` = `pixi run regenerate-notebooks`
- `pixi run check` = `pixi run check-notebooks`

---

## Workflow Rules

1. **Edit `.ipynb` files only** — Use Jupyter extension to edit `notebooks/*.ipynb`
2. **Sync before commit** — Run `pixi run sync` to refresh `.py` files
3. **Commit `.py` files only** — Never commit `.ipynb` files; pre-commit will block them
4. **Check before pushing** — Run `pixi run check` to validate sync state

---

## Common Tasks

### I edited my notebook. What do I do?

1. Run `pixi run sync` to refresh the `.py` file
2. Run `pixi run check` to verify everything is in sync
3. Commit `notebooks/text/my_notebook.py`

### I cloned the repo or pulled new notebooks. How do I edit them?

1. Run `pixi run regen` to restore all `.ipynb` files
2. Open `notebooks/<name>.ipynb` in VS Code and edit

### I deleted my `.ipynb` file by accident. How do I recover it?

1. Run `pixi run regen <notebook_name>.py` to restore it from the tracked `.py` file

### I want to check what changed in my notebook. How do I see the diff?

1. Look at `notebooks/text/<notebook>.py` in git:
   - Changed cells appear as new/modified Python sections
   - New cell outputs appear at the bottom
2. The diff is much cleaner than `.ipynb` binary diffs

### Pre-commit hook blocked my commit. What do I do?

If the hook says "notebook policy violation", you tried to commit an `.ipynb` file. Fix it:

```bash
pixi run check  # Shows which file violated the policy
git rm notebooks/my_notebook.ipynb  # Remove from staging
pixi run sync  # Refresh the .py file
git add notebooks/text/my_notebook.py  # Add the .py instead
git commit  # Retry
```

---

## Policy Enforcement

### Local Repository (Pre-commit)

Two hooks run automatically on `git commit`:

1. **notebook-policy**: Blocks commits of `.ipynb` files in `notebooks/`
2. **notebook-sync**: Ensures `.py` files are up-to-date with `.ipynb` sources

### CI/CD (GitHub Actions)

On every pull request and push to main:
- GitHub Actions runs `pixi run check` to ensure policy compliance
- If checks fail, the workflow halts; fix and re-push

---

## For Contributors

When contributing a new notebook or updating an existing one:

1. **Clone the repo**: `git clone <url>`
2. **Setup environment**: `pixi install && pixi run bootstrap`
3. **Restore notebooks**: `pixi run regen`
4. **Create/edit**: Edit `notebooks/my_feature.ipynb`
5. **Sync and check**: `pixi run sync && pixi run check`
6. **Commit and push**: Commit only `notebooks/text/my_feature.py`, then push

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `pixi run sync` fails with "notebook is not JSON" | Delete any empty `.ipynb` files and run sync again |
| Notebooks won't restore with `pixi run regen` | Ensure `notebooks/text/` has the `.py` files; run `git status` to confirm |
| Pre-commit hook fails unexpectedly | Run `pixi run check` to see the full error message |
| `.py` file differs from notebook after sync | The notebook was edited but sync wasn't run; run `pixi run sync` again |

---

## Further Reading

- [Pixi Documentation](https://pixi.sh)
- [Jupytext Documentation](https://jupytext.readthedocs.io/)
- Implementation details: See [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)

