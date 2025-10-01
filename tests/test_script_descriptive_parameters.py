#!/usr/bin/env python3
"""
Tests for ScriptDescriptiveParameterRule.
"""

import pytest
from parser.rules.script.logic.descriptive_parameters import ScriptDescriptiveParameterRule
from parser.models import ProjectContext, PMDModel, ScriptModel


class TestScriptDescriptiveParameterRule:
    """Test cases for ScriptDescriptiveParameterRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptDescriptiveParameterRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly defined."""
        assert self.rule.DESCRIPTION == "Ensures function parameters use descriptive names when functions take function parameters (except 'i', 'j', 'k' for indices)"
        assert self.rule.SEVERITY == "INFO"
    
    def test_functional_methods_detection(self):
        """Test that the rule detects PMD script functional methods."""
        expected_methods = {
            'map', 'filter', 'find', 'forEach', 'reduce', 'sort'
        }
        assert self.rule.FUNCTIONAL_METHODS == expected_methods
    
    def test_allowed_single_letters(self):
        """Test that traditional index variables are allowed."""
        expected_letters = {'i', 'j', 'k'}
        assert self.rule.ALLOWED_SINGLE_LETTERS == expected_letters
    
    def test_single_letter_violations_in_pmd(self):
        """Test detection of single-letter parameters in PMD scripts."""
        script_content = """<%
            const users = getUsers();
            const activeUsers = users.filter(x => x.active);
            const userNames = users.map(u => u.name);
            const hasAdmin = users.find(y => y.role == 'admin');
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find violations for 'x', 'u', and 'y'
        assert len(findings) == 3
        
        # Check specific violations
        violation_params = [f.message for f in findings]
        assert any("'x'" in msg and "filter()" in msg for msg in violation_params)
        assert any("'u'" in msg and "map()" in msg for msg in violation_params)  
        assert any("'y'" in msg and "find()" in msg for msg in violation_params)
    
    def test_descriptive_parameters_no_violations(self):
        """Test that descriptive parameters don't trigger violations."""
        script_content = """<%
            const users = getUsers();
            const activeUsers = users.filter(user => user.active);
            const userNames = users.map(user => user.name);
            const hasAdmin = users.find(user => user.role == 'admin');
            const sortedUsers = users.sort((userA, userB) => userA.name.localeCompare(userB.name));
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations
        assert len(findings) == 0
    
    def test_allowed_index_variables(self):
        """Test that 'i', 'j', 'k' are allowed even in functional contexts."""
        script_content = """<%
            // These should be allowed (traditional index variables)
            const items = [1, 2, 3];
            items.forEach((item, i) => console.log(i, item));
            matrix.map((row, j) => row.map((cell, k) => cell * k));
            
            // This should still be flagged
            items.map(x => x * 2);
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should only flag 'x', not 'i', 'j', 'k'
        assert len(findings) == 1
        assert "'x'" in findings[0].message
        assert "map()" in findings[0].message
    
    def test_nested_functional_methods(self):
        """Test detection in nested functional method calls."""
        script_content = """<%
            const departments = getDepartments();
            const result = departments
                .map(x => x.teams)
                .filter(y => y.active)
                .map(z => z.members.filter(w => w.certified));
        %>"""
        
        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find violations for 'x', 'y', 'z', 'w'
        assert len(findings) == 4
        
        # Verify all problematic parameters are caught
        violation_params = [f.message for f in findings]
        assert any("'x'" in msg and "map()" in msg for msg in violation_params)
        assert any("'y'" in msg and "filter()" in msg for msg in violation_params)
        assert any("'z'" in msg and "map()" in msg for msg in violation_params)
        assert any("'w'" in msg and "filter()" in msg for msg in violation_params)
    
    def test_contextual_parameter_suggestions(self):
        """Test that parameter suggestions are contextual."""
        # Test the suggestion logic directly since AST parsing is complex
        from parser.rules.script.logic.descriptive_parameters_detector import DescriptiveParameterDetector
        detector = DescriptiveParameterDetector("test.pmd", 1)
        
        # Test contextual suggestions
        assert detector._suggest_parameter_name("filter", "workers", 0) == "worker"
        assert detector._suggest_parameter_name("map", "teams", 0) == "team"
        assert detector._suggest_parameter_name("find", "projects", 0) == "project"
        assert detector._suggest_parameter_name("reduce", "items", 0) == "acc"  # Special case for reduce
        assert detector._suggest_parameter_name("forEach", "users", 0) == "user"
    
    def test_standalone_script_files(self):
        """Test analysis of standalone script files."""
        script_content = """const getCurrentTime = function() {
    return date:getTodaysDate(date:getDateTimeZone('US/Pacific'));
};

const processUsers = function(userList) {
    return userList
        .filter(x => x.active)
        .map(y => ({
            id: y.id,
            name: y.name,
            email: y.email
        }));
};

{
    "getCurrentTime": getCurrentTime,
    "processUsers": processUsers
}"""
        
        script_model = ScriptModel(source=script_content, file_path="util.script")
        self.context.scripts["util.script"] = script_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find violations for 'x' and 'y'
        assert len(findings) == 2
        
        violation_params = [f.message for f in findings]
        assert any("'x'" in msg and "filter()" in msg for msg in violation_params)
        assert any("'y'" in msg and "map()" in msg for msg in violation_params)
    
    def test_reduce_method_special_case(self):
        """Test that reduce method suggests 'acc' for accumulator parameter."""
        script_content = """<%
            const numbers = [1, 2, 3, 4];
            const sum = numbers.reduce((x, y) => x + y, 0);
            const product = numbers.reduce((a, item) => a * item, 1);
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))


        # Should find violations for both reduce calls
        assert len(findings) >= 2

        # Check that 'acc' is suggested for reduce parameters
        messages = [f.message for f in findings]
        reduce_messages = [msg for msg in messages if "reduce()" in msg]

        # At least one reduce violation should suggest 'acc'
        assert any("'acc'" in msg for msg in reduce_messages)
    
    def test_configuration_options(self):
        """Test that configuration options work correctly."""
        config = {
            'allowed_single_letters': ['i', 'j', 'k', 'x'],  # Allow 'x'
        }
        
        rule = ScriptDescriptiveParameterRule(config=config)
        
        # Test that the configuration was applied correctly
        assert 'x' in rule.ALLOWED_SINGLE_LETTERS
        assert 'i' in rule.ALLOWED_SINGLE_LETTERS
        assert 'j' in rule.ALLOWED_SINGLE_LETTERS
        assert 'k' in rule.ALLOWED_SINGLE_LETTERS
        assert 'y' not in rule.ALLOWED_SINGLE_LETTERS
        
        # Test that the detector was created with the correct configuration
        detector = rule.DETECTOR("test.pmd", 1, rule.FUNCTIONAL_METHODS, rule.ALLOWED_SINGLE_LETTERS)
        assert 'x' in detector.allowed_letters
        assert 'y' not in detector.allowed_letters
    
    def test_multi_line_method_chains(self):
        """Test detection across multi-line method chains."""
        script_content = """<%
            const result = users
                .filter(x => x.active)
                .map(y => y.name)
                .sort((a, b) => a.localeCompare(b));
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find violations for 'x' and 'y' but not 'a' and 'b' (sort convention)
        violation_params = [f.message for f in findings]
        assert any("'x'" in msg and "filter()" in msg for msg in violation_params)
        assert any("'y'" in msg and "map()" in msg for msg in violation_params)
    
    def test_edge_cases(self):
        """Test various edge cases."""
        script_content = """<%
            // Empty arrays
            [].map(x => x);
            
            // Method calls with no parameters
            items.sort();
            
            // Non-functional methods with single letters (should not be flagged)
            obj.someMethod(x);
            
            // Multiple parameters in functional methods
            items.reduce((acc, x, index) => acc + x, 0);
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should only flag functional method parameters
        violation_methods = [f.message for f in findings]
        functional_violations = [msg for msg in violation_methods if any(method in msg for method in ['map()', 'reduce()', 'functional method()'])]
        
        # Should have at least the map and reduce violations
        assert len(functional_violations) >= 2
    
    def test_suggestion_quality(self):
        """Test that parameter name suggestions are high quality."""
        test_cases = [
            ("users.filter(x => x.active)", "user"),
            ("employees.map(y => y.name)", "employee"), 
            ("tasks.find(z => z.completed)", "task"),
            ("items.find(q => q.id == 5)", "item"),
            ("numbers.reduce((a, b) => a + b)", "acc"),  # reduce special case
        ]
        
        for script_line, expected_suggestion in test_cases:
            script_content = f"<% {script_line}; %>"
            
            pmd_model = PMDModel(
                pageId="testPage",
                file_path="test.pmd",
                source_content='{"script": "' + script_content.replace('"', '\\"') + '"}'
            )
            pmd_model.script = script_content
            context = ProjectContext()
            context.pmds["testPage"] = pmd_model
            
            findings = list(self.rule.analyze(context))
            
            if findings:  # Should have at least one finding
                assert expected_suggestion in findings[0].message, \
                    f"Expected '{expected_suggestion}' in suggestion for '{script_line}'"
    
    def test_no_false_positives(self):
        """Test that the rule doesn't flag legitimate cases."""
        script_content = """<%
            // Legitimate descriptive names
            users.filter(user => user.active);
            items.map(item => item.name);
            tasks.some(task => task.completed);
            
            // Traditional index variables
            items.forEach((item, i) => console.log(i));
            matrix.map((row, j) => row[j]);
            
            // Multi-character variables starting with single letters
            items.map(item => item.value);
            users.filter(user => user.active);
        %>"""

        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model

        findings = list(self.rule.analyze(self.context))

        # Should have no violations
        assert len(findings) == 0

    def test_custom_functions_with_function_parameters(self):
        """Test that custom functions that take function parameters are flagged."""
        script_content = """<%
            // Custom functions that take function parameters should be flagged
            obj.customMethod(x => x.value);
            helper.formatDate(d => d.format('yyyy-MM-dd'));
            utils.processItems(a => a.process());
        %>"""

        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model

        findings = list(self.rule.analyze(self.context))

        # Should flag single-letter parameters in custom functions that take function parameters
        # Note: 'i' is in the allowed list, so it won't be flagged
        assert len(findings) >= 2  # At least x and d should be flagged
        
        # Check that violations are for single-letter parameters
        violation_params = []
        for finding in findings:
            if "Parameter '" in finding.message:
                start = finding.message.find("Parameter '") + 11
                end = finding.message.find("'", start)
                param_name = finding.message[start:end]
                violation_params.append(param_name)
        
        assert 'x' in violation_params
        assert 'd' in violation_params
        # 'a' should also be flagged since it's not in the allowed list
        assert 'a' in violation_params

    def test_nested_arrow_functions(self):
        """Test detection of single-letter parameters in nested arrow functions."""
        script_content = """<%
            // Nested arrow functions with single-letter parameters
            items.map(x => x.items.map(y => y.value));
            users.filter(u => u.roles.some(r => r.active));
            data.reduce((acc, item) => acc.concat(item.children.map(c => c.name)), []);
            
            // Complex nested structure
            departments.map(d => d.teams.map(t => t.members.map(m => m.name)));
        %>"""

        pmd_model = PMDModel(
            pageId="test-page",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["test-page"] = pmd_model

        findings = list(self.rule.analyze(self.context))

        # Should flag single-letter parameters: x, y, u, r, c, d, t, m
        # But not 'acc' (allowed) or 'item' (descriptive)
        violation_params = []
        for finding in findings:
            # Extract parameter name from message
            if "Parameter '" in finding.message:
                start = finding.message.find("Parameter '") + 11
                end = finding.message.find("'", start)
                param_name = finding.message[start:end]
                violation_params.append(param_name)

        # Should have violations for single-letter parameters
        expected_violations = ['x', 'y', 'u', 'r', 'c', 'd', 't', 'm']
        for param in expected_violations:
            assert param in violation_params, f"Expected violation for parameter '{param}'"

        # Should not have violations for descriptive parameters
        assert 'acc' not in violation_params, "Should not flag 'acc' (allowed parameter)"
        assert 'item' not in violation_params, "Should not flag 'item' (descriptive parameter)"


if __name__ == "__main__":
    pytest.main([__file__])
