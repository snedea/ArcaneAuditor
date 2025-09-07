"""
Rules package for PMD validation.

This package contains validation rules for code reviewers:

STRUCTURE VALIDATION (WARNING severity - structure and naming violations):
- structure_validation_rules: Catches structure and naming violations that code reviewers should catch
  Examples: naming conventions, data structure compliance, required field validation

SCRIPT VALIDATION (WARNING severity - script quality violations):
- script_validation_rules: Catches script quality violations that code reviewers should catch
  Examples: use of var vs let/const, nested block levels, code complexity metrics

BASE CLASSES:
- base: Core Rule abstract base class
- base_validation: Enhanced ValidationRule base class for validation patterns
- common_validations: Common validation utility functions

Note: Basic structural validation (missing required fields, etc.) is handled by the compiler.
This tool focuses on structure, naming, and script quality compliance for code reviewers.

Rules are automatically discovered by the rules engine - no manual imports needed.
"""
