# Plan: P1.1 -- Project Scaffold (pyproject.toml + init files)

## Task
Create pyproject.toml with dependencies (typer, pydantic>=2.0, pygithub, pytest) and project metadata. Create src/__init__.py and tests/__init__.py. Verify with `uv sync`.

## Context
This is the very first task in the agent system -- nothing exists yet under `agents/` except documentation files (ARCHITECTURE.md, CLAUDE.md, IMPL_PLAN.md, docs/). The parent Arcane Auditor project at `../` uses Python 3.12, uv, and has its own pyproject.toml.

## Files to Create

### 1. `agents/pyproject.toml`

Full path: `/Users/name/homelab/ArcaneAuditor/agents/pyproject.toml`

Contents:

```toml
[project]
name = "arcane-auditor-agents"
version = "0.1.0"
description = "Autonomous agent wrapper for Arcane Auditor deterministic code review"
license = "MIT"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "typer[all]>=0.16.1",
    "pydantic>=2.0",
    "pygithub>=2.1.1",
    "pyyaml>=6.0",
]

[project.scripts]
arcane-agent = "src.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.backends"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23.0",
]
```

Key decisions:
- `requires-python = ">=3.12"` -- matches parent project's `.python-version` (3.12)
- `typer[all]>=0.16.1` -- matches parent project's typer version for consistency
- `pydantic>=2.0` -- as specified in IMPL_PLAN.md (Pydantic v2)
- `pygithub>=2.1.1` -- latest stable for GitHub API access
- `pyyaml>=6.0` -- needed by P1.3 (config.py loads YAML config files)
- `pytest` goes in `[dependency-groups] dev` since it's a dev-only dependency
- `hatchling` as build backend (standard for modern Python projects)
- `pythonpath = ["."]` in pytest config so `from src.models import ...` works
- `[project.scripts]` entry point for the CLI (per ARCHITECTURE.md: `python -m agents.src.cli`)

### 2. `agents/src/__init__.py`

Full path: `/Users/name/homelab/ArcaneAuditor/agents/src/__init__.py`

Contents:
```python
"""Arcane Auditor agent system -- deterministic code review automation."""
```

Just a docstring. This marks `src/` as a Python package. No imports needed yet (future tasks will add modules).

### 3. `agents/tests/__init__.py`

Full path: `/Users/name/homelab/ArcaneAuditor/agents/tests/__init__.py`

Contents:
```python
```

Empty file. Marks `tests/` as a Python package for pytest discovery.

## Directories to Create

- `agents/src/` (will be created implicitly when writing `src/__init__.py`)
- `agents/tests/` (will be created implicitly when writing `tests/__init__.py`)

## Dependencies to Install

Run from `agents/` directory:
```bash
cd /Users/name/homelab/ArcaneAuditor/agents && uv sync
```

This will:
1. Resolve all dependencies in pyproject.toml
2. Create a `.venv/` virtual environment (or reuse existing)
3. Generate/update `uv.lock`
4. Install all deps + dev deps

## Verification Steps

### Step 1: uv sync succeeds
```bash
cd /Users/name/homelab/ArcaneAuditor/agents && uv sync
```
Expected: Exit code 0, no errors. A `uv.lock` file and `.venv/` directory are created.

### Step 2: Python packages are importable
```bash
cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "import src; print('src OK')"
```
Expected: Prints "src OK".

### Step 3: Dependencies are importable
```bash
cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "import typer; import pydantic; import github; import yaml; print('All deps OK')"
```
Expected: Prints "All deps OK".

### Step 4: pytest runs (with no tests yet)
```bash
cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest --co -q
```
Expected: Exit code 5 (no tests collected) or exit code 0 with "no tests ran". No import errors.

## What NOT to Do
- Do not create any other source files (models.py, config.py, etc.) -- those are separate tasks
- Do not modify the parent project's pyproject.toml
- Do not create a `.python-version` file (inherits from parent's `3.12`)
- Do not add a `.gitignore` (parent's `.gitignore` already covers `.venv/`, `__pycache__/`, etc.)
