#!/usr/bin/env python3
"""Unit tests for ScriptNullSafetyRule."""

import pytest
from parser.rules.script.logic.null_safety import ScriptNullSafetyRule
from parser.models import ProjectContext, PMDModel


class TestScriptNullSafetyRule:
    """Test cases for ScriptNullSafetyRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptNullSafetyRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ACTION"
        assert "null" in self.rule.DESCRIPTION.lower()
    
    def test_empty_function_protection(self):
        """Test that empty() function provides null safety protection."""
        pmd_content = {
            "pageId": "testPage",
            "script": "<% if (empty(user.profile.name)) { return 'No name'; } else { return user.profile.name; } %>"
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # The empty() function should provide protection, so we shouldn't get violations
        assert len(findings) == 0, f"Expected 0 violations but got {len(findings)}: {[f.message for f in findings]}"
    
    def test_empty_keyword_protection(self):
        """Test that empty keyword provides null safety protection."""
        pmd_content = {
            "pageId": "testPage", 
            "script": "<% if (empty user.profile.name) { return 'No name'; } else { return user.profile.name; } %>"
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # The empty keyword should provide protection, so we shouldn't get violations
        assert len(findings) == 0, f"Expected 0 violations but got {len(findings)}: {[f.message for f in findings]}"
    
    def test_not_empty_function_protection(self):
        """Test that !empty() function provides null safety protection."""
        pmd_content = {
            "pageId": "testPage",
            "script": "<% if (!empty(user.profile.name)) { return user.profile.name; } else { return 'No name'; } %>"
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # The !empty() function should provide protection, so we shouldn't get violations
        assert len(findings) == 0, f"Expected 0 violations but got {len(findings)}: {[f.message for f in findings]}"
    
    def test_unsafe_property_access_without_protection(self):
        """Test that unsafe property access without protection generates violations."""
        pmd_content = {
            "pageId": "testPage",
            "script": "<% return user.profile.name; %>"
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # Should get violations for unsafe property access
        assert len(findings) > 0, "Expected violations for unsafe property access"
        assert any("unsafe property access" in f.message.lower() for f in findings)
    
    def test_empty_function_in_ternary_operator(self):
        """Test empty() function protection in ternary operator."""
        pmd_content = {
            "pageId": "testPage",
            "script": "<% return empty(user.profile.name) ? 'No name' : user.profile.name; %>"
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
    def test_level_plus_one_safety_logic(self):
        """Test that null safety allows one level deeper than explicitly checked."""
        # Test case: !empty workerPhoto should make workerPhoto.workerPhotos safe
        # but workerPhoto.workerPhotos.href should still be unsafe
        pmd_content = {
            "pageId": "testPage",
            "presentation": {
                "body": {
                    "type": "section",
                    "children": [
                        {
                            "type": "text",
                            "render": "<% !empty workerPhoto %>",
                            "value": "<% return workerPhoto.workerPhotos.href; %>"
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # Should get violations for workerPhoto.workerPhotos.href (level +2)
        # but NOT for workerPhoto.workerPhotos (level +1)
        href_violations = [f for f in findings if "workerPhoto.workerPhotos.href" in f.message]
        photos_violations = [f for f in findings if "workerPhoto.workerPhotos" in f.message and "href" not in f.message]
        
        assert len(href_violations) > 0, "Expected violations for workerPhoto.workerPhotos.href (level +2)"
        assert len(photos_violations) == 0, "Expected NO violations for workerPhoto.workerPhotos (level +1)"
    
    def test_deeper_property_access_still_unsafe(self):
        """Test that property access beyond level +1 is still flagged as unsafe."""
        pmd_content = {
            "pageId": "testPage",
            "presentation": {
                "body": {
                    "type": "section",
                    "children": [
                        {
                            "type": "text",
                            "render": "<% !empty user.profile %>",
                            "value": "<% return user.profile.name.first; %>"
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # Should get violations for user.profile.name.first (level +2 from user.profile)
        first_violations = [f for f in findings if "user.profile.name.first" in f.message]
        assert len(first_violations) > 0, "Expected violations for user.profile.name.first (level +2)"
    
    def test_explicit_chain_check_provides_full_protection(self):
        """Test that explicitly checking a full chain provides protection for that chain."""
        pmd_content = {
            "pageId": "testPage",
            "script": "<% if (!empty user.profile.name) { return user.profile.name.first; } %>"
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # Should NOT get violations for user.profile.name.first (explicitly checked)
        first_violations = [f for f in findings if "user.profile.name.first" in f.message]
        assert len(first_violations) == 0, "Expected NO violations for user.profile.name.first (explicitly checked)"
    
    def test_single_property_access_not_flagged(self):
        """Test that single property access (no dots) is not flagged."""
        pmd_content = {
            "pageId": "testPage",
            "script": "<% return user; %>"
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # Should NOT get violations for single property access
        user_violations = [f for f in findings if "user" in f.message and "." not in f.message]
        assert len(user_violations) == 0, "Expected NO violations for single property access"
    
    def test_template_string_interpolation_unsafe_access(self):
        """Test that template string interpolation with unsafe property access is flagged."""
        pmd_content = {
            "pageId": "testPage",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "text",
                            "render": "<% !empty workerPhoto %>",
                            "value": "<% `{{workerPhoto.workerPhotos.href.ff}}` %>"
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # Should get violations for workerPhoto.workerPhotos.href.ff (level +3 from workerPhoto)
        href_violations = [f for f in findings if "workerPhoto.workerPhotos.href.ff" in f.message]
        assert len(href_violations) > 0, "Expected violations for workerPhoto.workerPhotos.href.ff in template string"
    
    def test_template_string_interpolation_safe_access(self):
        """Test that template string interpolation with safe property access (level +1) is not flagged."""
        pmd_content = {
            "pageId": "testPage",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "text",
                            "render": "<% !empty workerPhoto %>",
                            "value": "<% `{{workerPhoto.workerPhotos}}` %>"
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # Should NOT get violations for workerPhoto.workerPhotos (level +1 from workerPhoto)
        photos_violations = [f for f in findings if "workerPhoto.workerPhotos" in f.message and "href" not in f.message]
        assert len(photos_violations) == 0, "Expected NO violations for workerPhoto.workerPhotos (level +1)"
    
    def test_template_string_multiple_interpolations(self):
        """Test template string with multiple interpolations."""
        pmd_content = {
            "pageId": "testPage",
            "script": "<% `Hello {{user.name}}, your email is {{user.profile.email}}` %>"
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # Should get violations for user.profile.email (level +2 from user)
        email_violations = [f for f in findings if "user.profile.email" in f.message]
        assert len(email_violations) > 0, "Expected violations for user.profile.email in template string"
        
        # Should NOT get violations for user.name (level +1 from user)
        name_violations = [f for f in findings if "user.name" in f.message]
        assert len(name_violations) == 0, "Expected NO violations for user.name (level +1)"
    
    def test_template_string_null_coalescing_protection(self):
        """Test that template string interpolation with null coalescing is safe."""
        pmd_content = {
            "pageId": "testPage",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "text",
                            "render": "<% !empty workerPhoto %>",
                            "value": "<% `{{workerPhoto.workerPhotos.href.ff ?? ''}}` %>"
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # Should NOT get violations for workerPhoto.workerPhotos.href.ff (protected by null coalescing)
        href_violations = [f for f in findings if "workerPhoto.workerPhotos.href.ff" in f.message]
        assert len(href_violations) == 0, "Expected NO violations for workerPhoto.workerPhotos.href.ff (protected by null coalescing)"
    
    def test_regular_null_coalescing_protection(self):
        """Test that regular property access with null coalescing is safe."""
        pmd_content = {
            "pageId": "testPage",
            "script": "<% return user.profile.email ?? 'No email'; %>"
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        
        # Should NOT get violations for user.profile.email (protected by null coalescing)
        email_violations = [f for f in findings if "user.profile.email" in f.message]
        assert len(email_violations) == 0, "Expected NO violations for user.profile.email (protected by null coalescing)"


if __name__ == '__main__':
    pytest.main([__file__])
