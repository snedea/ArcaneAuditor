#!/usr/bin/env python3
"""Unit tests for PMD/POD long script block rule."""

import pytest
from parser.rules.script.complexity.long_script_block import ScriptLongBlockRule
from parser.rules.base import Finding
from parser.models import PMDModel, PodModel, ProjectContext


class TestScriptLongBlockRule:
    """Test cases for PMD/POD long script block rule."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptLongBlockRule()

    def test_rule_metadata(self):
        """Test rule metadata."""
        assert self.rule.ID == "ScriptLongBlockRule"
        assert self.rule.DESCRIPTION == "Ensures non-function script blocks in PMD/POD files don't exceed maximum line count (max 30 lines). Excludes function definitions which are handled by ScriptLongFunctionRule."
        assert self.rule.SEVERITY == "ADVICE"

    def test_pmd_with_short_onload(self):
        """Test PMD with short onLoad script block."""
        pmd_content = {
            "pageId": "test-page",
            "onLoad": "<% pageVariables.isGood = true; %>",
            "presentation": {
                "body": {
                    "type": "section",
                    "children": []
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        
        findings = list(self.rule.analyze(context))
        assert len(findings) == 0

    def test_pmd_with_long_onload(self):
        """Test PMD with long onLoad script block."""
        # Use a script with many individual statements to exceed the 20-statement threshold
        long_script = """<%
                pageVariables.data1 = processData1();
                pageVariables.data2 = processData2();
                pageVariables.data3 = processData3();
                pageVariables.data4 = processData4();
                pageVariables.data5 = processData5();
                pageVariables.data6 = processData6();
                pageVariables.data7 = processData7();
                pageVariables.data8 = processData8();
                pageVariables.data9 = processData9();
                pageVariables.data10 = processData10();
                pageVariables.data11 = processData11();
                pageVariables.data12 = processData12();
                pageVariables.data13 = processData13();
                pageVariables.data14 = processData14();
                pageVariables.data15 = processData15();
                pageVariables.data16 = processData16();
                pageVariables.data17 = processData17();
                pageVariables.data18 = processData18();
                pageVariables.data19 = processData19();
                pageVariables.data20 = processData20();
                pageVariables.data21 = processData21();
               %>"""
        
        pmd_content = {
            "pageId": "test-page",
            "onLoad": long_script,
            "presentation": {
                "body": {
                    "type": "section",
                    "children": []
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        findings = list(self.rule.analyze(context))
        assert len(findings) == 1
        
        finding = findings[0]
        assert finding.rule == self.rule
        assert "onLoad" in finding.message
        assert "script block" in finding.message.lower()
        # The script has many statements (21) which exceeds the 20-statement threshold
        assert "21 lines" in finding.message or "lines" in finding.message

    def test_pmd_with_long_onchange(self):
        """Test PMD with long onChange script block."""
        # Use a script with many individual statements to exceed the 20-statement threshold
        long_script = """<%
                widget1.setValue(value1);
                widget2.setValue(value2);
                widget3.setValue(value3);
                widget4.setValue(value4);
                widget5.setValue(value5);
                widget6.setValue(value6);
                widget7.setValue(value7);
                widget8.setValue(value8);
                widget9.setValue(value9);
                widget10.setValue(value10);
                widget11.setValue(value11);
                widget12.setValue(value12);
                widget13.setValue(value13);
                widget14.setValue(value14);
                widget15.setValue(value15);
                widget16.setValue(value16);
                widget17.setValue(value17);
                widget18.setValue(value18);
                widget19.setValue(value19);
                widget20.setValue(value20);
                widget21.setValue(value21);
               %>"""
        
        pmd_content = {
            "pageId": "test-page",
            "presentation": {
                "body": {
                    "type": "section",
                    "children": [{
                        "type": "widget",
                        "onChange": long_script
                    }]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        findings = list(self.rule.analyze(context))
        assert len(findings) == 1
        
        finding = findings[0]
        assert finding.rule == self.rule
        assert "onChange" in finding.message
        assert "script block" in finding.message.lower()
        # The script has many statements which exceeds the 20-statement threshold
        assert "lines" in finding.message

    def test_pmd_with_multiple_long_scripts(self):
        """Test PMD with multiple long script blocks."""
        long_script = """<%
                // This is a long script block with many lines
                pageVariables.data1 = processData1();
                pageVariables.data2 = processData2();
                pageVariables.data3 = processData3();
                pageVariables.data4 = processData4();
                pageVariables.data5 = processData5();
                pageVariables.data6 = processData6();
                pageVariables.data7 = processData7();
                pageVariables.data8 = processData8();
                pageVariables.data9 = processData9();
                pageVariables.data10 = processData10();
                pageVariables.data11 = processData11();
                pageVariables.data12 = processData12();
                pageVariables.data13 = processData13();
                pageVariables.data14 = processData14();
                pageVariables.data15 = processData15();
                pageVariables.data16 = processData16();
                pageVariables.data17 = processData17();
                pageVariables.data18 = processData18();
                pageVariables.data19 = processData19();
                pageVariables.data20 = processData20();
                pageVariables.data21 = processData21();
               %>"""
        
        pmd_content = {
            "pageId": "test-page",
            "onLoad": long_script,
            "script": long_script,
            "presentation": {
                "body": {
                    "type": "section",
                    "children": [{
                        "type": "widget",
                        "onChange": long_script
                    }]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        findings = list(self.rule.analyze(context))
        assert len(findings) == 3  # onLoad, script, onChange
        
        # Check that all findings mention script blocks
        for finding in findings:
            assert finding.rule == self.rule
            assert "script block" in finding.message.lower()

    def test_pmd_with_mixed_script_lengths(self):
        """Test PMD with both short and long script blocks."""
        short_script = "<% pageVariables.isGood = true; %>"
        long_script = """<%
                // Long script block
                pageVariables.data1 = processData1();
                pageVariables.data2 = processData2();
                pageVariables.data3 = processData3();
                pageVariables.data4 = processData4();
                pageVariables.data5 = processData5();
                pageVariables.data6 = processData6();
                pageVariables.data7 = processData7();
                pageVariables.data8 = processData8();
                pageVariables.data9 = processData9();
                pageVariables.data10 = processData10();
                pageVariables.data11 = processData11();
                pageVariables.data12 = processData12();
                pageVariables.data13 = processData13();
                pageVariables.data14 = processData14();
                pageVariables.data15 = processData15();
                pageVariables.data16 = processData16();
                pageVariables.data17 = processData17();
                pageVariables.data18 = processData18();
                pageVariables.data19 = processData19();
                pageVariables.data20 = processData20();
                pageVariables.data21 = processData21();
               %>"""
        
        pmd_content = {
            "pageId": "test-page",
            "onLoad": short_script,
            "script": long_script,
            "presentation": {
                "body": {
                    "type": "section",
                    "children": [{
                        "type": "widget",
                        "onChange": short_script
                    }]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        findings = list(self.rule.analyze(context))
        assert len(findings) == 1  # Only script should be flagged
        
        finding = findings[0]
        assert finding.rule == self.rule
        assert "script" in finding.message

    def test_pod_with_long_script(self):
        """Test POD with long script block."""
        long_script = """<%
                // Long POD script block
                pageVariables.podData1 = processPodData1();
                pageVariables.podData2 = processPodData2();
                pageVariables.podData3 = processPodData3();
                pageVariables.podData4 = processPodData4();
                pageVariables.podData5 = processPodData5();
                pageVariables.podData6 = processPodData6();
                pageVariables.podData7 = processPodData7();
                pageVariables.podData8 = processPodData8();
                pageVariables.podData9 = processPodData9();
                pageVariables.podData10 = processPodData10();
                pageVariables.podData11 = processPodData11();
                pageVariables.podData12 = processPodData12();
                pageVariables.podData13 = processPodData13();
                pageVariables.podData14 = processPodData14();
                pageVariables.podData15 = processPodData15();
                pageVariables.podData16 = processPodData16();
                pageVariables.podData17 = processPodData17();
                pageVariables.podData18 = processPodData18();
                pageVariables.podData19 = processPodData19();
                pageVariables.podData20 = processPodData20();
                pageVariables.podData21 = processPodData21();
               %>"""
        
        pod_content = {
            "podId": "test-pod",
            "seed": {
                "parameters": [],
                "endPoints": [{
                    "name": "test-endpoint",
                    "onReceive": long_script
                }],
                "template": {
                    "body": {
                        "type": "section",
                        "children": []
                    }
                }
            }
        }
        
        pod_model = PodModel(**pod_content, file_path="test.pod")
        context = ProjectContext()
        context.pods = {'test': pod_model}
        findings = list(self.rule.analyze(context))
        assert len(findings) == 1
        
        finding = findings[0]
        assert finding.rule == self.rule
        assert "onReceive" in finding.message
        assert "test.pod" in finding.file_path

    def test_script_without_template_syntax(self):
        """Test that non-template script content is ignored."""
        pmd_content = {
            "pageId": "test-page",
            "onLoad": "pageVariables.isGood = true;",  # No <% %> wrapper
            "presentation": {
                "body": {
                    "type": "section",
                    "children": []
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        findings = list(self.rule.analyze(context))
        assert len(findings) == 0

    def test_empty_script_blocks(self):
        """Test that empty script blocks are ignored."""
        pmd_content = {
            "pageId": "test-page",
            "onLoad": "<%  %>",
            "onSubmit": "<% %>",
            "presentation": {
                "body": {
                    "type": "section",
                    "children": []
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        findings = list(self.rule.analyze(context))
        assert len(findings) == 0

    def test_function_definitions_are_excluded(self):
        """Test that function definitions are excluded from this rule (handled by ScriptLongFunctionRule)."""
        long_function_script = """<%
                function processLongData() {
                    // This is a long function that should be handled by ScriptLongFunctionRule
                    pageVariables.data1 = processData1();
                    pageVariables.data2 = processData2();
                    pageVariables.data3 = processData3();
                    pageVariables.data4 = processData4();
                    pageVariables.data5 = processData5();
                    pageVariables.data6 = processData6();
                    pageVariables.data7 = processData7();
                    pageVariables.data8 = processData8();
                    pageVariables.data9 = processData9();
                    pageVariables.data10 = processData10();
                    pageVariables.data11 = processData11();
                    pageVariables.data12 = processData12();
                    pageVariables.data13 = processData13();
                    pageVariables.data14 = processData14();
                    pageVariables.data15 = processData15();
                    pageVariables.data16 = processData16();
                    pageVariables.data17 = processData17();
                    pageVariables.data18 = processData18();
                    pageVariables.data19 = processData19();
                    pageVariables.data20 = processData20();
                    pageVariables.data21 = processData21();
                    return pageVariables;
                }
               %>"""
        
        pmd_content = {
            "pageId": "test-page",
            "onLoad": long_function_script,
            "presentation": {
                "body": {
                    "type": "section",
                    "children": []
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        findings = list(self.rule.analyze(context))
        # Should be 0 findings because this rule excludes function definitions
        assert len(findings) == 0

    def test_finding_message_content(self):
        """Test that finding messages contain helpful information."""
        long_script = """<%
                // Long script block
                pageVariables.data1 = processData1();
                pageVariables.data2 = processData2();
                pageVariables.data3 = processData3();
                pageVariables.data4 = processData4();
                pageVariables.data5 = processData5();
                pageVariables.data6 = processData6();
                pageVariables.data7 = processData7();
                pageVariables.data8 = processData8();
                pageVariables.data9 = processData9();
                pageVariables.data10 = processData10();
                pageVariables.data11 = processData11();
                pageVariables.data12 = processData12();
                pageVariables.data13 = processData13();
                pageVariables.data14 = processData14();
                pageVariables.data15 = processData15();
                pageVariables.data16 = processData16();
                pageVariables.data17 = processData17();
                pageVariables.data18 = processData18();
                pageVariables.data19 = processData19();
                pageVariables.data20 = processData20();
                pageVariables.data21 = processData21();
               %>"""
        
        pmd_content = {
            "pageId": "test-page",
            "onLoad": long_script,
            "presentation": {
                "body": {
                    "type": "section",
                    "children": []
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_content, file_path="test.pmd")
        context = ProjectContext()
        context.pmds = {'test': pmd_model}
        findings = list(self.rule.analyze(context))
        assert len(findings) == 1
        
        message = findings[0].message
        assert "onLoad" in message
        assert "script block" in message.lower()
        assert "recommended" in message.lower() or "should" in message.lower() or "consider" in message.lower()
