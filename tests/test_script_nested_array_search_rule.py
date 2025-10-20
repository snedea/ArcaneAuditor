#!/usr/bin/env python3
"""Test cases for ScriptNestedArraySearchRule."""

from parser.rules.script.logic.nested_array_search import ScriptNestedArraySearchRule
from parser.rules.script.logic.nested_array_search_detector import NestedArraySearchDetector


class TestScriptNestedArraySearchRule:
    """Test cases for ScriptNestedArraySearchRule."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptNestedArraySearchRule()

    def test_rule_metadata(self):
        """Test rule metadata."""
        assert self.rule.DESCRIPTION == "Detects nested array search patterns that cause severe performance issues"
        assert self.rule.SEVERITY == "ADVICE"
        assert self.rule.DETECTOR == NestedArraySearchDetector

    def test_basic_nested_find_should_flag(self):
        """Test 1: Basic nested find should be flagged."""
        script_content = """
        const result = workers.map(worker => orgData.find(org => org.id == worker.orgId));
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "nested array search" in violations[0].message.lower()
        assert "list:toMap" in violations[0].message

    def test_basic_nested_filter_should_flag(self):
        """Test 2: Basic nested filter should be flagged."""
        script_content = """
        const result = workers.map(worker => orgData.filter(org => org.type == worker.type));
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "nested array search" in violations[0].message.lower()

    def test_foreach_with_find_should_flag(self):
        """Test 3: forEach with find should be flagged."""
        script_content = """
        workers.forEach(worker => {
            const org = orgData.find(orgItem => orgItem.id == worker.orgId);
            console.info(org);
        });
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "nested array search" in violations[0].message.lower()

    def test_triple_nested_should_flag(self):
        """Test 4: Triple nested should be flagged."""
        script_content = """
        const result = departments.map(department => 
            department.teams.map(team => 
                orgData.find(org => org.id == team.orgId)
            )
        );
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        # Should find 1 violation: the innermost search (orgData.find)
        assert len(violations) == 1
        assert "nested array search" in violations[0].message.lower()

    def test_filter_within_filter_should_flag(self):
        """Test 5: filter within filter should be flagged."""
        script_content = """
        const result = workers.filter(worker => {
            return orgData.filter(org => org.id == worker.orgId).length > 0;
        });
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "nested array search" in violations[0].message.lower()
        assert "orgData.filter" in violations[0].message

    def test_constant_comparison_should_flag(self):
        """Test 6: Constant comparison should still be flagged."""
        script_content = """
        const targetId = 5;
        const result = workers.map(worker => orgData.find(org => org.id == targetId));
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "nested array search" in violations[0].message.lower()

    def test_map_pattern_should_not_flag(self):
        """Test 7: Using list:toMap pattern should NOT be flagged."""
        script_content = """
        const orgById = list:toMap(orgData, 'id');
        const result = workers.map(worker => orgById[worker.orgId]);
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0

    def test_simple_transform_should_not_flag(self):
        """Test 8: Simple transform should NOT be flagged."""
        script_content = """
        const names = workers.map(worker => worker.name);
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0

    def test_nested_owned_data_should_not_flag(self):
        """Test 9: Nested owned data should NOT be flagged."""
        script_content = """
        const result = workers.map(worker => worker.skills.map(skill => skill.name));
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0

    def test_direct_array_operations_should_not_flag(self):
        """Test 10: Direct array operations should NOT be flagged."""
        script_content = """
        const active = workers.filter(worker => worker.active);
        const found = orgData.find(org => org.id == targetId);
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0

    def test_multiple_parameters_should_flag(self):
        """Test 11: Multiple parameters should still be flagged."""
        script_content = """
        const result = workers.map((worker, index) => 
            orgData.find(org => org.workerId == worker.id)
        );
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "nested array search" in violations[0].message.lower()

    def test_empty_script_no_violations(self):
        """Test empty script has no violations."""
        script_content = ""
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0

    def test_simple_variable_assignment_no_violations(self):
        """Test simple variable assignment has no violations."""
        script_content = """
        const posX = 1;
        const posY = posX + 1;
        return posY;
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0

    def test_violation_message_contains_helpful_advice(self):
        """Test that violation message contains helpful advice."""
        script_content = """
        const result = workers.map(worker => orgData.find(org => org.id == worker.orgId));
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        
        message = violations[0].message
        assert "nested array search:" in message.lower()
        assert "out-of-memory issues" in message.lower()
        assert "list:tomap" in message.lower()
        assert "orgdatamap" in message.lower()

    def test_detector_helper_methods(self):
        """Test detector helper methods work correctly."""
        detector = NestedArraySearchDetector("test.pmd", 1)
        
        # Test search methods
        assert 'find' in detector.SEARCH_METHODS
        assert 'filter' in detector.SEARCH_METHODS
        
        # Test iteration methods
        assert 'map' in detector.ITERATION_METHODS
        assert 'forEach' in detector.ITERATION_METHODS
        assert 'filter' in detector.ITERATION_METHODS
        # Note: 'reduce' removed as it's not a meaningful pattern in real PMD Script usage  # filter can be both

    def test_complex_nested_structure_should_flag(self):
        """Test complex nested structure with multiple violations."""
        script_content = """
        const result1 = workers.map(worker => orgData.find(org => org.id == worker.orgId));
        const result2 = departments.forEach(department => {
            const team = teams.filter(team => team.deptId == department.id);
        });
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 2  # Should find both violations

    def test_function_with_nested_search_should_flag(self):
        """Test function containing nested search should be flagged."""
        script_content = """
        const processWorkers = function() {
            return workers.map(worker => orgData.find(org => org.id == worker.orgId));
        };
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        # The new implementation doesn't include function context in the message
        assert "nested array search" in violations[0].message.lower()

    def test_arrow_function_with_block_body(self):
        """Test arrow function with block body containing nested search."""
        script_content = """
        const result = workers.map(worker => {
            const org = orgData.find(orgItem => orgItem.id == worker.orgId);
            return org ? org.name : 'Unknown';
        });
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 1
        assert "nested array search" in violations[0].message.lower()

    def test_owned_data_traversal_edge_cases(self):
        """Test various owned data traversal patterns that should NOT be flagged."""
        script_content = f"""
        // These should NOT be flagged - they're traversing owned data
        const result1 = workers.map(worker => worker.skills.map(skill => {{skill.name}}));
        const result2 = departments.map(department => department.teams.map(team => team.name));
        const result3 = users.map(user => user.profile.settings.map(setting => setting.value));
        """
        ast = self.rule._parse_script_content(script_content, None)
        detector = NestedArraySearchDetector("test.pmd", 1)
        violations = list(detector.detect(ast, "test"))
        assert len(violations) == 0
