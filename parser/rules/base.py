from abc import ABC, abstractmethod
from typing import Generator
from dataclasses import dataclass
from ..models import ProjectContext, PMDModel

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