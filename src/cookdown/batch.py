#!/usr/bin/env python3
"""
Batch converter for Crouton .crumb files to Obsidian markdown format.

This module provides functionality to process multiple .crumb files in parallel,
either in a single directory or recursively through subdirectories.
"""

import os
import glob
import argparse
import subprocess
import concurrent.futures
import sys
from pathlib import Path

from cookdown import convert


def find_crumb_files(input_dir, recursive=False):
    """
    Find all .crumb files in the input directory.
    
    Args:
        input_dir: Directory to search in
        recursive: Whether to search recursively in subdirectories
        
    Returns:
        List of paths to .crumb files
    """
    if recursive:
        # Use glob pattern for recursive search
        return glob.glob(os.path.join(input_dir, "**", "*.crumb"), recursive=True)
    else:
        # Non-recursive search in just the input directory
        return glob.glob(os.path.join(input_dir, "*.crumb"))


def convert_file(crumb_file, output_dir, use_subprocess=True, converter_script=None):
    """
    Convert a single .crumb file using either direct function call or subprocess.
    
    Args:
        crumb_file: Path to the .crumb file
        output_dir: Directory to save the converted file
        use_subprocess: Whether to use subprocess or direct function call
        converter_script: Path to the converter script (if using subprocess)
        
    Returns:
        Tuple of (success, file_path, output)
    """
    if use_subprocess and converter_script:
        try:
            # Use subprocess to call the converter script
            cmd = [sys.executable, converter_script, "-f", crumb_file, "-o", output_dir]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, crumb_file, result.stdout
        except subprocess.CalledProcessError as e:
            return False, crumb_file, e.stderr
    else:
        # Direct function call
        try:
            convert.convert_crumb_to_md(crumb_file, output_dir)
            return True, crumb_file, f"Converted {crumb_file} to {output_dir}"
        except Exception as e:
            return False, crumb_file, str(e)


def process_files(crumb_files, output_dir, converter_script=None, max_workers=None, use_subprocess=False):
    """
    Process multiple .crumb files using thread pool for parallel execution.
    
    Args:
        crumb_files: List of paths to .crumb files
        output_dir: Directory to save converted files
        converter_script: Path to the converter script (if using subprocess)
        max_workers: Maximum number of parallel workers
        use_subprocess: Whether to use subprocess or direct function call
        
    Returns:
        Tuple of (success_count, error_count)
    """
    success_count = 0
    error_count = 0

    print(f"Processing {len(crumb_files)} file(s)...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(convert_file, crumb_file, output_dir, use_subprocess, converter_script)
            for crumb_file in crumb_files
        ]

        for future in concurrent.futures.as_completed(futures):
            success, file_path, message = future.result()
            if success:
                print(f"✓ Converted: {os.path.basename(file_path)}")
                success_count += 1
            else:
                print(f"✗ Error processing {os.path.basename(file_path)}: {message}")
                error_count += 1

    return success_count, error_count


def find_converter_script():
    """
    Find the convert.py script location.
    
    Returns:
        Path to the convert.py script
    """
    # First check if we're running from the installed package
    try:
        import cookdown
        package_dir = os.path.dirname(os.path.abspath(cookdown.__file__))
        script_path = os.path.join(package_dir, "convert.py")
        if os.path.exists(script_path):
            return script_path
    except ImportError:
        pass
    
    # Otherwise look for it relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "convert.py")
    
    # If not found, try in the current directory
    if not os.path.exists(script_path):
        script_path = os.path.join(os.getcwd(), "convert.py")
        
    # If still not found, try the old name in the current directory
    if not os.path.exists(script_path):
        script_path = os.path.join(os.getcwd(), "crumb_to_md.py")
    
    return script_path if os.path.exists(script_path) else None


def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments object
    """
    parser = argparse.ArgumentParser(
        description="Batch convert Crouton .crumb files to Obsidian markdown format."
    )
    parser.add_argument(
        "-i",
        "--input",
        default=None,
        help="Input directory containing .crumb files. Defaults to 'data/input' subdirectory.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output directory for markdown files. Defaults to 'data/output' subdirectory.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search recursively for .crumb files in input directory.",
    )
    parser.add_argument(
        "-p",
        "--parallel",
        type=int,
        default=4,
        help="Maximum number of parallel conversions. Default is 4.",
    )
    parser.add_argument(
        "-s",
        "--subprocess",
        action="store_true",
        help="Use subprocess to call the converter script instead of direct function call.",
    )
    return parser.parse_args()


def main():
    """Main function to batch process .crumb files."""
    args = parse_args()

    # Get appropriate directories
    input_dir = args.input if args.input else convert.find_input_directory()
    output_dir = args.output if args.output else convert.find_output_directory()

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Find the converter script if using subprocess
    converter_script = None
    if args.subprocess:
        converter_script = find_converter_script()
        if not converter_script:
            print("Error: Converter script not found.")
            return

    # Find all .crumb files
    crumb_files = find_crumb_files(input_dir, args.recursive)

    if not crumb_files:
        print(f"No .crumb files found in {input_dir}")
        return

    # Process the files
    success_count, error_count = process_files(
        crumb_files, output_dir, converter_script, args.parallel, args.subprocess
    )

    # Print summary
    print(f"\nConversion Summary:")
    print(f"  Total: {len(crumb_files)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {error_count}")
    print(f"\nOutput saved to: {output_dir}")


if __name__ == "__main__":
    main() 