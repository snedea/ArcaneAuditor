from pydantic import BaseModel, Field, PrivateAttr
from typing import List, Optional, Dict, Any
from lark import Tree

# --- Lazy import for the Lark parser ---
# This avoids a circular dependency if the parser ever needs the models.
_pmd_script_parser = None

def get_pmd_script_parser():
    """Lazily imports and returns the PMD Script parser to avoid circular imports."""
    global _pmd_script_parser
    if _pmd_script_parser is None:
        from .pmd_script_parser import pmd_script_parser
        _pmd_script_parser = pmd_script_parser
    return _pmd_script_parser

# -----------------------------------------------------------------------------
# 📄 Models for Individual File Types
# -----------------------------------------------------------------------------

class ScriptModel(BaseModel):
    """Represents the structure of a .script file."""
    source: str
    file_path: str = Field(..., exclude=True) # Exclude from exported model data

class PMDIncludes(BaseModel):
    scripts: Optional[List[str]] = Field(default_factory=list)

class PMDPresentation(BaseModel):
    attributes: Dict[str, Any] = Field(default_factory=dict)
    title: Dict[str, Any] = Field(default_factory=dict)
    body: Dict[str, Any] = Field(default_factory=dict)
    footer: Dict[str, Any] = Field(default_factory=dict)

class PMDModel(BaseModel):
    """Represents the structure of a .pmd page file."""
    pageId: str
    securityDomains: Optional[List[str]] = Field(default_factory=list)
    inboundEndpoints: Optional[List[dict]] = Field(default_factory=list)
    outboundEndpoints: Optional[List[dict]] = Field(default_factory=list)
    presentation: PMDPresentation = None
    onLoad: Optional[str] = None
    script: Optional[str] = None
    includes: Optional[PMDIncludes] = None
    file_path: str = Field(..., exclude=True)

    # Private attribute to cache the parsed AST of the 'onLoad' script
    _onLoad_ast: Optional[Tree] = PrivateAttr(default=None)
    # Private attribute to cache the parsed AST of the page-level 'script'
    _script_ast: Optional[Tree] = PrivateAttr(default=None)
    # Private attribute to store line mappings for script fields
    _line_mappings: Optional[Dict[str, List[int]]] = PrivateAttr(default=None)

    def _parse_script(self, script_content: Optional[str]) -> Optional[Tree]:
        """A helper method to parse a script string using the custom Lark parser."""
        if not script_content or not script_content.strip():
            return None
        try:
            parser = get_pmd_script_parser()
            return parser.parse(script_content)
        except Exception:
            # Failed to parse, return None to signal an error
            return None

    def get_onLoad_ast(self) -> Optional[Tree]:
        """Parses the onLoad script string and caches the result."""
        if self._onLoad_ast is None:
            self._onLoad_ast = self._parse_script(self.onLoad)
        return self._onLoad_ast

    def get_script_ast(self) -> Optional[Tree]:
        """Parses the page-level script string and caches the result."""
        if self._script_ast is None:
            self._script_ast = self._parse_script(self.script)
        return self._script_ast
    
    def set_line_mappings(self, line_mappings: Dict[str, List[int]]):
        """Set the line mappings for script fields."""
        self._line_mappings = line_mappings
    
    def get_original_line_number(self, field_path: str, processed_line: int) -> int:
        """
        Get the original line number for a field at a given processed line.
        
        Args:
            field_path: Path to the field (e.g., "onLoad", "endPoints.0.onSend")
            processed_line: Line number in the processed content
            
        Returns:
            Original line number
        """
        if not self._line_mappings or field_path not in self._line_mappings:
            return processed_line
        
        # For now, return the first line of the script field
        # This could be enhanced to map specific lines within the script
        return self._line_mappings[field_path][0] if self._line_mappings[field_path] else processed_line

class AMDRoute(BaseModel):
    pageId: str
    parameters: Optional[List[str]] = Field(default_factory=list)

class AMDModel(BaseModel):
    """Represents the structure of an .amd application definition file."""
    routes: Dict[str, AMDRoute]
    baseUrls: Optional[Dict[str, str]] = Field(default_factory=dict)
    flows: Optional[Dict[str, Any]] = Field(default_factory=dict)
    file_path: str = Field(..., exclude=True)
    
# NOTE: You would continue to define models for .pod and .smd files here
# in a similar fashion.

# -----------------------------------------------------------------------------
# 🗂️ The Central Project Context
# -----------------------------------------------------------------------------

class ProjectContext:
    """A central repository to hold all parsed models from the application."""
    def __init__(self):
        self.pmds: Dict[str, PMDModel] = {}          # Maps pageId to PMDModel
        self.scripts: Dict[str, ScriptModel] = {}    # Maps file name to ScriptModel
        self.amd: AMDModel = None          # Assumes one .amd file per app
        # self.pods: Dict[str, PODModel] = {}        # Placeholder for PODs
        # self.smd: Optional[SMDModel] = None        # Placeholder for SMD
        self.parsing_errors: List[str] = []          # To track files that failed validation

    def get_script_by_name(self, name: str) -> Optional[ScriptModel]:
        """Retrieves a script model by its file name (e.g., 'utils.script')."""
        return self.scripts.get(name)

    def get_pmd_by_id(self, page_id: str) -> Optional[PMDModel]:
        """Retrieves a PMD model by its pageId."""
        return self.pmds.get(page_id)