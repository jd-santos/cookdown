#!/usr/bin/env python3
"""
Utility script to extract Paprika recipe files to JSON.

This script provides a way to extract both:
- .paprikarecipes archives (ZIP files containing multiple .paprikarecipe files)
- Individual .paprikarecipe files (gzipped JSON)

The extracted JSON files can then be processed by cookdown or used directly.
"""

import os
import sys
import json
import glob
import gzip
import argparse
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('extract_paprika')


def extract_paprikarecipes_archive(archive_path: str, output_dir: str) -> List[str]:
    """
    Extract a .paprikarecipes archive to individual .paprikarecipe files.
    
    Args:
        archive_path: Path to the .paprikarecipes archive
        output_dir: Directory to extract the .paprikarecipe files
        
    Returns:
        List of paths to extracted .paprikarecipe files
    """
    logger.info(f"Extracting archive: {archive_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    extracted_files = []
    
    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            # Get list of files in the archive
            recipe_files = [f for f in zip_ref.namelist() if f.endswith('.paprikarecipe')]
            logger.info(f"Archive contains {len(recipe_files)} recipe files")
            
            # Extract each recipe file
            for recipe_file in recipe_files:
                # Extract to output directory
                zip_ref.extract(recipe_file, output_dir)
                extracted_path = os.path.join(output_dir, recipe_file)
                extracted_files.append(extracted_path)
                logger.debug(f"Extracted: {recipe_file}")
    except Exception as e:
        logger.error(f"Failed to extract archive {archive_path}: {e}")
        return []
    
    return extracted_files


def extract_paprikarecipe_to_json(recipe_path: str, output_dir: str) -> str:
    """
    Extract a .paprikarecipe file to JSON.
    
    Args:
        recipe_path: Path to the .paprikarecipe file
        output_dir: Directory to save the JSON file
        
    Returns:
        Path to the created JSON file, or empty string if extraction failed
    """
    # Create output filename - replace .paprikarecipe with .json
    recipe_name = os.path.basename(recipe_path)
    json_filename = os.path.splitext(recipe_name)[0] + '.json'
    json_path = os.path.join(output_dir, json_filename)
    
    logger.info(f"Extracting: {recipe_name} -> {json_filename}")
    
    try:
        # Open and decompress the gzipped file
        with gzip.open(recipe_path, 'rb') as f_in:
            # Read and decode the JSON data
            json_data = f_in.read().decode('utf-8')
            
            # Validate it's proper JSON
            json_obj = json.loads(json_data)
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Write the JSON to file with pretty formatting for readability
            with open(json_path, 'w', encoding='utf-8') as f_out:
                json.dump(json_obj, f_out, indent=2, ensure_ascii=False)
            
            logger.debug(f"Successfully extracted {json_filename}")
            return json_path
            
    except json.JSONDecodeError:
        logger.error(f"The file {recipe_path} does not contain valid JSON")
    except Exception as e:
        logger.error(f"Failed to extract {recipe_path}: {e}")
    
    return ""


def process_directory(input_dir: str, output_dir: str, keep_intermediate: bool = False) -> Dict[str, List[str]]:
    """
    Process a directory containing Paprika recipe files.
    
    Args:
        input_dir: Directory containing Paprika recipe files
        output_dir: Directory to save extracted JSON files
        keep_intermediate: Whether to keep intermediate .paprikarecipe files extracted from archives
        
    Returns:
        Dictionary with statistics on processed files
    """
    logger.info(f"Processing Paprika recipes from {input_dir}")
    
    # Create output directories
    json_dir = output_dir
    intermediate_dir = os.path.join(output_dir, "paprikarecipe_files")
    os.makedirs(json_dir, exist_ok=True)
    
    stats = {
        "archives_processed": [],
        "recipes_processed": [],
        "json_files_created": []
    }
    
    # Step 1: Find and extract all .paprikarecipes archives
    archives = glob.glob(os.path.join(input_dir, "*.paprikarecipes"))
    
    for archive_path in archives:
        extracted_files = extract_paprikarecipes_archive(archive_path, intermediate_dir)
        if extracted_files:
            stats["archives_processed"].append(archive_path)
            
            # Step 2: Extract each .paprikarecipe file to JSON
            for recipe_path in extracted_files:
                json_path = extract_paprikarecipe_to_json(recipe_path, json_dir)
                if json_path:
                    stats["recipes_processed"].append(recipe_path)
                    stats["json_files_created"].append(json_path)
    
    # Step 3: Process any standalone .paprikarecipe files
    recipe_files = glob.glob(os.path.join(input_dir, "*.paprikarecipe"))
    
    for recipe_path in recipe_files:
        json_path = extract_paprikarecipe_to_json(recipe_path, json_dir)
        if json_path:
            stats["recipes_processed"].append(recipe_path)
            stats["json_files_created"].append(json_path)
    
    # Step 4: Clean up intermediate files if not keeping them
    if not keep_intermediate and os.path.exists(intermediate_dir):
        try:
            import shutil
            logger.info("Cleaning up intermediate files")
            shutil.rmtree(intermediate_dir)
        except Exception as e:
            logger.error(f"Failed to clean up intermediate files: {e}")
    
    return stats


def main():
    """Command-line entry point for the Paprika extractor."""
    parser = argparse.ArgumentParser(
        description="Extract Paprika recipe files to JSON"
    )
    parser.add_argument(
        "input", 
        help="Directory containing Paprika recipe files or a specific .paprikarecipe(s) file"
    )
    parser.add_argument(
        "-o", "--output", 
        help="Directory to save extracted JSON files (default: input_dir/json)"
    )
    parser.add_argument(
        "-k", "--keep-intermediate", 
        action="store_true", 
        help="Keep intermediate .paprikarecipe files extracted from archives"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set log level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Determine input type (file or directory)
    input_path = args.input
    
    if os.path.isfile(input_path):
        # Input is a single file
        input_dir = os.path.dirname(input_path)
        filename = os.path.basename(input_path)
        
        # Default output directory
        output_dir = args.output if args.output else os.path.join(input_dir, "json")
        
        if filename.endswith('.paprikarecipes'):
            # Process a single archive
            intermediate_dir = os.path.join(output_dir, "paprikarecipe_files")
            extracted_files = extract_paprikarecipes_archive(input_path, intermediate_dir)
            for recipe_path in extracted_files:
                extract_paprikarecipe_to_json(recipe_path, output_dir)
                
            # Clean up intermediate files if not keeping them
            if not args.keep_intermediate and os.path.exists(intermediate_dir):
                try:
                    import shutil
                    shutil.rmtree(intermediate_dir)
                except Exception as e:
                    logger.error(f"Failed to clean up intermediate files: {e}")
                    
        elif filename.endswith('.paprikarecipe'):
            # Process a single recipe file
            extract_paprikarecipe_to_json(input_path, output_dir)
            
        else:
            logger.error(f"Unsupported file type: {filename}")
            sys.exit(1)
            
    elif os.path.isdir(input_path):
        # Input is a directory
        output_dir = args.output if args.output else os.path.join(input_path, "json")
        stats = process_directory(input_path, output_dir, args.keep_intermediate)
        
        # Print summary
        logger.info(f"Processed {len(stats['archives_processed'])} archives")
        logger.info(f"Processed {len(stats['recipes_processed'])} recipe files")
        logger.info(f"Created {len(stats['json_files_created'])} JSON files")
        logger.info(f"Output directory: {output_dir}")
        
    else:
        logger.error(f"Input path not found: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main() 