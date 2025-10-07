#!/usr/bin/env python3
"""Test PMDSecurityDomainRule strict mode functionality."""

import pytest
from parser.rules.structure.validation.pmd_security_domain import PMDSecurityDomainRule
from parser.models import PMDModel, ProjectContext


def test_strict_mode_disabled_by_default():
    """Test that strict mode is disabled by default."""
    rule = PMDSecurityDomainRule()
    assert rule.strict_mode is False


def test_strict_mode_configuration():
    """Test that strict mode can be configured."""
    rule = PMDSecurityDomainRule()
    
    # Test enabling strict mode
    rule.apply_settings({"strict": True})
    assert rule.strict_mode is True
    
    # Test disabling strict mode
    rule.apply_settings({"strict": False})
    assert rule.strict_mode is False


def test_description_changes_with_strict_mode():
    """Test that description changes based on strict mode."""
    rule = PMDSecurityDomainRule()
    
    # Default description
    default_desc = rule.get_description()
    assert "excludes microConclusion and error pages" in default_desc
    
    # Strict mode description
    rule.apply_settings({"strict": True})
    strict_desc = rule.get_description()
    assert "strict mode - no exclusions" in strict_desc


def test_micro_conclusion_exclusion_in_normal_mode():
    """Test that microConclusion pages are excluded in normal mode."""
    rule = PMDSecurityDomainRule()
    rule.apply_settings({"strict": False})
    
    # Create a microConclusion page without security domains
    pmd_content = {
        "pageId": "test-page",
        "presentation": {
            "attributes": {"microConclusion": True},
            "body": {"type": "primaryLayout"}
        }
    }
    
    pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
    context = ProjectContext()
    
    # Should not generate any findings (excluded)
    findings = list(rule.visit_pmd(pmd_model, context))
    assert len(findings) == 0


def test_micro_conclusion_not_excluded_in_strict_mode():
    """Test that microConclusion pages are NOT excluded in strict mode."""
    rule = PMDSecurityDomainRule()
    rule.apply_settings({"strict": True})
    
    # Create a microConclusion page without security domains
    pmd_content = {
        "pageId": "test-page",
        "presentation": {
            "attributes": {"microConclusion": True},
            "body": {"type": "primaryLayout"}
        }
    }
    
    pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
    context = ProjectContext()
    
    # Should generate a finding (not excluded in strict mode)
    findings = list(rule.visit_pmd(pmd_model, context))
    assert len(findings) == 1
    assert "strict mode enabled" in findings[0].message


def test_error_page_exclusion_in_normal_mode():
    """Test that error pages are excluded in normal mode."""
    rule = PMDSecurityDomainRule()
    rule.apply_settings({"strict": False})
    
    # Create an error page without security domains
    pmd_content = {
        "pageId": "error-page",
        "presentation": {
            "body": {"type": "primaryLayout"}
        }
    }
    
    pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
    
    # Create context with SMD containing error page
    context = ProjectContext()
    context.smd = type('SMD', (), {
        'get_error_pages': lambda self: [{'pageId': 'error-page'}]
    })()
    
    # Should not generate any findings (excluded)
    findings = list(rule.visit_pmd(pmd_model, context))
    assert len(findings) == 0


def test_error_page_not_excluded_in_strict_mode():
    """Test that error pages are NOT excluded in strict mode."""
    rule = PMDSecurityDomainRule()
    rule.apply_settings({"strict": True})
    
    # Create an error page without security domains
    pmd_content = {
        "pageId": "error-page",
        "presentation": {
            "body": {"type": "primaryLayout"}
        }
    }
    
    pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
    
    # Create context with SMD containing error page
    context = ProjectContext()
    context.smd = type('SMD', (), {
        'get_error_pages': lambda self: [{'pageId': 'error-page'}]
    })()
    
    # Should generate a finding (not excluded in strict mode)
    findings = list(rule.visit_pmd(pmd_model, context))
    assert len(findings) == 1
    assert "strict mode enabled" in findings[0].message


def test_normal_page_requires_security_in_both_modes():
    """Test that normal pages require security domains in both modes."""
    rule = PMDSecurityDomainRule()
    
    # Create a normal page without security domains
    pmd_content = {
        "pageId": "normal-page",
        "presentation": {
            "body": {"type": "primaryLayout"}
        }
    }
    
    pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
    context = ProjectContext()
    
    # Test normal mode
    rule.apply_settings({"strict": False})
    findings = list(rule.visit_pmd(pmd_model, context))
    assert len(findings) == 1
    assert "excludes microConclusion and error pages" in findings[0].message
    
    # Test strict mode
    rule.apply_settings({"strict": True})
    findings = list(rule.visit_pmd(pmd_model, context))
    assert len(findings) == 1
    assert "strict mode enabled" in findings[0].message


def test_page_with_security_domains_passes_in_both_modes():
    """Test that pages with security domains pass in both modes."""
    rule = PMDSecurityDomainRule()
    
    # Create a page with security domains
    pmd_content = {
        "pageId": "secure-page",
        "securityDomains": ["workday-common"],
        "presentation": {
            "body": {"type": "primaryLayout"}
        }
    }
    
    pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
    context = ProjectContext()
    
    # Test normal mode
    rule.apply_settings({"strict": False})
    findings = list(rule.visit_pmd(pmd_model, context))
    assert len(findings) == 0
    
    # Test strict mode
    rule.apply_settings({"strict": True})
    findings = list(rule.visit_pmd(pmd_model, context))
    assert len(findings) == 0
