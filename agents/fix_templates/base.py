"""Base classes for deterministic fix templates."""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from abc import ABC, abstractmethod
from typing import Literal

import fix_templates
from src.models import Finding, FixResult

logger = logging.getLogger(__name__)


class FixTemplate(ABC):
    """Abstract base class that every fix template must subclass."""

    confidence: Literal["HIGH", "MEDIUM", "LOW"]

    @abstractmethod
    def match(self, finding: Finding) -> bool:
        """Return True if this template can handle the given finding."""

    @abstractmethod
    def apply(self, finding: Finding, source_content: str) -> FixResult | None:
        """Apply the fix to source_content and return a FixResult, or None if unsafe."""


class FixTemplateRegistry:
    """Discovers all concrete FixTemplate subclasses and provides lookup by finding."""

    def __init__(self) -> None:
        self._templates: list[FixTemplate] = []
        self._templates = self._discover_templates()

    def _discover_templates(self) -> list[FixTemplate]:
        """Walk all modules under fix_templates and collect concrete FixTemplate subclasses."""
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
        """Return all registered templates whose match() returns True for the given finding."""
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
        """Read-only view of all discovered templates."""
        return list(self._templates)
