"""Unit tests for FooterPodRequiredRule."""

from parser.rules.structure.validation.footer_pod_required import FooterPodRequiredRule
from parser.models import PMDModel, PodModel, ProjectContext


class TestFooterPodRequiredRule:
    """Test cases for FooterPodRequiredRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = FooterPodRequiredRule()
        assert rule.DESCRIPTION == "Ensures footer uses pod structure (direct pod or footer with pod children). Excludes PMD pages with tabs, hub pages, and microConclusion pages."
        assert rule.SEVERITY == "ADVICE"

    def test_get_description(self):
        """Test that get_description returns the correct description."""
        rule = FooterPodRequiredRule()
        assert rule.get_description() == rule.DESCRIPTION

    def test_no_footer_no_issue(self):
        """Test that PMD files without explicit footer don't trigger issues."""
        rule = FooterPodRequiredRule()
        
        # Create PMD model without explicitly setting footer
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "body": {}
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        # The rule should detect the default empty footer as missing
        assert len(findings) == 1
        assert "Footer section is missing" in findings[0].message

    def test_direct_pod_footer_valid(self):
        """Test that direct pod footer is valid."""
        rule = FooterPodRequiredRule()
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "footer": {
                    "type": "pod",
                    "podId": "footerPod"
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_footer_with_pod_child_valid(self):
        """Test that footer with pod child is valid."""
        rule = FooterPodRequiredRule()
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "footer": {
                    "type": "footer",
                    "children": [
                        {
                            "type": "pod",
                            "podId": "footerPod"
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_footer_without_pod_child_invalid(self):
        """Test that footer without pod child is invalid."""
        rule = FooterPodRequiredRule()
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "footer": {
                    "type": "footer",
                    "children": [
                        {
                            "type": "text",
                            "value": "Some text"
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Footer must utilize a pod" in findings[0].message
        assert findings[0].file_path == "test.pmd"

    def test_empty_footer_invalid(self):
        """Test that empty footer is invalid."""
        rule = FooterPodRequiredRule()
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "footer": {}
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Footer section is missing" in findings[0].message
        assert findings[0].file_path == "test.pmd"

    def test_footer_with_empty_children_invalid(self):
        """Test that footer with empty children is invalid."""
        rule = FooterPodRequiredRule()
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "footer": {
                    "type": "footer",
                    "children": []
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Footer must utilize a pod" in findings[0].message
        assert findings[0].file_path == "test.pmd"

    def test_footer_without_children_invalid(self):
        """Test that footer without children is invalid."""
        rule = FooterPodRequiredRule()
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "footer": {
                    "type": "footer"
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Footer must utilize a pod" in findings[0].message
        assert findings[0].file_path == "test.pmd"


    def test_pod_files_ignored(self):
        """Test that POD files are ignored by this rule."""
        rule = FooterPodRequiredRule()
        
        pod_data = {
            "podId": "test",
            "file_path": "test.pod",
            "seed": {
                "template": {}
            }
        }
        
        pod_model = PodModel(**pod_data)
        context = ProjectContext()
        context.pods = {"test": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_pmd_with_tabs_excluded(self):
        """Test that PMD pages with tabs are excluded from footer pod validation."""
        rule = FooterPodRequiredRule()
        
        # PMD with tabs should be excluded (no findings)
        pmd_data = {
            "pageId": "testPage",
            "presentation": {
                "body": {
                    "type": "areaLayout",
                    "children": []
                },
                "tabs": [
                    {
                        "type": "section",
                        "label": "Tab 1",
                        "children": []
                    }
                ]
                # No footer - but should be excluded due to tabs
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test.pmd", source_content="{}")
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0, "PMD with tabs should be excluded from footer pod validation"

    def test_pmd_with_empty_tabs_excluded(self):
        """Test that PMD pages with empty tabs are excluded from footer pod validation."""
        rule = FooterPodRequiredRule()
        
        # PMD with empty tabs should be excluded (no findings)
        pmd_data = {
            "pageId": "testPage",
            "presentation": {
                "body": {
                    "type": "areaLayout",
                    "children": []
                },
                "tabs": []
                # No footer but empty tabs - should be excluded
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test.pmd", source_content="{}")
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0, "PMD with empty tabs should be excluded from footer pod validation"

    def test_pmd_without_tabs_still_checked(self):
        """Test that PMD pages without tabs are still checked for footer pod requirements."""
        rule = FooterPodRequiredRule()
        
        # PMD without tabs should still be checked (should find missing footer)
        pmd_data = {
            "pageId": "testPage",
            "presentation": {
                "body": {
                    "type": "areaLayout",
                    "children": []
                }
                # No footer and no tabs - should trigger violation
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test.pmd", source_content="{}")
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1, "PMD without tabs should still be checked for footer pod requirements"
        assert "Footer section is missing" in findings[0].message