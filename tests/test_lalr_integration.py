import unittest
from parser.pmd_script_parser import parse_with_preprocessor

class TestLALRIntegration(unittest.TestCase):
    
    def test_simple_assignment(self):
        """Test parsing a simple assignment with LALR + preprocessor"""
        code = "var x = 5;"
        result = parse_with_preprocessor(code)
        self.assertIsNotNone(result)
        self.assertEqual(result.data, 'source_elements')
    
    def test_empty_set_assignment(self):
        """Test parsing empty set assignment with LALR + preprocessor"""
        code = "var x = {};"
        result = parse_with_preprocessor(code)
        self.assertIsNotNone(result)
        self.assertEqual(result.data, 'source_elements')
    
    def test_empty_object_assignment(self):
        """Test parsing empty object assignment with LALR + preprocessor"""
        code = "var x = {:};"
        result = parse_with_preprocessor(code)
        self.assertIsNotNone(result)
        self.assertEqual(result.data, 'source_elements')
    
    def test_object_literal_assignment(self):
        """Test parsing object literal assignment with LALR + preprocessor"""
        code = 'var x = {"key": "value"};'
        result = parse_with_preprocessor(code)
        self.assertIsNotNone(result)
        self.assertEqual(result.data, 'source_elements')
    
    def test_function_expression(self):
        """Test parsing function expression with LALR + preprocessor"""
        code = "var f = function() { return 5; };"
        result = parse_with_preprocessor(code)
        self.assertIsNotNone(result)
        self.assertEqual(result.data, 'source_elements')
    
    def test_if_statement(self):
        """Test parsing if statement with LALR + preprocessor"""
        code = "if (x > 0) { return true; }"
        result = parse_with_preprocessor(code)
        self.assertIsNotNone(result)
        self.assertEqual(result.data, 'if_statement')
    
    def test_nested_structures(self):
        """Test parsing nested structures with LALR + preprocessor"""
        code = 'var test = function() { if (condition) { var obj = {"key": {}}; return obj; } };'
        result = parse_with_preprocessor(code)
        self.assertIsNotNone(result)
        self.assertEqual(result.data, 'source_elements')
    
    def test_multiline_code(self):
        """Test parsing multiline code with LALR + preprocessor"""
        code = "var x = {\"key\": \"value\"}; var f = function() { return x; };"
        result = parse_with_preprocessor(code)
        self.assertIsNotNone(result)
        self.assertEqual(result.data, 'source_elements')
    
    def test_complex_expression(self):
        """Test parsing complex expression with LALR + preprocessor"""
        code = 'var result = func({"config": {"nested": {}}, "other": [1, 2, 3]});'
        result = parse_with_preprocessor(code)
        self.assertIsNotNone(result)
        self.assertEqual(result.data, 'source_elements')

if __name__ == '__main__':
    unittest.main()
