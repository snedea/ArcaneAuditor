"""
Common validation functions for shared validation patterns.

This module contains reusable validation functions that can be used across
different validation rules. These functions provide consistent validation
logic for common patterns like lowerCamelCase naming conventions, field 
requirements, URL formats, email formats, etc.
"""
import re
from typing import List, Dict, Any


def validate_lower_camel_case(value: str, field_name: str, entity_type: str, entity_name: str) -> List[str]:
    """
    Validate that a value follows lowerCamelCase convention.
    
    Args:
        value: The value to validate
        field_name: Name of the field being validated
        entity_type: Type of entity (widget, endpoint, etc.)
        entity_name: Name of the entity
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    camel_case_pattern = re.compile(r'^[a-z][a-zA-Z0-9]*$')
    
    if not camel_case_pattern.match(value):
        errors.append(
            f"{entity_type.capitalize()} '{entity_name}' has invalid {field_name} '{value}'. "
            f"Must follow lowerCamelCase convention (e.g., 'myField', 'userName')."
        )
    
    return errors


def validate_required_field(entity: Dict[str, Any], field_name: str, entity_type: str, entity_name: str) -> List[str]:
    """Validate that a required field exists."""
    errors = []
    
    if field_name not in entity:
        errors.append(
            f"{entity_type.capitalize()} '{entity_name}' is missing required '{field_name}' field."
        )
    
    return errors


def validate_field_not_empty(entity: Dict[str, Any], field_name: str, entity_type: str, entity_name: str) -> List[str]:
    """Validate that a field is not empty."""
    errors = []
    
    field_value = entity.get(field_name, '')
    if not field_value or (isinstance(field_value, str) and not field_value.strip()):
        errors.append(
            f"{entity_type.capitalize()} '{entity_name}' has empty '{field_name}' field."
        )
    
    return errors


def validate_url_format(url: str, entity_type: str, entity_name: str) -> List[str]:
    """Validate that a URL follows the expected format."""
    errors = []
    
    if url and not url.startswith('/'):
        errors.append(
            f"{entity_type.capitalize()} '{entity_name}' URL should start with '/'."
        )
    
    return errors


def validate_email_format(email: str, entity_type: str, entity_name: str) -> List[str]:
    """Validate that an email follows the expected format."""
    errors = []
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    if email and not email_pattern.match(email):
        errors.append(
            f"{entity_type.capitalize()} '{entity_name}' has invalid email format '{email}'."
        )
    
    return errors


def validate_script_variable_camel_case(var_name: str) -> tuple[bool, str]:
    """
    Validate that a script variable name follows lowerCamelCase convention.
    
    Args:
        var_name: The variable name to validate
        
    Returns:
        Tuple of (is_valid, suggestion)
        - is_valid: True if the name follows camelCase convention
        - suggestion: Suggested camelCase version if invalid, otherwise the original name
    """
    camel_case_pattern = re.compile(r'^[a-z][a-zA-Z0-9]*$')
    
    if camel_case_pattern.match(var_name):
        return True, var_name
    
    # Generate suggestion
    suggestion = _suggest_camel_case(var_name)
    return False, suggestion


def _suggest_camel_case(var_name: str) -> str:
    """Suggest a camelCase version of the variable name."""
    # Convert snake_case to camelCase
    if '_' in var_name:
        parts = var_name.split('_')
        return parts[0].lower() + ''.join(word.capitalize() for word in parts[1:])
    # Convert PascalCase to camelCase
    elif var_name and var_name[0].isupper():
        return var_name[0].lower() + var_name[1:]
    return var_name