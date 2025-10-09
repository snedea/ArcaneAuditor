"""
Unit tests for rule skipping behavior when context dependencies are missing.

Tests that rules properly register skipped checks with ProjectContext when
cross-file dependencies like AMD or SMD files are not available.
"""
import pytest
from parser.models import ProjectContext, PMDModel, PodModel, SMDModel
from file_processing.context_tracker import AnalysisContext
from parser.rules.structure.validation.pmd_security_domain import PMDSecurityDomainRule
from parser.rules.structure.validation.hardcoded_application_id import HardcodedApplicationIdRule


class TestPMDSecurityDomainRuleSkipping:
    """Tests for PMDSecurityDomainRule context awareness."""
    
    def test_does_not_skip_check_when_smd_present(self):
        """Test that rule doesn't register skipped check when SMD is present."""
        # Create context with SMD
        context = ProjectContext()
        context.smd = SMDModel(
            id="site1",
            applicationId="test_app",
            siteId="site1",
            errorPageConfigurations=[{"page": {"id": "errorPage"}}],
            file_path="app.smd"
        )
        context.analysis_context = AnalysisContext(
            analysis_type="full_app",
            files_analyzed=["app.smd", "page.pmd"],
            files_present={"SMD", "PMD"}
        )
        
        # Create PMD that is NOT an error page
        pmd_model = PMDModel(
            pageId="regularPage",
            securityDomains=[],  # Missing security domains
            presentation={"attributes": {}},
            file_path="page.pmd",
            source_content="{}"
        )
        
        # Run rule
        rule = PMDSecurityDomainRule()
        findings = list(rule.visit_pmd(pmd_model, context))
        
        # Should find the violation (missing security domains)
        assert len(findings) == 1
        assert "securitydomains" in findings[0].message.lower()
        
        # Should NOT register any skipped checks
        assert len(context.analysis_context.skipped_checks) == 0
    
    def test_skips_check_when_smd_missing(self):
        """Test that rule registers skipped check when SMD is missing."""
        # Create context without SMD
        context = ProjectContext()
        context.analysis_context = AnalysisContext(
            analysis_type="individual_files",
            files_analyzed=["page.pmd"],
            files_present={"PMD"}
        )
        
        # Create PMD and add to context
        pmd_model = PMDModel(
            pageId="regularPage",
            securityDomains=[],  # Missing security domains
            presentation={"attributes": {}},
            file_path="page.pmd",
            source_content="{}"
        )
        context.pmds["page.pmd"] = pmd_model
        
        # Run rule
        rule = PMDSecurityDomainRule()
        findings = list(rule.analyze(context))
        
        # Should still find the violation (missing security domains)
        assert len(findings) == 1
        
        # Should register a skipped check for error_page_exclusion
        assert len(context.analysis_context.skipped_checks) == 1
        skipped = context.analysis_context.skipped_checks[0]
        assert skipped.rule_name == "PMDSecurityDomainRule"
        assert skipped.check_name == "error_page_exclusion"
        assert "SMD file" in skipped.reason
    
    def test_error_page_detection_works_with_smd(self):
        """Test that error pages are correctly excluded when SMD is present."""
        # Create context with SMD that defines an error page
        context = ProjectContext()
        context.smd = SMDModel(
            id="site1",
            applicationId="test_app",
            siteId="site1",
            errorPageConfigurations=[{"page": {"id": "myErrorPage"}}],
            file_path="app.smd"
        )
        context.analysis_context = AnalysisContext(
            analysis_type="full_app",
            files_analyzed=["app.smd", "error.pmd"],
            files_present={"SMD", "PMD"}
        )
        
        # Create PMD that IS an error page
        pmd_model = PMDModel(
            pageId="myErrorPage",
            securityDomains=[],  # Missing security domains (but should be excluded)
            presentation={"attributes": {}},
            file_path="error.pmd",
            source_content="{}"
        )
        
        # Run rule
        rule = PMDSecurityDomainRule()
        findings = list(rule.visit_pmd(pmd_model, context))
        
        # Should NOT find any violations (error pages are excluded)
        assert len(findings) == 0
        
        # Should NOT register any skipped checks (check was performed)
        assert len(context.analysis_context.skipped_checks) == 0


class TestHardcodedApplicationIdRuleSkipping:
    """Tests for HardcodedApplicationIdRule context awareness."""
    
    def test_does_not_skip_check_when_smd_present(self):
        """Test that rule doesn't register skipped check when SMD is present."""
        # Create context with SMD
        context = ProjectContext()
        context.smd = SMDModel(
            id="site1",
            applicationId="myAppId123",
            siteId="site1",
            errorPageConfigurations=[],
            file_path="app.smd"
        )
        context.analysis_context = AnalysisContext(
            analysis_type="full_app",
            files_analyzed=["app.smd", "page.pmd"],
            files_present={"SMD", "PMD"}
        )
        
        # Create PMD with hardcoded app ID
        pmd_model = PMDModel(
            pageId="testPage",
            securityDomains=["domain1"],
            presentation={"attributes": {}},
            file_path="page.pmd",
            source_content='{"pageId": "testPage", "someField": "myAppId123"}'
        )
        
        # Run rule
        rule = HardcodedApplicationIdRule()
        findings = list(rule.visit_pmd(pmd_model, context))
        
        # Should find the violation (hardcoded app ID)
        assert len(findings) == 1
        assert "myAppId123" in findings[0].message
        
        # Should NOT register any skipped checks
        assert len(context.analysis_context.skipped_checks) == 0
    
    def test_skips_check_when_smd_missing_pmd(self):
        """Test that rule registers skipped check for PMD when SMD is missing."""
        # Create context without SMD
        context = ProjectContext()
        context.analysis_context = AnalysisContext(
            analysis_type="individual_files",
            files_analyzed=["page.pmd"],
            files_present={"PMD"}
        )
        
        # Create PMD
        pmd_model = PMDModel(
            pageId="testPage",
            securityDomains=["domain1"],
            presentation={"attributes": {}},
            file_path="page.pmd",
            source_content='{"pageId": "testPage"}'
        )
        
        # Run rule
        rule = HardcodedApplicationIdRule()
        findings = list(rule.visit_pmd(pmd_model, context))
        
        # Should NOT find any violations (no app ID to check against)
        assert len(findings) == 0
        
        # Should NOT register a skipped check (rule is added to rules_not_executed instead)
        assert len(context.analysis_context.skipped_checks) == 0
        
        # Rule will be listed in rules_not_executed by the context tracker
        rules_not_executed = context.analysis_context.rules_not_executed
        rule_names = [r["rule"] for r in rules_not_executed]
        assert "HardcodedApplicationIdRule" in rule_names
    
    def test_skips_check_when_smd_missing_pod(self):
        """Test that rule registers skipped check for POD when SMD is missing."""
        # Create context without SMD
        context = ProjectContext()
        context.analysis_context = AnalysisContext(
            analysis_type="individual_files",
            files_analyzed=["footer.pod"],
            files_present={"POD"}
        )
        
        # Create POD
        pod_model = PodModel(
            podId="footerPod",
            seed={},
            file_path="footer.pod",
            source_content='{"podId": "footerPod"}'
        )
        
        # Run rule
        rule = HardcodedApplicationIdRule()
        findings = list(rule.visit_pod(pod_model, context))
        
        # Should NOT find any violations (no app ID to check against)
        assert len(findings) == 0
        
        # Should NOT register a skipped check (rule is added to rules_not_executed instead)
        assert len(context.analysis_context.skipped_checks) == 0
        
        # Rule will be listed in rules_not_executed by the context tracker
        rules_not_executed = context.analysis_context.rules_not_executed
        rule_names = [r["rule"] for r in rules_not_executed]
        assert "HardcodedApplicationIdRule" in rule_names


class TestRuleSkippingIntegration:
    """Integration tests for multiple rules registering skipped checks."""
    
    def test_multiple_rules_register_skipped_checks(self):
        """Test that multiple rules can register skipped checks in the same context."""
        # Create context without SMD
        context = ProjectContext()
        context.analysis_context = AnalysisContext(
            analysis_type="individual_files",
            files_analyzed=["page.pmd"],
            files_present={"PMD"}
        )
        
        # Create PMD and add to context
        pmd_model = PMDModel(
            pageId="testPage",
            securityDomains=[],  # Missing
            presentation={"attributes": {}},
            file_path="page.pmd",
            source_content='{"pageId": "testPage"}'
        )
        context.pmds["page.pmd"] = pmd_model
        
        # Run both rules
        security_rule = PMDSecurityDomainRule()
        appid_rule = HardcodedApplicationIdRule()
        
        security_findings = list(security_rule.analyze(context))
        appid_findings = list(appid_rule.analyze(context))
        
        # Security rule should find violation
        assert len(security_findings) == 1
        
        # App ID rule should not find violations (no app ID)
        assert len(appid_findings) == 0
        
        # Only PMDSecurityDomainRule should register skipped check
        # HardcodedApplicationIdRule is now in rules_not_executed instead
        assert len(context.analysis_context.skipped_checks) == 1
        
        skipped = context.analysis_context.skipped_checks[0]
        assert skipped.rule_name == "PMDSecurityDomainRule"
        
        # HardcodedApplicationIdRule will be in rules_not_executed
        rules_not_executed = context.analysis_context.rules_not_executed
        rule_names = [r["rule"] for r in rules_not_executed]
        assert "HardcodedApplicationIdRule" in rule_names
    
    def test_no_skipped_checks_with_complete_context(self):
        """Test that no skipped checks are registered when all files are present."""
        # Create context with all files
        context = ProjectContext()
        context.smd = SMDModel(
            id="site1",
            applicationId="myAppId",
            siteId="site1",
            errorPageConfigurations=[],
            file_path="app.smd"
        )
        context.analysis_context = AnalysisContext(
            analysis_type="full_app",
            files_analyzed=["app.smd", "page.pmd"],
            files_present={"SMD", "PMD", "AMD"}
        )
        
        # Create PMD
        pmd_model = PMDModel(
            pageId="testPage",
            securityDomains=["domain1"],
            presentation={"attributes": {}},
            file_path="page.pmd",
            source_content='{"pageId": "testPage"}'
        )
        
        # Run both rules
        security_rule = PMDSecurityDomainRule()
        appid_rule = HardcodedApplicationIdRule()
        
        security_findings = list(security_rule.visit_pmd(pmd_model, context))
        appid_findings = list(appid_rule.visit_pmd(pmd_model, context))
        
        # No skipped checks should be registered
        assert len(context.analysis_context.skipped_checks) == 0

