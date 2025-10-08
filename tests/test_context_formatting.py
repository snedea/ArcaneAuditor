"""
Integration tests for context awareness formatting in CLI and JSON output.
"""
import pytest
from output.formatter import OutputFormatter, OutputFormat
from parser.models import ProjectContext
from file_processing.context_tracker import AnalysisContext
from parser.rules.base import Finding


class MockRule:
    """Mock rule for testing."""
    def __init__(self, rule_id="TestRule", severity="ADVICE"):
        self.ID = rule_id
        self.SEVERITY = severity


class TestContextFormattingCLI:
    """Tests for CLI console output with context awareness."""
    
    def test_console_output_with_complete_context(self):
        """Test console output when all context files are present."""
        # Create context with complete analysis
        context = ProjectContext()
        context.analysis_context = AnalysisContext(
            analysis_type="full_app",
            files_analyzed=["app.amd", "app.smd", "page.pmd"],
            files_present={"AMD", "SMD", "PMD"}
        )
        
        # Create formatter
        formatter = OutputFormatter(OutputFormat.CONSOLE)
        
        # Format with no findings
        output = formatter.format_results([], 3, 10, context)
        
        # Should show complete analysis
        assert "✓  Context: Complete Analysis" in output
        assert "All context files provided" in output
        assert "Missing Context Files" not in output
    
    def test_console_output_with_partial_context(self):
        """Test console output when context files are missing."""
        # Create context with partial analysis
        context = ProjectContext()
        context.analysis_context = AnalysisContext(
            analysis_type="individual_files",
            files_analyzed=["page.pmd"],
            files_present={"PMD"}
        )
        
        # Register a skipped check
        context.register_skipped_check(
            "TestRule",
            "test_check",
            "Requires SMD file"
        )
        
        # Create formatter
        formatter = OutputFormatter(OutputFormat.CONSOLE)
        
        # Format with no findings
        output = formatter.format_results([], 1, 10, context)
        
        # Should show partial analysis
        assert "ℹ️  Context: Partial Analysis" in output
        assert "Missing Context Files:" in output
        assert "AMD" in output
        assert "SMD" in output
        assert "Rules Partially Executed" in output
        assert "TestRule" in output
        assert "test_check skipped" in output
    
    def test_console_output_with_rules_not_executed(self):
        """Test console output showing rules that didn't run."""
        # Create context missing AMD (which prevents AMDDataProvidersWorkdayRule)
        context = ProjectContext()
        context.analysis_context = AnalysisContext(
            analysis_type="individual_files",
            files_analyzed=["page.pmd", "app.smd"],
            files_present={"PMD", "SMD"}
        )
        
        # Create formatter
        formatter = OutputFormatter(OutputFormat.CONSOLE)
        
        # Format with no findings
        output = formatter.format_results([], 2, 10, context)
        
        # Should show rules not executed
        assert "Rules Not Executed" in output
        assert "AMDDataProvidersWorkdayRule" in output
        assert "Requires AMD file" in output
    
    def test_console_output_without_context(self):
        """Test console output when context is None (backwards compatibility)."""
        # Create formatter
        formatter = OutputFormatter(OutputFormat.CONSOLE)
        
        # Format with no context
        output = formatter.format_results([], 1, 10, None)
        
        # Should not crash, should not show context panel
        assert "Context: Complete Analysis" not in output
        assert "Context: Partial Analysis" not in output
        assert "No issues found" in output


class TestContextFormattingJSON:
    """Tests for JSON output with context awareness."""
    
    def test_json_output_with_complete_context(self):
        """Test JSON output when all context files are present."""
        import json
        
        # Create context with complete analysis
        context = ProjectContext()
        context.analysis_context = AnalysisContext(
            analysis_type="full_app",
            files_analyzed=["app.amd", "app.smd", "page.pmd"],
            files_present={"AMD", "SMD", "PMD"}
        )
        
        # Create formatter
        formatter = OutputFormatter(OutputFormat.JSON)
        
        # Format with no findings
        output = formatter.format_results([], 3, 10, context)
        result = json.loads(output)
        
        # Should have context field
        assert "context" in result
        assert result["context"]["analysis_type"] == "full_app"
        assert result["context"]["context_status"] == "complete"
        assert len(result["context"]["files_analyzed"]) == 3
        assert "AMD" in result["context"]["files_present"]
        assert "SMD" in result["context"]["files_present"]
    
    def test_json_output_with_partial_context(self):
        """Test JSON output when context files are missing."""
        import json
        
        # Create context with partial analysis
        context = ProjectContext()
        context.analysis_context = AnalysisContext(
            analysis_type="individual_files",
            files_analyzed=["page.pmd"],
            files_present={"PMD"}
        )
        
        # Register a skipped check
        context.register_skipped_check(
            "TestRule",
            "test_check",
            "Requires SMD file"
        )
        
        # Create formatter
        formatter = OutputFormatter(OutputFormat.JSON)
        
        # Format with no findings
        output = formatter.format_results([], 1, 10, context)
        result = json.loads(output)
        
        # Should have context field with partial status
        assert "context" in result
        assert result["context"]["context_status"] == "partial"
        assert "AMD" in result["context"]["files_missing"]
        assert "SMD" in result["context"]["files_missing"]
        
        # Should have impact information
        assert "impact" in result["context"]
        assert len(result["context"]["impact"]["rules_not_executed"]) == 1
        assert len(result["context"]["impact"]["rules_partially_executed"]) == 1
        
        # Check partially executed rule details
        partial_rule = result["context"]["impact"]["rules_partially_executed"][0]
        assert partial_rule["rule"] == "TestRule"
        assert "test_check" in partial_rule["skipped_checks"]
        assert partial_rule["reason"] == "Requires SMD file"
    
    def test_json_output_without_context(self):
        """Test JSON output when context is None (backwards compatibility)."""
        import json
        
        # Create formatter
        formatter = OutputFormatter(OutputFormat.JSON)
        
        # Format with no context
        output = formatter.format_results([], 1, 10, None)
        result = json.loads(output)
        
        # Should not have context field
        assert "context" not in result
        assert "summary" in result
        assert "findings" in result

