"""Test FooterPodRequiredRule exclusions for hub and microConclusion pages."""

import pytest
from parser.models import PMDModel
from parser.rules.structure.validation.footer_pod_required import FooterPodRequiredRule
from parser.models import ProjectContext


class TestFooterPodHubMicroExclusions:
    """Test FooterPodRequiredRule exclusions for hub and microConclusion pages."""

    @pytest.fixture
    def rule(self):
        """Create FooterPodRequiredRule instance."""
        return FooterPodRequiredRule()

    @pytest.fixture
    def context(self):
        """Create ProjectContext instance."""
        return ProjectContext()
    
    def test_rule_metadata(self, rule):
        """Test rule metadata is correctly set."""
        assert rule.ID == "RULE000"  # Base class default
        assert rule.SEVERITY == "ADVICE"
        assert "footer" in rule.DESCRIPTION.lower()

    def test_hub_page_excluded(self, rule, context):
        """Test that hub pages are excluded from footer pod requirements."""
        # Create PMD with hub body type
        pmd_data = {
            "pageId": "testHubPage",
            "presentation": {
                "body": {
                    "type": "hub",
                    "children": []
                },
                "footer": {
                    "type": "text",
                    "label": "Footer without pod"
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test_hub.pmd", source_content="{}")
        
        # Should not yield any findings for hub page
        findings = list(rule.visit_pmd(pmd_model, context))
        assert len(findings) == 0

    def test_micro_conclusion_page_excluded(self, rule, context):
        """Test that microConclusion pages are excluded from footer pod requirements."""
        # Create PMD with microConclusion attribute
        pmd_data = {
            "pageId": "testMicroPage",
            "presentation": {
                "body": {
                    "type": "layout",
                    "children": []
                },
                "footer": {
                    "type": "text",
                    "label": "Footer without pod"
                },
                "attributes": {
                    "microConclusion": True
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test_micro.pmd", source_content="{}")
        
        # Should not yield any findings for microConclusion page
        findings = list(rule.visit_pmd(pmd_model, context))
        assert len(findings) == 0

    def test_hub_page_with_tabs_still_excluded(self, rule, context):
        """Test that hub pages with tabs are still excluded."""
        # Create PMD with both hub type and tabs
        pmd_data = {
            "pageId": "testHubTabsPage",
            "presentation": {
                "body": {
                    "type": "hub",
                    "children": []
                },
                "footer": {
                    "type": "text",
                    "label": "Footer without pod"
                },
                "tabs": []
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test_hub_tabs.pmd", source_content="{}")
        
        # Should not yield any findings for hub page with tabs
        findings = list(rule.visit_pmd(pmd_model, context))
        assert len(findings) == 0

    def test_micro_conclusion_page_with_tabs_still_excluded(self, rule, context):
        """Test that microConclusion pages with tabs are still excluded."""
        # Create PMD with both microConclusion and tabs
        pmd_data = {
            "pageId": "testMicroTabsPage",
            "presentation": {
                "body": {
                    "type": "layout",
                    "children": []
                },
                "footer": {
                    "type": "text",
                    "label": "Footer without pod"
                },
                "tabs": [],
                "attributes": {
                    "microConclusion": True
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test_micro_tabs.pmd", source_content="{}")
        
        # Should not yield any findings for microConclusion page with tabs
        findings = list(rule.visit_pmd(pmd_model, context))
        assert len(findings) == 0

    def test_regular_page_still_checked(self, rule, context):
        """Test that regular pages (not hub, not microConclusion, no tabs) are still checked."""
        # Create regular PMD without proper footer pod
        pmd_data = {
            "pageId": "testRegularPage",
            "presentation": {
                "body": {
                    "type": "layout",
                    "children": []
                },
                "footer": {
                    "type": "text",
                    "label": "Footer without pod"
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test_regular.pmd", source_content="{}")
        
        # Should yield findings for regular page without proper footer pod
        findings = list(rule.visit_pmd(pmd_model, context))
        assert len(findings) == 1
        assert "Footer must utilize a pod" in findings[0].message

    def test_hub_page_with_proper_footer_pod_still_excluded(self, rule, context):
        """Test that hub pages with proper footer pods are still excluded (no findings)."""
        # Create PMD with hub type and proper footer pod
        pmd_data = {
            "pageId": "testHubWithPodPage",
            "presentation": {
                "body": {
                    "type": "hub",
                    "children": []
                },
                "footer": {
                    "type": "pod",
                    "podId": "footerPod"
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test_hub_pod.pmd", source_content="{}")
        
        # Should not yield any findings for hub page (excluded regardless of footer)
        findings = list(rule.visit_pmd(pmd_model, context))
        assert len(findings) == 0

    def test_micro_conclusion_page_with_proper_footer_pod_still_excluded(self, rule, context):
        """Test that microConclusion pages with proper footer pods are still excluded (no findings)."""
        # Create PMD with microConclusion and proper footer pod
        pmd_data = {
            "pageId": "testMicroWithPodPage",
            "presentation": {
                "body": {
                    "type": "layout",
                    "children": []
                },
                "footer": {
                    "type": "pod",
                    "podId": "footerPod"
                },
                "attributes": {
                    "microConclusion": True
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data, file_path="test_micro_pod.pmd", source_content="{}")
        
        # Should not yield any findings for microConclusion page (excluded regardless of footer)
        findings = list(rule.visit_pmd(pmd_model, context))
        assert len(findings) == 0

    def test_hub_detection_edge_cases(self, rule, context):
        """Test edge cases for hub page detection."""
        # Test with missing body
        pmd_data = {
            "pageId": "testNoBodyPage",
            "presentation": {
                "footer": {"type": "text", "label": "Footer"}
            }
        }
        pmd_model = PMDModel(**pmd_data, file_path="test_no_body.pmd", source_content="{}")
        assert not rule._is_hub_page(pmd_model)

        # Test with body but no type
        pmd_data = {
            "pageId": "testNoTypePage",
            "presentation": {
                "body": {"children": []},
                "footer": {"type": "text", "label": "Footer"}
            }
        }
        pmd_model = PMDModel(**pmd_data, file_path="test_no_type.pmd", source_content="{}")
        assert not rule._is_hub_page(pmd_model)

        # Test with body type != "hub"
        pmd_data = {
            "pageId": "testLayoutPage",
            "presentation": {
                "body": {"type": "layout", "children": []},
                "footer": {"type": "text", "label": "Footer"}
            }
        }
        pmd_model = PMDModel(**pmd_data, file_path="test_layout.pmd", source_content="{}")
        assert not rule._is_hub_page(pmd_model)

    def test_micro_conclusion_detection_edge_cases(self, rule, context):
        """Test edge cases for microConclusion page detection."""
        # Test with missing presentation
        pmd_data = {"pageId": "testNoPresentationPage"}
        pmd_model = PMDModel(**pmd_data, file_path="test_no_presentation.pmd", source_content="{}")
        assert not rule._is_micro_conclusion_page(pmd_model)

        # Test with missing attributes
        pmd_data = {
            "pageId": "testNoAttributesPage",
            "presentation": {
                "body": {"type": "layout", "children": []},
                "footer": {"type": "text", "label": "Footer"}
            }
        }
        pmd_model = PMDModel(**pmd_data, file_path="test_no_attributes.pmd", source_content="{}")
        assert not rule._is_micro_conclusion_page(pmd_model)

        # Test with microConclusion = False
        pmd_data = {
            "pageId": "testMicroFalsePage",
            "presentation": {
                "body": {"type": "layout", "children": []},
                "footer": {"type": "text", "label": "Footer"},
                "attributes": {"microConclusion": False}
            }
        }
        pmd_model = PMDModel(**pmd_data, file_path="test_micro_false.pmd", source_content="{}")
        assert not rule._is_micro_conclusion_page(pmd_model)
