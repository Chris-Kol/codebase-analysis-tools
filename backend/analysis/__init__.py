"""
Analysis Layer Public API
Exposes the main interfaces and factory functions for external use
Single Responsibility: Provide clean public API for the analysis layer
"""

# Public interfaces
from .interfaces import (
    DependencyAnalysisService,
    AnalysisDataRepository,
    CacheService,
    ValidationService,
    MetricsCollector,
    ConfigurationProvider,
    AnalysisServiceFactory,

    # Exceptions
    AnalysisError,
    RepositoryError,
    CacheError,
    ValidationError,
    ConfigurationError
)

# Domain models
from .domain_models import (
    DependencyType,
    Dependency,
    FileAnalysis,
    AnalysisResult,
    AnalysisMetadata,
    SummaryStatistics
)

# Factory functions (main entry points)
from .factories import (
    create_analysis_service,
    create_service_provider,
    create_test_service,
    DefaultAnalysisServiceFactory,
    TestAnalysisServiceFactory,
    AnalysisServiceProvider
)

# Version information
__version__ = "1.0.0"
__author__ = "Branch Analysis Team"

# Public API - what external code should use
__all__ = [
    # Main entry points
    'create_analysis_service',
    'create_service_provider',
    'create_test_service',

    # Interfaces
    'DependencyAnalysisService',
    'AnalysisDataRepository',
    'CacheService',
    'ValidationService',
    'MetricsCollector',
    'ConfigurationProvider',
    'AnalysisServiceFactory',

    # Domain models
    'DependencyType',
    'Dependency',
    'FileAnalysis',
    'AnalysisResult',
    'AnalysisMetadata',
    'SummaryStatistics',

    # Factories
    'DefaultAnalysisServiceFactory',
    'TestAnalysisServiceFactory',
    'AnalysisServiceProvider',

    # Exceptions
    'AnalysisError',
    'RepositoryError',
    'CacheError',
    'ValidationError',
    'ConfigurationError'
]