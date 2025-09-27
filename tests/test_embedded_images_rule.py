"""Unit tests for EmbeddedImagesRule."""

import pytest
from parser.rules.structure.validation.embedded_images import EmbeddedImagesRule
from parser.rules.base import Finding
from parser.models import PMDModel, PodModel, ProjectContext


class TestEmbeddedImagesRule:
    """Test cases for EmbeddedImagesRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = EmbeddedImagesRule()
        assert rule.ID == "EmbeddedImagesRule"
        assert rule.DESCRIPTION == "Detects embedded images that should be stored as external files"
        assert rule.SEVERITY == "WARNING"
        assert rule.MIN_IMAGE_SIZE_THRESHOLD == 100

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

    def test_detect_large_binary_content(self):
        """Test detection of large binary-like content."""
        rule = EmbeddedImagesRule()
        
        # Create large binary-like content with high base64 ratio
        large_binary_content = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" * 30  # Large string with high base64 ratio
        
        pmd_data = {
            "pageId": "test",
            "file_path": "test.pmd",
            "presentation": {
                "body": {
                    "children": [
                        {
                            "type": "image",
                            "data": large_binary_content
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
        assert "Large embedded content found" in findings[0].message
        assert findings[0].file_path == "test.pmd"

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
                            "data": small_content
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

    def test_is_potentially_embedded_image_data(self):
        """Test the helper method for detecting embedded image data."""
        rule = EmbeddedImagesRule()
        
        # Test with high base64 ratio
        high_base64_content = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" * 20
        assert rule._is_potentially_embedded_image_data(high_base64_content) == True
        
        # Test with low base64 ratio - shorter string to avoid high ratio
        low_base64_content = "Hello world! This is just regular text content."
        assert rule._is_potentially_embedded_image_data(low_base64_content) == False
        
        # Test with small content
        small_content = "small"
        assert rule._is_potentially_embedded_image_data(small_content) == False

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
