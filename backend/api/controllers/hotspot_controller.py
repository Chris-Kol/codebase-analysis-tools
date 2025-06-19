"""
Hotspots Controller for API endpoints
Handles dependency hotspots endpoints
Single Responsibility: Handle hotspot-related HTTP requests
"""

from typing import Tuple, Any

from backend.analysis import DependencyAnalysisService
from ..utils.response_builder import APIResponse
from .base_controller import BaseController


class HotspotsController(BaseController):
    """
    Controller for dependency hotspots endpoints
    Single Responsibility: Handle hotspot operations only
    """

    def __init__(self, analysis_service: DependencyAnalysisService):
        """
        Initialize hotspots controller

        Args:
            analysis_service: Dependency analysis service instance
        """
        super().__init__(analysis_service)

    def get_hotspots(self) -> Tuple[Any, int]:
        """
        Get dependency hotspots (files with most dependencies)

        Returns:
            Tuple[Any, int]: Flask response and status code
        """

        def get_hotspots_operation():
            # Validate request parameters
            is_valid, result = self.validate_request(
                self.request_validator.validate_hotspots_request
            )

            if not is_valid:
                return result  # Return validation error response

            # Extract validated parameters
            params = result
            limit = params.get('limit', 20)

            # Get hotspots from analysis service
            hotspots = self.analysis_service.find_dependency_hotspots(limit)

            # Convert to dictionaries for JSON response
            hotspots_data = [hotspot.to_dict() for hotspot in hotspots]

            # Log successful operation
            self.log_success("get_hotspots", len(hotspots_data))

            # Return successful response
            return APIResponse.success(
                data=hotspots_data,
                message=f"Retrieved {len(hotspots_data)} dependency hotspots"
            )

        return self.execute_with_error_handling("get_hotspots", get_hotspots_operation)