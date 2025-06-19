import subprocess
import json
from pathlib import Path
from typing import Dict, Any


class PHPParserBridge:
    """
    Bridge to communicate with the PHP nikic/PHP-Parser via subprocess.
    This handles calling our PHP script and parsing the JSON response.
    """

    def __init__(self):
        """Initialize the bridge with the path to our PHP parsing script."""
        # Get the path to our PHP script - try multiple strategies

        # Strategy 1: Relative to this file
        project_root = Path(__file__).parent.parent.parent
        php_script_1 = project_root / "php-tools" / "parse-file.php"

        # Strategy 2: Relative to current working directory
        php_script_2 = Path.cwd() / "php-tools" / "parse-file.php"

        # Strategy 3: Absolute path (if the others fail)
        php_script_3 = Path("/Users/ckoleri/code/codebase-analysis-tools/php-tools/parse-file.php")

        # Try each strategy
        for i, script_path in enumerate([php_script_1, php_script_2, php_script_3], 1):
            if script_path.exists():
                self.php_script = script_path
                break
        else:
            raise FileNotFoundError(
                f"PHP parser script not found. Tried:\n"
                f"  1. {php_script_1}\n"
                f"  2. {php_script_2}\n"
                f"  3. {php_script_3}"
            )

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a PHP file using nikic/PHP-Parser via subprocess.

        Args:
            file_path: Path to the PHP file to parse

        Returns:
            Dictionary containing either:
            - success: True, ast: <ast_data>, file: <file_path>
            - error: <error_message>, file: <file_path>
        """
        try:
            # Run the PHP parser script
            result = subprocess.run([
                'php',  # Use the PHP executable
                str(self.php_script),  # Our PHP parsing script
                str(file_path)  # The file to parse
            ],
                capture_output=True,  # Capture stdout and stderr
                text=True,  # Return strings, not bytes
                timeout=30  # 30 second timeout per file
            )

            # Check if the command succeeded
            if result.returncode == 0:
                # Parse the JSON output from our PHP script
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as e:
                    return {
                        'error': f'Invalid JSON from PHP parser: {str(e)}',
                        'file': file_path,
                        'raw_output': result.stdout
                    }
            else:
                # Command failed, return error
                return {
                    'error': f'PHP parser failed with code {result.returncode}: {result.stderr}',
                    'file': file_path
                }

        except subprocess.TimeoutExpired:
            return {
                'error': 'Parser timeout (30 seconds exceeded)',
                'file': file_path
            }
        except FileNotFoundError:
            return {
                'error': 'PHP executable not found. Make sure PHP is installed and in PATH.',
                'file': file_path
            }
        except Exception as e:
            return {
                'error': f'Unexpected subprocess error: {str(e)}',
                'file': file_path
            }

    def test_connection(self) -> bool:
        """
        Test if the PHP parser bridge is working correctly.

        Returns:
            True if the bridge works, False otherwise
        """
        try:
            # Create a simple test PHP file content
            test_content = "<?php\nclass TestClass {}\n"

            # Create a temporary test file
            test_file = Path("/tmp/php_parser_test.php")
            with open(test_file, 'w') as f:
                f.write(test_content)

            # Try to parse it
            result = self.parse_file(str(test_file))

            # Clean up
            test_file.unlink()

            # Check if parsing succeeded
            return 'success' in result and result['success'] is True

        except Exception:
            return False


# Test the bridge if run directly
if __name__ == "__main__":
    bridge = PHPParserBridge()

    print("Testing PHP Parser Bridge...")

    # Test connection
    if bridge.test_connection():
        print("✓ PHP Parser Bridge is working correctly")
    else:
        print("✗ PHP Parser Bridge test failed")
        exit(1)

    # Test with a real file if available
    test_file = "../../epignosis/efront/libraries/Efront/Application.php"
    if Path(test_file).exists():
        print(f"\nTesting with real file: {test_file}")
        result = bridge.parse_file(test_file)

        if 'success' in result:
            print("✓ Successfully parsed real PHP file")
            print(f"AST length: {len(result.get('ast', ''))}")
        else:
            print(f"✗ Failed to parse real file: {result.get('error', 'Unknown error')}")
    else:
        print(f"\nSkipping real file test - {test_file} not found")