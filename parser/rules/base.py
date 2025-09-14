from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, List, Tuple
from dataclasses import dataclass
from ..models import ProjectContext, PMDModel
import re

@dataclass
class Finding:
    """Represents a single issue found by a rule."""
    rule: 'Rule'
    message: str
    line: int = 0
    column: int = 0
    file_path: str = ""
    
    def __post_init__(self):
        # Set derived fields automatically
        self.rule_id = self.rule.ID
        self.rule_description = self.rule.DESCRIPTION
        self.severity = self.rule.SEVERITY

    def __repr__(self) -> str:
        return f"[{self.rule_id}:{self.line}] ({self.severity}) in '{self.file_path}': {self.message}"

# The abstract base class that all rule implementations must inherit from.
class Rule(ABC):
    """Abstract base class for all analysis rules."""
    # --- Metadata for the rule ---
    ID: str = "RULE000"
    DESCRIPTION: str = "This is a base rule."
    SEVERITY: str = "INFO" # Can be 'INFO', 'WARNING', 'ERROR'

    @abstractmethod
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """
        The main entry point for a rule, which analyzes the entire project.
        This method should be a generator that yields Finding objects.
        
        Args:
            context: The fully-built ProjectContext containing all application models.
        
        Yields:
            Finding objects for any violations discovered.
        """
        # This is an abstract method; it must be implemented by subclasses.
        # The 'yield from' statement is a convenient way to delegate to
        # more specific visitor methods if you choose to implement them.
        yield from []

    # --- Optional "visitor" methods for convenience ---
    # Subclasses can implement these to organize their logic.
    def visit_pmd(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Optional visitor method to run logic on a single PMD model."""
        yield from []

    def find_script_fields(self, pmd_model: PMDModel) -> List[Tuple[str, str, str, int]]:
        """
        Recursively find all fields in a PMD model that contain script content (<% %>).
        
        Args:
            pmd_model: The PMD model to search
        
        Returns:
            List of tuples: (field_path, field_value, field_name, line_offset)
            - field_path: Full path to the field (e.g., "script", "onLoad")
            - field_value: The actual script content
            - field_name: Just the field name for display purposes
            - line_offset: Line number where the script starts in the original file
        """
        script_fields = []
        script_pattern = r'<%.*?%>'
        
        def _search_dict(data: Dict[str, Any], prefix: str = "", file_content: str = "") -> None:
            """Recursively search a dictionary for script fields."""
            for key, value in data.items():
                if isinstance(value, str) and re.search(script_pattern, value, re.DOTALL):
                    field_path = f"{prefix}.{key}" if prefix else key
                    # Use the full path as the display name for better context
                    display_name = field_path
                    # Calculate line offset by finding the script content in the original file
                    line_offset = self._calculate_script_line_offset(file_content, value) if file_content else 1
                    script_fields.append((field_path, value, display_name, line_offset))
                elif isinstance(value, dict):
                    _search_dict(value, f"{prefix}.{key}" if prefix else key, file_content)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            _search_dict(item, f"{prefix}.{key}.{i}" if prefix else f"{key}.{i}", file_content)
                        elif isinstance(item, str) and re.search(script_pattern, item, re.DOTALL):
                            field_path = f"{prefix}.{key}.{i}" if prefix else f"{key}.{i}"
                            # Use the full path as the display name for better context
                            display_name = field_path
                            # Calculate line offset by finding the script content in the original file
                            line_offset = self._calculate_script_line_offset(file_content, item) if file_content else 1
                            script_fields.append((field_path, item, display_name, line_offset))
        
        # Get the source content from the PMD model
        source_content = getattr(pmd_model, 'source_content', '')
        
        # Convert PMD model to dict for recursive search
        pmd_dict = pmd_model.model_dump(exclude={'file_path', 'source_content'})
        _search_dict(pmd_dict, file_content=source_content)
        
        return script_fields
    
    def _calculate_script_line_offset(self, file_content: str, script_content: str) -> int:
        """Calculate the line number where the script content starts in the original file."""
        if not file_content or not script_content:
            return 1
        
        # Normalize both strings for comparison
        # The script_content has escaped newlines (\n), but file_content has actual newlines
        normalized_script = script_content.replace('\\n', '\n')
        
        # Find the specific script content within the file
        # We need to find where this exact script content appears in the file
        lines = file_content.split('\n')
        for i, line in enumerate(lines):
            if normalized_script.strip() in line:
                # The AST parser treats the stripped script content as starting from line 1
                # So we need to return the line where the script content starts
                return i + 1  # Convert to 1-based line numbering
        
        # Fallback: find the line with the <% tag (for cases where script content is too long)
        for i, line in enumerate(lines):
            if '<%' in line and 'script' in line.lower():
                # Look for the "script" field specifically
                # The AST parser treats the stripped script content as starting from line 1
                # But the stripped content starts on the next line after the <% tag
                # So we need to return the line where the stripped content starts
                return i + 2  # Convert to 1-based line numbering and add 1 for the next line
        
        return 1  # Default to line 1 if not found
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            content = content[2:-2].strip()
        
        # Convert escaped newlines to actual newlines for proper line number tracking
        content = content.replace('\\n', '\n')
        return content

    def traverse_widgets_recursively(self, widgets: List[Dict[str, Any]], widget_path: str = "") -> Generator[Tuple[Dict[str, Any], str, int], None, None]:
        """
        Recursively traverse widgets and their children arrays.
        
        Args:
            widgets: List of widget dictionaries to traverse
            widget_path: Current path in the widget hierarchy (e.g., "body.children", "body.children.0.children")
            
        Yields:
            Tuples of (widget, full_path, index) for each widget found
        """
        if not isinstance(widgets, list):
            return
            
        for i, widget in enumerate(widgets):
            if not isinstance(widget, dict):
                continue
                
            # Yield the current widget
            current_path = f"{widget_path}.{i}" if widget_path else str(i)
            yield (widget, current_path, i)
            
            # Check if this widget has children and recurse
            children = widget.get('children', [])
            if isinstance(children, list) and children:
                children_path = f"{current_path}.children"
                yield from self.traverse_widgets_recursively(children, children_path)
    
    def _parse_script_content(self, script_content: str):
        """Parse script content using the PMD script grammar."""
        try:
            from ..pmd_script_parser import pmd_script_parser
            # Strip PMD wrappers if present
            content = self._strip_pmd_wrappers(script_content)
            if not content:
                return None
            return pmd_script_parser.parse(content)
        except Exception as e:
            print(f"Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            return content[2:-2].strip()
        return content