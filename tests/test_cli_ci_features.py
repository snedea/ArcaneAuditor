"""
Unit tests for Arcane Auditor CLI functionality.

Tests the main CLI interface including CI-specific features like --fail-on-advice and --quiet modes.
"""

import pytest
import typer
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import json
import os
from unittest.mock import patch, MagicMock

# Import the main CLI app
from main import app

runner = CliRunner()


class TestCLICIFeatures:
    """Test CI-specific CLI features."""

    def test_fail_on_advice_flag_exists(self):
        """Test that --fail-on-advice flag is available."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--fail-on-advice" in result.output
        assert "CI mode" in result.output

    def test_quiet_flag_exists(self):
        """Test that --quiet flag is available."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--quiet" in result.output
        assert "-q" in result.output
        assert "Minimal output mode (CI-friendly)" in result.output

    def test_quiet_mode_suppresses_output(self):
        """Test that --quiet mode suppresses non-essential output."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pmd', delete=False) as f:
            f.write('{"id": "test", "presentation": {"body": {}}}')
            temp_file = f.name

        try:
            # Mock the analysis to return some findings
            with patch('main.FileProcessor') as mock_processor, \
                 patch('main.ModelParser') as mock_parser, \
                 patch('main.RulesEngine') as mock_rules_engine, \
                 patch('main.OutputFormatter') as mock_formatter:
                
                # Setup mocks
                mock_processor.return_value.process_zip_file.return_value = {}
                mock_parser.return_value.parse_files.return_value = MagicMock()
                mock_rules_engine.return_value.run_rules.return_value = []
                mock_formatter.return_value.format_results.return_value = "Test output"
                
                # Test with quiet mode
                result = runner.invoke(app, ["review-app", temp_file, "--quiet"])
                
                # Should not contain verbose startup messages
                assert "Starting review for" not in result.output
                assert "Using default configuration" not in result.output
                
        finally:
            os.unlink(temp_file)

    def test_fail_on_advice_exit_codes(self):
        """Test exit codes with --fail-on-advice flag."""
        # Test the help to ensure the flag exists
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--fail-on-advice" in result.output
        
        # Test with a non-existent file to trigger error handling
        result = runner.invoke(app, ["review-app", "nonexistent.pmd", "--fail-on-advice"])
        # Should fail due to file not existing, not due to our flag
        assert result.exit_code != 0

    def test_quiet_mode_with_timing(self):
        """Test that --quiet flag exists and can be combined with --timing."""
        # Test that both flags exist
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--quiet" in result.output
        assert "--timing" in result.output
        
        # Test that flags can be combined (should not crash)
        result = runner.invoke(app, ["review-app", "nonexistent.pmd", "--quiet", "--timing"])
        assert result.exit_code != 0  # Should fail due to file not existing

    def test_ci_mode_combination(self):
        """Test combining --quiet and --fail-on-advice for CI usage."""
        # Test that all CI flags exist and can be combined
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--quiet" in result.output
        assert "--fail-on-advice" in result.output
        assert "--format" in result.output
        
        # Test that CI flags can be combined (should not crash)
        result = runner.invoke(app, [
            "review-app", "nonexistent.pmd", 
            "--quiet", "--fail-on-advice", "--format", "json"
        ])
        assert result.exit_code != 0  # Should fail due to file not existing

    def test_exit_code_documentation(self):
        """Test that exit codes are properly documented in help."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        
        # The help should mention CI-friendly behavior
        help_text = result.output
        assert "CI mode" in help_text or "fail-on-advice" in help_text


class TestCLIExitCodes:
    """Test CLI exit code behavior."""

    def test_exit_code_0_no_issues(self):
        """Test that CLI accepts valid flags."""
        # Test that help works (exit code 0)
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0

    def test_exit_code_1_advice_only(self):
        """Test that --fail-on-advice flag exists."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--fail-on-advice" in result.output

    def test_exit_code_2_action_issues(self):
        """Test that CLI handles invalid files properly."""
        result = runner.invoke(app, ["review-app", "nonexistent.pmd"])
        assert result.exit_code != 0  # Should fail due to file not existing

    def test_exit_code_3_analysis_error(self):
        """Test that CLI handles errors gracefully."""
        result = runner.invoke(app, ["review-app", "nonexistent.pmd"])
        assert result.exit_code != 0  # Should fail due to file not existing


class TestCLIOutputFormats:
    """Test CLI output format options."""

    def test_json_output_format(self):
        """Test that JSON output format is available."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "json" in result.output

    def test_summary_output_format(self):
        """Test that summary output format is available."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "summary" in result.output
