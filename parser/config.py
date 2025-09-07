"""
Configuration models for the extend-reviewer tool.

This module defines the configuration structure for controlling rule execution,
file processing settings, and other tool behaviors.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum


class SeverityLevel(str, Enum):
    """Severity levels for findings."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class RuleConfig(BaseModel):
    """Configuration for a single rule."""
    enabled: bool = Field(default=True, description="Whether this rule is enabled")
    severity_override: Optional[SeverityLevel] = Field(default=None, description="Override the rule's default severity")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Custom settings for the rule")


class RulesConfig(BaseModel):
    """Configuration for all rules."""
    # Script validation rules
    SCRIPT001: RuleConfig = Field(default_factory=RuleConfig, description="Script var usage rule")
    SCRIPT002: RuleConfig = Field(default_factory=RuleConfig, description="Script nesting level rule")
    SCRIPT003: RuleConfig = Field(default_factory=RuleConfig, description="Script complexity rule")
    
    # Structure validation rules
    STRUCT001: RuleConfig = Field(default_factory=RuleConfig, description="Widget ID required rule")
    STRUCT002: RuleConfig = Field(default_factory=RuleConfig, description="Widget ID lower camel case rule")
    STRUCT003: RuleConfig = Field(default_factory=RuleConfig, description="Footer pod required rule")
    
    # Style validation rules
    STYLE001: RuleConfig = Field(default_factory=RuleConfig, description="Widget ID lower camel case rule")
    STYLE002: RuleConfig = Field(default_factory=RuleConfig, description="Endpoint name lower camel case rule")
    
    # PMD script rules (if they exist)
    PMD001: RuleConfig = Field(default_factory=RuleConfig, description="PMD script var usage rule")


class FileProcessingConfig(BaseModel):
    """Configuration for file processing."""
    max_file_size: int = Field(default=52428800, description="Maximum file size in bytes (50MB)")
    max_zip_size: int = Field(default=524288000, description="Maximum zip file size in bytes (500MB)")
    relevant_extensions: List[str] = Field(
        default=[".pod", ".pmd", ".script", ".amd", ".smd"],
        description="File extensions to process"
    )
    encoding: str = Field(default="utf-8", description="Default file encoding")
    log_level: str = Field(default="INFO", description="Logging level")
    chunk_size: int = Field(default=16384, description="Chunk size for file reading")
    max_concurrent_files: int = Field(default=20, description="Maximum concurrent files to process")
    fallback_encodings: List[str] = Field(
        default=["utf-8", "latin-1", "cp1252", "iso-8859-1"],
        description="Fallback encodings to try"
    )


class OutputConfig(BaseModel):
    """Configuration for output formatting."""
    format: str = Field(default="text", description="Output format (text, json, xml)")
    include_rule_details: bool = Field(default=True, description="Include rule ID and description in output")
    group_by_file: bool = Field(default=False, description="Group findings by file")
    sort_by_severity: bool = Field(default=True, description="Sort findings by severity")
    max_findings_per_rule: Optional[int] = Field(default=None, description="Maximum findings per rule (None = unlimited)")


class ExtendReviewerConfig(BaseModel):
    """Main configuration model for the extend-reviewer tool."""
    rules: RulesConfig = Field(default_factory=RulesConfig, description="Rule configuration")
    file_processing: FileProcessingConfig = Field(default_factory=FileProcessingConfig, description="File processing settings")
    output: OutputConfig = Field(default_factory=OutputConfig, description="Output formatting settings")
    
    # Global settings
    fail_on_error: bool = Field(default=False, description="Exit with error code if any ERROR severity findings are found")
    fail_on_warning: bool = Field(default=False, description="Exit with error code if any WARNING severity findings are found")
    quiet: bool = Field(default=False, description="Suppress non-essential output")
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ExtendReviewerConfig':
        """Load configuration from a JSON file."""
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return cls(**config_data)
    
    def to_file(self, config_path: str) -> None:
        """Save configuration to a JSON file."""
        import json
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
    
    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a specific rule is enabled."""
        rule_config = getattr(self.rules, rule_id, None)
        if rule_config is None:
            # If rule ID not found in config, assume it's enabled
            return True
        return rule_config.enabled
    
    def get_rule_severity(self, rule_id: str, default_severity: str) -> str:
        """Get the severity for a rule, using override if configured."""
        rule_config = getattr(self.rules, rule_id, None)
        if rule_config is None or rule_config.severity_override is None:
            return default_severity
        return rule_config.severity_override.value
    
    def get_rule_settings(self, rule_id: str) -> Dict[str, Any]:
        """Get custom settings for a rule."""
        rule_config = getattr(self.rules, rule_id, None)
        if rule_config is None:
            return {}
        return rule_config.custom_settings
