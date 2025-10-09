"""Unit tests for FileNameLowerCamelCaseRule."""

from parser.rules.structure.validation.file_name_lower_camel_case import FileNameLowerCamelCaseRule
from parser.models import PMDModel, PodModel, AMDModel, SMDModel, ScriptModel, ProjectContext


class TestFileNameLowerCamelCaseRule:
    """Test cases for FileNameLowerCamelCaseRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = FileNameLowerCamelCaseRule()
        assert rule.ID == "FileNameLowerCamelCaseRule"
        assert rule.DESCRIPTION == "Ensures all file names follow lowerCamelCase naming convention"
        assert rule.SEVERITY == "ADVICE"

    def test_get_description(self):
        """Test that get_description returns the correct description."""
        rule = FileNameLowerCamelCaseRule()
        assert rule.get_description() == rule.DESCRIPTION

    def test_valid_pmd_filename(self):
        """Test that valid lowerCamelCase PMD filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "myPage.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_pmd_filename_pascal_case(self):
        """Test that PascalCase PMD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "MyPage.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "MyPage.pmd" in findings[0].message
        assert "lowerCamelCase" in findings[0].message
        assert findings[0].file_path == "MyPage.pmd"

    def test_invalid_pmd_filename_snake_case(self):
        """Test that snake_case PMD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "my_page.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "my_page.pmd" in findings[0].message
        assert "lowerCamelCase" in findings[0].message

    def test_invalid_pmd_filename_uppercase(self):
        """Test that UPPERCASE PMD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "MYPAGE.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "MYPAGE.pmd" in findings[0].message

    def test_valid_pod_filename(self):
        """Test that valid lowerCamelCase POD filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pod_data = {
            "podId": "footerPod",
            "seed": {},
            "file_path": "footer.pod"
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"footerPod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_pod_filename(self):
        """Test that invalid POD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pod_data = {
            "podId": "footerPod",
            "seed": {},
            "file_path": "Footer_Pod.pod"
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"footerPod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Footer_Pod.pod" in findings[0].message

    def test_valid_amd_filename(self):
        """Test that valid lowerCamelCase AMD filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        amd_data = {
            "routes": {},
            "file_path": "myApp_abcdef.amd"
        }
        amd_model = AMDModel(**amd_data)
        context.amd = amd_model
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_amd_filename(self):
        """Test that invalid AMD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        amd_data = {
            "routes": {},
            "file_path": "MyApp_abcdef.amd"
        }
        amd_model = AMDModel(**amd_data)
        context.amd = amd_model
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "MyApp_abcdef.amd" in findings[0].message

    def test_valid_smd_filename(self):
        """Test that valid lowerCamelCase SMD filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        smd_model = SMDModel(
            id="site1",
            applicationId="myApp_abcdef",
            siteId="site1",
            file_path="myApp_abcdef.smd"
        )
        context.smd = smd_model
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_smd_filename(self):
        """Test that invalid SMD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        smd_model = SMDModel(
            id="site1",
            applicationId="MyApp_abcdef",
            siteId="site1",
            file_path="MyApp_abcdef.smd"
        )
        context.smd = smd_model
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "MyApp_abcdef.smd" in findings[0].message

    def test_valid_script_filename(self):
        """Test that valid lowerCamelCase Script filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        script_data = {
            "source": "function test() { }",
            "file_path": "helperFunctions.script"
        }
        script_model = ScriptModel(**script_data)
        context.scripts = {"helperFunctions": script_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_script_filename(self):
        """Test that invalid Script filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        script_data = {
            "source": "function test() { }",
            "file_path": "helper_functions.script"
        }
        script_model = ScriptModel(**script_data)
        context.scripts = {"helper_functions": script_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "helper_functions.script" in findings[0].message

    def test_multiple_invalid_filenames(self):
        """Test that multiple invalid filenames are all flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        # Add multiple files with invalid names
        pmd_data = {
            "pageId": "testPage",
            "file_path": "My_Page.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        pod_data = {
            "podId": "footerPod",
            "seed": {},
            "file_path": "Footer_Pod.pod"
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"footerPod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert any("My_Page.pmd" in f.message for f in findings)
        assert any("Footer_Pod.pod" in f.message for f in findings)

    def test_filename_with_numbers_valid(self):
        """Test that filenames with numbers following lowerCamelCase are valid."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "myPage2.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_filename_starting_with_number_invalid(self):
        """Test that filenames starting with numbers are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "2myPage.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "2myPage.pmd" in findings[0].message

    def test_single_lowercase_letter_filename_valid(self):
        """Test that a single lowercase letter filename is valid."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "a.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_filename_with_path_components(self):
        """Test that filenames with path components are handled correctly."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "presentation/MyPage.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "MyPage.pmd" in findings[0].message

