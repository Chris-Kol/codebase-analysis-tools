"""
Summary Controller for API endpoints
Handles summary statistics endpoints
Single Responsibility: Handle summary-related HTTP requests
"""

from typing import Tuple, Any

from backend.analysis import DependencyAnalysisService
from ..utils.response_builder import APIResponse
from .base_controller import BaseController


class SummaryController(BaseController):
    """
    Controller for summary statistics endpoints
    Single Responsibility: Handle summary operations only
    """

    def __init__(self, analysis_service: DependencyAnalysisService):
        """
        Initialize summary controller

        Args:
            analysis_service: Dependency analysis service instance
        """
        super().__init__(analysis_service)

    def get_summary(self) -> Tuple[Any, int]:
        """
        Get analysis summary statistics

        Returns:
            Tuple[Any, int]: Flask response and status code
        """

        def get_summary_operation():
            # Get summary statistics from analysis service
            summary_stats = self.analysis_service.get_summary_statistics()

            # Convert to dictionary for JSON response
            summary_data = summary_stats.to_dict()

            # Log successful operation
            self.log_success("get_summary", 1)

            # Return successful response
            return APIResponse.success(
                data=summary_data,
                message="Summary statistics retrieved successfully"
            )

        return self.execute_with_error_handling("get_summary", get_summary_operation)