# Review Report — P6.1

## Verdict: FAIL

## Runtime Checks
- Build: PASS (py_compile clean on both files)
- Tests: PASS (177 passed, 0 failures)
- Lint: SKIPPED (flake8/ruff not installed in venv)
- Docker: SKIPPED (no compose files changed)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "fix_templates/base.py",
      "line": 47,
      "issue": "except ImportError only catches ImportError, but importlib.import_module can raise SyntaxError, NameError, or other Exception subclasses for malformed/broken template modules. These escape the handler, propagate out of _discover_templates(), and crash FixTemplateRegistry.__init__(). The plan constraint states explicitly: 'The registry must silently skip templates that fail to import or instantiate -- discovery errors must never abort the entire registry initialization.' Confirmed with live test: a template file with a syntax error raises SyntaxError that is NOT caught, aborting all discovery.",
      "category": "crash"
    }
  ],
  "low": [
    {
      "file": "fix_templates/base.py",
      "line": 13,
      "issue": "Plan specifies 'from src.models import Finding, FixResult, Confidence' but Confidence is not imported. It is unused in base.py so this is not a functional bug, but concrete templates implementing apply() need Confidence to construct FixResult and will have to import it separately. Minor inconsistency with the plan's stated imports.",
      "category": "inconsistency"
    }
  ],
  "validated": [
    "fix_templates/__init__.py matches the plan spec exactly: docstring, from __future__ import annotations, re-export of FixTemplate and FixTemplateRegistry, __all__.",
    "fix_templates/base.py: FixTemplate is a plain ABC (not Pydantic BaseModel) with confidence as annotation-only class attribute (no default) and two abstractmethods match() and apply() -- matches plan.",
    "inspect.isabstract(FixTemplate) returns True -- ABC is not accidentally concrete.",
    "Circular import (base.py imports fix_templates package, which imports base.py) is safe in practice: fix_templates.__path__ is set before __init__.py executes, and _discover_templates() only uses it at runtime, not import time. Smoke tests confirm no circular import error.",
    "FixTemplateRegistry._discover_templates() uses inspect.getattr_static to avoid triggering descriptors when checking the confidence attribute -- correctly guards against misconfigured templates.",
    "hasattr(cls, 'confidence') checked before inspect.getattr_static call -- prevents AttributeError from getattr_static on annotation-only attributes.",
    "isinstance(inspect.getattr_static(cls, 'confidence'), str) correctly accepts both plain string literals ('HIGH') and Confidence enum values (since Confidence inherits str).",
    "find_matching() wraps each template.match() call in try/except Exception and logs + skips on failure -- matches plan.",
    "templates property returns list(self._templates) (defensive copy) -- matches plan.",
    "Smoke test 1: 'from fix_templates import FixTemplate, FixTemplateRegistry; r = FixTemplateRegistry(); print(r.templates)' prints [] -- correct.",
    "Smoke test 2: '0 templates discovered' printed -- correct since no concrete templates exist yet.",
    "Smoke test 3: inspect.isabstract(FixTemplate) prints True -- correct.",
    "All 177 existing tests pass -- no regressions."
  ]
}
```

## Fix Required

**fix_templates/base.py:47** -- Change `except ImportError:` to `except Exception:` so that SyntaxError, NameError, and any other import-time exception is caught and logged rather than aborting discovery. The log message should include the exception type for diagnosability:

```python
except Exception as exc:
    logger.warning(
        "Failed to import fix template module %s: %s: %s",
        module_name,
        type(exc).__name__,
        exc,
    )
    continue
```
