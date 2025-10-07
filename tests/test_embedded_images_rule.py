"""Unit tests for EmbeddedImagesRule."""

from parser.rules.structure.validation.embedded_images import EmbeddedImagesRule
from parser.models import PMDModel, PodModel, ProjectContext


class TestEmbeddedImagesRule:
    """Test cases for EmbeddedImagesRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = EmbeddedImagesRule()
        assert rule.ID == "EmbeddedImagesRule"
        assert rule.DESCRIPTION == "Detects embedded images that should be stored as external files"
        assert rule.SEVERITY == "ADVICE"

    def test_detect_base64_image(self):
        """Test detection of base64 encoded images."""
        rule = EmbeddedImagesRule()
        
        # Mock PMD model with base64 image
        base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "image",
                            "src": base64_image
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Embedded base64 image found" in findings[0].message
        assert findings[0].file_path == "test.pmd"

    def test_ignore_large_binary_content_without_base64_prefix(self):
        """Test that large binary-like content without base64 prefix is ignored."""
        rule = EmbeddedImagesRule()
        
        # Create large binary-like content without base64 prefix
        large_binary_content = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" * 30
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "image",
                            "src": large_binary_content
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_ignore_small_content(self):
        """Test that small content is ignored."""
        rule = EmbeddedImagesRule()
        
        # Small content should not trigger the rule
        small_content = "small image data"
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "image",
                            "src": small_content
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_ignore_external_image_references(self):
        """Test that external image references are ignored."""
        rule = EmbeddedImagesRule()
        
        # External image references should not trigger the rule
        external_image = "/images/logo.png"
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "image",
                            "src": external_image
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_check_pod_files(self):
        """Test that POD files are also checked."""
        rule = EmbeddedImagesRule()
        
        # Mock POD model with base64 image
        base64_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
        
        pod_data = {
            "podId": "test",
            "file_path": "test.pod",
            "seed": {
                "template": {
                    "body": {
                        "children": [
                            {
                                "type": "image",
                                "src": base64_image
                            }
                        ]
                    }
                }
            }
        }
        
        pod_model = PodModel(**pod_data)
        
        context = ProjectContext()
        context.pods = {"test": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Embedded base64 image found" in findings[0].message
        assert findings[0].file_path == "test.pod"

    def test_detect_base64_image_in_different_fields(self):
        """Test detection of base64 images in various field types."""
        rule = EmbeddedImagesRule()
        
        base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        # Test in different field types that were previously excluded
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "image",
                            "src": base64_image
                        },
                        {
                            "type": "text",
                            "value": base64_image
                        }
                    ]
                }
            },
            "endPoints": [
                {
                    "name": "testEndpoint",
                    "url": base64_image
                }
            ]
        }
        
        pmd_model = PMDModel(**pmd_data)
        
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2  # Should find base64 images in src and value fields
        assert all("Embedded base64 image found" in finding.message for finding in findings)

    def test_multiple_embedded_images(self):
        """Test detection of multiple embedded images in one file."""
        rule = EmbeddedImagesRule()
        
        base64_image1 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        base64_image2 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "image",
                            "src": base64_image1
                        },
                        {
                            "type": "image",
                            "src": base64_image2
                        }
                    ]
                }
            }
        }
        
        pmd_model = PMDModel(**pmd_data)
        
        context = ProjectContext()
        context.pmds = {"test": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert all("Embedded base64 image found" in finding.message for finding in findings)
