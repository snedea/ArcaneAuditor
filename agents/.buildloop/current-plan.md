# Plan: P6.1

## Dependencies
- list: [] (no new packages -- abc, importlib, inspect, pkgutil are stdlib)
- commands: [] (nothing to install)

## File Operations (in execution order)

### 1. CREATE fix_templates/__init__.py
- operation: CREATE
- reason: Makes fix_templates a proper Python package; re-exports FixTemplateRegistry for convenient import

#### Imports / Dependencies
- `from fix_templates.base import FixTemplate, FixTemplateRegistry`

#### Wiring / Integration
- Exposes `FixTemplate` and `FixTemplateRegistry` at the `fix_templates` package level so callers can do `from fix_templates import FixTemplateRegistry` without knowing internal layout.
- No logic in this file -- only the two re-export lines and a module docstring.

#### File body (complete)
```python
"""Fix template package for Arcane Auditor agent.

Auto-discovers FixTemplate subclasses and provides FixTemplateRegistry
for applying deterministic fixes to findings.
"""

from __future__ import annotations

from fix_templates.base import FixTemplate, FixTemplateRegistry

__all__ = ["FixTemplate", "FixTemplateRegistry"]
```

---

### 2. CREATE fix_templates/base.py
- operation: CREATE
- reason: Defines the FixTemplate ABC and FixTemplateRegistry auto-discovery class

#### Imports / Dependencies
- `from __future__ import annotations`
- `import importlib`
- `import inspect`
- `import logging`
- `import pkgutil`
- `from abc import ABC, abstractmethod`
- `from typing import Literal`
- `import fix_templates`
- `from src.models import Finding, FixResult`

#### Structs / Types

```python
# No new Pydantic models needed -- FixResult already exists in src/models.py.
# The Confidence enum already exists in src/models.py.
# FixTemplate is an ABC (not a Pydantic model) because its methods are behavioral, not data.
```

#### Functions

- **class FixTemplate(ABC)**
  - purpose: Abstract base class that every fix template must subclass
  - class attributes:
    - `confidence: Literal["HIGH", "MEDIUM", "LOW"]` -- concrete subclasses MUST set this at the class level (no default)
  - abstract methods:
    1. `match(self, finding: Finding) -> bool`
       - purpose: Return True if this template can handle the given finding
       - logic:
         1. Inspect `finding.rule_id` (and optionally `finding.severity`) to determine applicability
         2. Return True or False -- no side effects
       - returns: `bool`
       - error handling: must not raise; return False on any unexpected input
    2. `apply(self, finding: Finding, source_content: str) -> FixResult | None`
       - purpose: Apply the fix to source_content and return a FixResult, or None if the fix cannot be applied safely
       - logic:
         1. Inspect `source_content` and `finding` to locate the construct to fix
         2. Produce `fixed_content` (the modified source string)
         3. If the fix cannot be applied (e.g., content is malformed, ambiguous match), return None
         4. Construct and return `FixResult(finding=finding, original_content=source_content, fixed_content=fixed_content, confidence=Confidence[self.confidence])`
       - returns: `FixResult | None`
       - error handling: catch any exception during regex/string manipulation, log it at WARNING level, return None

- **class FixTemplateRegistry**
  - purpose: Discovers all concrete FixTemplate subclasses in the fix_templates package and provides lookup by finding
  - `__init__(self) -> None`
    - logic:
      1. Set `self._templates: list[FixTemplate] = []`
      2. Call `self._templates = self._discover_templates()`
    - returns: None

  - `_discover_templates(self) -> list[FixTemplate]`
    - purpose: Walk all modules under the fix_templates package and collect instantiated concrete FixTemplate subclasses
    - logic:
      1. Import `fix_templates` package (already imported at module level)
      2. Call `pkgutil.walk_packages(fix_templates.__path__, prefix=fix_templates.__name__ + ".")` to iterate all sub-modules
      3. For each `(_, module_name, _)` tuple yielded:
         a. Call `importlib.import_module(module_name)` to import the module; wrap in try/except ImportError, log WARNING and continue on failure
         b. Call `inspect.getmembers(module, inspect.isclass)` to get all classes in that module
         c. For each `(_, cls)` in the result:
            - Skip if `cls is FixTemplate` (don't register the ABC itself)
            - Skip if `inspect.isabstract(cls)` is True (skip any other abstract intermediates)
            - Skip if `not issubclass(cls, FixTemplate)` (only register FixTemplate subclasses)
            - Skip if the class does not define `confidence` as a class-level attribute (guard against misconfigured templates)
            - Instantiate `cls()` and append to `discovered`
      4. Log at DEBUG level: `"FixTemplateRegistry: discovered %d templates"` with count
      5. Return `discovered`
    - returns: `list[FixTemplate]`
    - error handling: ImportError per module is caught and logged at WARNING; does not abort discovery

  - `find_matching(self, finding: Finding) -> list[FixTemplate]`
    - purpose: Return all registered templates whose match() returns True for the given finding
    - logic:
      1. Iterate `self._templates`
      2. For each template, call `template.match(finding)` in a try/except Exception block; log WARNING and skip on exception
      3. Collect templates where match returned True into result list
      4. Return result list (may be empty)
    - returns: `list[FixTemplate]`
    - error handling: per-template exceptions are caught, logged at WARNING, template is skipped

  - `templates` property
    - purpose: Read-only view of all discovered templates
    - logic: Return `list(self._templates)` (copy to prevent external mutation)
    - returns: `list[FixTemplate]`

#### Wiring / Integration
- `fix_templates/base.py` imports `from src.models import Finding, FixResult, Confidence`
- `fix_templates/__init__.py` re-exports `FixTemplate` and `FixTemplateRegistry` from this file
- Future template files (e.g., `fix_templates/script_fixes.py`) will import `FixTemplate` from `fix_templates.base` and subclass it
- `src/fixer.py` (P6.4) will instantiate `FixTemplateRegistry()` and call `find_matching(finding)` on it

---

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from fix_templates import FixTemplate, FixTemplateRegistry; r = FixTemplateRegistry(); print('templates:', r.templates)"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m py_compile fix_templates/__init__.py fix_templates/base.py && echo OK`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -x -q` (no new test file for P6.1 -- tests come in P6.5; existing suite must still pass)
- smoke:
  1. Run `uv run python -c "from fix_templates import FixTemplateRegistry; r = FixTemplateRegistry(); print(len(r.templates), 'templates discovered')"` -- should print `0 templates discovered` (no concrete templates exist yet)
  2. Run `uv run python -c "from fix_templates.base import FixTemplate; import inspect; print(inspect.isabstract(FixTemplate))"` -- should print `True`
  3. Run `uv run python -c "from fix_templates import FixTemplate, FixTemplateRegistry"` with no error

## Constraints
- Do NOT create `src/fixer.py` -- that is P6.4
- Do NOT create `fix_templates/script_fixes.py` or `fix_templates/structure_fixes.py` -- those are P6.2 and P6.3
- Do NOT modify `src/models.py` -- `Finding`, `FixResult`, and `Confidence` are already defined there
- Do NOT modify `pyproject.toml` -- no new dependencies are needed
- Do NOT modify `CLAUDE.md`, `ARCHITECTURE.md`, or `IMPL_PLAN.md`
- The `confidence` attribute on `FixTemplate` must be a class-level `Literal["HIGH", "MEDIUM", "LOW"]` annotation -- not an instance variable, not a Pydantic field
- `FixTemplate` must be a plain `ABC` subclass (not a Pydantic `BaseModel`) because its interface is behavioral
- The registry must silently skip templates that fail to import or instantiate -- discovery errors must never abort the entire registry initialization
- Use `logging` module only -- no `print()` calls anywhere in these files
- Include `from __future__ import annotations` as the first import in every .py file
