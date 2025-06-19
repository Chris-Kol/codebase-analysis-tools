"""
Factory implementations for creating analysis services with proper dependency injection
Single Responsibility: Create and wire up service dependencies following SOLID principles
"""

import logging
from typing import Optional, Dict, Any

from .interfaces import (
    AnalysisServiceFactory,
    DependencyAnalysisService,
    AnalysisDataRepository,
    CacheService,
    ValidationService,
    MetricsCollector,
    ConfigurationProvider,
    ConfigurationError
)
from .repositories import (
    JsonAnalysisDataRepository,
    InMemoryCacheService,
    NullCacheService,
    FileBasedConfigurationProvider,
    RepositoryFactory
)
from .services import (
    BranchDependencyAnalysisService,
    StandardValidationService,
    SimpleMetricsCollector
)


class DefaultAnalysisServiceFactory(AnalysisServiceFactory):
    """
    Default factory implementation for creating analysis services
    Single Responsibility: Create and configure all analysis service dependencies
    """

    def __init__(self,
                 analysis_file_path: Optional[str] = None,
                 config_overrides: Optional[Dict[str, Any]] = None):
        """
        Initialize factory with optional configuration

        Args:
            analysis_file_path: Override for analysis file path
            config_overrides: Dictionary of configuration overrides
        """
        self.analysis_file_path = analysis_file_path
        self.config_overrides = config_overrides or {}
        self.logger = logging.getLogger(__name__)

        # Cached instances for singleton behavior
        self._config_provider: Optional[ConfigurationProvider] = None
        self._cache_service: Optional[CacheService] = None
        self._validation_service: Optional[ValidationService] = None
        self._metrics_collector: Optional[MetricsCollector] = None

        # Configure logging
        self._configure_logging()

    def create_dependency_analysis_service(self) -> DependencyAnalysisService:
        """
        Create a fully configured dependency analysis service

        Returns:
            DependencyAnalysisService: Configured service instance

        Raises:
            ConfigurationError: If service cannot be created
        """
        try:
            self.logger.info("Creating dependency analysis service...")

            # Create all dependencies
            repository = self.create_repository()
            validation_service = self.create_validation_service()
            cache_service = self.create_cache_service()
            metrics_collector = self.create_metrics_collector()

            # Create the main service with all dependencies
            service = BranchDependencyAnalysisService(
                repository=repository,
                validation_service=validation_service,
                cache_service=cache_service,
                metrics_collector=metrics_collector
            )

            self.logger.info("Dependency analysis service created successfully")
            return service

        except Exception as e:
            error_msg = f"Failed to create dependency analysis service: {e}"
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg) from e

    def create_repository(self) -> AnalysisDataRepository:
        """
        Create data repository with proper configuration

        Returns:
            AnalysisDataRepository: Configured repository instance
        """
        try:
            config_provider = self._get_config_provider()
            cache_service = self.create_cache_service()

            repository = RepositoryFactory.create_analysis_repository(
                config_provider=config_provider,
                cache_service=cache_service
            )

            self.logger.debug("Analysis repository created successfully")
            return repository

        except Exception as e:
            error_msg = f"Failed to create repository: {e}"
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg) from e

    def create_cache_service(self) -> CacheService:
        """
        Create cache service with proper configuration

        Returns:
            CacheService: Configured cache service instance
        """
        if self._cache_service is None:
            try:
                config_provider = self._get_config_provider()

                # Apply configuration overrides
                cache_settings = config_provider.get_cache_settings()
                cache_settings.update(self.config_overrides.get('cache', {}))

                # Create cache service based on configuration
                if cache_settings.get('enabled', True):
                    max_size = cache_settings.get('max_size', 1000)
                    self._cache_service = InMemoryCacheService(max_size=max_size)
                    self.logger.debug(f"Created in-memory cache service (max_size: {max_size})")
                else:
                    self._cache_service = NullCacheService()
                    self.logger.debug("Created null cache service (caching disabled)")

            except Exception as e:
                error_msg = f"Failed to create cache service: {e}"
                self.logger.error(error_msg)
                raise ConfigurationError(error_msg) from e

        return self._cache_service

    def create_validation_service(self) -> ValidationService:
        """
        Create validation service

        Returns:
            ValidationService: Configured validation service instance
        """
        if self._validation_service is None:
            try:
                self._validation_service = StandardValidationService()
                self.logger.debug("Created standard validation service")

            except Exception as e:
                error_msg = f"Failed to create validation service: {e}"
                self.logger.error(error_msg)
                raise ConfigurationError(error_msg) from e

        return self._validation_service

    def create_metrics_collector(self) -> MetricsCollector:
        """
        Create metrics collector

        Returns:
            MetricsCollector: Configured metrics collector instance
        """
        if self._metrics_collector is None:
            try:
                # Check if metrics collection is enabled
                metrics_enabled = self.config_overrides.get('metrics', {}).get('enabled', True)

                if metrics_enabled:
                    self._metrics_collector = SimpleMetricsCollector()
                    self.logger.debug("Created simple metrics collector")
                else:
                    self._metrics_collector = NullMetricsCollector()
                    self.logger.debug("Created null metrics collector (metrics disabled)")

            except Exception as e:
                error_msg = f"Failed to create metrics collector: {e}"
                self.logger.error(error_msg)
                raise ConfigurationError(error_msg) from e

        return self._metrics_collector

    def _get_config_provider(self) -> ConfigurationProvider:
        """Get or create configuration provider (singleton)"""
        if self._config_provider is None:
            self._config_provider = FileBasedConfigurationProvider(self.analysis_file_path)
        return self._config_provider

    def _configure_logging(self) -> None:
        """Configure logging based on settings"""
        try:
            config_provider = self._get_config_provider()
            logging_settings = config_provider.get_logging_settings()

            # Apply logging overrides
            logging_settings.update(self.config_overrides.get('logging', {}))

            # Configure logging level
            log_level = getattr(logging, logging_settings.get('level', 'INFO').upper())
            logging.basicConfig(
                level=log_level,
                format=logging_settings.get('format',
                                            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )

        except Exception as e:
            # If logging configuration fails, use basic setup
            logging.basicConfig(level=logging.INFO)
            logging.getLogger(__name__).warning(f"Failed to configure logging: {e}")


class TestAnalysisServiceFactory(AnalysisServiceFactory):
    """
    Factory for creating test instances with mock dependencies
    Single Responsibility: Create analysis services suitable for testing
    """

    def __init__(self, test_data: Optional[Dict[str, Any]] = None):
        """
        Initialize test factory with optional test data

        Args:
            test_data: Optional test data to use instead of real files
        """
        self.test_data = test_data
        self.logger = logging.getLogger(__name__)

    def create_dependency_analysis_service(self) -> DependencyAnalysisService:
        """Create service with test-friendly dependencies"""
        repository = self.create_repository()
        validation_service = self.create_validation_service()
        cache_service = self.create_cache_service()
        metrics_collector = self.create_metrics_collector()

        return BranchDependencyAnalysisService(
            repository=repository,
            validation_service=validation_service,
            cache_service=cache_service,
            metrics_collector=metrics_collector
        )

    def create_repository(self) -> AnalysisDataRepository:
        """Create test repository with mock data"""
        if self.test_data:
            return MockAnalysisDataRepository(self.test_data)
        else:
            # Use a temporary file path for testing
            return JsonAnalysisDataRepository('/tmp/test_analysis.json')

    def create_cache_service(self) -> CacheService:
        """Create cache service for testing (smaller size)"""
        return InMemoryCacheService(max_size=10)

    def create_validation_service(self) -> ValidationService:
        """Create validation service for testing"""
        return StandardValidationService()

    def create_metrics_collector(self) -> MetricsCollector:
        """Create metrics collector for testing"""
        return SimpleMetricsCollector()


class NullMetricsCollector(MetricsCollector):
    """
    Null object implementation of metrics collector
    Single Responsibility: Provide no-op metrics collection when disabled
    """

    def record_analysis_time(self, operation: str, duration_seconds: float) -> None:
        """Do nothing (metrics disabled)"""
        pass

    def record_cache_hit(self, key: str) -> None:
        """Do nothing (metrics disabled)"""
        pass

    def record_cache_miss(self, key: str) -> None:
        """Do nothing (metrics disabled)"""
        pass

    def record_error(self, operation: str, error_type: str) -> None:
        """Do nothing (metrics disabled)"""
        pass

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Return empty metrics summary"""
        return {
            'operations': {},
            'cache': {'total_hits': 0, 'total_misses': 0, 'hit_rate': 0},
            'errors': {}
        }


class MockAnalysisDataRepository(AnalysisDataRepository):
    """
    Mock repository implementation for testing
    Single Responsibility: Provide test data without file system dependencies
    """

    def __init__(self, test_data: Dict[str, Any]):
        """
        Initialize with test data

        Args:
            test_data: Dictionary containing mock analysis data
        """
        self.test_data = test_data
        from .domain_models import AnalysisResult
        self._analysis_result = AnalysisResult.from_dict(test_data)

    def load_analysis_result(self):
        """Return mock analysis result"""
        return self._analysis_result

    def save_analysis_result(self, result) -> None:
        """Update mock data"""
        self._analysis_result = result
        self.test_data = result.to_dict()

    def exists(self) -> bool:
        """Always return True for mock data"""
        return True

    def get_last_modified(self) -> Optional[float]:
        """Return current timestamp for mock data"""
        import time
        return time.time()


class AnalysisServiceProvider:
    """
    Service provider that manages service lifecycle and provides easy access
    Single Responsibility: Provide centralized access to analysis services
    """

    def __init__(self, factory: AnalysisServiceFactory):
        """
        Initialize service provider with factory

        Args:
            factory: Factory for creating services
        """
        self.factory = factory
        self._service_cache: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

    def get_dependency_analysis_service(self) -> DependencyAnalysisService:
        """Get dependency analysis service (cached)"""
        if 'dependency_analysis' not in self._service_cache:
            self._service_cache['dependency_analysis'] = self.factory.create_dependency_analysis_service()
            self.logger.debug("Created and cached dependency analysis service")

        return self._service_cache['dependency_analysis']

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary from all services"""
        try:
            metrics_collector = self.factory.create_metrics_collector()
            return metrics_collector.get_metrics_summary()
        except Exception as e:
            self.logger.error(f"Failed to get metrics summary: {e}")
            return {}

    def refresh_services(self) -> None:
        """Clear service cache to force recreation"""
        self._service_cache.clear()
        self.logger.info("Service cache cleared - services will be recreated on next access")


# Convenience functions for easy service creation

def create_analysis_service(analysis_file_path: Optional[str] = None,
                            config_overrides: Optional[Dict[str, Any]] = None) -> DependencyAnalysisService:
    """
    Convenience function to create a dependency analysis service

    Args:
        analysis_file_path: Optional path to analysis file
        config_overrides: Optional configuration overrides

    Returns:
        DependencyAnalysisService: Configured service instance
    """
    factory = DefaultAnalysisServiceFactory(analysis_file_path, config_overrides)
    return factory.create_dependency_analysis_service()


def create_service_provider(analysis_file_path: Optional[str] = None,
                            config_overrides: Optional[Dict[str, Any]] = None) -> AnalysisServiceProvider:
    """
    Convenience function to create a service provider

    Args:
        analysis_file_path: Optional path to analysis file
        config_overrides: Optional configuration overrides

    Returns:
        AnalysisServiceProvider: Configured service provider
    """
    factory = DefaultAnalysisServiceFactory(analysis_file_path, config_overrides)
    return AnalysisServiceProvider(factory)


def create_test_service(test_data: Optional[Dict[str, Any]] = None) -> DependencyAnalysisService:
    """
    Convenience function to create a test service

    Args:
        test_data: Optional test data

    Returns:
        DependencyAnalysisService: Test service instance
    """
    factory = TestAnalysisServiceFactory(test_data)
    return factory.create_dependency_analysis_service()