"""HIGH-confidence fix templates for Workday Extend script violations."""

from __future__ import annotations

import logging
import re
from typing import Literal

from fix_templates.base import FixTemplate
from src.models import Confidence, Finding, FixResult

logger = logging.getLogger(__name__)


class VarToLetConst(FixTemplate):
    """Replace var declarations with let or const based on reassignment analysis."""

    confidence: Literal["HIGH"] = "HIGH"

    _VAR_DECL_RE: re.Pattern[str] = re.compile(r'\bvar\s+(\w+)\s*=')

    def match(self, finding: Finding) -> bool:
        """Return True if the finding is a ScriptVarUsageRule violation."""
        return finding.rule_id == "ScriptVarUsageRule"

    def _determine_keyword(self, varname: str, context: str) -> str:
        """Return 'let' if varname is mutated anywhere in context, else 'const'.

        Detects simple assignment, all compound assignments (+=, -=, **=, &&=,
        ||=, ??=, &=, |=, ^=, <<=, >>=, >>>=), and increment/decrement (++/--).
        """
        pattern = re.compile(
            r'(?:'
            r'(?:\+\+|--)' + re.escape(varname) + r'\b'
            r'|\b' + re.escape(varname) + r'(?:'
            r'\s*(?:\+\+|--)'
            r'|\s*(?:\*\*|&&|\|\||\?\?|>>>=|>>=|<<=|[+\-*\/%&|^])?=(?!=)'
            r')'
            r')'
        )
        if pattern.search(context):
            return "let"
        return "const"

    def apply(self, finding: Finding, source_content: str) -> FixResult | None:
        """Replace var declarations on the finding's line with let or const."""
        if finding.line == 0:
            return None
        lines: list[str] = source_content.splitlines(keepends=True)
        if finding.line > len(lines):
            return None
        target_idx: int = finding.line - 1
        target_line: str = lines[target_idx]
        if self._VAR_DECL_RE.search(target_line) is None:
            return None
        after_context: str = "".join(lines[target_idx + 1:])

        def _replacer(m: re.Match[str]) -> str:
            first_varname: str = m.group(1)
            # Include the rest of the current line so same-line mutations are
            # detected (e.g. for (var i = 0; i < n; i++) on one line).
            same_line_tail: str = target_line[m.end():]
            primary_context: str = same_line_tail + "\n" + after_context
            # Detect additional variable names in multi-var declarations:
            # var x = 1, y = 2  ->  extra_varnames = ['y']
            extra_varnames: list[str] = re.findall(r',\s*(\w+)\s*=', same_line_tail)
            if self._determine_keyword(first_varname, primary_context) == "let":
                keyword: str = "let"
            else:
                keyword = "const"
                for vn in extra_varnames:
                    decl_m = re.search(r',\s*' + re.escape(vn) + r'\s*=', same_line_tail)
                    vn_tail = same_line_tail[decl_m.end():] if decl_m else ""
                    if self._determine_keyword(vn, vn_tail + "\n" + after_context) == "let":
                        keyword = "let"
                        break
            return m.group(0).replace("var", keyword, 1)

        modified_line: str = self._VAR_DECL_RE.sub(_replacer, target_line)
        if modified_line == target_line:
            return None
        lines[target_idx] = modified_line
        return FixResult(
            finding=finding,
            original_content=source_content,
            fixed_content="".join(lines),
            confidence=Confidence.HIGH,
        )


class RemoveConsoleLog(FixTemplate):
    """Remove console.log/warn/error/info/debug calls from script files."""

    confidence: Literal["HIGH"] = "HIGH"

    _CONSOLE_RE: re.Pattern[str] = re.compile(
        r'console\.(log|warn|error|info|debug)\s*\([^()]*\)\s*;?'
    )

    def match(self, finding: Finding) -> bool:
        """Return True if the finding is a ScriptConsoleLogRule violation."""
        return finding.rule_id == "ScriptConsoleLogRule"

    def apply(self, finding: Finding, source_content: str) -> FixResult | None:
        """Remove the console.* call on the finding's line; remove entire line if empty."""
        if finding.line == 0:
            return None
        lines: list[str] = source_content.splitlines(keepends=True)
        if finding.line > len(lines):
            return None
        target_idx: int = finding.line - 1
        target_line: str = lines[target_idx]
        if self._CONSOLE_RE.search(target_line) is None:
            return None
        modified_line: str = self._CONSOLE_RE.sub("", target_line)
        if "console." in modified_line:
            return None
        stripped: str = modified_line.strip()
        if stripped == "" or stripped in ("%>", "<%"):
            lines.pop(target_idx)
        else:
            lines[target_idx] = modified_line
        return FixResult(
            finding=finding,
            original_content=source_content,
            fixed_content="".join(lines),
            confidence=Confidence.HIGH,
        )


class TemplateLiteralFix(FixTemplate):
    """Convert simple string concatenation to template literals."""

    confidence: Literal["HIGH"] = "HIGH"

    _CONCAT_A_RE: re.Pattern[str] = re.compile(r"'([^'\\`\${}]*)'\s*\+\s*(\w+)\b(?!\s*\(|\.)")
    _CONCAT_B_RE: re.Pattern[str] = re.compile(r"(?<!\.)\b(\w+)\s*\+\s*'([^'\\`\${}]*)'")

    def match(self, finding: Finding) -> bool:
        """Return True if the finding is a ScriptStringConcatRule violation."""
        return finding.rule_id == "ScriptStringConcatRule"

    def apply(self, finding: Finding, source_content: str) -> FixResult | None:
        """Convert a simple string concatenation on the finding's line to a template literal."""
        if finding.line == 0:
            return None
        lines: list[str] = source_content.splitlines(keepends=True)
        if finding.line > len(lines):
            return None
        target_idx: int = finding.line - 1
        target_line: str = lines[target_idx]
        matches_a: list[tuple[str, str]] = self._CONCAT_A_RE.findall(target_line)
        matches_b: list[tuple[str, str]] = self._CONCAT_B_RE.findall(target_line)
        if len(matches_a) == 1 and len(matches_b) == 0:
            m = self._CONCAT_A_RE.search(target_line)
            literal: str = m.group(1)  # type: ignore[union-attr]
            varname: str = m.group(2)  # type: ignore[union-attr]
            replacement: str = f"`{literal}${{{varname}}}`"
            modified_line: str = target_line[:m.start()] + replacement + target_line[m.end():]  # type: ignore[union-attr]
        elif len(matches_b) == 1 and len(matches_a) == 0:
            m = self._CONCAT_B_RE.search(target_line)
            varname = m.group(1)  # type: ignore[union-attr]
            literal = m.group(2)  # type: ignore[union-attr]
            replacement = f"`${{{varname}}}{literal}`"
            modified_line = target_line[:m.start()] + replacement + target_line[m.end():]  # type: ignore[union-attr]
        else:
            return None
        if modified_line == target_line:
            return None
        lines[target_idx] = modified_line
        return FixResult(
            finding=finding,
            original_content=source_content,
            fixed_content="".join(lines),
            confidence=Confidence.HIGH,
        )
