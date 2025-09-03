"""
Unit tests for the PMDParser class.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock
from parser.app_parser import PMDParser
from parser.models import ProjectContext, PMDModel, ScriptModel, AMDModel


class TestPMDParser:
    """Test cases for PMDParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PMDParser()
        self.mock_source_file = Mock()
        self.mock_source_file.content = "test content"
    
    def test_init(self):
        """Test parser initialization."""
        assert self.parser.supported_extensions == {'.pmd', '.script', '.amd', '.pod', '.smd'}
    
    def test_parse_files_empty_map(self):
        """Test parsing empty source files map."""
        result = self.parser.parse_files({})
        assert isinstance(result, ProjectContext)
        assert len(result.pmds) == 0
        assert len(result.scripts) == 0
        assert result.amd is None
    
    def test_parse_pmd_file_json_success(self):
        """Test successful JSON parsing of PMD file."""
        # Mock PMD content as JSON
        pmd_content = json.dumps({
            "pageId": "test-page",
            "securityDomains": ["domain1"],
            "onLoad": "function() { var x = 1; }",
            "script": "var y = 2;"
        })
        
        mock_file = Mock()
        mock_file.content = pmd_content
        
        context = ProjectContext()
        self.parser._parse_pmd_file("test.pmd", mock_file, context)
        
        assert "test-page" in context.pmds
        pmd_model = context.pmds["test-page"]
        assert pmd_model.pageId == "test-page"
        assert pmd_model.securityDomains == ["domain1"]
        assert pmd_model.onLoad == "function() { var x = 1; }"
        assert pmd_model.script == "var y = 2;"
    
    def test_parse_pmd_file_json_fallback(self):
        """Test PMD file parsing fallback when JSON fails."""
        # Mock PMD content as plain text
        pmd_content = "This is not JSON\nonLoad: function() { var x = 1; }\nscript: var y = 2;"
        
        mock_file = Mock()
        mock_file.content = pmd_content
        
        context = ProjectContext()
        self.parser._parse_pmd_file("test.pmd", mock_file, context)
        
        # Should use filename as pageId in fallback
        assert "test" in context.pmds
        pmd_model = context.pmds["test"]
        assert pmd_model.pageId == "test"
        assert pmd_model.onLoad == pmd_content  # Contains 'onLoad'
        assert pmd_model.script == pmd_content  # Contains 'script'
    
    def test_parse_script_file(self):
        """Test script file parsing."""
        script_content = "var x = 1;\nfunction test() { return x; }"
        
        mock_file = Mock()
        mock_file.content = script_content
        
        context = ProjectContext()
        self.parser._parse_script_file("utils.script", mock_file, context)
        
        assert "utils.script" in context.scripts
        script_model = context.scripts["utils.script"]
        assert script_model.source == script_content
        assert script_model.file_path == "utils.script"
    
    def test_parse_amd_file_json_success(self):
        """Test successful JSON parsing of AMD file."""
        amd_content = json.dumps({
            "routes": {
                "main": {"pageId": "main-page", "parameters": []}
            },
            "baseUrls": {"api": "/api/v1"}
        })
        
        mock_file = Mock()
        mock_file.content = amd_content
        
        context = ProjectContext()
        self.parser._parse_amd_file("app.amd", mock_file, context)
        
        assert context.amd is not None
        assert context.amd.routes["main"].pageId == "main-page"
        assert context.amd.baseUrls["api"] == "/api/v1"
    
    def test_parse_amd_file_json_fallback(self):
        """Test AMD file parsing fallback when JSON fails."""
        amd_content = "This is not valid JSON"
        
        mock_file = Mock()
        mock_file.content = amd_content
        
        context = ProjectContext()
        self.parser._parse_amd_file("app.amd", mock_file, context)
        
        assert context.amd is not None
        assert context.amd.routes == {}
    
    def test_parse_single_file_pmd(self):
        """Test single file parsing for PMD files."""
        pmd_content = '{"pageId": "test-page"}'
        
        mock_file = Mock()
        mock_file.content = pmd_content
        
        context = ProjectContext()
        self.parser._parse_single_file("test.pmd", mock_file, context)
        
        assert "test-page" in context.pmds
    
    def test_parse_single_file_script(self):
        """Test single file parsing for script files."""
        mock_file = Mock()
        mock_file.content = "var x = 1;"
        
        context = ProjectContext()
        self.parser._parse_single_file("utils.script", mock_file, context)
        
        assert "utils.script" in context.scripts
    
    def test_parse_single_file_amd(self):
        """Test single file parsing for AMD files."""
        amd_content = '{"routes": {}}'
        
        mock_file = Mock()
        mock_file.content = amd_content
        
        context = ProjectContext()
        self.parser._parse_single_file("app.amd", mock_file, context)
        
        assert context.amd is not None
    
    def test_parse_single_file_unsupported_extension(self):
        """Test parsing of unsupported file extensions."""
        mock_file = Mock()
        mock_file.content = "some content"
        
        context = ProjectContext()
        # Should not raise an exception
        self.parser._parse_single_file("test.pod", mock_file, context)
        
        # Should not add anything to context
        assert len(context.pmds) == 0
        assert len(context.scripts) == 0
        assert context.amd is None
    
    def test_parse_files_with_errors(self):
        """Test parsing files with some parsing errors."""
        source_files_map = {
            "valid.pmd": Mock(content='{"pageId": "valid"}'),
            "invalid.pmd": Mock(content="invalid json content"),
            "valid.script": Mock(content="var x = 1;")
        }
        
        # Mock the _parse_single_file method to simulate an error
        original_method = self.parser._parse_single_file
        
        def mock_parse_with_error(file_path, source_file, context):
            if file_path == "invalid.pmd":
                raise Exception("JSON parse error")
            return original_method(file_path, source_file, context)
        
        self.parser._parse_single_file = mock_parse_with_error
        
        try:
            result = self.parser.parse_files(source_files_map)
            
            # Should continue processing other files
            assert "valid" in result.pmds
            assert "valid.script" in result.scripts
            assert len(result.parsing_errors) == 1
            assert "invalid.pmd" in result.parsing_errors[0]
            
        finally:
            # Restore original method
            self.parser._parse_single_file = original_method
    
    def test_parse_files_integration(self):
        """Test full integration of parsing multiple files."""
        source_files_map = {
            "main.pmd": Mock(content='{"pageId": "main-page", "onLoad": "var x = 1;"}'),
            "utils.script": Mock(content="var y = 2;"),
            "app.amd": Mock(content='{"routes": {"main": {"pageId": "main-page"}}}')
        }
        
        result = self.parser.parse_files(source_files_map)
        
        # Check all files were parsed
        assert "main-page" in result.pmds
        assert "utils.script" in result.scripts
        assert result.amd is not None
        assert result.amd.routes["main"].pageId == "main-page"
        
        # Check no parsing errors
        assert len(result.parsing_errors) == 0


if __name__ == "__main__":
    pytest.main([__file__])
