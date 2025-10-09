"""Unit tests for NoPMDSessionVariablesRule."""

from parser.rules.structure.endpoints.no_pmd_session_variables import NoPMDSessionVariablesRule
from parser.models import PMDModel, ProjectContext


class TestNoPMDSessionVariablesRule:
    """Test cases for NoPMDSessionVariablesRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = NoPMDSessionVariablesRule()
        assert rule.ID == "NoPMDSessionVariablesRule"
        assert rule.DESCRIPTION == "Detects outboundVariable endpoints with variableScope: session which can cause performance degradation"
        assert rule.SEVERITY == "ACTION"

    def test_get_description(self):
        """Test that get_description returns the correct description."""
        rule = NoPMDSessionVariablesRule()
        assert rule.get_description() == rule.DESCRIPTION

    def test_outbound_variable_with_session_scope(self):
        """Test that outboundVariable with session scope is flagged."""
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "outboundEndpoints": [
                {
                    "name": "saveUserPreference",
                    "type": "outboundVariable",
                    "variableScope": "session"
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "saveUserPreference" in findings[0].message
        assert "session" in findings[0].message.lower()
        assert "performance" in findings[0].message.lower()
        assert findings[0].severity == "ACTION"

    def test_outbound_variable_with_page_scope(self):
        """Test that outboundVariable with page scope is not flagged."""
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "outboundEndpoints": [
                {
                    "name": "saveUserPreference",
                    "type": "outboundVariable",
                    "variableScope": "page"
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_outbound_variable_with_task_scope(self):
        """Test that outboundVariable with task scope is not flagged."""
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "outboundEndpoints": [
                {
                    "name": "saveUserPreference",
                    "type": "outboundVariable",
                    "variableScope": "task"
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_non_outbound_variable_type_not_flagged(self):
        """Test that non-outboundVariable endpoints are not flagged even with session scope."""
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "outboundEndpoints": [
                {
                    "name": "callAPI",
                    "type": "rest",
                    "variableScope": "session"
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_outbound_variable_without_variable_scope(self):
        """Test that outboundVariable without variableScope is not flagged."""
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "outboundEndpoints": [
                {
                    "name": "saveData",
                    "type": "outboundVariable"
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_inbound_endpoints_not_checked(self):
        """Test that inbound endpoints are not checked (only outbound)."""
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "getData",
                    "type": "outboundVariable",
                    "variableScope": "session"
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0  # Inbound endpoints not checked

    def test_multiple_outbound_variables_with_session_scope(self):
        """Test that multiple outboundVariable endpoints with session scope are all flagged."""
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "outboundEndpoints": [
                {
                    "name": "savePreference1",
                    "type": "outboundVariable",
                    "variableScope": "session"
                },
                {
                    "name": "savePreference2",
                    "type": "outboundVariable",
                    "variableScope": "session"
                },
                {
                    "name": "savePreference3",
                    "type": "outboundVariable",
                    "variableScope": "page"
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert any("savePreference1" in f.message for f in findings)
        assert any("savePreference2" in f.message for f in findings)
        assert not any("savePreference3" in f.message for f in findings)

    def test_empty_outbound_endpoints_no_issues(self):
        """Test that files with no outbound endpoints don't cause issues."""
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "outboundEndpoints": []
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_variable_scope_string_session(self):
        """Test that variableScope: 'session' as string is also caught."""
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "outboundEndpoints": [
                {
                    "name": "saveData",
                    "type": "outboundVariable",
                    "variableScope": "session"  # String value
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "saveData" in findings[0].message

    def test_multiple_pmds_with_session_variables(self):
        """Test that session variables in multiple PMD files are all flagged."""
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        
        # First PMD
        pmd_data1 = {
            "pageId": "page1",
            "file_path": "page1.pmd",
            "outboundEndpoints": [
                {
                    "name": "saveData1",
                    "type": "outboundVariable",
                    "variableScope": "session"
                }
            ]
        }
        pmd_model1 = PMDModel(**pmd_data1)
        
        # Second PMD
        pmd_data2 = {
            "pageId": "page2",
            "file_path": "page2.pmd",
            "outboundEndpoints": [
                {
                    "name": "saveData2",
                    "type": "outboundVariable",
                    "variableScope": "session"
                }
            ]
        }
        pmd_model2 = PMDModel(**pmd_data2)
        
        context.pmds = {"page1": pmd_model1, "page2": pmd_model2}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert any(f.file_path == "page1.pmd" for f in findings)
        assert any(f.file_path == "page2.pmd" for f in findings)

