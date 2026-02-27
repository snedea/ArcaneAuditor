"""Fix template package for Arcane Auditor agent.

Auto-discovers FixTemplate subclasses and provides FixTemplateRegistry
for applying deterministic fixes to findings.
"""

from __future__ import annotations

from fix_templates.base import FixTemplate, FixTemplateRegistry

__all__ = ["FixTemplate", "FixTemplateRegistry"]
