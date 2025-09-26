"""
Configuration models for the Arcane Auditor tool.

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
    SEVERE = "SEVERE"


class RuleConfig(BaseModel):
    """Configuration for a single rule."""
    enabled: bool = Field(default=True, description="Whether this rule is enabled")
    severity_override: Optional[SeverityLevel] = Field(default=None, description="Override the rule's default severity")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Custom settings for the rule")


class RulesConfig(BaseModel):
    """Configuration for all rules using human-readable class names."""
    
    # Script Complexity & Structure Rules
    ScriptComplexityRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures scripts don't exceed complexity thresholds (max 10 cyclomatic complexity)")
    ScriptFunctionParameterCountRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures functions don't have too many parameters (max 5 parameters)")
    ScriptLongFunctionRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures functions don't exceed maximum line count (max 50 lines)")
    ScriptNestingLevelRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures scripts don't have excessive nesting levels (max 4 levels)")
    
    # Script Code Quality Rules
    ScriptConsoleLogRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures scripts don't contain console.log statements (production code)")
    ScriptVarUsageRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures scripts use 'let' or 'const' instead of 'var' (best practice)")
    ScriptFileVarUsageRule: RuleConfig = Field(default_factory=RuleConfig, description="Validates variable declaration and export patterns in standalone script files")
    ScriptVariableNamingRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures variables follow lowerCamelCase naming convention")
    ScriptFunctionalMethodUsageRule: RuleConfig = Field(default_factory=RuleConfig, description="Recommends using functional methods (map, filter, forEach) instead of manual loops")
    ScriptMagicNumberRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures scripts don't contain magic numbers (use named constants)")
    ScriptNullSafetyRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures property access chains are protected against null reference exceptions")
    ScriptFunctionReturnConsistencyRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures functions have consistent return patterns")
    ScriptStringConcatRule: RuleConfig = Field(default_factory=RuleConfig, description="Recommends using template literals instead of string concatenation")
    ScriptVerboseBooleanCheckRule: RuleConfig = Field(default_factory=RuleConfig, description="Recommends using concise boolean expressions")
    ScriptDescriptiveParameterRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures functional method parameters use descriptive names instead of single letters")
    
    # Script Unused Code Rules
    ScriptEmptyFunctionRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects empty function bodies")
    ScriptUnusedFunctionRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects functions that are declared but never called")
    ScriptUnusedFunctionParametersRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects unused function parameters")
    ScriptUnusedVariableRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures all declared variables are used (prevents dead code)")
    ScriptUnusedScriptIncludesRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects script files that are included but never used in PMD files")
    
    # Endpoint Structure Rules
    EndpointFailOnStatusCodesRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures endpoints handle failure status codes properly")
    EndpointNameLowerCamelCaseRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures endpoint names follow lowerCamelCase convention")
    EndpointOnSendSelfDataRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures endpoint onSend methods use self.data appropriately")
    EndpointBaseUrlTypeRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures endpoint URLs don't include hardcoded workday.com or apiGatewayEndpoint values")
    
    # Widget Structure Rules
    WidgetIdRequiredRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures all widgets have required 'id' field")
    WidgetIdLowerCamelCaseRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures widget IDs follow lowerCamelCase convention")
    
    # General Structure Rules
    FooterPodRequiredRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures footer widgets utilize pods")
    StringBooleanRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures boolean values are not stored as strings")
    PMDSectionOrderingRule: RuleConfig = Field(default_factory=RuleConfig, description="Ensures PMD file sections follow consistent ordering for better readability")
    HardcodedApplicationIdRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects hardcoded applicationId values that should be replaced with site.applicationId")
    HardcodedWidRule: RuleConfig = Field(default_factory=RuleConfig, description="Detects hardcoded WID values that should be configured in app attributes")
    PMDSecurityDomainRule: RuleConfig = Field(default_factory=RuleConfig, description="Validates that PMD files have a securityDomains section and that it is not empty")


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


class ArcaneAuditorConfig(BaseModel):
    """Main configuration model for the Arcane Auditor tool."""
    rules: RulesConfig = Field(default_factory=RulesConfig, description="Rule configuration")
    file_processing: FileProcessingConfig = Field(default_factory=FileProcessingConfig, description="File processing settings")
    output: OutputConfig = Field(default_factory=OutputConfig, description="Output formatting settings")
    
    # Global settings
    fail_on_severe: bool = Field(default=False, description="Exit with error code if any SEVERE severity findings are found")
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
    
    def is_rule_enabled(self, rule_class_name: str) -> bool:
        """Check if a specific rule is enabled using class name."""
        rule_config = getattr(self.rules, rule_class_name, None)
        if rule_config is None:
            # If rule class name not found in config, assume it's disabled
            return False
        return rule_config.enabled
    
    def get_rule_severity(self, rule_class_name: str, default_severity: str) -> str:
        """Get the severity for a rule using class name, using override if configured."""
        rule_config = getattr(self.rules, rule_class_name, None)
        if rule_config is None or rule_config.severity_override is None:
            return default_severity
        return rule_config.severity_override.value
    
    def get_rule_settings(self, rule_class_name: str) -> Dict[str, Any]:
        """Get custom settings for a rule using class name."""
        rule_config = getattr(self.rules, rule_class_name, None)
        if rule_config is None:
            return {}
        return rule_config.custom_settings
