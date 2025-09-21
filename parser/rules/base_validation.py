"""
Enhanced base class for validation rules with common validation patterns.
"""
from abc import ABC, abstractmethod
from typing import Generator, List, Dict, Any
from .base import Rule, Finding
from ..models import PMDModel, PodModel


class ValidationRule(Rule, ABC):
    """
    Enhanced base class for validation rules that can be applied to different entities.
    Provides common validation patterns and utilities.
    """
    
    def __init__(self, rule_id: str, description: str, severity: str = "WARNING"):
        self.ID = rule_id
        self.DESCRIPTION = description
        self.SEVERITY = severity
    
    @abstractmethod
    def get_entities_to_validate(self, pmd_model: PMDModel) -> List[Dict[str, Any]]:
        """
        Return a list of entities to validate, each with:
        - 'entity': the actual entity data
        - 'entity_type': type of entity (widget, endpoint, etc.)
        - 'entity_name': name of the entity
        - 'entity_context': additional context (section, etc.)
        - 'entity_index': index of the entity
        """
        pass
    
    @abstractmethod
    def get_field_to_validate(self, entity: Dict[str, Any]) -> str:
        """Get the field name to validate from the entity."""
        pass
    
    def validate_field(self, field_value: str, entity_info: Dict[str, Any]) -> List[str]:
        """
        Validate the field value and return list of error messages.
        Override this method to implement specific validation logic.
        """
        return []
    
    def get_line_number(self, pmd_model: PMDModel, entity_info: Dict[str, Any]) -> int:
        """Get line number for the entity. Override for custom line tracking."""
        return 1
    
    def analyze(self, context):
        """Main entry point - analyze all PMD models and Pod models in the context."""
        # Analyze PMD models
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model)
        
        # Analyze Pod models
        for pod_model in context.pods.values():
            yield from self.visit_pod(pod_model)
    
    def visit_pmd(self, pmd_model: PMDModel):
        """Validate entities in the PMD model."""
        entities = self.get_entities_to_validate(pmd_model)
        
        for entity_info in entities:
            field_name = self.get_field_to_validate(entity_info)
            field_value = entity_info['entity'].get(field_name, '')
            
            if field_value:
                errors = self.validate_field(field_value, entity_info)
                for error_message in errors:
                    line_number = self.get_line_number(pmd_model, entity_info)
                    
                    yield Finding(
                        rule=self,
                        message=error_message,
                        line=line_number,
                        column=1,
                        file_path=pmd_model.file_path
                    )
    
    def get_entities_to_validate_pod(self, pod_model: PodModel) -> List[Dict[str, Any]]:
        """
        Return a list of entities to validate from a Pod model.
        Override this method to provide Pod-specific entity extraction.
        Default implementation returns empty list (no Pod validation).
        """
        return []
    
    def get_line_number_pod(self, pod_model: PodModel, entity_info: Dict[str, Any]) -> int:
        """Get line number for the entity in a Pod file. Override for custom line tracking."""
        return 1
    
    def visit_pod(self, pod_model: PodModel):
        """Validate entities in the Pod model."""
        entities = self.get_entities_to_validate_pod(pod_model)
        
        for entity_info in entities:
            field_name = self.get_field_to_validate(entity_info)
            field_value = entity_info['entity'].get(field_name, '')
            
            if field_value:
                errors = self.validate_field(field_value, entity_info)
                for error_message in errors:
                    line_number = self.get_line_number_pod(pod_model, entity_info)
                    
                    yield Finding(
                        rule=self,
                        message=error_message,
                        line=line_number,
                        column=1,
                        file_path=pod_model.file_path
                    )
