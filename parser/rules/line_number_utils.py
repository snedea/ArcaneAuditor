"""
Utility functions for calculating line numbers in validation rules.
Consolidates common line numbering patterns to reduce duplication.
"""
from typing import Optional
from ..models import PMDModel


class LineNumberUtils:
    """Utility class for common line numbering operations in validation rules."""
    
    @staticmethod
    def find_field_line_number(pmd_model: PMDModel, field_name: str, field_value: str, 
                              search_range: int = 50) -> int:
        """
        Find the line number of a field with a specific value in PMD source content.
        
        Args:
            pmd_model: The PMD model containing source content
            field_name: Name of the field to search for (e.g., 'name', 'id')
            field_value: Value of the field to match
            search_range: Maximum number of lines to search after finding the field
            
        Returns:
            Line number (1-based) where the field is found, or 1 if not found
        """
        try:
            if not pmd_model.source_content:
                return 1
            
            lines = pmd_model.source_content.split('\n')
            
            # Search for the field with the specific value
            for i, line in enumerate(lines):
                if f'"{field_name}": "{field_value}"' in line or f'"{field_name}":"{field_value}"' in line:
                    return i + 1  # Convert to 1-based line numbering
            
            return 1
        except Exception:
            return 1
    
    @staticmethod
    def find_field_after_entity(pmd_model: PMDModel, entity_field: str, entity_value: str,
                               target_field: str, search_range: int = 20) -> int:
        """
        Find the line number of a field that appears after a specific entity.
        
        Args:
            pmd_model: The PMD model containing source content
            entity_field: Field name of the entity to find first (e.g., 'name')
            entity_value: Value of the entity field
            target_field: Field name to find after the entity (e.g., 'failOnStatusCodes')
            search_range: Maximum lines to search after finding the entity
            
        Returns:
            Line number (1-based) where the target field is found, or entity line + 1 if not found
        """
        try:
            if not pmd_model.source_content:
                return 1
            
            lines = pmd_model.source_content.split('\n')
            
            # Find the entity first
            entity_line = -1
            for i, line in enumerate(lines):
                if f'"{entity_field}": "{entity_value}"' in line or f'"{entity_field}":"{entity_value}"' in line:
                    entity_line = i
                    break
            
            if entity_line >= 0:
                # Look for the target field after the entity
                for i in range(entity_line, min(entity_line + search_range, len(lines))):
                    if f'"{target_field}"' in lines[i]:
                        return i + 1  # Convert to 1-based line numbering
            
            return entity_line + 1 if entity_line >= 0 else 1
            
        except Exception:
            return 1
    
    @staticmethod
    def find_section_line_number(pmd_model: PMDModel, section_name: str) -> int:
        """
        Find the line number of a specific section in PMD source content.
        
        Args:
            pmd_model: The PMD model containing source content
            section_name: Name of the section to find (e.g., 'footer', 'presentation')
            
        Returns:
            Line number (1-based) where the section is found, or 1 if not found
        """
        try:
            if not pmd_model.source_content:
                return 1
            
            lines = pmd_model.source_content.split('\n')
            
            # Look for the section
            for i, line in enumerate(lines):
                if f'"{section_name}"' in line:
                    return i + 1  # Convert to 1-based line numbering
            
            return 1  # Default to line 1 if not found
        except Exception:
            return 1
    
    @staticmethod
    def calculate_script_line_offset(pmd_model: PMDModel, script_content: str) -> int:
        """
        Calculate the line offset for script content within the PMD file.
        
        Args:
            pmd_model: The PMD model containing source content
            script_content: The script content to find the offset for
            
        Returns:
            Line number (1-based) where the script starts, or 1 if not found
        """
        try:
            if not pmd_model.source_content or not script_content:
                return 1
            
            lines = pmd_model.source_content.split('\n')
            
            # Find the script content in the source
            script_start = script_content.strip()[:50]  # First 50 chars for matching
            
            for i, line in enumerate(lines):
                if script_start in line:
                    return i + 1  # Convert to 1-based line numbering
            
            return 1
        except Exception:
            return 1
    
    @staticmethod
    def get_widget_line_number_simplified(pmd_model: PMDModel, widget_id: str, 
                                         section: str = "body") -> int:
        """
        Simplified widget line number calculation.
        This is a basic implementation - for complex widget positioning,
        the original complex logic might still be needed.
        
        Args:
            pmd_model: The PMD model containing source content
            widget_id: ID of the widget to find
            section: Section where the widget is located
            
        Returns:
            Line number (1-based) where the widget is found, or estimated line
        """
        try:
            if not pmd_model.source_content:
                return 1
            
            lines = pmd_model.source_content.split('\n')
            
            # Look for the widget ID directly
            for i, line in enumerate(lines):
                if f'"id": "{widget_id}"' in line or f'"id":"{widget_id}"' in line:
                    return i + 1  # Convert to 1-based line numbering
            
            # Fallback: estimate based on section
            section_base_lines = {
                'title': 1,
                'body': 5,
                'footer': 10
            }
            base_line = section_base_lines.get(section, 5)
            return base_line
            
        except Exception:
            return 1
