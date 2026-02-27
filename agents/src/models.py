"""Pydantic models, enums, and custom exceptions for the Arcane Auditor agent system."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, SecretStr


# --- Enums ---


class Severity(str, Enum):
    """Severity levels matching the parent Arcane Auditor tool output."""

    ACTION = "ACTION"
    ADVICE = "ADVICE"


class ReportFormat(str, Enum):
    """Supported output formats for scan reports."""

    JSON = "json"
    SARIF = "sarif"
    GITHUB_ISSUES = "github_issues"
    PR_COMMENT = "pr_comment"


class Confidence(str, Enum):
    """Confidence level for automated fix templates."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ExitCode(int, Enum):
    """Exit codes from the parent Arcane Auditor tool."""

    CLEAN = 0
    ISSUES_FOUND = 1
    USAGE_ERROR = 2
    RUNTIME_ERROR = 3


# --- Models ---


class Finding(BaseModel):
    """A single finding from the parent Arcane Auditor JSON output."""

    model_config = ConfigDict(frozen=True)

    rule_id: str
    severity: Severity
    message: str
    file_path: str
    line: int = 0

    @property
    def description(self) -> str:
        """Alias for message, matching the IMPL_PLAN interface."""
        return self.message


class ScanResult(BaseModel):
    """Full output of running Arcane Auditor on a repo or path."""

    repo: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    findings_count: int
    findings: list[Finding]
    exit_code: ExitCode

    @property
    def has_issues(self) -> bool:
        """Whether the scan found actionable issues."""
        return self.exit_code == ExitCode.ISSUES_FOUND

    @property
    def action_count(self) -> int:
        """Count of ACTION-severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.ACTION)

    @property
    def advice_count(self) -> int:
        """Count of ADVICE-severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.ADVICE)


class FixResult(BaseModel):
    """Result of applying a fix template to a finding."""

    finding: Finding
    original_content: str
    fixed_content: str
    confidence: Confidence

    @property
    def is_auto_applicable(self) -> bool:
        """Whether this fix can be applied automatically (HIGH confidence only)."""
        return self.confidence == Confidence.HIGH


class AgentConfig(BaseModel):
    """Configuration for the agent system."""

    repos: list[str] = Field(default_factory=list)
    config_preset: str | None = None
    output_format: ReportFormat = ReportFormat.JSON
    github_token: SecretStr | None = None
    auditor_path: Path = Path("../")


# --- Custom Exceptions ---


class ArcaneAgentError(Exception):
    """Base exception for all agent errors."""


class ScanError(ArcaneAgentError):
    """Raised when scanning for Extend artifacts fails."""


class RunnerError(ArcaneAgentError):
    """Raised when invoking Arcane Auditor subprocess fails."""


class ReporterError(ArcaneAgentError):
    """Raised when formatting or delivering a report fails."""


class FixerError(ArcaneAgentError):
    """Raised when applying a fix template fails."""


class ConfigError(ArcaneAgentError):
    """Raised when configuration is missing, malformed, or fails validation."""
