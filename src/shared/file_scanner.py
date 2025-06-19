import os
from pathlib import Path
from typing import List
import config


class FileScanner:
    """
    Scans directories for files based on configuration settings.
    This class handles finding all PHP files we want to analyze.
    """

    def __init__(self):
        """
        Constructor - runs when you create a new FileScanner object.
        Sets up the scanner with paths from our config file.
        """
        # Convert relative path to absolute path
        self.base_path = Path(config.LMS_BASE_PATH).resolve()
        self.analyze_folders = config.ANALYZE_FOLDERS
        self.exclude_folders = config.EXCLUDE_FOLDERS
        self.file_extensions = config.FILE_EXTENSIONS

    def scan_files(self) -> List[str]:
        """
        Main method that finds all files we want to analyze.
        Returns a list of file paths as strings.

        The -> List[str] is a type hint telling us this method returns
        a list of strings.
        """
        found_files = []

        # Loop through each folder we want to analyze
        for folder in self.analyze_folders:
            # Create full path: base_path + folder
            folder_path = self.base_path / folder

            # Check if the folder actually exists
            if not folder_path.exists():
                print(f"Warning: Folder {folder_path} does not exist!")
                continue

            # Find all files in this folder and subfolders
            files_in_folder = self._scan_directory(folder_path)
            found_files.extend(files_in_folder)

        return found_files

    def _scan_directory(self, directory: Path) -> List[str]:
        """
        Private method (starts with _) that recursively scans a directory.

        Args:
            directory: Path object representing the directory to scan

        Returns:
            List of file paths that match our criteria
        """
        files = []

        # Walk through directory and all subdirectories
        # os.walk gives us (current_dir, subdirs, files) for each directory
        for root, dirs, filenames in os.walk(directory):
            # Convert current directory to Path object for easier manipulation
            current_dir = Path(root)

            # Check if current directory should be excluded
            if self._should_exclude_directory(current_dir):
                continue

            # Check each file in current directory
            for filename in filenames:
                if self._should_include_file(filename):
                    # Create full file path
                    file_path = current_dir / filename
                    # Convert to string and add to our list
                    files.append(str(file_path))

        return files

    def _should_exclude_directory(self, directory: Path) -> bool:
        """
        Check if a directory should be excluded from scanning.

        Args:
            directory: Path object of the directory to check

        Returns:
            True if directory should be excluded, False otherwise
        """
        # Convert directory path to string relative to base path
        try:
            relative_path = directory.relative_to(self.base_path)
            relative_path_str = str(relative_path)

            # Check if this path matches any of our exclude patterns
            for exclude_pattern in self.exclude_folders:
                if relative_path_str.startswith(exclude_pattern):
                    return True

        except ValueError:
            # relative_to() throws ValueError if directory is not under base_path
            # This shouldn't happen in normal usage
            pass

        return False

    def _should_include_file(self, filename: str) -> bool:
        """
        Check if a file should be included based on its extension.

        Args:
            filename: Name of the file (not full path)

        Returns:
            True if file should be included, False otherwise
        """
        # Get file extension (everything after the last dot)
        file_extension = filename.split('.')[-1].lower()

        # Check if extension is in our list of extensions to analyze
        return file_extension in self.file_extensions

    def print_summary(self, files: List[str]) -> None:
        """
        Print a nice summary of what files were found.

        Args:
            files: List of file paths that were found
        """
        print(f"\n=== File Scanner Summary ===")
        print(f"Base path: {self.base_path}")
        print(f"Analyzed folders: {', '.join(self.analyze_folders)}")
        print(f"Excluded folders: {', '.join(self.exclude_folders)}")
        print(f"File extensions: {', '.join(self.file_extensions)}")
        print(f"Total files found: {len(files)}")

        if files:
            print(f"\nFirst 5 files found:")
            for file_path in files[:5]:
                # Show relative path for cleaner output
                rel_path = Path(file_path).relative_to(self.base_path)
                print(f"  - {rel_path}")

            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more files")


# Example usage (you can test this)
if __name__ == "__main__":
    # Create scanner instance
    scanner = FileScanner()

    # Find all files
    files = scanner.scan_files()

    # Print summary
    scanner.print_summary(files)