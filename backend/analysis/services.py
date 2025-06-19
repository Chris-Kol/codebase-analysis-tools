"""
Service implementations for Branch Dependency Analysis
Business logic layer that orchestrates domain operations
Single Responsibility: Implement business operations using domain models and repositories
"""

import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from .interfaces import (
    DependencyAnalysisService,
    AnalysisDataRepository,
    CacheService,
    ValidationService,
    MetricsCollector,
    AnalysisError,
    ValidationError
)
from .domain_models import (
    AnalysisResult,
    FileAnalysis,
    SummaryStatistics,
    DependencyType,
    Dependency
)


class BranchDependencyAnalysisService(DependencyAnalysisService):
    """
    Core service for Branch dependency analysis operations
    Single Responsibility: Orchestrate business logic for dependency analysis
    """

    def __init__(
            self,
            repository: AnalysisDataRepository,
            validation_service: ValidationService,
            cache_service: Optional[CacheService] = None,
            metrics_collector: Optional[MetricsCollector] = None
    ):
        """
        Initialize service with dependencies

        Args:
            repository: Data repository for loading analysis results
            validation_service: Input validation service
            cache_service: Optional caching service for performance
            metrics_collector: Optional metrics collection service
        """
        self.repository = repository
        self.validation_service = validation_service
        self.cache_service = cache_service
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)

        # Internal cache for loaded analysis result
        self._analysis_result: Optional[AnalysisResult] = None
        self._last_loaded_time: Optional[float] = None

    def get_summary_statistics(self) -> SummaryStatistics:
        """
        Get comprehensive summary statistics

        Returns:
            SummaryStatistics: Computed summary statistics

        Raises:
            AnalysisError: If statistics cannot be computed
        """
        start_time = time.time()

        try:
            # Check cache first
            cache_key = "summary_statistics"
            if self.cache_service:
                cached_stats = self.cache_service.get(cache_key)
                if cached_stats is not None:
                    if self.metrics_collector:
                        self.metrics_collector.record_cache_hit(cache_key)
                    self.logger.debug("Returned cached summary statistics")
                    return cached_stats

                if self.metrics_collector:
                    self.metrics_collector.record_cache_miss(cache_key)

            # Load analysis result and compute statistics
            analysis_result = self._get_analysis_result()
            summary_stats = SummaryStatistics.from_analysis_result(analysis_result)

            # Cache the result
            if self.cache_service:
                self.cache_service.set(cache_key, summary_stats, ttl=1800)  # 30 minutes

            # Record metrics
            if self.metrics_collector:
                duration = time.time() - start_time
                self.metrics_collector.record_analysis_time("get_summary_statistics", duration)

            self.logger.info("Generated summary statistics successfully")
            return summary_stats

        except Exception as e:
            if self.metrics_collector:
                self.metrics_collector.record_error("get_summary_statistics", type(e).__name__)

            error_msg = f"Failed to get summary statistics: {e}"
            self.logger.error(error_msg)
            raise AnalysisError(error_msg) from e

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
        start_time = time.time()

        try:
            # Validate input
            if not self.validation_service.validate_limit_parameter(limit):
                raise ValueError(f"Invalid limit parameter: {limit}")

            # Check cache
            cache_key = f"hotspots_{limit}"
            if self.cache_service:
                cached_hotspots = self.cache_service.get(cache_key)
                if cached_hotspots is not None:
                    if self.metrics_collector:
                        self.metrics_collector.record_cache_hit(cache_key)
                    return cached_hotspots

                if self.metrics_collector:
                    self.metrics_collector.record_cache_miss(cache_key)

            # Get hotspots from analysis result
            analysis_result = self._get_analysis_result()
            hotspots = list(analysis_result.get_hotspots(limit))

            # Cache the result
            if self.cache_service:
                self.cache_service.set(cache_key, hotspots, ttl=3600)  # 1 hour

            # Record metrics
            if self.metrics_collector:
                duration = time.time() - start_time
                self.metrics_collector.record_analysis_time("find_dependency_hotspots", duration)

            self.logger.info(f"Found {len(hotspots)} dependency hotspots (limit: {limit})")
            return hotspots

        except ValueError as e:
            # Re-raise validation errors as-is
            raise e
        except Exception as e:
            if self.metrics_collector:
                self.metrics_collector.record_error("find_dependency_hotspots", type(e).__name__)

            error_msg = f"Failed to find dependency hotspots: {e}"
            self.logger.error(error_msg)
            raise AnalysisError(error_msg) from e

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
        start_time = time.time()

        try:
            # Validate dependency type
            if not self.validation_service.validate_dependency_type(dep_type.value):
                raise ValueError(f"Invalid dependency type: {dep_type}")

            # Check cache
            cache_key = f"dependencies_by_type_{dep_type.value}"
            if self.cache_service:
                cached_deps = self.cache_service.get(cache_key)
                if cached_deps is not None:
                    if self.metrics_collector:
                        self.metrics_collector.record_cache_hit(cache_key)
                    return cached_deps

                if self.metrics_collector:
                    self.metrics_collector.record_cache_miss(cache_key)

            # Get dependencies from analysis result
            analysis_result = self._get_analysis_result()
            dependencies = []

            for file_analysis in analysis_result.files:
                file_deps = file_analysis.get_dependencies_by_type(dep_type)
                for dependency in file_deps:
                    dep_dict = dependency.to_dict()
                    dep_dict['file'] = file_analysis.relative_path
                    dependencies.append(dep_dict)

            # Cache the result
            if self.cache_service:
                self.cache_service.set(cache_key, dependencies, ttl=3600)  # 1 hour

            # Record metrics
            if self.metrics_collector:
                duration = time.time() - start_time
                self.metrics_collector.record_analysis_time("get_dependencies_by_type", duration)

            self.logger.info(f"Found {len(dependencies)} dependencies of type: {dep_type.value}")
            return dependencies

        except ValueError as e:
            # Re-raise validation errors as-is
            raise e
        except Exception as e:
            if self.metrics_collector:
                self.metrics_collector.record_error("get_dependencies_by_type", type(e).__name__)

            error_msg = f"Failed to get dependencies by type: {e}"
            self.logger.error(error_msg)
            raise AnalysisError(error_msg) from e

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
        start_time = time.time()

        try:
            # Validate query
            if not self.validation_service.validate_search_query(query):
                raise ValueError(f"Invalid search query: {query}")

            # No caching for search results as they depend on dynamic input
            analysis_result = self._get_analysis_result()
            search_results = list(analysis_result.search_files(query))

            # Record metrics
            if self.metrics_collector:
                duration = time.time() - start_time
                self.metrics_collector.record_analysis_time("search_dependencies", duration)

            self.logger.info(f"Search for '{query}' returned {len(search_results)} results")
            return search_results

        except ValueError as e:
            # Re-raise validation errors as-is
            raise e
        except Exception as e:
            if self.metrics_collector:
                self.metrics_collector.record_error("search_dependencies", type(e).__name__)

            error_msg = f"Failed to search dependencies: {e}"
            self.logger.error(error_msg)
            raise AnalysisError(error_msg) from e

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
        start_time = time.time()

        try:
            # Validate file path
            if not self.validation_service.validate_file_path(file_path):
                raise ValueError(f"Invalid file path: {file_path}")

            # Search through analysis result
            analysis_result = self._get_analysis_result()

            for file_analysis in analysis_result.files:
                if (file_analysis.relative_path == file_path or
                        file_analysis.file_path == file_path):

                    # Record metrics
                    if self.metrics_collector:
                        duration = time.time() - start_time
                        self.metrics_collector.record_analysis_time("get_file_analysis", duration)

                    self.logger.debug(f"Found analysis for file: {file_path}")
                    return file_analysis

            # File not found
            self.logger.debug(f"No analysis found for file: {file_path}")
            return None

        except ValueError as e:
            # Re-raise validation errors as-is
            raise e
        except Exception as e:
            if self.metrics_collector:
                self.metrics_collector.record_error("get_file_analysis", type(e).__name__)

            error_msg = f"Failed to get file analysis: {e}"
            self.logger.error(error_msg)
            raise AnalysisError(error_msg) from e

    def refresh_analysis(self) -> None:
        """
        Force reload of analysis data from repository

        Raises:
            AnalysisError: If refresh fails
        """
        try:
            # Clear internal cache
            self._analysis_result = None
            self._last_loaded_time = None

            # Clear external cache if available
            if self.cache_service:
                self.cache_service.clear()
                self.logger.debug("Cleared all cached data")

            # Force reload by accessing the analysis result
            self._get_analysis_result()

            self.logger.info("Analysis data refreshed successfully")

        except Exception as e:
            if self.metrics_collector:
                self.metrics_collector.record_error("refresh_analysis", type(e).__name__)

            error_msg = f"Failed to refresh analysis: {e}"
            self.logger.error(error_msg)
            raise AnalysisError(error_msg) from e

    def _get_analysis_result(self) -> AnalysisResult:
        """
        Get analysis result with lazy loading and caching

        Returns:
            AnalysisResult: Complete analysis data

        Raises:
            AnalysisError: If analysis cannot be loaded
        """
        # Check if we need to reload
        should_reload = (
                self._analysis_result is None or
                self._should_reload_data()
        )

        if should_reload:
            self.logger.debug("Loading analysis result from repository")
            self._analysis_result = self.repository.load_analysis_result()
            self._last_loaded_time = time.time()

        return self._analysis_result

    def _should_reload_data(self) -> bool:
        """
        Determine if data should be reloaded based on file modification time

        Returns:
            bool: True if data should be reloaded
        """
        if self._last_loaded_time is None:
            return True

        # Check if source file has been modified
        last_modified = self.repository.get_last_modified()
        if last_modified is None:
            return False

        return last_modified > self._last_loaded_time


class StandardValidationService(ValidationService):
    """
    Standard implementation of validation service
    Single Responsibility: Validate inputs according to business rules
    """

    # Business rule constants
    MIN_SEARCH_QUERY_LENGTH = 0
    MAX_SEARCH_QUERY_LENGTH = 100
    MIN_LIMIT = 1
    MAX_LIMIT = 1000
    VALID_DEPENDENCY_TYPES = {dt.value for dt in DependencyType}

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_search_query(self, query: str) -> bool:
        """Validate search query according to business rules"""
        if not isinstance(query, str):
            return False

        query_length = len(query.strip())
        is_valid = self.MIN_SEARCH_QUERY_LENGTH <= query_length <= self.MAX_SEARCH_QUERY_LENGTH

        if not is_valid:
            self.logger.debug(f"Invalid search query length: {query_length}")

        return is_valid

    def validate_limit_parameter(self, limit: int) -> bool:
        """Validate limit parameter for pagination/results"""
        if not isinstance(limit, int):
            return False

        is_valid = self.MIN_LIMIT <= limit <= self.MAX_LIMIT

        if not is_valid:
            self.logger.debug(f"Invalid limit parameter: {limit}")

        return is_valid

    def validate_dependency_type(self, dep_type: str) -> bool:
        """Validate dependency type string"""
        if not isinstance(dep_type, str):
            return False

        is_valid = dep_type in self.VALID_DEPENDENCY_TYPES

        if not is_valid:
            self.logger.debug(f"Invalid dependency type: {dep_type}")

        return is_valid

    def validate_file_path(self, file_path: str) -> bool:
        """Validate file path format"""
        if not isinstance(file_path, str):
            return False

        # Basic validation - not empty and reasonable length
        stripped_path = file_path.strip()
        is_valid = 0 < len(stripped_path) < 1000

        if not is_valid:
            self.logger.debug(f"Invalid file path: {file_path}")

        return is_valid


class SimpleMetricsCollector(MetricsCollector):
    """
    Simple in-memory metrics collection implementation
    Single Responsibility: Collect and aggregate performance metrics
    """

    def __init__(self):
        self.operation_times: Dict[str, List[float]] = {}
        self.cache_hits: Dict[str, int] = {}
        self.cache_misses: Dict[str, int] = {}
        self.errors: Dict[str, Dict[str, int]] = {}
        self.logger = logging.getLogger(__name__)

    def record_analysis_time(self, operation: str, duration_seconds: float) -> None:
        """Record time taken for an analysis operation"""
        if operation not in self.operation_times:
            self.operation_times[operation] = []

        self.operation_times[operation].append(duration_seconds)
        self.logger.debug(f"Recorded timing for {operation}: {duration_seconds:.3f}s")

    def record_cache_hit(self, key: str) -> None:
        """Record cache hit event"""
        self.cache_hits[key] = self.cache_hits.get(key, 0) + 1

    def record_cache_miss(self, key: str) -> None:
        """Record cache miss event"""
        self.cache_misses[key] = self.cache_misses.get(key, 0) + 1

    def record_error(self, operation: str, error_type: str) -> None:
        """Record error occurrence"""
        if operation not in self.errors:
            self.errors[operation] = {}

        self.errors[operation][error_type] = self.errors[operation].get(error_type, 0) + 1
        self.logger.debug(f"Recorded error for {operation}: {error_type}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        # Calculate operation statistics
        operation_stats = {}
        for operation, times in self.operation_times.items():
            if times:
                operation_stats[operation] = {
                    'count': len(times),
                    'avg_duration': sum(times) / len(times),
                    'min_duration': min(times),
                    'max_duration': max(times)
                }

        # Calculate cache statistics
        total_hits = sum(self.cache_hits.values())
        total_misses = sum(self.cache_misses.values())
        total_requests = total_hits + total_misses

        cache_stats = {
            'total_hits': total_hits,
            'total_misses': total_misses,
            'total_requests': total_requests,
            'hit_rate': total_hits / total_requests if total_requests > 0 else 0
        }

        return {
            'operations': operation_stats,
            'cache': cache_stats,
            'errors': self.errors
        }