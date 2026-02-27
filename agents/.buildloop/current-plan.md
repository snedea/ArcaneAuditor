# Plan: P6.1

## Context

Both `fix_templates/__init__.py` and `fix_templates/base.py` already exist from
a WIP commit (`c4bf9c1`). The existing implementation is complete and correct.
This plan tells the builder to:
1. Verify the two existing files match the spec exactly (see exact expected content below).
2. Fix one real gap: `pyproject.toml` lists only `src` in `packages`, so `fix_templates`
   won't be installed when the package is built as a wheel. Add it.
3. Run existing tests to confirm nothing broke.

## Dependencies

- list: (none — no new packages required)
- commands: (none)

## File Operations (in execution order)

---

### 1. MODIFY fix_templates/__init__.py

- operation: MODIFY
- reason: File exists from WIP commit; verify it contains exactly this content and fix if it does not.
- anchor: `from fix_templates.base import FixTemplate, FixTemplateRegistry`

#### Expected exact file content

```python
"""Fix template package for Arcane Auditor agent.

Auto-discovers FixTemplate subclasses and provides FixTemplateRegistry
for applying deterministic fixes to findings.
"""

from __future__ import annotations

from fix_templates.base import FixTemplate, FixTemplateRegistry

__all__ = ["FixTemplate", "FixTemplateRegistry"]
```

The builder must read the existing file and confirm it matches this content
character-for-character (ignoring trailing newline differences). If it differs,
overwrite it with the content above.

---

### 2. MODIFY fix_templates/base.py

- operation: MODIFY
- reason: File exists from WIP commit; verify it contains exactly this content and fix if it does not.
- anchor: `class FixTemplate(ABC):`

#### Imports / Dependencies

```python
from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from abc import ABC, abstractmethod
from typing import Literal

import fix_templates
from src.models import Finding, FixResult
```

#### Classes

**FixTemplate (ABC)**

```python
class FixTemplate(ABC):
    """Abstract base class that every fix template must subclass.

    Attributes:
        confidence: Fixed string declaring how safe auto-application is.
            Concrete subclasses MUST set this as a class-level string attribute,
            e.g. confidence = "HIGH". Type annotation alone is not sufficient;
            the FixTemplateRegistry validates this at discovery time.
    """

    confidence: Literal["HIGH", "MEDIUM", "LOW"]

    @abstractmethod
    def match(self, finding: Finding) -> bool:
        """Return True if this template can handle the given finding.

        Args:
            finding: The Finding from Arcane Auditor JSON output.

        Returns:
            True if this template applies to the finding's rule_id.
        """

    @abstractmethod
    def apply(self, finding: Finding, source_content: str) -> FixResult | None:
        """Apply the fix to source_content and return a FixResult, or None if unsafe.

        Args:
            finding: The Finding that triggered this template.
            source_content: Full text content of the source file to be fixed.

        Returns:
            A FixResult with original_content and fixed_content, or None if the
            fix cannot be applied safely (e.g. ambiguous match, multiple occurrences).
        """
```

**FixTemplateRegistry**

```python
class FixTemplateRegistry:
    """Discovers all concrete FixTemplate subclasses and provides lookup by finding.

    Discovery uses pkgutil.walk_packages on the fix_templates package, mirrors the
    pattern used by RulesEngine in the parent Arcane Auditor project. Templates are
    instantiated once at registry construction time.
    """

    def __init__(self) -> None:
        """Initialize registry and trigger template auto-discovery."""
        self._templates: list[FixTemplate] = []
        self._templates = self._discover_templates()

    def _discover_templates(self) -> list[FixTemplate]:
        """Walk all modules under fix_templates and collect concrete FixTemplate subclasses.

        Skips:
        - FixTemplate itself
        - Abstract subclasses (inspect.isabstract)
        - Classes that are not subclasses of FixTemplate
        - Classes that do not have a string-valued `confidence` class attribute
        - Classes whose constructor raises any exception

        Returns:
            List of instantiated FixTemplate objects.
        """
        discovered: list[FixTemplate] = []
        for _, module_name, _ in pkgutil.walk_packages(
            fix_templates.__path__, prefix=fix_templates.__name__ + "."
        ):
            try:
                module = importlib.import_module(module_name)
            except ImportError:
                logger.warning("Failed to import fix template module: %s", module_name)
                continue
            for _, cls in inspect.getmembers(module, inspect.isclass):
                if cls is FixTemplate:
                    continue
                if inspect.isabstract(cls):
                    continue
                if not issubclass(cls, FixTemplate):
                    continue
                if not hasattr(cls, "confidence") or not isinstance(
                    inspect.getattr_static(cls, "confidence"), str
                ):
                    continue
                try:
                    discovered.append(cls())
                except Exception:
                    logger.warning("Failed to instantiate fix template: %s", cls.__name__)
                    continue
        logger.debug("FixTemplateRegistry: discovered %d templates", len(discovered))
        return discovered

    def find_matching(self, finding: Finding) -> list[FixTemplate]:
        """Return all registered templates whose match() returns True for the given finding.

        Args:
            finding: The Finding to look up.

        Returns:
            List of FixTemplate instances that match the finding (may be empty).
        """
        result: list[FixTemplate] = []
        for template in self._templates:
            try:
                if template.match(finding):
                    result.append(template)
            except Exception:
                logger.warning(
                    "Exception in match() for template %s",
                    type(template).__name__,
                )
                continue
        return result

    @property
    def templates(self) -> list[FixTemplate]:
        """Read-only view of all discovered templates.

        Returns:
            Shallow copy of the internal template list.
        """
        return list(self._templates)
```

#### Module-level logger

Add this line after the imports and before the class definitions:

```python
logger = logging.getLogger(__name__)
```

#### Expected full file content

The builder must read the existing `fix_templates/base.py` and confirm it contains
all of the following (in this order):
1. Module docstring: `"""Base classes for deterministic fix templates."""`
2. `from __future__ import annotations` as the first real import
3. stdlib imports: `importlib`, `inspect`, `logging`, `pkgutil`, `abc.ABC`, `abc.abstractmethod`, `typing.Literal`
4. `import fix_templates` (the package itself, used for `__path__` in discovery)
5. `from src.models import Finding, FixResult`
6. `logger = logging.getLogger(__name__)`
7. `class FixTemplate(ABC)` with `confidence` annotation, `match` abstractmethod, `apply` abstractmethod
8. `class FixTemplateRegistry` with `__init__`, `_discover_templates`, `find_matching`, `templates` property

If the existing file matches this structure, make no changes. If any element is
missing or incorrect, rewrite the file with the exact content derived from the
class definitions above.

---

### 3. MODIFY pyproject.toml

- operation: MODIFY
- reason: `fix_templates` package is not in the hatch `packages` list; it will not be installed when the wheel is built, causing ImportError for anyone installing the package outside of the dev environment.
- anchor: `packages = ["src"]`

#### Change

Replace:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src"]
```

With:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src", "fix_templates"]
```

---

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: (no lint tool configured in pyproject.toml; skip)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -x -q`
- smoke:
  1. Run: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from fix_templates import FixTemplate, FixTemplateRegistry; r = FixTemplateRegistry(); print('registry ok, templates:', len(r.templates))"`
  2. Expected output: `registry ok, templates: 0` (zero because no concrete templates exist yet; P6.2/P6.3 add them)
  3. Run: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from fix_templates.base import FixTemplate; import inspect; print('abstract methods:', sorted(inspect.abstractmethods(FixTemplate)))"`
  4. Expected output: `abstract methods: ['apply', 'match']`

## Constraints

- Do NOT modify `src/models.py` -- `Finding`, `FixResult`, and `Confidence` already exist exactly as needed.
- Do NOT create `src/fixer.py` -- that is P6.4.
- Do NOT create `fix_templates/script_fixes.py` or `fix_templates/structure_fixes.py` -- those are P6.2 and P6.3.
- Do NOT create any test file for fix_templates -- test_fixer.py is P6.5.
- Do NOT add the `fix_templates` package to `pyproject.toml` `[project]` `dependencies` -- it is part of this project, not an external dep.
- The `confidence` attribute on `FixTemplate` must remain a class-level annotation (`confidence: Literal["HIGH", "MEDIUM", "LOW"]`) with NO default value and NO `@abstractmethod` decorator. Concrete subclasses provide the value as a plain class attribute string (e.g. `confidence = "HIGH"`). The registry validates this at instantiation time.
- The `import fix_templates` in `base.py` must remain at module level (not inside the method). It is safe because by the time Python executes `base.py`, `fix_templates.__path__` is already set on the partially-initialized package object.
