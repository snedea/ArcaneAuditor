import unittest
from parser.pmd_preprocessor import PMDPreprocessor

class TestPMDPreprocessor(unittest.TestCase):
    
    def setUp(self):
        self.preprocessor = PMDPreprocessor()
    
    def test_empty_set_assignment(self):
        """Test: var x = {} -> var x = #{}"""
        code = "var x = {}"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "var x = #{}")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_empty_object_assignment(self):
        """Test: var x = {:} -> var x = #{:}"""
        code = "var x = {:}"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "var x = {:}")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_object_literal_assignment(self):
        """Test: var x = {"a": 1} -> var x = #{"a": 1}"""
        code = 'var x = {"a": 1}'
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, 'var x = {"a": 1}')
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_if_block(self):
        """Test: if (x) {} -> if (x) {}"""
        code = "if (x) {}"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "if (x) {}")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_function_block(self):
        """Test: function f() {} -> function f() {}"""
        code = "function f() {}"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "function f() {}")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_arrow_function_block(self):
        """Test: () => {} -> () => {}"""
        code = "() => {}"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "() => {}")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_function_call_with_empty_set(self):
        """Test: func({}) -> func(#{})"""
        code = "func({})"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "func(#{})")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_array_with_empty_set(self):
        """Test: arr[{}] -> arr[#{}]"""
        code = "arr[{}]"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "arr[#{}]")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_multiline_assignment(self):
        """Test multiline assignment with brace on new line"""
        code = """var x = 
{}"""
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, """var x = 
#{}""")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_multiline_function(self):
        """Test multiline function with brace on new line"""
        code = """function f()
{}"""
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, """function f()
{}""")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_multiline_if(self):
        """Test multiline if with brace on new line"""
        code = """if (condition)
{}"""
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, """if (condition)
{}""")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_multiline_arrow_function(self):
        """Test multiline arrow function with brace on new line"""
        code = """const fn = () =>
{}"""
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, """const fn = () =>
{}""")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_nested_expressions(self):
        """Test nested expressions with multiple braces"""
        code = 'func({"key": {}})'
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, 'func({"key": #{}})')
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_while_loop(self):
        """Test: while (x) {} -> while (x) {}"""
        code = "while (x) {}"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "while (x) {}")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_for_loop(self):
        """Test: for (i = 0; i < 10; i++) {} -> for (i = 0; i < 10; i++) {}"""
        code = "for (i = 0; i < 10; i++) {}"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "for (i = 0; i < 10; i++) {}")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_do_while_loop(self):
        """Test: do {} while (x) -> do {} while (x)"""
        code = "do {} while (x)"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "do {} while (x)")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_else_block(self):
        """Test: else {} -> else {}"""
        code = "else {}"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "else {}")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_object_with_property_on_new_line(self):
        """Test object with property starting on new line"""
        code = """const obj = {
    "key": "value"
}"""
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, """const obj = {
    "key": "value"
}""")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_complex_nested_case(self):
        """Test complex nested case with multiple braces"""
        code = """function test() {
    if (condition) {
        const obj = {
            "nested": {}
        };
    }
}"""
        expected = """function test() {
    if (condition) {
        const obj = {
            "nested": #{}
        };
    }
}"""
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, expected)
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_warnings_disabled(self):
        """Test that warnings are not generated when disabled"""
        preprocessor = PMDPreprocessor(warn_ambiguous=False)
        # This should trigger an ambiguous case but not generate warnings
        code = "someWeirdCase {}"
        result = preprocessor.preprocess(code)
        self.assertEqual(result, "someWeirdCase {}")
        self.assertEqual(len(preprocessor.warnings), 0)
    
    def test_warnings_enabled(self):
        """Test that warnings are generated for ambiguous cases"""
        preprocessor = PMDPreprocessor(warn_ambiguous=True)
        # This should trigger an ambiguous case and generate a warning
        code = "someWeirdCase {}"
        result = preprocessor.preprocess(code)
        self.assertEqual(result, "someWeirdCase {}")
        self.assertEqual(len(preprocessor.warnings), 1)
        self.assertIn("Ambiguous brace", preprocessor.warnings[0])
    
    def test_empty_string(self):
        """Test preprocessing empty string"""
        result = self.preprocessor.preprocess("")
        self.assertEqual(result, "")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_no_braces(self):
        """Test preprocessing code with no braces"""
        code = "var x = 5; var y = 10;"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, code)
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_multiple_braces_same_line(self):
        """Test multiple braces on the same line"""
        code = "var x = {}; var y = {};"
        result = self.preprocessor.preprocess(code)
        self.assertEqual(result, "var x = #{}; var y = #{};")
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_json_with_multiline_script_blocks(self):
        """Test that newlines in PMD script blocks within JSON are escaped"""
        code = '''{
  "title": "<%
         fundType.fundType
         
        %>",
  "value": "<% single.line %>"
}'''
        result = self.preprocessor.preprocess(code)
        expected = '''{
  "title": "<%\\n         fundType.fundType\\n         \\n        %>",
  "value": "<% single.line %>"
}'''
        self.assertEqual(result, expected)
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_json_with_carriage_return_newlines(self):
        """Test that carriage returns in PMD script blocks are also escaped"""
        code = '''{
  "title": "<%line1\r\nline2\r\nline3%>"
}'''
        result = self.preprocessor.preprocess(code)
        expected = '''{
  "title": "<%line1\\r\\nline2\\r\\nline3%>"
}'''
        self.assertEqual(result, expected)
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_json_with_property_access_in_field_names(self):
        """Test that JSON with property access patterns in field names is detected as JSON"""
        code = '''{
  "stepAction.id": "value",
  "helperFunctions.script": "another_value",
  "responseErrorDetail": {}
}'''
        result = self.preprocessor.preprocess(code)
        # Should remain unchanged since it's detected as JSON
        self.assertEqual(result, code)
        self.assertEqual(len(self.preprocessor.warnings), 0)
    
    def test_long_if_condition_with_brace(self):
        """Test that long if conditions are properly detected as blocks"""
        code = '''if(empty adaptiveTasksGET || adaptiveTaskStatusGET.status =='Pending' || adaptiveTaskStatusGET.status =='InProgress'){
    return false;
}'''
        result = self.preprocessor.preprocess(code)
        # Should remain unchanged since it's detected as a block
        self.assertEqual(result, code)
        self.assertEqual(len(self.preprocessor.warnings), 0)

if __name__ == '__main__':
    unittest.main()
