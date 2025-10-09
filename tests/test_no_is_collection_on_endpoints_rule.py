"""Unit tests for NoIsCollectionOnEndpointsRule."""

from parser.rules.structure.endpoints.no_is_collection_on_endpoints import NoIsCollectionOnEndpointsRule
from parser.models import PMDModel, PodModel, ProjectContext


class TestNoIsCollectionOnEndpointsRule:
    """Test cases for NoIsCollectionOnEndpointsRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = NoIsCollectionOnEndpointsRule()
        assert rule.ID == "NoIsCollectionOnEndpointsRule"
        assert rule.DESCRIPTION == "Detects isCollection: true on inbound endpoints which can cause tenant-wide performance issues"
        assert rule.SEVERITY == "ACTION"

    def test_get_description(self):
        """Test that get_description returns the correct description."""
        rule = NoIsCollectionOnEndpointsRule()
        assert rule.get_description() == rule.DESCRIPTION

    def test_inbound_endpoint_with_is_collection_true(self):
        """Test that inbound endpoints with isCollection: true are flagged."""
        rule = NoIsCollectionOnEndpointsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers",
                    "isCollection": True
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "GetWorkers" in findings[0].message
        assert "isCollection" in findings[0].message
        assert "performance" in findings[0].message.lower()
        assert findings[0].severity == "ACTION"

    def test_inbound_endpoint_with_is_collection_false(self):
        """Test that inbound endpoints with isCollection: false are not flagged."""
        rule = NoIsCollectionOnEndpointsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers",
                    "isCollection": False
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_inbound_endpoint_without_is_collection(self):
        """Test that inbound endpoints without isCollection field are not flagged."""
        rule = NoIsCollectionOnEndpointsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers"
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_outbound_endpoint_with_is_collection_true_not_flagged(self):
        """Test that outbound endpoints with isCollection: true are NOT flagged (OK for outbound)."""
        rule = NoIsCollectionOnEndpointsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "outboundEndpoints": [
                {
                    "name": "ProcessWorkers",
                    "isCollection": True
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0  # Should NOT flag outbound endpoints

    def test_multiple_inbound_endpoints_with_is_collection(self):
        """Test that multiple inbound endpoints with isCollection are all flagged."""
        rule = NoIsCollectionOnEndpointsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers",
                    "isCollection": True
                },
                {
                    "name": "GetDepartments",
                    "isCollection": True
                },
                {
                    "name": "GetSingleWorker",
                    "isCollection": False
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert any("GetWorkers" in f.message for f in findings)
        assert any("GetDepartments" in f.message for f in findings)
        assert not any("GetSingleWorker" in f.message for f in findings)

    def test_mixed_inbound_and_outbound_endpoints(self):
        """Test that only inbound endpoints are checked, not outbound."""
        rule = NoIsCollectionOnEndpointsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers",
                    "isCollection": True
                }
            ],
            "outboundEndpoints": [
                {
                    "name": "ProcessWorkers",
                    "isCollection": True
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "GetWorkers" in findings[0].message
        assert "inbound" in findings[0].message.lower()

    def test_pod_endpoint_with_is_collection(self):
        """Test that POD endpoints with isCollection are flagged."""
        rule = NoIsCollectionOnEndpointsRule()
        context = ProjectContext()
        
        pod_data = {
            "podId": "testPod",
            "file_path": "test.pod",
            "seed": {
                "endPoints": [
                    {
                        "name": "GetData",
                        "isCollection": True
                    }
                ]
            }
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"testPod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "GetData" in findings[0].message
        assert "isCollection" in findings[0].message

    def test_empty_endpoints_no_issues(self):
        """Test that files with no endpoints don't cause issues."""
        rule = NoIsCollectionOnEndpointsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": []
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_is_collection_string_true(self):
        """Test that isCollection: "true" as string is also caught."""
        rule = NoIsCollectionOnEndpointsRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers",
                    "isCollection": "true"
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        # Should handle both boolean and string "true"
        assert len(findings) == 1
        assert "GetWorkers" in findings[0].message

