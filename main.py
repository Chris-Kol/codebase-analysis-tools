#!/usr/bin/env python3
"""
Main CLI interface for the codebase analysis tools.
This orchestrates the file scanning and Branch dependency analysis.
"""

import click
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Import our analysis components
from src.shared.file_scanner import FileScanner
from src.branch_analyzer.analyzer import BranchAnalyzer
import config


@click.group()
def cli():
    """Codebase Analysis Tools - A suite for analyzing large codebases."""
    pass


@cli.command()
@click.option('--output', '-o', default='branch_dependencies.json',
              help='Output file for the analysis results')
@click.option('--verbose', '-v', is_flag=True,
              help='Show detailed progress information')
@click.option('--limit', '-l', type=int, default=None,
              help='Limit analysis to first N files (for testing)')
def analyze_branch(output: str, verbose: bool, limit: int):
    """
    Analyze the codebase for Branch dependencies.

    This command will:
    1. Scan all PHP files in the configured directories
    2. Parse each file using nikic/PHP-Parser
    3. Detect Branch class dependencies
    4. Output a comprehensive JSON report
    """

    click.echo("🔍 Starting Branch dependency analysis...")
    start_time = time.time()

    # Step 1: Initialize components
    if verbose:
        click.echo("Initializing file scanner and analyzer...")

    try:
        scanner = FileScanner()
        analyzer = BranchAnalyzer()
    except Exception as e:
        click.echo(f"❌ Failed to initialize components: {e}", err=True)
        exit(1)

    # Step 2: Scan for files
    if verbose:
        click.echo(f"Scanning files in: {config.LMS_BASE_PATH}")
        click.echo(f"Analyzing folders: {', '.join(config.ANALYZE_FOLDERS)}")
        click.echo(f"Excluding folders: {', '.join(config.EXCLUDE_FOLDERS)}")

    files = scanner.scan_files()

    if not files:
        click.echo("❌ No PHP files found to analyze", err=True)
        exit(1)

    # Apply limit if specified
    if limit and limit < len(files):
        files = files[:limit]
        click.echo(f"🔧 Limiting analysis to first {limit} files")

    click.echo(f"📁 Found {len(files)} PHP files to analyze")

    # Step 3: Analyze each file
    results = []
    files_with_dependencies = 0
    total_dependencies = 0

    with click.progressbar(files, label='Analyzing files') as file_list:
        for i, file_path in enumerate(file_list):
            try:
                # Analyze the file
                result = analyzer.analyze_file(file_path)

                # Add relative path for cleaner output
                try:
                    base_path = Path(config.LMS_BASE_PATH).resolve()
                    file_path_obj = Path(file_path).resolve()
                    result['relative_path'] = str(file_path_obj.relative_to(base_path))
                except ValueError:
                    result['relative_path'] = file_path

                results.append(result)

                # Track statistics
                if result['total_dependencies'] > 0:
                    files_with_dependencies += 1
                    total_dependencies += result['total_dependencies']

                # Show verbose progress
                if verbose and (i + 1) % 100 == 0:
                    click.echo(f"\n  Processed {i + 1}/{len(files)} files...")

            except Exception as e:
                # Handle individual file errors gracefully
                error_result = {
                    'file_path': file_path,
                    'relative_path': file_path,
                    'dependencies': [],
                    'error': f'Analysis failed: {str(e)}',
                    'total_dependencies': 0
                }
                results.append(error_result)

    # Step 4: Generate summary
    analysis_time = time.time() - start_time

    summary = {
        'analysis_metadata': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'analysis_time_seconds': round(analysis_time, 2),
            'base_path': config.LMS_BASE_PATH,
            'analyzed_folders': config.ANALYZE_FOLDERS,
            'excluded_folders': config.EXCLUDE_FOLDERS,
            'total_files_analyzed': len(files),
            'files_with_dependencies': files_with_dependencies,
            'total_dependencies_found': total_dependencies
        },
        'files': results
    }

    # Step 5: Save results
    output_path = Path(config.OUTPUT_DIR) / output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Step 6: Display results
    click.echo(f"\n✅ Analysis completed in {analysis_time:.2f} seconds")
    click.echo(f"📊 Results:")
    click.echo(f"   • Total files analyzed: {len(files)}")
    click.echo(f"   • Files with Branch dependencies: {files_with_dependencies}")
    click.echo(f"   • Total Branch dependencies found: {total_dependencies}")
    click.echo(f"   • Results saved to: {output_path}")

    # Show some examples if dependencies were found
    if total_dependencies > 0:
        click.echo(f"\n🎯 Top files with most dependencies:")

        # Sort files by dependency count
        sorted_files = sorted(
            [r for r in results if r['total_dependencies'] > 0],
            key=lambda x: x['total_dependencies'],
            reverse=True
        )

        for i, file_result in enumerate(sorted_files[:5]):
            rel_path = file_result.get('relative_path', file_result['file_path'])
            count = file_result['total_dependencies']
            click.echo(f"   {i + 1}. {rel_path} ({count} dependencies)")
    else:
        click.echo(f"\n ℹ️  No Branch dependencies found in the analyzed files")


@cli.command()
def test_setup():
    """Test that all components are working correctly."""

    click.echo("🧪 Testing analysis tool setup...")

    # Test 1: File scanner
    try:
        scanner = FileScanner()
        files = scanner.scan_files()
        click.echo(f"✅ File scanner: Found {len(files)} files")
    except Exception as e:
        click.echo(f"❌ File scanner failed: {e}")
        return

    # Test 2: PHP parser bridge
    try:
        analyzer = BranchAnalyzer()
        if analyzer.php_bridge.test_connection():
            click.echo("✅ PHP parser bridge: Working correctly")
        else:
            click.echo("❌ PHP parser bridge: Test failed")
            return
    except Exception as e:
        click.echo(f"❌ PHP parser bridge failed: {e}")
        return

    # Test 3: End-to-end test with a sample file
    if files:
        try:
            test_file = files[0]  # Use first file found
            result = analyzer.analyze_file(test_file)

            if 'error' in result and result['error']:
                click.echo(f"⚠️  Sample file analysis had error: {result['error']}")
            else:
                click.echo(f"✅ Sample file analysis: Processed {Path(test_file).name}")

        except Exception as e:
            click.echo(f"❌ Sample file analysis failed: {e}")
            return

    click.echo("🎉 All tests passed! The analysis tool is ready to use.")


if __name__ == '__main__':
    cli()