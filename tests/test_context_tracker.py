"""
Unit tests for the AnalysisContext and SkippedCheck classes.
"""
import pytest
from file_processing.context_tracker import AnalysisContext, SkippedCheck


class TestSkippedCheck:
    """Tests for the SkippedCheck dataclass."""
    
    def test_skipped_check_creation(self):
        """Test creating a SkippedCheck instance."""
        skip = SkippedCheck(
            rule_name="TestRule",
            check_name="test_check",
            reason="Test reason"
        )
        
        assert skip.rule_name == "TestRule"
        assert skip.check_name == "test_check"
        assert skip.reason == "Test reason"


class TestAnalysisContext:
    """Tests for the AnalysisContext class."""
    
    def test_empty_context_creation(self):
        """Test creating an empty AnalysisContext."""
        context = AnalysisContext(analysis_type="individual_files")
        
        assert context.analysis_type == "individual_files"
        assert context.files_analyzed == []
        assert context.files_present == set()
        assert context.skipped_checks == []
    
    def test_files_missing_property(self):
        """Test files_missing property calculation."""
        context = AnalysisContext(
            analysis_type="individual_files",
            files_present={"PMD", "AMD"}
        )
        
        missing = context.files_missing
        assert "POD" in missing
        assert "SMD" in missing
        assert "SCRIPT" in missing
        assert "PMD" not in missing
        assert "AMD" not in missing
    
    def test_is_complete_with_all_files(self):
        """Test is_complete returns True when AMD and SMD present."""
        context = AnalysisContext(
            analysis_type="full_app",
            files_present={"PMD", "AMD", "SMD"}
        )
        
        assert context.is_complete is True
    
    def test_is_complete_missing_amd(self):
        """Test is_complete returns False when AMD missing."""
        context = AnalysisContext(
            analysis_type="individual_files",
            files_present={"PMD", "SMD"}
        )
        
        assert context.is_complete is False
    
    def test_is_complete_missing_smd(self):
        """Test is_complete returns False when SMD missing."""
        context = AnalysisContext(
            analysis_type="individual_files",
            files_present={"PMD", "AMD"}
        )
        
        assert context.is_complete is False
    
    def test_is_complete_missing_both(self):
        """Test is_complete returns False when both AMD and SMD missing."""
        context = AnalysisContext(
            analysis_type="individual_files",
            files_present={"PMD", "POD"}
        )
        
        assert context.is_complete is False
    
    def test_register_skipped_check(self):
        """Test registering a skipped check."""
        context = AnalysisContext(analysis_type="individual_files")
        
        context.register_skipped_check(
            rule_name="TestRule",
            check_name="test_check",
            reason="Missing SMD"
        )
        
        assert len(context.skipped_checks) == 1
        skip = context.skipped_checks[0]
        assert skip.rule_name == "TestRule"
        assert skip.check_name == "test_check"
        assert skip.reason == "Missing SMD"
    
    def test_register_multiple_skipped_checks(self):
        """Test registering multiple skipped checks."""
        context = AnalysisContext(analysis_type="individual_files")
        
        context.register_skipped_check("Rule1", "check1", "reason1")
        context.register_skipped_check("Rule1", "check2", "reason1")
        context.register_skipped_check("Rule2", "check1", "reason2")
        
        assert len(context.skipped_checks) == 3
    
    def test_rules_not_executed_with_amd(self):
        """Test rules_not_executed when AMD present."""
        context = AnalysisContext(
            analysis_type="individual_files",
            files_present={"PMD", "AMD", "SMD"}
        )
        
        not_executed = context.rules_not_executed
        assert len(not_executed) == 0
    
    def test_rules_not_executed_without_amd(self):
        """Test rules_not_executed when AMD missing."""
        context = AnalysisContext(
            analysis_type="individual_files",
            files_present={"PMD", "SMD"}
        )
        
        not_executed = context.rules_not_executed
        assert len(not_executed) == 1
        assert not_executed[0]["rule"] == "AMDDataProvidersWorkdayRule"
        assert not_executed[0]["reason"] == "Requires AMD file"
    
    def test_rules_partially_executed_empty(self):
        """Test rules_partially_executed with no skipped checks."""
        context = AnalysisContext(analysis_type="individual_files")
        
        partial = context.rules_partially_executed
        assert len(partial) == 0
    
    def test_rules_partially_executed_single_rule(self):
        """Test rules_partially_executed with one rule skipping checks."""
        context = AnalysisContext(analysis_type="individual_files")
        
        context.register_skipped_check("TestRule", "check1", "Missing SMD")
        context.register_skipped_check("TestRule", "check2", "Missing SMD")
        
        partial = context.rules_partially_executed
        assert len(partial) == 1
        assert "TestRule" in partial
        assert partial["TestRule"]["skipped_checks"] == ["check1", "check2"]
        assert partial["TestRule"]["reason"] == "Missing SMD"
    
    def test_rules_partially_executed_multiple_rules(self):
        """Test rules_partially_executed with multiple rules."""
        context = AnalysisContext(analysis_type="individual_files")
        
        context.register_skipped_check("Rule1", "check1", "Missing SMD")
        context.register_skipped_check("Rule2", "check2", "Missing AMD")
        
        partial = context.rules_partially_executed
        assert len(partial) == 2
        assert "Rule1" in partial
        assert "Rule2" in partial
        assert partial["Rule1"]["skipped_checks"] == ["check1"]
        assert partial["Rule2"]["skipped_checks"] == ["check2"]
    
    def test_to_dict_complete_analysis(self):
        """Test to_dict() for complete analysis."""
        context = AnalysisContext(
            analysis_type="full_app",
            files_analyzed=["app.amd", "app.smd", "page.pmd"],
            files_present={"AMD", "SMD", "PMD"}
        )
        
        result = context.to_dict()
        
        assert result["analysis_type"] == "full_app"
        assert len(result["files_analyzed"]) == 3
        assert result["context_status"] == "complete"
        assert "AMD" in result["files_present"]
        assert "SMD" in result["files_present"]
        assert "POD" in result["files_missing"]
        assert len(result["impact"]["rules_not_executed"]) == 0
        assert len(result["impact"]["rules_partially_executed"]) == 0
    
    def test_to_dict_partial_analysis(self):
        """Test to_dict() for partial analysis with skipped checks."""
        context = AnalysisContext(
            analysis_type="individual_files",
            files_analyzed=["page.pmd"],
            files_present={"PMD"}
        )
        
        context.register_skipped_check("TestRule", "check1", "Missing SMD")
        
        result = context.to_dict()
        
        assert result["analysis_type"] == "individual_files"
        assert result["context_status"] == "partial"
        assert "AMD" in result["files_missing"]
        assert "SMD" in result["files_missing"]
        assert len(result["impact"]["rules_not_executed"]) == 2  # AMDDataProvidersWorkdayRule and HardcodedApplicationIdRule
        assert len(result["impact"]["rules_partially_executed"]) == 1
        assert result["impact"]["rules_partially_executed"][0]["rule"] == "TestRule"
    
    def test_to_dict_sorted_output(self):
        """Test that to_dict() returns sorted lists for consistency."""
        context = AnalysisContext(
            analysis_type="individual_files",
            files_present={"SMD", "PMD", "AMD"}  # Unsorted
        )
        
        result = context.to_dict()
        
        # Should be sorted alphabetically
        assert result["files_present"] == ["AMD", "PMD", "SMD"]
        assert result["files_missing"] == ["POD", "SCRIPT"]

