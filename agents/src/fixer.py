"""Apply deterministic fix templates to Arcane Auditor findings."""

from __future__ import annotations

import logging
from pathlib import Path

from fix_templates.base import FixTemplateRegistry
from src.models import Confidence, FixerError, FixResult, ScanResult

logger = logging.getLogger(__name__)


def fix_findings(scan_result: ScanResult, source_dir: Path) -> list[FixResult]:
    """Iterate every finding in scan_result and apply the first HIGH-confidence matching template.

    Args:
        scan_result: The full scan output from Arcane Auditor.
        source_dir: Root directory of the scanned application.

    Returns:
        List of FixResult objects for findings that had a matching HIGH-confidence template.
    """
    registry = FixTemplateRegistry()
    results: list[FixResult] = []

    for finding in scan_result.findings:
        file_path = source_dir / finding.file_path

        if not file_path.exists():
            logger.warning("fixer: file not found, skipping: %s", file_path)
            continue

        try:
            original_content = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("fixer: cannot read %s: %s", file_path, exc)
            continue

        matching = registry.find_matching(finding)
        high_conf = [t for t in matching if t.confidence == Confidence.HIGH]

        if not high_conf:
            logger.debug("fixer: no HIGH template for rule %s", finding.rule_id)
            continue

        template = high_conf[0]

        try:
            fix_result = template.apply(finding, original_content)
        except Exception as exc:
            logger.warning(
                "fixer: template %s raised %s for rule %s: %s",
                type(template).__name__,
                type(exc).__name__,
                finding.rule_id,
                exc,
            )
            continue

        if fix_result is None:
            logger.debug(
                "fixer: template %s returned None for rule %s",
                type(template).__name__,
                finding.rule_id,
            )
            continue

        results.append(fix_result)

    return results


def apply_fixes(fix_results: list[FixResult], target_dir: Path) -> list[Path]:
    """Write each FixResult's fixed_content to the corresponding file under target_dir.

    Args:
        fix_results: List of FixResult objects to write.
        target_dir: Root directory to write fixed files into.

    Returns:
        List of file paths that were successfully written.

    Raises:
        FixerError: If writing a file fails.
    """
    written: list[Path] = []
    seen: set[str] = set()

    for fix_result in fix_results:
        file_path_str = fix_result.finding.file_path

        # Deduplication: first fix for a file wins; subsequent ones are skipped.
        if file_path_str in seen:
            logger.warning(
                "apply_fixes: duplicate fix for %s — skipping to avoid discarding previous fix",
                file_path_str,
            )
            continue

        # Path safety: reject absolute paths and traversal sequences.
        candidate = Path(file_path_str)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise FixerError(f"apply_fixes: unsafe path in finding: {file_path_str}")

        dest = target_dir / candidate

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(fix_result.fixed_content, encoding="utf-8")
        except OSError as exc:
            raise FixerError(f"apply_fixes: failed to write {dest}: {exc}") from exc

        logger.debug("apply_fixes: wrote %s", dest)
        seen.add(file_path_str)
        written.append(dest)

    return written
