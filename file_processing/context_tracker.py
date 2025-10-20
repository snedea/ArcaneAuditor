"""
Context tracking for analysis to inform users about missing cross-file dependencies.

This module tracks which files were analyzed and which validation checks were skipped
due to missing context files (AMD, SMD, etc.).
"""
from dataclasses import dataclass, field
from typing import Set, List, Dict, Optional


@dataclass
class SkippedCheck:
    """Represents a validation check that was skipped by a rule."""
    rule_name: str
    check_name: str  # e.g., "error_page_exclusion", "app_id_detection"
    reason: str  # e.g., "Requires SMD file"


@dataclass
class AnalysisContext:
    """
    Tracks analysis context including which files were analyzed and what's missing.
    
    This helps users understand when validation is partial due to missing cross-file
    dependencies like AMD or SMD files.
    """
    analysis_type: str  # "full_app" | "individual_files"
    files_analyzed: List[str] = field(default_factory=list)
    files_present: Set[str] = field(default_factory=set)  # {"PMD", "POD", "AMD", "SMD", "SCRIPT"}
    
    # Track validation impact
    skipped_checks: List[SkippedCheck] = field(default_factory=list)
    
    def register_skipped_check(self, rule_name: str, check_name: str, reason: str) -> None:
        """
        Register when a rule skips a check due to missing context.
        
        Args:
            rule_name: The ID/name of the rule that skipped the check
            check_name: A descriptive name for the check that was skipped
            reason: Human-readable reason why the check was skipped
        """
        self.skipped_checks.append(SkippedCheck(rule_name, check_name, reason))
    
    @property
    def files_missing(self) -> Set[str]:
        """
        Calculate which standard file types are missing from the analysis.
        
        Returns:
            Set of missing file type identifiers (e.g., {"AMD", "SMD"})
        """
        all_types = {"PMD", "POD", "AMD", "SMD", "SCRIPT"}
        return all_types - self.files_present
    
    @property
    def is_complete(self) -> bool:
        """
        Check if all expected context files are present for complete analysis.
        
        A complete analysis requires at minimum AMD and SMD files, as these provide
        critical cross-file context for many validation rules.
        
        Returns:
            True if AMD and SMD are both present, False otherwise
        """
        return "AMD" in self.files_present and "SMD" in self.files_present
    
    @property
    def rules_not_executed(self) -> List[Dict]:
        """
        Get list of rules that didn't execute at all due to missing files.
        
        This identifies rules that are file-type specific and couldn't run because
        those file types weren't provided (e.g., AMD-only rules when no AMD file).
        
        Returns:
            List of dicts with 'rule' and 'reason' keys
        """
        not_executed = []
        
        # AMD-specific rules
        if "AMD" not in self.files_present:
            # HardcodedWorkdayAPIRule can run without AMD (checks PMD/POD endpoints)
            # Only add AMD-only rules here
            pass
        
        # SMD-specific rules
        if "SMD" not in self.files_present:
            not_executed.append({
                "rule": "HardcodedApplicationIdRule",
                "reason": "Requires SMD file"
            })
        
        return not_executed
    
    @property
    def rules_partially_executed(self) -> Dict[str, Dict]:
        """
        Group skipped checks by rule to show which rules ran partially.
        
        Returns:
            Dict mapping rule names to their skipped checks and reasons:
            {
                "RuleName": {
                    "skipped_checks": ["check1", "check2"],
                    "reason": "Requires SMD file"
                }
            }
        """
        partial = {}
        for skip in self.skipped_checks:
            if skip.rule_name not in partial:
                partial[skip.rule_name] = {
                    "skipped_checks": [],
                    "reason": skip.reason
                }
            partial[skip.rule_name]["skipped_checks"].append(skip.check_name)
        return partial
    
    def to_dict(self) -> Dict:
        """
        Export analysis context as dictionary for JSON serialization.
        
        Returns:
            Dictionary representation suitable for JSON export
        """
        return {
            "analysis_type": self.analysis_type,
            "files_analyzed": self.files_analyzed,
            "context_status": "complete" if self.is_complete else "partial",
            "files_present": sorted(list(self.files_present)),
            "files_missing": sorted(list(self.files_missing)),
            "impact": {
                "rules_not_executed": self.rules_not_executed,
                "rules_partially_executed": [
                    {
                        "rule": rule_name,
                        "skipped_checks": details["skipped_checks"],
                        "reason": details["reason"]
                    }
                    for rule_name, details in self.rules_partially_executed.items()
                ]
            }
        }

