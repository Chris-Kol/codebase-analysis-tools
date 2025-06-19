"""
Domain Models for Branch Dependency Analysis
Pure business objects following Domain-Driven Design principles
Single Responsibility: Define the core domain entities and value objects
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime


class DependencyType(Enum):
    """Enumeration of all supported dependency types"""
    INSTANTIATION = "instantiation"  # new Branch()
    STATIC_CALL = "static_call"  # Branch::method()
    TYPE_HINT = "type_hint"  # function foo(Branch $branch)
    USE_STATEMENT = "use_statement"  # use Some\Namespace\Branch
    INSTANCEOF = "instanceof"  # $obj instanceof Branch
    CLASS_CONSTANT = "class_constant"  # Branch::CONSTANT
    CLASS_REFERENCE = "class_reference"  # Any other Branch reference


@dataclass(frozen=True)
class Dependency:
    """
    Immutable value object representing a single dependency
    Contains all information about where and how Branch is used
    """
    type: DependencyType
    line: int
    context: str
    details: Dict[str, Any]

    def __post_init__(self):
        """Validate dependency data after initialization"""
        if self.line < 0:
            raise ValueError("Line number must be non-negative")
        if not self.context.strip():
            raise ValueError("Context cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'type': self.type.value,
            'line': self.line,
            'context': self.context,
            'details': self.details
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dependency':
        """Create Dependency from dictionary"""
        return cls(
            type=DependencyType(data['type']),
            line=data['line'],
            context=data['context'],
            details=data.get('details', {})
        )


@dataclass(frozen=True)
class FileAnalysis:
    """
    Immutable value object representing analysis of a single file
    Contains all dependencies found in that file
    """
    file_path: str
    relative_path: str
    dependencies: tuple[Dependency, ...]  # Immutable tuple
    error: Optional[str] = None

    def __post_init__(self):
        """Validate file analysis data"""
        if not self.file_path.strip():
            raise ValueError("File path cannot be empty")
        if not self.relative_path.strip():
            raise ValueError("Relative path cannot be empty")

    @property
    def total_dependencies(self) -> int:
        """Get total number of dependencies in this file"""
        return len(self.dependencies)

    @property
    def has_dependencies(self) -> bool:
        """Check if file has any dependencies"""
        return self.total_dependencies > 0

    @property
    def dependency_types(self) -> set[DependencyType]:
        """Get unique dependency types in this file"""
        return {dep.type for dep in self.dependencies}

    def get_dependencies_by_type(self, dep_type: DependencyType) -> tuple[Dependency, ...]:
        """Get all dependencies of specific type"""
        return tuple(dep for dep in self.dependencies if dep.type == dep_type)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'file_path': self.file_path,
            'relative_path': self.relative_path,
            'dependencies': [dep.to_dict() for dep in self.dependencies],
            'total_dependencies': self.total_dependencies,
            'error': self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileAnalysis':
        """Create FileAnalysis from dictionary"""
        dependencies = tuple(
            Dependency.from_dict(dep_data)
            for dep_data in data.get('dependencies', [])
        )

        return cls(
            file_path=data['file_path'],
            relative_path=data.get('relative_path', data['file_path']),
            dependencies=dependencies,
            error=data.get('error')
        )


@dataclass(frozen=True)
class AnalysisMetadata:
    """
    Immutable value object containing metadata about the analysis run
    """
    timestamp: str
    analysis_time_seconds: float
    base_path: str
    analyzed_folders: tuple[str, ...]
    excluded_folders: tuple[str, ...]
    total_files_analyzed: int

    def __post_init__(self):
        """Validate metadata"""
        if self.analysis_time_seconds < 0:
            raise ValueError("Analysis time cannot be negative")
        if self.total_files_analyzed < 0:
            raise ValueError("Total files analyzed cannot be negative")

    @property
    def analysis_date(self) -> datetime:
        """Parse timestamp to datetime object"""
        try:
            return datetime.strptime(self.timestamp, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Fallback for different timestamp formats
            return datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp,
            'analysis_time_seconds': self.analysis_time_seconds,
            'base_path': self.base_path,
            'analyzed_folders': list(self.analyzed_folders),
            'excluded_folders': list(self.excluded_folders),
            'total_files_analyzed': self.total_files_analyzed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisMetadata':
        """Create AnalysisMetadata from dictionary"""
        return cls(
            timestamp=data.get('timestamp', ''),
            analysis_time_seconds=data.get('analysis_time_seconds', 0.0),
            base_path=data.get('base_path', ''),
            analyzed_folders=tuple(data.get('analyzed_folders', [])),
            excluded_folders=tuple(data.get('excluded_folders', [])),
            total_files_analyzed=data.get('total_files_analyzed', 0)
        )


@dataclass(frozen=True)
class AnalysisResult:
    """
    Immutable aggregate root containing complete analysis results
    This is the main domain entity that encapsulates all analysis data
    """
    files: tuple[FileAnalysis, ...]
    metadata: AnalysisMetadata

    @property
    def total_files(self) -> int:
        """Get total number of files analyzed"""
        return len(self.files)

    @property
    def files_with_dependencies(self) -> tuple[FileAnalysis, ...]:
        """Get only files that have dependencies"""
        return tuple(f for f in self.files if f.has_dependencies)

    @property
    def total_dependencies(self) -> int:
        """Get total number of dependencies across all files"""
        return sum(f.total_dependencies for f in self.files)

    @property
    def dependency_type_distribution(self) -> Dict[DependencyType, int]:
        """Get distribution of dependency types across all files"""
        distribution = {}
        for file_analysis in self.files:
            for dependency in file_analysis.dependencies:
                dep_type = dependency.type
                distribution[dep_type] = distribution.get(dep_type, 0) + 1
        return distribution

    def get_hotspots(self, limit: int = 20) -> tuple[FileAnalysis, ...]:
        """Get files with most dependencies (hotspots)"""
        if limit <= 0:
            raise ValueError("Limit must be positive")

        sorted_files = sorted(
            self.files_with_dependencies,
            key=lambda f: f.total_dependencies,
            reverse=True
        )
        return tuple(sorted_files[:limit])

    def get_files_by_dependency_type(self, dep_type: DependencyType) -> tuple[FileAnalysis, ...]:
        """Get all files that contain dependencies of specific type"""
        return tuple(
            f for f in self.files
            if dep_type in f.dependency_types
        )

    def search_files(self, query: str) -> tuple[FileAnalysis, ...]:
        """Search files by path or dependency context"""
        if len(query.strip()) < 2:
            return tuple()

        query_lower = query.lower()
        matching_files = []

        for file_analysis in self.files_with_dependencies:
            # Check file path match
            path_match = query_lower in file_analysis.relative_path.lower()

            # Check dependency context match
            context_match = any(
                query_lower in dep.context.lower()
                for dep in file_analysis.dependencies
            )

            if path_match or context_match:
                matching_files.append(file_analysis)

        return tuple(matching_files)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'files': [f.to_dict() for f in self.files],
            'analysis_metadata': self.metadata.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create AnalysisResult from dictionary"""
        files = tuple(
            FileAnalysis.from_dict(file_data)
            for file_data in data.get('files', [])
        )

        metadata = AnalysisMetadata.from_dict(
            data.get('analysis_metadata', {})
        )

        return cls(files=files, metadata=metadata)


@dataclass(frozen=True)
class SummaryStatistics:
    """
    Value object containing computed summary statistics
    Derived from AnalysisResult but cached for performance
    """
    total_files: int
    files_with_dependencies: int
    total_dependencies: int
    dependency_type_counts: Dict[str, int]  # String keys for JSON serialization
    analysis_metadata: Dict[str, Any]

    @classmethod
    def from_analysis_result(cls, result: AnalysisResult) -> 'SummaryStatistics':
        """Create summary statistics from analysis result"""
        # Convert DependencyType enum to string for JSON compatibility
        type_counts = {
            dep_type.value: count
            for dep_type, count in result.dependency_type_distribution.items()
        }

        return cls(
            total_files=result.total_files,
            files_with_dependencies=len(result.files_with_dependencies),
            total_dependencies=result.total_dependencies,
            dependency_type_counts=type_counts,
            analysis_metadata=result.metadata.to_dict()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'total_files': self.total_files,
            'files_with_dependencies': self.files_with_dependencies,
            'total_dependencies': self.total_dependencies,
            'dependency_type_counts': self.dependency_type_counts,
            'analysis_metadata': self.analysis_metadata
        }