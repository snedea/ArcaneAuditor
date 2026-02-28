"""
Test file for the simplified file processor.
Demonstrates the core features and error handling for internal use.
"""
import tempfile
import zipfile
from pathlib import Path
import logging
from file_processing import FileProcessor, ZipProcessingError, FileProcessorConfig

# Set up logging for tests
logging.basicConfig(level=logging.DEBUG)

def create_test_zip(zip_path: Path, files: dict) -> None:
    """Create a test zip file with specified content."""
    with zipfile.ZipFile(zip_path, 'w') as zip_ref:
        for filename, content in files.items():
            zip_ref.writestr(filename, content)

def test_basic_functionality():
    """Test basic zip file processing functionality."""
    print("\n=== Testing Basic Functionality ===")
    
    # Create test zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
        zip_path = Path(tmp_zip.name)
    
    try:
        # Create test content with Workday Extend file types
        test_files = {
            'config.pod': '{"key": "value", "number": 42}',
            'metadata.pmd': '<config><setting>test</setting></config>',
            'main.script': 'Workday Extend script content',
            'ignore.txt': 'This file should be ignored'
        }
        
        create_test_zip(zip_path, test_files)
        
        # Test with default processor
        processor = FileProcessor()
        result = processor.process_zip_file(zip_path)
        
        print(f"Found {len(result)} relevant files")
        for file_path, source_file in result.items():
            print(f"  - {file_path}: {source_file.size} bytes")
        
        assert len(result) == 3, f"Expected 3 files, got {len(result)}"
        assert 'config.pod' in result
        assert 'metadata.pmd' in result
        assert 'main.script' in result
        assert 'ignore.txt' not in result
        
        print("✅ Basic functionality test passed")
        
    finally:
        zip_path.unlink(missing_ok=True)

def test_configuration():
    """Test configuration-based processing."""
    print("\n=== Testing Configuration ===")
    
    # Create custom configuration
    config = FileProcessorConfig(
        max_file_size=1024,  # 1KB limit
        max_zip_size=1024 * 1024,  # 1MB limit
        relevant_extensions={".pod", ".pmd"},
        encoding="utf-8"
    )
    
    # Create test zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
        zip_path = Path(tmp_zip.name)
    
    try:
        # Create test content
        test_files = {
            'small.pod': '{"small": "file"}',
            'large.pod': 'x' * 2048,  # 2KB file
            'config.pmd': '<config>test</config>'
        }
        
        create_test_zip(zip_path, test_files)
        
        # Test with custom configuration
        processor = FileProcessor(config=config)
        result = processor.process_zip_file(zip_path)
        
        print(f"Found {len(result)} files within size limit")
        for file_path, source_file in result.items():
            print(f"  - {file_path}: {source_file.size} bytes")
        
        assert len(result) == 2, f"Expected 2 files, got {len(result)}"
        assert 'small.pod' in result
        assert 'config.pmd' in result
        assert 'large.pod' not in result  # Should be skipped due to size
        
        print("✅ Configuration test passed")
        
    finally:
        zip_path.unlink(missing_ok=True)

def test_error_handling():
    """Test error handling for various scenarios."""
    print("\n=== Testing Error Handling ===")
    
    # Test non-existent file
    try:
        processor = FileProcessor()
        processor.process_zip_file(Path("nonexistent.zip"))
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        print("✅ FileNotFoundError handled correctly")
    
    # Test invalid zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
        zip_path = Path(tmp_zip.name)
        zip_path.write_text("This is not a zip file")
    
    try:
        processor = FileProcessor()
        processor.process_zip_file(zip_path)
        assert False, "Should have raised ZipProcessingError"
    except ZipProcessingError:
        print("✅ ZipProcessingError handled correctly")
    finally:
        zip_path.unlink(missing_ok=True)
    
    # Test oversized zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
        zip_path = Path(tmp_zip.name)
    
    try:
        # Create a large zip file
        large_content = 'x' * (1024 * 1024)  # 1MB
        test_files = {f'large_{i}.txt': large_content for i in range(150)}  # 150MB total
        
        create_test_zip(zip_path, test_files)
        
        processor = FileProcessor(max_zip_size=1024 * 1024)  # 1MB limit
        processor.process_zip_file(zip_path)
        assert False, "Should have raised ZipProcessingError"
    except ZipProcessingError:
        print("✅ Oversized zip file handled correctly")
    finally:
        zip_path.unlink(missing_ok=True)

def test_large_file_handling():
    """Test handling of large files within limits."""
    print("\n=== Testing Large File Handling ===")
    
    # Create configuration with reasonable limits
    config = FileProcessorConfig(
        max_file_size=1024 * 1024,  # 1MB
        max_zip_size=10 * 1024 * 1024,  # 10MB
        relevant_extensions={".script", ".amd"}
    )
    
    # Create test zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
        zip_path = Path(tmp_zip.name)
    
    try:
        # Create test content with files of various sizes
        test_files = {
            'small.script': 'Small script content',
            'medium.amd': 'x' * (512 * 1024),  # 512KB
            'large.script': 'x' * (2 * 1024 * 1024),  # 2MB - exceeds limit
            'data.amd': '{"data": "value"}'
        }
        
        create_test_zip(zip_path, test_files)
        
        # Test with configuration
        processor = FileProcessor(config=config)
        result = processor.process_zip_file(zip_path)
        
        print(f"Found {len(result)} files within size limits")
        for file_path, source_file in result.items():
            print(f"  - {file_path}: {source_file.size} bytes")
        
        # Should only process files within size limits
        assert len(result) == 3, f"Expected 3 files, got {len(result)}"
        assert 'small.script' in result
        assert 'medium.amd' in result
        assert 'data.amd' in result
        assert 'large.script' not in result  # Should be skipped due to size
        
        print("✅ Large file handling test passed")
        
    finally:
        zip_path.unlink(missing_ok=True)

def test_macos_artifacts_excluded_from_zip():
    """Test that macOS __MACOSX directories and ._ resource fork files are excluded."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
        zip_path = Path(tmp_zip.name)

    try:
        test_files = {
            'dirty_app/helpers.script': 'function helper() { return true; }',
            'dirty_app/main.pmd': '{"key": "value"}',
            '__MACOSX/dirty_app/._helpers.script': 'macOS resource fork',
            '__MACOSX/._dirty_app': 'macOS resource fork',
            'dirty_app/._hidden.script': 'dot-underscore resource fork at file level',
        }

        create_test_zip(zip_path, test_files)

        processor = FileProcessor()
        result = processor.process_zip_file(zip_path)

        result_keys = set(result.keys())
        # Only the two real files should be present
        assert 'dirty_app/helpers.script' in result_keys
        assert 'dirty_app/main.pmd' in result_keys
        # macOS artifacts must be excluded
        assert not any('__MACOSX' in k for k in result_keys), \
            f"__MACOSX files leaked through: {[k for k in result_keys if '__MACOSX' in k]}"
        assert not any(Path(k).name.startswith('._') for k in result_keys), \
            f"._ files leaked through: {[k for k in result_keys if Path(k).name.startswith('._')]}"
        assert len(result) == 2, f"Expected 2 files, got {len(result)}: {list(result_keys)}"

    finally:
        zip_path.unlink(missing_ok=True)


def test_macos_artifacts_excluded_from_directory():
    """Test that macOS artifacts are excluded when processing a directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create real files
        (tmp_path / 'app').mkdir()
        (tmp_path / 'app' / 'main.script').write_text('function main() {}')
        (tmp_path / 'app' / 'config.pod').write_text('{"config": true}')

        # Create macOS artifacts
        (tmp_path / '__MACOSX').mkdir()
        (tmp_path / '__MACOSX' / '._main.script').write_text('resource fork')
        (tmp_path / 'app' / '._config.pod').write_text('resource fork')

        processor = FileProcessor()
        result = processor.process_directory(tmp_path)

        result_keys = set(result.keys())
        assert 'app/main.script' in result_keys
        assert 'app/config.pod' in result_keys
        assert not any('__MACOSX' in k for k in result_keys), \
            f"__MACOSX files leaked through: {result_keys}"
        assert not any(Path(k).name.startswith('._') for k in result_keys), \
            f"._ files leaked through: {result_keys}"
        assert len(result) == 2, f"Expected 2 files, got {len(result)}: {list(result_keys)}"


def main():
    """Run all tests."""
    print("🚀 Starting Simplified File Processor Tests")
    
    try:
        test_basic_functionality()
        test_configuration()
        test_error_handling()
        test_large_file_handling()
        
        print("\n🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
