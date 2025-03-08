#!/usr/bin/env python3
"""
Batch converter for recipe files to Obsidian markdown format.

This module provides functionality to process multiple recipe files in parallel,
from different formats to Obsidian markdown format.
"""

import os
import glob
import argparse
import subprocess
import concurrent.futures
import sys
from pathlib import Path

from cookdown.parsers import get_parser_for_extension, get_supported_extensions
from cookdown.formatter import convert_to_markdown
from cookdown.convert import find_input_directory, find_output_directory


def find_recipe_files(input_dir, recursive=False, extensions=None):
    """
    Find all recipe files in the input directory with supported extensions.
    
    Args:
        input_dir: Directory to search in
        recursive: Whether to search recursively in subdirectories
        extensions: List of file extensions to search for (without dots)
        
    Returns:
        List of paths to recipe files
    """
    # Get list of supported extensions if not provided
    if extensions is None:
        extensions = get_supported_extensions()
    
    all_files = []
    
    for ext in extensions:
        if recursive:
            # Use glob pattern for recursive search
            pattern = os.path.join(input_dir, "**", f"*.{ext}")
            all_files.extend(glob.glob(pattern, recursive=True))
        else:
            # Non-recursive search in just the input directory
            pattern = os.path.join(input_dir, f"*.{ext}")
            all_files.extend(glob.glob(pattern))
    
    return all_files


def convert_file(
    recipe_file, 
    output_dir, 
    use_subprocess=False, 
    converter_script=None
):
    """
    Convert a single recipe file using either direct function call or subprocess.
    
    Args:
        recipe_file: Path to the recipe file
        output_dir: Directory to save the converted file
        use_subprocess: Whether to use subprocess or direct function call
        converter_script: Path to the converter script (if using subprocess)
        
    Returns:
        Tuple of (success, file_path, output)
    """
    try:
        if use_subprocess:
            # Use subprocess to call the converter script
            if converter_script is None:
                # Default to the cli entry point
                converter_script = [sys.executable, "-m", "cookdown.convert"]
            else:
                # Use the specified script
                converter_script = [sys.executable, converter_script]
            
            # Build the command
            cmd = converter_script + ["-f", recipe_file, "-o", output_dir]
            
            # Run the command
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            # Check for errors
            if result.returncode != 0:
                return (False, recipe_file, result.stderr)
            
            return (True, recipe_file, result.stdout)
        else:
            # Use direct function call
            # Get the file extension to determine the parser
            extension = os.path.splitext(recipe_file)[1][1:].lower()
            parser_class = get_parser_for_extension(extension)
            
            if parser_class is None:
                return (
                    False, 
                    recipe_file, 
                    f"No parser found for extension: {extension}"
                )
            
            # Convert the file
            output_path = convert_to_markdown(recipe_file, output_dir, parser_class)
            return (True, recipe_file, f"Converted to {output_path}")
    
    except Exception as e:
        # Handle any exceptions
        return (False, recipe_file, str(e))


def batch_convert(
    input_dir=None,
    output_dir=None,
    recursive=False,
    max_workers=4,
    use_subprocess=False,
    converter_script=None,
    extensions=None
):
    """
    Convert multiple recipe files in parallel.
    
    Args:
        input_dir: Directory containing recipe files
        output_dir: Directory to save converted files
        recursive: Whether to search recursively for files
        max_workers: Maximum number of parallel conversions
        use_subprocess: Whether to use subprocess for conversion
        converter_script: Path to converter script if using subprocess
        extensions: List of extensions to process (default: all supported)
        
    Returns:
        List of (success, file_path, output) tuples
    """
    # Use default directories if not specified
    if input_dir is None:
        input_dir = find_input_directory()
    
    if output_dir is None:
        output_dir = find_output_directory()
    
    # Find all recipe files with supported extensions
    recipe_files = find_recipe_files(input_dir, recursive, extensions)
    
    if not recipe_files:
        supported = ", ".join(get_supported_extensions() if extensions is None else extensions)
        print(f"No recipe files found in {input_dir}")
        print(f"Supported extensions: {supported}")
        return []
    
    # Convert files in parallel
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all conversion tasks
        future_to_file = {
            executor.submit(
                convert_file, 
                recipe_file, 
                output_dir, 
                use_subprocess, 
                converter_script
            ): recipe_file 
            for recipe_file in recipe_files
        }
        
        # Process the results as they complete
        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            
            try:
                result = future.result()
                results.append(result)
                
                # Print status
                success, _, output = result
                if success:
                    print(f"✓ {file_path}: {output}")
                else:
                    print(f"✗ {file_path}: {output}")
                
            except Exception as e:
                print(f"✗ {file_path}: Exception: {e}")
                results.append((False, file_path, str(e)))
    
    return results


def main():
    """Command-line entry point for the batch converter."""
    parser = argparse.ArgumentParser(
        description="Batch convert recipe files to Obsidian markdown."
    )
    parser.add_argument(
        "-i", "--input", 
        help="Input directory containing recipe files (defaults to 'data/input' subdirectory)"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Output directory for markdown files (defaults to 'data/output' subdirectory)"
    )
    parser.add_argument(
        "-r", "--recursive", 
        action="store_true", 
        help="Search recursively for recipe files in input directory"
    )
    parser.add_argument(
        "-p", "--parallel",
        type=int,
        default=4,
        help="Maximum number of parallel conversions (default is 4)"
    )
    parser.add_argument(
        "-s", "--subprocess",
        action="store_true",
        help="Use subprocess to call the converter script instead of direct function call"
    )
    parser.add_argument(
        "-e", "--extensions",
        nargs="+",
        help="List of file extensions to process (default: all supported extensions)"
    )
    parser.add_argument(
        "-l", "--list-formats", 
        action="store_true",
        help="List supported file formats"
    )
    
    args = parser.parse_args()
    
    # List supported formats if requested
    if args.list_formats:
        extensions = get_supported_extensions()
        print("Supported recipe file formats:")
        for ext in sorted(extensions):
            print(f"  .{ext}")
        return
    
    # Run the batch conversion
    results = batch_convert(
        input_dir=args.input,
        output_dir=args.output,
        recursive=args.recursive,
        max_workers=args.parallel,
        use_subprocess=args.subprocess,
        extensions=args.extensions
    )
    
    # Print summary
    success_count = sum(1 for r in results if r[0])
    error_count = len(results) - success_count
    
    print("\nBatch conversion complete!")
    print(f"Successfully converted: {success_count}")
    print(f"Errors: {error_count}")
    
    if error_count > 0:
        print("\nFiles with errors:")
        for result in results:
            if not result[0]:
                print(f"  {result[1]}: {result[2]}")


if __name__ == "__main__":
    main() 