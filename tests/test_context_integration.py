"""
Integration tests for the full context awareness flow.

Tests the complete pipeline from file parsing through rule execution to output formatting.
"""
import pytest
import json
from pathlib import Path
from parser.app_parser import ModelParser
from parser.rules_engine import RulesEngine
from parser.config import ArcaneAuditorConfig
from file_processing.models import SourceFile
from output.formatter import OutputFormatter, OutputFormat


class TestContextAwarenessIntegration:
    """Integration tests for context awareness across the full pipeline."""
    
    def test_full_pipeline_with_complete_context(self):
        """Test the complete pipeline when all context files are present."""
        # Create source files map with PMD, SMD, and AMD
        pmd_content = '{"pageId": "testPage", "securityDomains": ["domain1"], "presentation": {"attributes": {}, "title": {}, "body": {}, "footer": {}}}'
        smd_content = '{"id": "site1", "applicationId": "myApp", "siteId": "site1", "errorPageConfigurations": []}'
        amd_content = '{"applicationId": "myApp", "dataProviders": []}'
        
        source_files_map = {
            "page.pmd": SourceFile(
                path=Path("page.pmd"),
                content=pmd_content,
                size=len(pmd_content)
            ),
            "app.smd": SourceFile(
                path=Path("app.smd"),
                content=smd_content,
                size=len(smd_content)
            ),
            "app.amd": SourceFile(
                path=Path("app.amd"),
                content=amd_content,
                size=len(amd_content)
            )
        }
        
        # Parse files
        parser = ModelParser()
        context = parser.parse_files(source_files_map)
        
        # Verify analysis context was created
        assert context.analysis_context is not None
        assert context.analysis_context.is_complete
        assert "PMD" in context.analysis_context.files_present
        assert "SMD" in context.analysis_context.files_present
        assert "AMD" in context.analysis_context.files_present
        
        # Run rules
        config = ArcaneAuditorConfig()
        rules_engine = RulesEngine(config)
        findings = rules_engine.run(context)
        
        # Verify no skipped checks
        assert len(context.analysis_context.skipped_checks) == 0
        
        # Format output (console)
        formatter = OutputFormatter(OutputFormat.CONSOLE)
        output = formatter.format_results(findings, 3, len(rules_engine.rules), context)
        
        # Verify output contains complete context
        assert "Context: Complete Analysis" in output
        assert "All context files provided" in output
    
    def test_full_pipeline_with_partial_context(self):
        """Test the complete pipeline when some context files are missing."""
        # Create source files map with only PMD (missing SMD and AMD)
        pmd_content = '{"pageId": "testPage", "securityDomains": [], "presentation": {"attributes": {}, "title": {}, "body": {}, "footer": {}}}'
        
        source_files_map = {
            "page.pmd": SourceFile(
                path=Path("page.pmd"),
                content=pmd_content,
                size=len(pmd_content)
            )
        }
        
        # Parse files
        parser = ModelParser()
        context = parser.parse_files(source_files_map)
        
        # Verify analysis context was created
        assert context.analysis_context is not None
        assert not context.analysis_context.is_complete
        assert "PMD" in context.analysis_context.files_present
        assert "SMD" in context.analysis_context.files_missing
        assert "AMD" in context.analysis_context.files_missing
        
        # Run rules
        config = ArcaneAuditorConfig()
        rules_engine = RulesEngine(config)
        findings = rules_engine.run(context)
        
        # Verify skipped checks were registered
        assert len(context.analysis_context.skipped_checks) > 0
        
        # Format output (console)
        formatter = OutputFormatter(OutputFormat.CONSOLE)
        output = formatter.format_results(findings, 1, len(rules_engine.rules), context)
        
        # Verify output contains partial context warning
        assert "Context: Partial Analysis" in output
        assert "Missing Context Files:" in output
    
    def test_json_export_includes_context(self):
        """Test that JSON export includes complete context information."""
        # Create source files map with partial context
        pmd_content = '{"pageId": "testPage", "securityDomains": ["domain1"], "presentation": {"attributes": {}, "title": {}, "body": {}, "footer": {}}}'
        
        source_files_map = {
            "page.pmd": SourceFile(
                path=Path("page.pmd"),
                content=pmd_content,
                size=len(pmd_content)
            )
        }
        
        # Parse files
        parser = ModelParser()
        context = parser.parse_files(source_files_map)
        
        # Run rules
        config = ArcaneAuditorConfig()
        rules_engine = RulesEngine(config)
        findings = rules_engine.run(context)
        
        # Format as JSON
        formatter = OutputFormatter(OutputFormat.JSON)
        json_output = formatter.format_results(findings, 1, len(rules_engine.rules), context)
        result = json.loads(json_output)
        
        # Verify context is in JSON output
        assert "context" in result
        assert result["context"]["analysis_type"] == "individual_files"
        assert result["context"]["context_status"] == "partial"
        assert "PMD" in result["context"]["files_present"]
        assert "AMD" in result["context"]["files_missing"]
        assert "SMD" in result["context"]["files_missing"]
        
        # Verify impact information
        assert "impact" in result["context"]
        assert "rules_not_executed" in result["context"]["impact"]
        assert "rules_partially_executed" in result["context"]["impact"]

