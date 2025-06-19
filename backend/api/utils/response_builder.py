"""
API Response Builder Utilities
Standardized response building for consistent API responses
Single Responsibility: Create consistent HTTP responses across all endpoints
"""

from flask import jsonify
from typing import Any, Dict, Optional, Tuple
import logging


class APIResponse:
    """
    Utility class for building consistent API responses
    Single Responsibility: Standardize all API response formats
    """

    @staticmethod
    def success(data: Any, status: int = 200, message: Optional[str] = None) -> Tuple[Any, int]:
        """
        Create a successful API response

        Args:
            data: Response data (can be dict, list, or primitive)
            status: HTTP status code (default: 200)
            message: Optional success message

        Returns:
            Tuple[Any, int]: Flask response and status code
        """
        response_body = {
            'success': True,
            'data': data
        }

        if message:
            response_body['message'] = message

        return jsonify(response_body), status

    @staticmethod
    def error(
            message: str,
            error_type: str = "error",
            status: int = 400,
            details: Optional[Dict[str, Any]] = None
    ) -> Tuple[Any, int]:
        """
        Create an error API response

        Args:
            message: Error message for the user
            error_type: Type/category of error
            status: HTTP status code
            details: Optional additional error details

        Returns:
            Tuple[Any, int]: Flask response and status code
        """
        response_body = {
            'success': False,
            'error': {
                'message': message,
                'type': error_type
            }
        }

        if details:
            response_body['error']['details'] = details

        return jsonify(response_body), status

    @staticmethod
    def validation_error(
            message: str,
            field: Optional[str] = None,
            value: Optional[Any] = None
    ) -> Tuple[Any, int]:
        """
        Create a validation error response

        Args:
            message: Validation error message
            field: Field that failed validation (optional)
            value: Value that failed validation (optional)

        Returns:
            Tuple[Any, int]: Flask response and status code
        """
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = value

        return APIResponse.error(
            message=message,
            error_type="validation_error",
            status=400,
            details=details if details else None
        )

    @staticmethod
    def not_found(resource: str = "Resource", identifier: Optional[str] = None) -> Tuple[Any, int]:
        """
        Create a not found error response

        Args:
            resource: Type of resource not found
            identifier: Identifier of the resource (optional)

        Returns:
            Tuple[Any, int]: Flask response and status code
        """
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"

        return APIResponse.error(
            message=message,
            error_type="not_found",
            status=404
        )

    @staticmethod
    def server_error(message: str = "Internal server error") -> Tuple[Any, int]:
        """
        Create a server error response

        Args:
            message: Error message (default: generic message)

        Returns:
            Tuple[Any, int]: Flask response and status code
        """
        return APIResponse.error(
            message=message,
            error_type="server_error",
            status=500
        )

    @staticmethod
    def method_not_allowed(allowed_methods: Optional[list] = None) -> Tuple[Any, int]:
        """
        Create a method not allowed response

        Args:
            allowed_methods: List of allowed HTTP methods

        Returns:
            Tuple[Any, int]: Flask response and status code
        """
        message = "Method not allowed"
        details = {}

        if allowed_methods:
            details['allowed_methods'] = allowed_methods
            message += f". Allowed methods: {', '.join(allowed_methods)}"

        return APIResponse.error(
            message=message,
            error_type="method_not_allowed",
            status=405,
            details=details if details else None
        )

    @staticmethod
    def paginated_success(
            data: list,
            page: int,
            per_page: int,
            total: int,
            message: Optional[str] = None
    ) -> Tuple[Any, int]:
        """
        Create a paginated success response

        Args:
            data: List of items for current page
            page: Current page number
            per_page: Items per page
            total: Total number of items
            message: Optional success message

        Returns:
            Tuple[Any, int]: Flask response and status code
        """
        total_pages = (total + per_page - 1) // per_page  # Ceiling division
        has_next = page < total_pages
        has_prev = page > 1

        response_data = {
            'items': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            }
        }

        return APIResponse.success(response_data, message=message)


class ResponseLogger:
    """
    Utility for logging API responses
    Single Responsibility: Handle response logging consistently
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def log_success(self, endpoint: str, status_code: int, data_size: int = 0):
        """Log successful API response"""
        self.logger.info(f"SUCCESS {endpoint} - {status_code} - {data_size} items")

    def log_error(self, endpoint: str, status_code: int, error_type: str, message: str):
        """Log error API response"""
        self.logger.warning(f"ERROR {endpoint} - {status_code} - {error_type}: {message}")

    def log_validation_error(self, endpoint: str, field: str, value: Any):
        """Log validation error"""
        self.logger.debug(f"VALIDATION_ERROR {endpoint} - {field}: {value}")


# Singleton response logger instance
response_logger = ResponseLogger()