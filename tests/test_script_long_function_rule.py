#!/usr/bin/env python3
"""Unit tests for ScriptLongFunctionRule."""

import pytest
from parser.rules.script.complexity.long_function import ScriptLongFunctionRule
from parser.models import ProjectContext


class TestScriptLongFunctionRule:
    """Test cases for ScriptLongFunctionRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptLongFunctionRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "function" in self.rule.DESCRIPTION.lower()
    
    def test_long_function_flagged(self):
        """Test that long functions are flagged."""
        from parser.models import PMDModel
        
        # Create a function with many lines
        long_function = """<%
  const processData = function(data) {
    const result = {:};
    result.step1 = data.field1;
    result.step2 = data.field2;
    result.step3 = data.field3;
    result.step4 = data.field4;
    result.step5 = data.field5;
    result.step6 = data.field6;
    result.step7 = data.field7;
    result.step8 = data.field8;
    result.step9 = data.field9;
    result.step10 = data.field10;
    result.step11 = data.field11;
    result.step12 = data.field12;
    result.step13 = data.field13;
    result.step14 = data.field14;
    result.step15 = data.field15;
    result.step16 = data.field16;
    result.step17 = data.field17;
    result.step18 = data.field18;
    result.step19 = data.field19;
    result.step20 = data.field20;
    result.step21 = data.field21;
    result.step22 = data.field22;
    result.step23 = data.field23;
    result.step24 = data.field24;
    result.step25 = data.field25;
    result.step26 = data.field26;
    result.step27 = data.field27;
    result.step28 = data.field28;
    result.step29 = data.field29;
    result.step30 = data.field30;
    result.step31 = data.field31;
    result.step32 = data.field32;
    result.step33 = data.field33;
    result.step34 = data.field34;
    result.step35 = data.field35;
    result.step36 = data.field36;
    result.step37 = data.field37;
    result.step38 = data.field38;
    result.step39 = data.field39;
    result.step40 = data.field40;
    result.step41 = data.field41;
    result.step42 = data.field42;
    result.step43 = data.field43;
    result.step44 = data.field44;
    result.step45 = data.field45;
    result.step46 = data.field46;
    result.step47 = data.field47;
    result.step48 = data.field48;
    result.step49 = data.field49;
    result.step50 = data.field50;
    result.step51 = data.field51;
    return result;
  };
%>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script=long_function
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) >= 1
        assert "long" in findings[0].message.lower() or "lines" in findings[0].message.lower()
    
    def test_short_function_not_flagged(self):
        """Test that short functions are not flagged."""
        from parser.models import PMDModel
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content="",
            script="<%\n  const getTotal = function(items) {\n    return items.reduce((sum, item) => sum + item.value, 0);\n  };\n%>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        assert len(findings) == 0


if __name__ == '__main__':
    pytest.main([__file__])
