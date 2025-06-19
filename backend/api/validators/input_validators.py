"""
Input Validation for API Layer
Validates HTTP request parameters and data
Single Responsibility: Validate all API inputs according to business rules
"""

import re
from typing import Any, Optional, Dict, List
from flask import request
import logging

# Import from analysis layer for validation rules
from backend.analysis import DependencyType


class InputValidator:
    """
    Comprehensive input validator for API requests
    Single Responsibility: Validate all types of API inputs
    """

    # Validation constants
    MIN_SEARCH_QUERY_LENGTH = 0
    MAX_SEARCH_QUERY_LENGTH = 100
    MIN_LIMIT = 1
    MAX_LIMIT = 1000
    MIN_PAGE = 1
    MAX_PAGE = 10000

    # Valid dependency types (from domain model)
    VALID_DEPENDENCY_TYPES = {dt.value for dt in DependencyType}

    # File path validation pattern
    FILE_PATH_PATTERN = re.compile(r'^[a-zA-Z0-9_/\-\.\\]+$')

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_search_query(self, query: Any) -> Dict[str, Any]:
        """
        Validate search query parameter

        Args:
            query: Search query to validate

        Returns:
            Dict with 'is_valid' bool and optional 'error' message
        """
        if query is None:
            return {'is_valid': False, 'error': 'Search query is required'}

        if not isinstance(query, str):
            return {'is_valid': False, 'error': 'Search query must be a string'}

        query_length = len(query.strip())

        if query_length < self.MIN_SEARCH_QUERY_LENGTH:
            return {'is_valid': False, 'error': f'Search query too short (minimum: {self.MIN_SEARCH_QUERY_LENGTH})'}

        if query_length > self.MAX_SEARCH_QUERY_LENGTH:
            return {'is_valid': False, 'error': f'Search query too long (maximum: {self.MAX_SEARCH_QUERY_LENGTH})'}

        return {'is_valid': True}

    def validate_limit_parameter(self, limit: Any) -> Dict[str, Any]:
        """
        Validate limit parameter for pagination

        Args:
            limit: Limit value to validate

        Returns:
            Dict with 'is_valid' bool and optional 'error' message
        """
        if limit is None:
            return {'is_valid': True}  # Limit is optional

        # Try to convert to integer
        try:
            limit_int = int(limit)
        except (ValueError, TypeError):
            return {'is_valid': False, 'error': 'Limit must be a valid integer'}

        if limit_int < self.MIN_LIMIT:
            return {'is_valid': False, 'error': f'Limit too small (minimum: {self.MIN_LIMIT})'}

        if limit_int > self.MAX_LIMIT:
            return {'is_valid': False, 'error': f'Limit too large (maximum: {self.MAX_LIMIT})'}

        return {'is_valid': True, 'value': limit_int}

    def validate_dependency_type(self, dep_type: Any) -> Dict[str, Any]:
        """
        Validate dependency type parameter

        Args:
            dep_type: Dependency type to validate

        Returns:
            Dict with 'is_valid' bool and optional 'error' message
        """
        if dep_type is None:
            return {'is_valid': False, 'error': 'Dependency type is required'}

        if not isinstance(dep_type, str):
            return {'is_valid': False, 'error': 'Dependency type must be a string'}

        if dep_type not in self.VALID_DEPENDENCY_TYPES:
            valid_types = ', '.join(sorted(self.VALID_DEPENDENCY_TYPES))
            return {
                'is_valid': False,
                'error': f'Invalid dependency type. Valid types: {valid_types}'
            }

        return {'is_valid': True}

    def validate_file_path(self, file_path: Any) -> Dict[str, Any]:
        """
        Validate file path parameter

        Args:
            file_path: File path to validate

        Returns:
            Dict with 'is_valid' bool and optional 'error' message
        """
        if file_path is None:
            return {'is_valid': False, 'error': 'File path is required'}

        if not isinstance(file_path, str):
            return {'is_valid': False, 'error': 'File path must be a string'}

        file_path_stripped = file_path.strip()

        if not file_path_stripped:
            return {'is_valid': False, 'error': 'File path cannot be empty'}

        if len(file_path_stripped) > 1000:
            return {'is_valid': False, 'error': 'File path too long (maximum: 1000 characters)'}

        # Basic pattern validation (adjust as needed for your file naming conventions)
        if not self.FILE_PATH_PATTERN.match(file_path_stripped):
            return {'is_valid': False, 'error': 'File path contains invalid characters'}

        return {'is_valid': True}

    def validate_page_parameter(self, page: Any) -> Dict[str, Any]:
        """
        Validate page parameter for pagination

        Args:
            page: Page number to validate

        Returns:
            Dict with 'is_valid' bool and optional 'error' message
        """
        if page is None:
            return {'is_valid': True, 'value': 1}  # Default to page 1

        # Try to convert to integer
        try:
            page_int = int(page)
        except (ValueError, TypeError):
            return {'is_valid': False, 'error': 'Page must be a valid integer'}

        if page_int < self.MIN_PAGE:
            return {'is_valid': False, 'error': f'Page number too small (minimum: {self.MIN_PAGE})'}

        if page_int > self.MAX_PAGE:
            return {'is_valid': False, 'error': f'Page number too large (maximum: {self.MAX_PAGE})'}

        return {'is_valid': True, 'value': page_int}


class RequestValidator:
    """
    High-level request validator that validates entire requests
    Single Responsibility: Validate complete HTTP requests
    """

    def __init__(self):
        self.input_validator = InputValidator()
        self.logger = logging.getLogger(__name__)

    def validate_search_request(self) -> Dict[str, Any]:
        """
        Validate search endpoint request

        Returns:
            Dict with validation results and extracted parameters
        """
        # Get query parameter
        query = request.args.get('q', '')

        # Validate query
        query_validation = self.input_validator.validate_search_query(query)
        if not query_validation['is_valid']:
            return {
                'is_valid': False,
                'error': query_validation['error'],
                'field': 'q'
            }

        return {
            'is_valid': True,
            'params': {
                'query': query.strip()
            }
        }

    def validate_hotspots_request(self) -> Dict[str, Any]:
        """
        Validate hotspots endpoint request

        Returns:
            Dict with validation results and extracted parameters
        """
        # Get limit parameter
        limit = request.args.get('limit', 20)

        # Validate limit
        limit_validation = self.input_validator.validate_limit_parameter(limit)
        if not limit_validation['is_valid']:
            return {
                'is_valid': False,
                'error': limit_validation['error'],
                'field': 'limit'
            }

        return {
            'is_valid': True,
            'params': {
                'limit': limit_validation.get('value', 20)
            }
        }

    def validate_dependencies_by_type_request(self, dep_type: str) -> Dict[str, Any]:
        """
        Validate dependencies by type endpoint request

        Args:
            dep_type: Dependency type from URL path

        Returns:
            Dict with validation results and extracted parameters
        """
        # Validate dependency type
        type_validation = self.input_validator.validate_dependency_type(dep_type)
        if not type_validation['is_valid']:
            return {
                'is_valid': False,
                'error': type_validation['error'],
                'field': 'dep_type'
            }

        return {
            'is_valid': True,
            'params': {
                'dependency_type': dep_type
            }
        }

    def validate_file_details_request(self, file_path: str) -> Dict[str, Any]:
        """
        Validate file details endpoint request

        Args:
            file_path: File path from URL path

        Returns:
            Dict with validation results and extracted parameters
        """
        # Validate file path
        path_validation = self.input_validator.validate_file_path(file_path)
        if not path_validation['is_valid']:
            return {
                'is_valid': False,
                'error': path_validation['error'],
                'field': 'file_path'
            }

        return {
            'is_valid': True,
            'params': {
                'file_path': file_path.strip()
            }
        }


# Singleton instances for easy import
input_validator = InputValidator()
request_validator = RequestValidator()