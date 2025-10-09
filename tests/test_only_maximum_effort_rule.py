"""Unit tests for OnlyMaximumEffortRule."""

from parser.rules.structure.endpoints.only_maximum_effort import OnlyMaximumEffortRule
from parser.models import PMDModel, PodModel, ProjectContext


class TestOnlyMaximumEffortRule:
    """Test cases for OnlyMaximumEffortRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = OnlyMaximumEffortRule()
        assert rule.ID == "OnlyMaximumEffortRule"
        assert rule.DESCRIPTION == "Ensures endpoints use maximumEffort instead of bestEffort to prevent masked API failures"
        assert rule.SEVERITY == "ACTION"

    def test_get_description(self):
        """Test that get_description returns the correct description."""
        rule = OnlyMaximumEffortRule()
        assert rule.get_description() == rule.DESCRIPTION

    def test_inbound_endpoint_with_best_effort_true(self):
        """Test that inbound endpoints with bestEffort: true are flagged."""
        rule = OnlyMaximumEffortRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers",
                    "bestEffort": True
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "GetWorkers" in findings[0].message
        assert "bestEffort" in findings[0].message
        assert "mask" in findings[0].message.lower() or "failure" in findings[0].message.lower()
        assert findings[0].severity == "ACTION"

    def test_outbound_endpoint_with_best_effort_true(self):
        """Test that outbound endpoints with bestEffort: true are also flagged."""
        rule = OnlyMaximumEffortRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "outboundEndpoints": [
                {
                    "name": "UpdateWorker",
                    "bestEffort": True
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "UpdateWorker" in findings[0].message

    def test_endpoint_with_best_effort_false(self):
        """Test that endpoints with bestEffort: false are not flagged."""
        rule = OnlyMaximumEffortRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers",
                    "bestEffort": False
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_endpoint_without_best_effort(self):
        """Test that endpoints without bestEffort field are not flagged."""
        rule = OnlyMaximumEffortRule()
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

    def test_multiple_endpoints_with_best_effort(self):
        """Test that multiple endpoints with bestEffort are all flagged."""
        rule = OnlyMaximumEffortRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers",
                    "bestEffort": True
                },
                {
                    "name": "GetDepartments",
                    "bestEffort": False
                }
            ],
            "outboundEndpoints": [
                {
                    "name": "UpdateWorker",
                    "bestEffort": True
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert any("GetWorkers" in f.message for f in findings)
        assert any("UpdateWorker" in f.message for f in findings)
        assert not any("GetDepartments" in f.message for f in findings)

    def test_pod_endpoint_with_best_effort(self):
        """Test that POD endpoints with bestEffort are flagged."""
        rule = OnlyMaximumEffortRule()
        context = ProjectContext()
        
        pod_data = {
            "podId": "testPod",
            "file_path": "test.pod",
            "seed": {
                "endPoints": [
                    {
                        "name": "GetData",
                        "bestEffort": True
                    }
                ]
            }
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"testPod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "GetData" in findings[0].message

    def test_empty_endpoints_no_issues(self):
        """Test that files with no endpoints don't cause issues."""
        rule = OnlyMaximumEffortRule()
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

    def test_best_effort_string_true(self):
        """Test that bestEffort: 'true' as string is also caught."""
        rule = OnlyMaximumEffortRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "test.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers",
                    "bestEffort": "true"
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "GetWorkers" in findings[0].message

    def test_multiple_files_with_best_effort(self):
        """Test that best effort violations in multiple files are all flagged."""
        rule = OnlyMaximumEffortRule()
        context = ProjectContext()
        
        # PMD with bestEffort
        pmd_data = {
            "pageId": "page1",
            "file_path": "page1.pmd",
            "inboundEndpoints": [
                {
                    "name": "GetWorkers",
                    "bestEffort": True
                }
            ]
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"page1": pmd_model}
        
        # POD with bestEffort
        pod_data = {
            "podId": "pod1",
            "file_path": "pod1.pod",
            "seed": {
                "endPoints": [
                    {
                        "name": "GetData",
                        "bestEffort": True
                    }
                ]
            }
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"pod1": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert any(f.file_path == "page1.pmd" for f in findings)
        assert any(f.file_path == "pod1.pod" for f in findings)

