from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import re
import sys
import os

# Add the shared directory to the path so we can import the bridge
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from php_parser_bridge import PHPParserBridge


class BranchDependency:
    """
    Represents a single Branch dependency found in a file.
    This is like a data class to hold information about each dependency.
    """

    def __init__(self, dependency_type: str, line: int, context: str, details: Dict[str, Any] = None):
        """
        Args:
            dependency_type: Type of dependency (e.g., 'instantiation', 'static_call', 'type_hint')
            line: Line number where dependency was found
            context: The actual code snippet
            details: Additional information about the dependency
        """
        self.type = dependency_type
        self.line = line
        self.context = context
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert this dependency to a dictionary for JSON output."""
        return {
            'type': self.type,
            'line': self.line,
            'context': self.context,
            'details': self.details
        }


class BranchAnalyzer:
    """
    Analyzes PHP files using nikic/PHP-Parser via subprocess to find Branch dependencies.
    This is the core analyzer that does the actual dependency detection.
    """

    def __init__(self):
        """Initialize the analyzer."""
        # Create the PHP parser bridge
        self.php_bridge = PHPParserBridge()

        # These are the different types of Branch dependencies we're looking for
        self.dependency_types = {
            'instantiation',  # new Branch()
            'static_call',  # Branch::method()
            'type_hint',  # function foo(Branch $branch)
            'use_statement',  # use Some\Namespace\Branch
            'class_constant',  # Branch::CONSTANT
            'instanceof',  # $obj instanceof Branch
            'class_reference'  # Any other Branch class reference
        }

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a single PHP file for Branch dependencies.

        Args:
            file_path: Path to the PHP file to analyze

        Returns:
            Dictionary containing file info and found dependencies
        """
        file_path = Path(file_path)

        # Initialize result structure
        result = {
            'file_path': str(file_path),
            'relative_path': None,  # Will be set by caller if needed
            'dependencies': [],
            'error': None,
            'total_dependencies': 0
        }

        try:
            # Read the PHP file content for context extraction
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()

            # Parse PHP file using the bridge
            parse_result = self.php_bridge.parse_file(str(file_path))

            # Check if parsing failed
            if 'error' in parse_result:
                result['error'] = parse_result['error']
                return result

            # Extract AST from parse result
            ast_string = parse_result.get('ast', '')
            if not ast_string:
                result['error'] = 'No AST returned from parser'
                return result

            # Find all Branch dependencies in the AST
            dependencies = self._find_dependencies_in_ast_string(ast_string, source_code)

            result['dependencies'] = [dep.to_dict() for dep in dependencies]
            result['total_dependencies'] = len(dependencies)

        except Exception as e:
            result['error'] = f'Analysis error: {str(e)}'

        return result

    def _find_dependencies_in_ast_string(self, ast_string: str, source_code: str) -> List[BranchDependency]:
        """
        Find Branch dependencies by analyzing the AST string representation.

        The nikic/PHP-Parser gives us a string representation of the AST tree.
        We'll parse this string to find Branch-related nodes.

        Args:
            ast_string: String representation of the AST from nikic/PHP-Parser
            source_code: Original source code for context extraction

        Returns:
            List of BranchDependency objects found
        """
        dependencies = []

        # Split AST into lines for easier processing
        ast_lines = ast_string.split('\n')

        # Look for different types of Branch usage patterns
        for i, line in enumerate(ast_lines):
            line = line.strip()

            # Look for class names containing "Branch"
            if self._contains_branch_reference(line):
                # Determine what type of dependency this is
                dependency_type = self._determine_dependency_type(line, ast_lines, i)

                if dependency_type:
                    # Extract line number if available
                    line_num = self._extract_line_number(ast_lines, i)

                    # Get context from source code
                    context = self._get_line_context(source_code, line_num)

                    # Extract additional details
                    details = self._extract_details(line, dependency_type)

                    dependency = BranchDependency(
                        dependency_type=dependency_type,
                        line=line_num,
                        context=context,
                        details=details
                    )

                    dependencies.append(dependency)

        return dependencies

    def _contains_branch_reference(self, ast_line: str) -> bool:
        """Check if this AST line contains a reference to Branch."""
        # Look for "Branch" in class names, but be careful about context
        # We want to match things like:
        # - name: Branch
        # - name: UserBranch
        # - name: BranchManager

        # Pattern to match name fields that contain "Branch"
        name_patterns = [
            r'name:\s*[A-Za-z]*Branch[A-Za-z]*\s*$',  # name: Branch, name: UserBranch, etc.
            r'name:\s*Branch\s*$',  # exact match: name: Branch
        ]

        for pattern in name_patterns:
            if re.search(pattern, ast_line):
                return True

        return False

    def _determine_dependency_type(self, current_line: str, all_lines: List[str], current_index: int) -> Optional[str]:
        """
        Determine what type of dependency this Branch reference represents.

        We look at the current line and surrounding context to determine the type.
        """
        # Look at previous lines for context
        context_lines = []
        start_index = max(0, current_index - 5)
        end_index = min(len(all_lines), current_index + 3)

        for i in range(start_index, end_index):
            context_lines.append(all_lines[i].strip())

        context = ' '.join(context_lines).lower()

        # Determine type based on AST node types in context
        if 'expr_new' in context or 'stmt_new' in context:
            return 'instantiation'
        elif 'expr_staticcall' in context or 'staticcall' in context:
            return 'static_call'
        elif 'stmt_use' in context or 'useitem' in context:
            return 'use_statement'
        elif 'param(' in context or 'parameter' in context:
            return 'type_hint'
        elif 'instanceof' in context:
            return 'instanceof'
        elif 'classconstfetch' in context:
            return 'class_constant'
        else:
            return 'class_reference'  # Generic reference

    def _extract_line_number(self, ast_lines: List[str], current_index: int) -> int:
        """Extract line number from AST context."""
        # Look for line number in nearby AST nodes
        # nikic/PHP-Parser includes line numbers in various formats

        search_range = range(max(0, current_index - 3), min(len(ast_lines), current_index + 3))

        for i in search_range:
            line = ast_lines[i].strip()

            # Look for line number patterns
            line_patterns = [
                r'line:\s*(\d+)',  # line: 42
                r'lineno:\s*(\d+)',  # lineno: 42
                r'startLine:\s*(\d+)',  # startLine: 42
            ]

            for pattern in line_patterns:
                match = re.search(pattern, line)
                if match:
                    return int(match.group(1))

        return 0  # Default if no line number found

    def _get_line_context(self, source_code: str, line_num: int) -> str:
        """Get the actual line of code for context."""
        try:
            lines = source_code.split('\n')
            if 1 <= line_num <= len(lines):
                return lines[line_num - 1].strip()
        except Exception:
            pass
        return f"Line {line_num}"

    def _extract_details(self, ast_line: str, dependency_type: str) -> Dict[str, Any]:
        """Extract additional details about the dependency."""
        details = {}

        # Extract class name
        name_match = re.search(r'name:\s*([A-Za-z][A-Za-z0-9_]*)', ast_line)
        if name_match:
            details['class_name'] = name_match.group(1)

        # Add type-specific details
        details['dependency_type'] = dependency_type

        return details


# Test function
if __name__ == "__main__":
    analyzer = BranchAnalyzer()

    print("Testing Branch Analyzer...")

    # Test the PHP bridge first
    if not analyzer.php_bridge.test_connection():
        print("✗ PHP Parser Bridge is not working")
        exit(1)

    print("✓ PHP Parser Bridge is working")

    # Test with a specific file
    test_file = "../../epignosis/efront/libraries/Efront/Application.php"

    if Path(test_file).exists():
        print(f"\nAnalyzing test file: {test_file}")
        result = analyzer.analyze_file(test_file)

        print("Result:")
        print(json.dumps(result, indent=2))
    else:
        print(f"Test file {test_file} not found")
        print("Please update the test_file path to an actual PHP file from your codebase")