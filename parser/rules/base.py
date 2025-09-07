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
        return f"[{self.rule_id}:{self.line}] in '{self.file_path}': {self.message}"

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

    def find_script_fields(self, pmd_model: PMDModel) -> List[Tuple[str, str, str]]:
        """
        Recursively find all fields in a PMD model that contain script content (<% %>).
        
        Returns:
            List of tuples: (field_path, field_value, field_name)
            - field_path: Full path to the field (e.g., "script", "onLoad")
            - field_value: The actual script content
            - field_name: Just the field name for display purposes
        """
        script_fields = []
        script_pattern = r'<%[^%]*%>'
        
        def _search_dict(data: Dict[str, Any], prefix: str = "") -> None:
            """Recursively search a dictionary for script fields."""
            for key, value in data.items():
                if isinstance(value, str) and re.search(script_pattern, value):
                    field_path = f"{prefix}.{key}" if prefix else key
                    script_fields.append((field_path, value, key))
                elif isinstance(value, dict):
                    _search_dict(value, f"{prefix}.{key}" if prefix else key)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            _search_dict(item, f"{prefix}.{key}.{i}" if prefix else f"{key}.{i}")
                        elif isinstance(item, str) and re.search(script_pattern, item):
                            field_path = f"{prefix}.{key}.{i}" if prefix else f"{key}.{i}"
                            script_fields.append((field_path, item, f"{key}[{i}]"))
        
        # Convert PMD model to dict for recursive search
        pmd_dict = pmd_model.model_dump(exclude={'file_path'})
        _search_dict(pmd_dict)
        
        return script_fields

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