"""
Repository implementations for Branch Dependency Analysis
Concrete implementations of data access interfaces
Single Responsibility: Handle data persistence and retrieval operations
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from .interfaces import (
    AnalysisDataRepository,
    CacheService,
    ConfigurationProvider,
    RepositoryError,
    CacheError,
    ConfigurationError
)
from .domain_models import AnalysisResult


class JsonAnalysisDataRepository(AnalysisDataRepository):
    """
    Repository implementation for JSON file-based analysis data storage
    Single Responsibility: Handle JSON file operations for analysis data
    """

    def __init__(self, file_path: str, cache_service: Optional[CacheService] = None):
        """
        Initialize repository with file path and optional caching

        Args:
            file_path: Path to JSON analysis file
            cache_service: Optional cache service for performance
        """
        self.file_path = Path(file_path)
        self.cache_service = cache_service
        self._cache_key = f"analysis_result_{self.file_path.name}"

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def load_analysis_result(self) -> AnalysisResult:
        """
        Load analysis result from JSON file with optional caching

        Returns:
            AnalysisResult: Complete analysis data

        Raises:
            RepositoryError: If file cannot be read or parsed
        """
        try:
            # Try cache first if available
            if self.cache_service:
                cached_result = self.cache_service.get(self._cache_key)
                if cached_result is not None:
                    self.logger.debug(f"Loaded analysis result from cache: {self._cache_key}")
                    return cached_result

            # Load from file
            if not self.file_path.exists():
                self.logger.warning(f"Analysis file not found: {self.file_path}")
                return self._create_empty_result()

            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert to domain model
            result = AnalysisResult.from_dict(data)

            # Cache the result if cache service is available
            if self.cache_service:
                # Cache for 1 hour by default
                self.cache_service.set(self._cache_key, result, ttl=3600)
                self.logger.debug(f"Cached analysis result: {self._cache_key}")

            self.logger.info(f"Loaded analysis result from file: {self.file_path}")
            return result

        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in analysis file {self.file_path}: {e}"
            self.logger.error(error_msg)
            raise RepositoryError(error_msg) from e

        except (KeyError, ValueError, TypeError) as e:
            error_msg = f"Invalid analysis data format in {self.file_path}: {e}"
            self.logger.error(error_msg)
            raise RepositoryError(error_msg) from e

        except IOError as e:
            error_msg = f"Cannot read analysis file {self.file_path}: {e}"
            self.logger.error(error_msg)
            raise RepositoryError(error_msg) from e

    def save_analysis_result(self, result: AnalysisResult) -> None:
        """
        Save analysis result to JSON file

        Args:
            result: Analysis result to save

        Raises:
            RepositoryError: If file cannot be written
        """
        try:
            # Ensure directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dictionary
            data = result.to_dict()

            # Write to file with pretty printing
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Update cache if available
            if self.cache_service:
                self.cache_service.set(self._cache_key, result, ttl=3600)
                self.logger.debug(f"Updated cache after save: {self._cache_key}")

            self.logger.info(f"Saved analysis result to file: {self.file_path}")

        except IOError as e:
            error_msg = f"Cannot write analysis file {self.file_path}: {e}"
            self.logger.error(error_msg)
            raise RepositoryError(error_msg) from e
        except (TypeError, ValueError) as e:
            error_msg = f"Cannot serialize analysis result: {e}"
            self.logger.error(error_msg)
            raise RepositoryError(error_msg) from e

    def exists(self) -> bool:
        """Check if analysis data file exists"""
        return self.file_path.exists() and self.file_path.is_file()

    def get_last_modified(self) -> Optional[float]:
        """Get timestamp of last file modification"""
        try:
            if self.exists():
                return self.file_path.stat().st_mtime
            return None
        except OSError:
            return None

    def invalidate_cache(self) -> None:
        """Invalidate cached analysis result"""
        if self.cache_service:
            self.cache_service.delete(self._cache_key)
            self.logger.debug(f"Invalidated cache: {self._cache_key}")

    def _create_empty_result(self) -> AnalysisResult:
        """Create empty analysis result when no data file exists"""
        from .domain_models import AnalysisMetadata

        empty_metadata = AnalysisMetadata(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            analysis_time_seconds=0.0,
            base_path='',
            analyzed_folders=tuple(),
            excluded_folders=tuple(),
            total_files_analyzed=0
        )

        return AnalysisResult(files=tuple(), metadata=empty_metadata)


class InMemoryCacheService(CacheService):
    """
    Simple in-memory cache implementation
    Single Responsibility: Provide caching functionality using Python dictionaries
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize cache with maximum size

        Args:
            max_size: Maximum number of items to cache
        """
        self.cache: Dict[str, Any] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
        self.logger = logging.getLogger(__name__)

    def get(self, key: str) -> Optional[Any]:
        """Get cached value by key"""
        if key in self.cache:
            self.access_times[key] = datetime.now().timestamp()
            self.logger.debug(f"Cache hit: {key}")
            return self.cache[key]

        self.logger.debug(f"Cache miss: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set cached value with optional TTL
        Note: TTL is ignored in this simple implementation
        """
        # If cache is full, remove least recently used item
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()

        self.cache[key] = value
        self.access_times[key] = datetime.now().timestamp()
        self.logger.debug(f"Cache set: {key}")

    def delete(self, key: str) -> None:
        """Delete cached value"""
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
            self.logger.debug(f"Cache delete: {key}")

    def clear(self) -> None:
        """Clear all cached values"""
        self.cache.clear()
        self.access_times.clear()
        self.logger.debug("Cache cleared")

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        return key in self.cache

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'utilization': len(self.cache) / self.max_size
        }

    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self.access_times:
            return

        # Find least recently used key
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self.delete(lru_key)
        self.logger.debug(f"Evicted LRU item: {lru_key}")


class FileBasedConfigurationProvider(ConfigurationProvider):
    """
    Configuration provider that reads from environment variables and files
    Single Responsibility: Provide configuration values from various sources
    """

    def __init__(self, analysis_file_path: Optional[str] = None):
        """
        Initialize configuration provider

        Args:
            analysis_file_path: Override for analysis file path
        """
        self.analysis_file_path = analysis_file_path
        self.logger = logging.getLogger(__name__)

    def get_analysis_file_path(self) -> str:
        """Get path to analysis data file"""
        # Priority: constructor arg > environment > default
        if self.analysis_file_path:
            return self.analysis_file_path

        env_path = os.getenv('ANALYSIS_FILE_PATH')
        if env_path:
            return env_path

        # Default path relative to project root
        return '../analysis_results/branch_dependencies.json'

    def get_cache_settings(self) -> Dict[str, Any]:
        """Get caching configuration"""
        return {
            'enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            'max_size': int(os.getenv('CACHE_MAX_SIZE', '1000')),
            'default_ttl': int(os.getenv('CACHE_DEFAULT_TTL', '3600'))  # 1 hour
        }

    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance-related settings"""
        return {
            'max_search_results': int(os.getenv('MAX_SEARCH_RESULTS', '1000')),
            'max_hotspots': int(os.getenv('MAX_HOTSPOTS', '100')),
            'query_timeout_seconds': int(os.getenv('QUERY_TIMEOUT', '30'))
        }

    def get_logging_settings(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'enable_file_logging': os.getenv('ENABLE_FILE_LOGGING', 'false').lower() == 'true'
        }


class NullCacheService(CacheService):
    """
    Null object pattern implementation of cache service
    Single Responsibility: Provide no-op caching when caching is disabled
    """

    def get(self, key: str) -> Optional[Any]:
        """Always return None (no caching)"""
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Do nothing (no caching)"""
        pass

    def delete(self, key: str) -> None:
        """Do nothing (no caching)"""
        pass

    def clear(self) -> None:
        """Do nothing (no caching)"""
        pass

    def exists(self, key: str) -> bool:
        """Always return False (no caching)"""
        return False


class RepositoryFactory:
    """
    Factory for creating repository instances with proper configuration
    Single Responsibility: Create and configure repository dependencies
    """

    @staticmethod
    def create_analysis_repository(
            config_provider: ConfigurationProvider,
            cache_service: Optional[CacheService] = None
    ) -> AnalysisDataRepository:
        """
        Create analysis data repository with configuration

        Args:
            config_provider: Configuration provider instance
            cache_service: Optional cache service

        Returns:
            AnalysisDataRepository: Configured repository instance
        """
        analysis_file_path = config_provider.get_analysis_file_path()
        return JsonAnalysisDataRepository(analysis_file_path, cache_service)

    @staticmethod
    def create_cache_service(config_provider: ConfigurationProvider) -> CacheService:
        """
        Create cache service based on configuration

        Args:
            config_provider: Configuration provider instance

        Returns:
            CacheService: Configured cache service instance
        """
        cache_settings = config_provider.get_cache_settings()

        if cache_settings.get('enabled', True):
            max_size = cache_settings.get('max_size', 1000)
            return InMemoryCacheService(max_size=max_size)
        else:
            return NullCacheService()

    @staticmethod
    def create_configuration_provider(analysis_file_path: Optional[str] = None) -> ConfigurationProvider:
        """
        Create configuration provider

        Args:
            analysis_file_path: Optional override for analysis file path

        Returns:
            ConfigurationProvider: Configured provider instance
        """
        return FileBasedConfigurationProvider(analysis_file_path)