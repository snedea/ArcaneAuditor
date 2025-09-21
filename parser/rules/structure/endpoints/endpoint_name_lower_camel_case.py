from ...base_validation import ValidationRule
from ...common_validations import validate_lower_camel_case
from ...line_number_utils import LineNumberUtils
from ....models import PMDModel, PodModel
from typing import Dict, Any, List


class EndpointNameLowerCamelCaseRule(ValidationRule):
    """Validates that endpoint names follow lowerCamelCase convention (style guide)."""
    
    DESCRIPTION = "Ensures endpoint names follow lowerCamelCase naming convention (style guide)"
    SEVERITY = "WARNING"
    
    def __init__(self):
        super().__init__(
            self.__class__.__name__,
            self.DESCRIPTION,
            self.SEVERITY
        )
    
    def get_entities_to_validate(self, pmd_model: PMDModel):
        """Get all endpoints to validate."""
        entities = []
        
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict) and 'name' in endpoint:
                    entities.append({
                        'entity': endpoint,
                        'entity_type': 'inbound endpoint',
                        'entity_name': endpoint.get('name', 'unknown'),
                        'entity_context': 'inbound',
                        'entity_index': i
                    })
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict) and 'name' in endpoint:
                        entities.append({
                            'entity': endpoint,
                            'entity_type': 'outbound endpoint',
                            'entity_name': endpoint.get('name', 'unknown'),
                            'entity_context': 'outbound',
                            'entity_index': i
                        })
        return entities
    
    def get_field_to_validate(self, entity_info):
        """Validate the 'name' field."""
        return 'name'
    
    def validate_field(self, field_value: str, entity_info: Dict[str, Any]) -> List[str]:
        """Validate that the field value follows lowerCamelCase convention."""
        entity_type = entity_info['entity_type']
        entity_name = entity_info['entity_name']
        field_name = self.get_field_to_validate(entity_info)
        
        return validate_lower_camel_case(field_value, field_name, entity_type, entity_name)
    
    def get_line_number(self, pmd_model: PMDModel, entity_info: Dict[str, Any]) -> int:
        """Get line number for the endpoint name field."""
        entity = entity_info['entity']
        endpoint_name = entity.get('name', '')
        
        if endpoint_name:
            return LineNumberUtils.find_field_line_number(pmd_model, 'name', endpoint_name)
        
        return 1  # Default fallback
    
    def get_entities_to_validate_pod(self, pod_model: PodModel) -> List[Dict[str, Any]]:
        """Get all endpoints from POD seed to validate."""
        entities = []
        
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict) and 'name' in endpoint:
                    entities.append({
                        'entity': endpoint,
                        'entity_type': 'endpoint',
                        'entity_name': endpoint.get('name', 'unknown'),
                        'entity_context': 'pod_seed',
                        'entity_path': f"seed.endPoints[{i}]",
                        'entity_index': i
                    })
        
        return entities
