"""
Interfaces for Branch Dependency Analysis
Defines contracts that implementations must follow (Interface Segregation Principle)
Single Responsibility: Define abstract contracts, no implementation details
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from .domain_models import (
    AnalysisResult,
    FileAnalysis,
    SummaryStatistics,
    DependencyType,
    Dependency
)


class AnalysisDataRepository(ABC):
    """
    Interface for loading and persisting analysis data
    Single Responsibility: Data access operations only
    """

    @abstractmethod
    def load_analysis_result(self) -> AnalysisResult:
        """
        Load complete analysis result from storage

        Returns:
            AnalysisResult: Complete analysis data

        Raises:
            RepositoryError: If data cannot be loaded
        """
        pass

    @abstractmethod
    def save_analysis_result(self, result: AnalysisResult) -> None:
        """
        Save analysis result to storage

        Args:
            result: Analysis result to save

        Raises:
            RepositoryError: If data cannot be saved
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """
        Check if analysis data exists in storage

        Returns:
            bool: True if data exists, False otherwise
        """
        pass

    @abstractmethod
    def get_last_modified(self) -> Optional[float]:
        """
        Get timestamp of last modification

        Returns:
            Optional[float]: Unix timestamp or None if not available
        """
        pass


class DependencyAnalysisService(ABC):
    """
    Interface for dependency analysis operations
    Single Responsibility: Business logic operations for analyzing dependencies
    """

    @abstractmethod
    def get_summary_statistics(self) -> SummaryStatistics:
        """
        Get comprehensive summary statistics

        Returns:
            SummaryStatistics: Computed summary statistics

        Raises:
            AnalysisError: If statistics cannot be computed
        """
        pass

    @abstractmethod
    def find_dependency_hotspots(self, limit: int = 20) -> List[FileAnalysis]:
        """
        Find files with most dependencies

        Args:
            limit: Maximum number of hotspots to return

        Returns:
            List[FileAnalysis]: Files sorted by dependency count (descending)

        Raises:
            AnalysisError: If hotspots cannot be computed
            ValueError: If limit is invalid
        """
        pass

    @abstractmethod
    def get_dependencies_by_type(self, dep_type: DependencyType) -> List[Dict[str, Any]]:
        """
        Get all dependencies of specific type across all files

        Args:
            dep_type: Type of dependencies to retrieve

        Returns:
            List[Dict]: Dependencies with file context information

        Raises:
            AnalysisError: If dependencies cannot be retrieved
        """
        pass

    @abstractmethod
    def search_dependencies(self, query: str) -> List[FileAnalysis]:
        """
        Search for dependencies by file path or context

        Args:
            query: Search query string

        Returns:
            List[FileAnalysis]: Files matching the search criteria

        Raises:
            AnalysisError: If search cannot be performed
            ValueError: If query is invalid
        """
        pass

    @abstractmethod
    def get_file_analysis(self, file_path: str) -> Optional[FileAnalysis]:
        """
        Get analysis for specific file

        Args:
            file_path: Path to the file (relative or absolute)

        Returns:
            Optional[FileAnalysis]: File analysis or None if not found

        Raises:
            AnalysisError: If file analysis cannot be retrieved
        """
        pass

    @abstractmethod
    def refresh_analysis(self) -> None:
        """
        Force reload of analysis data from repository

        Raises:
            AnalysisError: If refresh fails
        """
        pass


class CacheService(ABC):
    """
    Interface for caching analysis results
    Single Responsibility: Handle caching operations only
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get cached value by key

        Args:
            key: Cache key

        Returns:
            Optional[Any]: Cached value or None if not found
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set cached value

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete cached value

        Args:
            key: Cache key to delete
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key to check

        Returns:
            bool: True if key exists, False otherwise
        """
        pass


class ConfigurationProvider(ABC):
    """
    Interface for accessing configuration settings
    Single Responsibility: Provide configuration values only
    """

    @abstractmethod
    def get_analysis_file_path(self) -> str:
        """
        Get path to analysis data file

        Returns:
            str: File path for analysis data
        """
        pass

    @abstractmethod
    def get_cache_settings(self) -> Dict[str, Any]:
        """
        Get caching configuration

        Returns:
            Dict[str, Any]: Cache configuration settings
        """
        pass

    @abstractmethod
    def get_performance_settings(self) -> Dict[str, Any]:
        """
        Get performance-related settings

        Returns:
            Dict[str, Any]: Performance settings (timeouts, limits, etc.)
        """
        pass


class ValidationService(ABC):
    """
    Interface for input validation
    Single Responsibility: Validate inputs according to business rules
    """

    @abstractmethod
    def validate_search_query(self, query: str) -> bool:
        """
        Validate search query

        Args:
            query: Search query to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pass

    @abstractmethod
    def validate_limit_parameter(self, limit: int) -> bool:
        """
        Validate limit parameter for pagination/results

        Args:
            limit: Limit value to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pass

    @abstractmethod
    def validate_dependency_type(self, dep_type: str) -> bool:
        """
        Validate dependency type string

        Args:
            dep_type: Dependency type to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pass

    @abstractmethod
    def validate_file_path(self, file_path: str) -> bool:
        """
        Validate file path format

        Args:
            file_path: File path to validate

        Returns:
            bool: True if valid, False otherwise
        """
        pass


class MetricsCollector(ABC):
    """
    Interface for collecting performance and usage metrics
    Single Responsibility: Collect and report metrics only
    """

    @abstractmethod
    def record_analysis_time(self, operation: str, duration_seconds: float) -> None:
        """
        Record time taken for an analysis operation

        Args:
            operation: Name of the operation
            duration_seconds: Time taken in seconds
        """
        pass

    @abstractmethod
    def record_cache_hit(self, key: str) -> None:
        """
        Record cache hit event

        Args:
            key: Cache key that was hit
        """
        pass

    @abstractmethod
    def record_cache_miss(self, key: str) -> None:
        """
        Record cache miss event

        Args:
            key: Cache key that was missed
        """
        pass

    @abstractmethod
    def record_error(self, operation: str, error_type: str) -> None:
        """
        Record error occurrence

        Args:
            operation: Operation where error occurred
            error_type: Type/category of error
        """
        pass

    @abstractmethod
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of collected metrics

        Returns:
            Dict[str, Any]: Metrics summary data
        """
        pass


# Custom Exceptions for the Analysis Layer

class AnalysisError(Exception):
    """Base exception for analysis-related errors"""
    pass


class RepositoryError(AnalysisError):
    """Exception for data repository errors"""
    pass


class CacheError(AnalysisError):
    """Exception for caching errors"""
    pass


class ValidationError(AnalysisError):
    """Exception for validation errors"""
    pass


class ConfigurationError(AnalysisError):
    """Exception for configuration errors"""
    pass


# Factory Interface for Creating Services

class AnalysisServiceFactory(ABC):
    """
    Interface for creating analysis services with proper dependency injection
    Single Responsibility: Create and wire up service dependencies
    """

    @abstractmethod
    def create_dependency_analysis_service(self) -> DependencyAnalysisService:
        """
        Create a fully configured dependency analysis service

        Returns:
            DependencyAnalysisService: Configured service instance

        Raises:
            ConfigurationError: If service cannot be created
        """
        pass

    @abstractmethod
    def create_repository(self) -> AnalysisDataRepository:
        """
        Create data repository with proper configuration

        Returns:
            AnalysisDataRepository: Configured repository instance
        """
        pass

    @abstractmethod
    def create_cache_service(self) -> CacheService:
        """
        Create cache service with proper configuration

        Returns:
            CacheService: Configured cache service instance
        """
        pass

    @abstractmethod
    def create_validation_service(self) -> ValidationService:
        """
        Create validation service

        Returns:
            ValidationService: Configured validation service instance
        """
        pass

    @abstractmethod
    def create_metrics_collector(self) -> MetricsCollector:
        """
        Create metrics collector

        Returns:
            MetricsCollector: Configured metrics collector instance
        """
        pass