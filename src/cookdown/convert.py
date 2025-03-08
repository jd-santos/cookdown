#!/usr/bin/env python3
"""
Command-line tool to convert recipe files to Obsidian markdown format.

This module provides a command-line interface to convert recipe files to 
Obsidian markdown using the appropriate parser based on file extension.
"""

import os
import glob
import argparse
from typing import Optional
from pathlib import Path

from cookdown.parsers import get_parser_for_extension, get_supported_extensions
from cookdown.formatter import convert_to_markdown


def find_input_directory() -> str:
    """
    Find the most appropriate input directory based on the package structure.
    
    Returns:
        Path to the input directory
    """
    # Try different possible locations for the input directory
    possible_paths = [
        os.path.join(os.getcwd(), "data", "input"),  # data/input in current directory
        os.path.join(os.getcwd(), "input"),          # input in current directory
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "input"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "input"),
    ]
    
    for path in possible_paths:
        if os.path.isdir(path):
            return path
    
    # If none exist, default to the first option and create it
    os.makedirs(possible_paths[0], exist_ok=True)
    return possible_paths[0]


def find_output_directory() -> str:
    """
    Find the most appropriate output directory based on the package structure.
    
    Returns:
        Path to the output directory
    """
    # Try different possible locations for the output directory
    possible_paths = [
        os.path.join(os.getcwd(), "data", "output"),  # data/output in current directory
        os.path.join(os.getcwd(), "output"),          # output in current directory
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "output"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output"),
    ]
    
    for path in possible_paths:
        if os.path.isdir(path):
            return path
    
    # If none exist, default to the first option and create it
    os.makedirs(possible_paths[0], exist_ok=True)
    return possible_paths[0]


def convert_recipe_file(
    filepath: str, 
    output_dir: Optional[str] = None
) -> str:
    """
    Convert a single recipe file to Obsidian markdown.
    
    Args:
        filepath: Path to the recipe file
        output_dir: Directory to save the output file (optional)
        
    Returns:
        Path to the created markdown file
    """
    # Use default output directory if not specified
    if output_dir is None:
        output_dir = find_output_directory()
    
    # Get the file extension to determine the parser
    extension = os.path.splitext(filepath)[1][1:].lower()
    parser_class = get_parser_for_extension(extension)
    
    if parser_class is None:
        supported = ", ".join(get_supported_extensions())
        raise ValueError(
            f"No parser found for extension '{extension}'. "
            f"Supported extensions are: {supported}"
        )
    
    # Convert the file
    return convert_to_markdown(filepath, output_dir, parser_class)


def main():
    """Command-line entry point for the converter."""
    parser = argparse.ArgumentParser(
        description="Convert recipe files to Obsidian markdown."
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
        "-f", "--file", 
        help="Process a single recipe file instead of a directory"
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
    
    # Set input and output directories
    input_dir = args.input if args.input else find_input_directory()
    output_dir = args.output if args.output else find_output_directory()
    
    # Process a single file if specified
    if args.file:
        convert_recipe_file(args.file, output_dir)
        return
    
    # Otherwise, process all files in the input directory with supported extensions
    supported_exts = get_supported_extensions()
    processed_files = []
    
    # Build the glob pattern for all supported extensions
    for ext in supported_exts:
        pattern = os.path.join(input_dir, f"*.{ext}")
        if args.recursive:
            pattern = os.path.join(input_dir, "**", f"*.{ext}")
        
        for filepath in glob.glob(pattern, recursive=args.recursive):
            try:
                output_path = convert_recipe_file(filepath, output_dir)
                processed_files.append((filepath, output_path))
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
    
    # Print summary
    print(f"\nProcessed {len(processed_files)} files")
    if not processed_files:
        print(f"No supported files found in {input_dir}")
        print(f"Supported extensions: {', '.join(supported_exts)}")


if __name__ == "__main__":
    main() 