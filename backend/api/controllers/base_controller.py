"""
Base Controller for API endpoints
Provides common functionality for all controllers
Single Responsibility: Handle common HTTP concerns and error management
"""

import logging
from typing import Tuple, Any
from flask import request

from backend.analysis import DependencyAnalysisService, AnalysisError, ValidationError
from ..utils.response_builder import APIResponse, response_logger
from ..validators.input_validators import RequestValidator


class BaseController:
    """
    Base controller with common functionality for all API endpoints
    Single Responsibility: Provide shared controller functionality
    """

    def __init__(self, analysis_service: DependencyAnalysisService):
        """
        Initialize controller with analysis service

        Args:
            analysis_service: Dependency analysis service instance
        """
        self.analysis_service = analysis_service
        self.request_validator = RequestValidator()
        self.logger = logging.getLogger(__name__)

    def handle_error(self, error: Exception, operation: str) -> Tuple[Any, int]:
        """
        Handle errors consistently across all controllers

        Args:
            error: Exception that occurred
            operation: Name of operation that failed

        Returns:
            Tuple[Any, int]: Flask response and status code
        """
        endpoint = request.endpoint or 'unknown'

        if isinstance(error, ValidationError) or isinstance(error, ValueError):
            # Validation errors (400)
            error_msg = str(error)
            response_logger.log_error(endpoint, 400, "validation_error", error_msg)
            return APIResponse.validation_error(error_msg)

        elif isinstance(error, AnalysisError):
            # Business logic errors (500)
            error_msg = f"Analysis operation failed: {str(error)}"
            response_logger.log_error(endpoint, 500, "analysis_error", error_msg)
            return APIResponse.server_error(error_msg)

        else:
            # Unexpected errors (500)
            error_msg = f"{operation} failed due to unexpected error"
            self.logger.error(f"Unexpected error in {operation}: {error}", exc_info=True)
            response_logger.log_error(endpoint, 500, "server_error", error_msg)
            return APIResponse.server_error(error_msg)

    def validate_request(self, validation_method, *args) -> Tuple[bool, Any]:
        """
        Validate request using specified validation method

        Args:
            validation_method: Method to use for validation
            *args: Arguments to pass to validation method

        Returns:
            Tuple[bool, Any]: (is_valid, result_or_error_response)
        """
        try:
            validation_result = validation_method(*args)

            if not validation_result['is_valid']:
                error_response = APIResponse.validation_error(
                    message=validation_result['error'],
                    field=validation_result.get('field')
                )
                return False, error_response

            return True, validation_result.get('params', {})

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            error_response = APIResponse.server_error("Request validation failed")
            return False, error_response

    def log_success(self, operation: str, data_size: int = 0):
        """
        Log successful operation

        Args:
            operation: Name of successful operation
            data_size: Size of returned data (number of items)
        """
        endpoint = request.endpoint or 'unknown'
        response_logger.log_success(endpoint, 200, data_size)
        self.logger.debug(f"Successful {operation} - returned {data_size} items")

    def execute_with_error_handling(self, operation_name: str, operation_func, *args, **kwargs):
        """
        Execute an operation with consistent error handling

        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of operation_func or error response
        """
        try:
            return operation_func(*args, **kwargs)
        except Exception as e:
            return self.handle_error(e, operation_name)