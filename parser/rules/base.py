from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, List, Tuple
from dataclasses import dataclass
from ..models import ProjectContext, PMDModel, PodModel
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
        self.rule_id = self.rule.__class__.__name__
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
        Uses caching to avoid repeated expensive parsing operations.
        
        Args:
            pmd_model: The PMD model to search
        
        Returns:
            List of tuples: (field_path, field_value, field_name, line_offset)
            - field_path: Full path to the field (e.g., "script", "onLoad")
            - field_value: The actual script content
            - field_name: Just the field name for display purposes
            - line_offset: Line number where the script starts in the original file
        """
        # Check if we have cached script fields
        cached_fields = pmd_model.get_cached_script_fields()
        if cached_fields is not None:
            return cached_fields
        
        # If not cached, extract and cache them
        script_fields = self._extract_script_fields(pmd_model)
        pmd_model.set_cached_script_fields(script_fields)
        return script_fields
    
    def _extract_script_fields(self, pmd_model: PMDModel) -> List[Tuple[str, str, str, int]]:
        """Internal method to extract script fields without caching."""
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
        """Parse script content using the PMD script grammar with caching support."""
        try:
            # Strip PMD wrappers if present
            content = self._strip_pmd_wrappers(script_content)
            if not content:
                return None
            
            # Use a simple hash-based cache to avoid re-parsing the same content
            cache_key = hash(content)
            if not hasattr(self, '_script_ast_cache'):
                self._script_ast_cache = {}
            
            if cache_key not in self._script_ast_cache:
                from ..pmd_script_parser import pmd_script_parser
                self._script_ast_cache[cache_key] = pmd_script_parser.parse(content)
            
            return self._script_ast_cache[cache_key]
        except Exception as e:
            print(f"Failed to parse script content: {e}")
            return None
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            return content[2:-2].strip()
        return content
    
    # Pod-specific utility methods
    
    def find_pod_script_fields(self, pod_model: PodModel) -> List[Tuple[str, str, str, int]]:
        """
        Find all script content within Pod endpoints and template widgets.
        
        Args:
            pod_model: The Pod model to search
            
        Returns:
            List of tuples containing:
            - field_path: Path to the field (e.g., "seed.endPoints[0].onReceive")
            - script_content: The actual script content
            - display_name: Human-readable field name
            - line_offset: Line number where the script starts
        """
        script_fields = []
        script_pattern = r'<%.*?%>'
        
        # Search endpoints in seed for script content (any field with <% %>)
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict):
                    for field_name, field_value in endpoint.items():
                        if isinstance(field_value, str) and re.search(script_pattern, field_value, re.DOTALL):
                            field_path = f"seed.endPoints[{i}].{field_name}"
                            display_name = f"endpoint '{endpoint.get('name', f'endpoint_{i}')}' {field_name}"
                            line_offset = self._calculate_pod_script_line_offset(pod_model.source_content, field_value)
                            script_fields.append((field_path, field_value, display_name, line_offset))
        
        # Search template widgets for script content (e.g., onClick, onLoad handlers)
        template_scripts = self._find_template_script_fields(pod_model.seed.template, "seed.template")
        script_fields.extend(template_scripts)
        
        return script_fields
    
    def _find_template_script_fields(self, widget_data: Any, path_prefix: str) -> List[Tuple[str, str, str, int]]:
        """Recursively search template widgets for script content."""
        script_fields = []
        script_pattern = r'<%.*?%>'
        
        def _search_widget(widget: Dict[str, Any], widget_path: str):
            # Search all widget fields for script content (any field with <% %>)
            for field_name, field_value in widget.items():
                if isinstance(field_value, str) and re.search(script_pattern, field_value, re.DOTALL):
                    field_path = f"{widget_path}.{field_name}"
                    widget_type = widget.get('type', 'unknown')
                    widget_id = widget.get('id', 'unnamed')
                    display_name = f"{widget_type} widget '{widget_id}' {field_name}"
                    line_offset = 1  # POD script line calculation would be more complex
                    script_fields.append((field_path, field_value, display_name, line_offset))
            
            # Recursively search children
            if 'children' in widget and isinstance(widget['children'], list):
                for i, child in enumerate(widget['children']):
                    if isinstance(child, dict):
                        child_path = f"{widget_path}.children[{i}]"
                        _search_widget(child, child_path)
        
        if isinstance(widget_data, dict):
            _search_widget(widget_data, path_prefix)
        elif isinstance(widget_data, list):
            for i, item in enumerate(widget_data):
                if isinstance(item, dict):
                    item_path = f"{path_prefix}[{i}]"
                    _search_widget(item, item_path)
        
        return script_fields
    
    def _calculate_pod_script_line_offset(self, file_content: str, script_content: str) -> int:
        """Calculate the line number where script content starts in a Pod file."""
        if not file_content or not script_content:
            return 1
        
        # For Pods, this is more complex since scripts can be in various places
        # For now, return a basic line number - this could be enhanced later
        lines = file_content.split('\n')
        for i, line in enumerate(lines):
            if '<%' in line:
                return i + 1
        return 1
    
    def find_pod_widgets(self, pod_model: PodModel) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Find all widgets in a Pod template with their paths.
        
        Args:
            pod_model: The Pod model to search
            
        Returns:
            List of tuples containing:
            - widget_path: Path to the widget (e.g., "seed.template.children[0]")
            - widget_data: The widget dictionary
        """
        widgets = []
        
        def _collect_widgets(widget_data: Any, path: str):
            if isinstance(widget_data, dict) and 'type' in widget_data:
                widgets.append((path, widget_data))
                
                # Recursively search children
                if 'children' in widget_data and isinstance(widget_data['children'], list):
                    for i, child in enumerate(widget_data['children']):
                        child_path = f"{path}.children[{i}]"
                        _collect_widgets(child, child_path)
            elif isinstance(widget_data, list):
                for i, item in enumerate(widget_data):
                    item_path = f"{path}[{i}]"
                    _collect_widgets(item, item_path)
        
        if pod_model.seed.template:
            _collect_widgets(pod_model.seed.template, "seed.template")
        
        return widgets