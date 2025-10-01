from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from ..models import ProjectContext, PMDModel, PodModel
from lark import Tree
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

    def find_script_fields(self, pmd_model: PMDModel, context=None) -> List[Tuple[str, str, str, int]]:
        """
        Recursively find all fields in a PMD model that contain script content (<% %>).
        Uses context-level caching to avoid repeated expensive parsing operations.
        
        Args:
            pmd_model: The PMD model to search
            context: ProjectContext for caching (optional)
        
        Returns:
            List of tuples: (field_path, field_value, field_name, line_offset)
            - field_path: Full path to the field (e.g., "script", "onLoad")
            - field_value: The actual script content
            - field_name: Just the field name for display purposes
            - line_offset: Line number where the script starts in the original file
        """
        # Use context-level caching if available
        if context is not None:
            cached_fields = context.get_cached_pmd_script_fields(pmd_model.pageId)
            if cached_fields is not None:
                return cached_fields
            
            # If not cached, extract and cache them
            script_fields = self._extract_script_fields(pmd_model)
            context.set_cached_pmd_script_fields(pmd_model.pageId, script_fields)
            return script_fields
        else:
            # Fallback to model-level caching for backward compatibility
            cached_fields = pmd_model.get_cached_script_fields()
            if cached_fields is not None:
                return cached_fields
            
            # If not cached, extract and cache them
            script_fields = self._extract_script_fields(pmd_model)
            pmd_model.set_cached_script_fields(script_fields)
            return script_fields
    
    def get_cached_ast(self, script_content: str, context=None) -> Optional[Tree]:
        """
        Get cached AST for script content, or parse and cache it.
        
        Args:
            script_content: The script content to parse
            context: ProjectContext for caching (optional)
        
        Returns:
            Parsed AST or None if parsing failed
        """
        if context is not None:
            # Check if AST is already cached
            cached_ast = context.get_cached_ast(script_content)
            if cached_ast is not None:
                return cached_ast
            
            # Parse and cache the AST
            try:
                from ..pmd_script_parser import pmd_script_parser
                ast = pmd_script_parser.parse(script_content)
                context.set_cached_ast(script_content, ast)
                return ast
            except Exception:
                return None
        else:
            # Fallback to direct parsing without caching
            try:
                from ..pmd_script_parser import pmd_script_parser
                return pmd_script_parser.parse(script_content)
            except Exception:
                return None
    
    def _extract_script_fields(self, pmd_model: PMDModel) -> List[Tuple[str, str, str, int]]:
        """Internal method to extract script fields without caching."""
        script_fields = []
        script_pattern = r'<%.*?%>'
        
        # Track the last line found to search forward from there
        last_line_found = 0
        
        def _search_dict(data: Dict[str, Any], prefix: str = "", file_content: str = "", display_prefix: str = "") -> None:
            """Recursively search a dictionary for script fields."""
            nonlocal last_line_found
            
            for key, value in data.items():
                if isinstance(value, str) and re.search(script_pattern, value, re.DOTALL):
                    field_path = f"{prefix}.{key}" if prefix else key
                    # Use human-readable display name
                    display_name = f"{display_prefix}->{key}" if display_prefix else key
                    # Calculate line offset by finding the script content in the original file
                    # Start searching from the last found position to avoid duplicates
                    line_offset = self._calculate_script_line_offset(file_content, value, search_start_line=last_line_found) if file_content else 1
                    last_line_found = line_offset
                    script_fields.append((field_path, value, display_name, line_offset))
                elif isinstance(value, dict):
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    new_display_prefix = f"{display_prefix}->{key}" if display_prefix else key
                    _search_dict(value, new_prefix, file_content, new_display_prefix)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            # Check if this item has a 'name' field for human-readable display
                            item_name = item.get('name', f'[{i}]')
                            
                            # Create technical path with index
                            new_prefix = f"{prefix}.{key}.{i}" if prefix else f"{key}.{i}"
                            
                            # Create human-readable path with name
                            if isinstance(item_name, str) and item_name != f'[{i}]':
                                # This item has a name - use it for display
                                new_display_prefix = f"{display_prefix}->{key}->name: {item_name}" if display_prefix else f"{key}->name: {item_name}"
                            else:
                                # No name field, fall back to index
                                new_display_prefix = f"{display_prefix}->{key}[{i}]" if display_prefix else f"{key}[{i}]"
                            
                            _search_dict(item, new_prefix, file_content, new_display_prefix)
                        elif isinstance(item, str) and re.search(script_pattern, item, re.DOTALL):
                            field_path = f"{prefix}.{key}.{i}" if prefix else f"{key}.{i}"
                            # Use human-readable display name
                            display_name = f"{display_prefix}->{key}[{i}]" if display_prefix else f"{key}[{i}]"
                            # Calculate line offset by finding the script content in the original file
                            # Start searching from the last found position to avoid duplicates
                            line_offset = self._calculate_script_line_offset(file_content, item, search_start_line=last_line_found) if file_content else 1
                            last_line_found = line_offset
                            script_fields.append((field_path, item, display_name, line_offset))
        
        # Get the source content from the PMD model
        source_content = getattr(pmd_model, 'source_content', '')
        
        # Convert PMD model to dict for recursive search
        pmd_dict = pmd_model.model_dump(exclude={'file_path', 'source_content'})
        _search_dict(pmd_dict, file_content=source_content)
        
        return script_fields
    
    def _calculate_script_line_offset(self, file_content: str, script_content: str, search_start_line: int = 0) -> int:
        """
        Calculate the line number where the script content starts in the original file.
        
        Args:
            file_content: The full source file content
            script_content: The script content to find
            search_start_line: Line number to start searching from (0-based, for avoiding duplicates)
            
        Returns:
            Line number (1-based) where the script starts
        """
        if not file_content or not script_content:
            return 1
        
        # Normalize both strings for comparison
        # The script_content has escaped newlines (\n), but file_content has actual newlines
        normalized_script = script_content.replace('\\n', '\n')
        
        # Strip the <% and %> wrappers from the script content for matching
        stripped_script = self._strip_pmd_wrappers(normalized_script)
        if not stripped_script:
            return 1
        
        lines = file_content.split('\n')
        
        # Start searching from the specified line (to avoid finding previous occurrences)
        start_index = max(0, search_start_line)
        
        # Strategy 1: Find by matching a unique part of the script content
        # Take the first 50 characters of the stripped script for matching
        script_start = stripped_script.strip()[:50]
        if script_start:
            for i in range(start_index, len(lines)):
                line = lines[i]
                if script_start in line:
                    # Found the line - return it (1-based)
                    return i + 1
        
        # Strategy 2: Find by matching the first significant line of the script
        if stripped_script:
            first_script_line = stripped_script.split('\n')[0].strip()
            if first_script_line and len(first_script_line) > 15:  # Only use if it's substantial
                for i in range(start_index, len(lines)):
                    line = lines[i]
                    if first_script_line in line:
                        return i + 1
        
        # Strategy 3: Look for the opening <% tag followed by our script content
        for i in range(start_index, len(lines)):
            line = lines[i]
            if '<%' in line:
                # Check if this line contains the start of our script content
                first_script_line = stripped_script.split('\n')[0].strip()
                if first_script_line and first_script_line in line:
                    # The script starts on this line after the <% tag
                    return i + 1
                elif first_script_line and len(first_script_line) > 15:
                    # The script content might start on the next line after the <% tag
                    # But only if the next line contains our script
                    if i + 1 < len(lines) and first_script_line in lines[i + 1]:
                        return i + 2
        
        # Fallback: if we have a start line, return at least that
        return max(1, search_start_line + 1)
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            content = content[2:-2].strip()
        
        # Unescape all escape sequences that were escaped during JSON processing
        # We need to be careful with single quotes - they should remain escaped for valid PMD Script
        import codecs
        
        # First, handle the case where we have double backslashes (from PMD source)
        # Convert \\' to \' (double backslash + quote becomes escaped quote)
        content = content.replace('\\\\', '\\')
        
        # Then handle other escape sequences
        content = content.replace('\\n', '\n')
        content = content.replace('\\t', '\t')
        content = content.replace('\\r', '\r')
        content = content.replace('\\"', '"')
        
        # Note: We do NOT unescape single quotes - they should remain as \' for valid PMD Script
        
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

    def traverse_presentation_structure(self, presentation_data: Dict[str, Any], base_path: str = "") -> Generator[Tuple[Dict[str, Any], str, int], None, None]:
        """
        Generic traversal of PMD presentation structure that handles different layout types.
        
        This method can handle:
        - Standard sections with 'children' arrays
        - areaLayout with 'primaryLayout' and 'secondaryLayout' 
        - basicFormLayout with 'sections' containing widgets
        - hubs and other layout types
        - Any nested structure containing widgets
        
        Args:
            presentation_data: The presentation dictionary to traverse
            base_path: Base path for tracking widget locations
            
        Yields:
            Tuples of (widget, full_path, index) for each widget found
        """
        if not isinstance(presentation_data, dict):
            return
            
        # Known widget container field names
        WIDGET_CONTAINERS = {
            'children', 'primaryLayout', 'secondaryLayout', 'sections', 
            'items', 'navigationTasks'
        }
        
        # Known layout types that may contain nested structures
        LAYOUT_TYPES = {
            'areaLayout', 'basicFormLayout', 'section', 'hub',
            'layout', 'panelList', 'grid', 'fieldSet'
        }
        
        def _traverse_container(container_data: Any, container_path: str, container_name: str = ""):
            """Recursively traverse a container that may hold widgets."""
            if isinstance(container_data, list):
                # Direct list of widgets
                for i, item in enumerate(container_data):
                    if isinstance(item, dict):
                        item_path = f"{container_path}.{i}" if container_path else str(i)
                        yield (item, item_path, i)
                        
                        # Recursively check for nested containers
                        yield from _traverse_container(item, item_path)
            elif isinstance(container_data, dict):
                # Check if this is a widget with nested containers
                widget_type = container_data.get('type', '')
                
                # Look for known widget container fields
                for field_name in WIDGET_CONTAINERS:
                    if field_name in container_data:
                        field_data = container_data[field_name]
                        field_path = f"{container_path}.{field_name}" if container_path else field_name
                        yield from _traverse_container(field_data, field_path, field_name)
                
                # For layout types, also check for any array fields that might contain widgets
                if widget_type in LAYOUT_TYPES:
                    for key, value in container_data.items():
                        if key not in WIDGET_CONTAINERS and isinstance(value, list):
                            # Check if this list contains widget-like objects
                            if value and isinstance(value[0], dict) and 'type' in value[0]:
                                field_path = f"{container_path}.{key}" if container_path else key
                                yield from _traverse_container(value, field_path, key)
        
        # Start traversal from the presentation data
        yield from _traverse_container(presentation_data, base_path)
    
    
    def _parse_script_content(self, script_content: str, context=None):
        """Parse script content using the PMD script grammar with context-level caching support."""
        try:
            # Strip PMD wrappers if present
            content = self._strip_pmd_wrappers(script_content)
            if not content:
                return None
            
            # Use context-level caching if available
            if context is not None:
                return self.get_cached_ast(content, context)
            else:
                # Fallback to per-rule caching for backward compatibility
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