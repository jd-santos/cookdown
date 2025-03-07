#!/usr/bin/env python3
"""
Convert Crouton .crumb files to Obsidian markdown format.

This module provides functions to parse Crouton's .crumb JSON files and convert 
them to a mixed YAML/markdown format compatible with Obsidian.
"""

import os
import json
import base64
import glob
import re
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


def read_crumb_file(filepath: str) -> Dict[str, Any]:
    """
    Read and parse a .crumb file.
    
    Args:
        filepath: Path to the .crumb file
        
    Returns:
        Dictionary containing the recipe data
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.loads(f.read())


def format_ingredients(ingredients: List[Dict[str, Any]]) -> List[str]:
    """
    Format ingredients into a list of strings.
    
    Args:
        ingredients: List of ingredient dictionaries
        
    Returns:
        List of formatted ingredient strings
    """
    result = []

    # Sort ingredients by order
    sorted_ingredients = sorted(ingredients, key=lambda x: x.get("order", 0))

    for item in sorted_ingredients:
        ingredient_name = item.get("ingredient", {}).get("name", "")

        # Get quantity information
        quantity_info = item.get("quantity", {})
        amount = quantity_info.get("amount", "")
        quantity_type = quantity_info.get("quantityType", "")

        # Format the ingredient string
        if amount and quantity_type:
            # Convert to lowercase for consistency
            quantity_type_lower = quantity_type.lower()
            # Handle plural forms
            if (
                amount > 1
                and quantity_type_lower != "pound"
                and not quantity_type_lower.endswith("s")
            ):
                quantity_type_lower += "s"
            ingredient_str = f"{amount} {quantity_type_lower} {ingredient_name}"
        else:
            ingredient_str = ingredient_name

        result.append(ingredient_str)

    return result


def format_steps(steps: List[Dict[str, Any]]) -> str:
    """
    Format recipe steps into markdown.
    
    Args:
        steps: List of step dictionaries
        
    Returns:
        Formatted markdown string with steps
    """
    # Sort steps by order
    sorted_steps = sorted(steps, key=lambda x: x.get("order", 0))

    # Process the steps and identify sections
    formatted_steps = []
    current_section = None

    for step in sorted_steps:
        step_text = step.get("step", "")
        is_section = step.get("isSection", False)

        # Remove Markdown formatting that will be redone
        # This pattern matches ** at the beginning of a line followed by text then **
        section_pattern = r"^\*\*(.*?)\*\*\s*"
        section_match = re.match(section_pattern, step_text)

        if section_match:
            # This is a section header within a step
            section_name = section_match.group(1)
            step_text = re.sub(section_pattern, "", step_text)
            formatted_steps.append(f"### {section_name}")

        # Add the step content as a numbered list item
        formatted_steps.append(f"1. {step_text}")

    return "\n".join(formatted_steps)


def save_image(image_data: str, recipe_name: str, index: int, output_dir: str) -> str:
    """
    Save base64 encoded image to a file.
    
    Args:
        image_data: Base64 encoded image string
        recipe_name: Name of the recipe for filename
        index: Image index for filename
        output_dir: Directory to save the image
        
    Returns:
        Relative path to the saved image
    """
    # Create images directory if it doesn't exist
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    # Create a safe filename from the recipe name
    safe_name = re.sub(r"[^a-zA-Z0-9]", "_", recipe_name)

    # Create the image filename
    image_filename = f"{safe_name}_{index}.jpg"
    image_path = os.path.join(images_dir, image_filename)

    try:
        # If the image data is complete (not truncated)
        if "truncated for LLM context" not in image_data:
            image_bytes = base64.b64decode(image_data)
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            return f"images/{image_filename}"
    except Exception as e:
        print(f"Warning: Could not save image {index} for {recipe_name}: {e}")
    
    return ""


def convert_crumb_to_md(crumb_path: str, output_dir: str) -> None:
    """
    Convert a .crumb file to Obsidian markdown format.
    
    Args:
        crumb_path: Path to the .crumb file
        output_dir: Directory where the markdown file will be saved
    """
    try:
        # Read and parse the .crumb file
        crumb_data = read_crumb_file(crumb_path)

        # Extract recipe information
        recipe_name = crumb_data.get("name", "Unnamed Recipe")

        # Create safe filename
        safe_filename = f"{recipe_name}.md"
        output_path = os.path.join(output_dir, safe_filename)

        # Process ingredients
        ingredients = format_ingredients(crumb_data.get("ingredients", []))

        # Process directions (steps)
        directions = format_steps(crumb_data.get("steps", []))

        # Process images
        image_paths = []
        for i, image_data in enumerate(crumb_data.get("images", [])):
            if image_data:
                image_path = save_image(image_data, recipe_name, i, output_dir)
                if image_path:
                    image_paths.append(image_path)

        # Create YAML frontmatter
        frontmatter = {
            "food-labels": "",  # Empty by default
            "created": datetime.now().strftime("%Y-%m-%d"),
            "updated": datetime.now().strftime("%Y-%m-%d"),
            "tags": ["food/recipe"],
            "photos": image_paths,
            "source": "",  # Can be populated if source info is available
            "source-url": crumb_data.get("webLink", ""),
            "cook-time": f"{crumb_data.get('cookingDuration', 0)} minutes",
            "difficulty": "",  # Not directly available in the .crumb format
            "servings": crumb_data.get("serves", ""),
            "ingredients": ingredients,
        }

        # Format the frontmatter as YAML
        yaml_lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, list):
                yaml_lines.append(f"{key}:")
                for item in value:
                    yaml_lines.append(f"  - {item}")
            else:
                yaml_lines.append(f"{key}: {value}")
        yaml_lines.append("---")

        # Combine everything into the final markdown
        md_content = []
        md_content.extend(yaml_lines)
        md_content.append("\n## Directions")
        md_content.append(directions)
        md_content.append("\n## Notes")
        md_content.append(crumb_data.get("notes", ""))
        md_content.append("\n## Nutrition Info")
        md_content.append(crumb_data.get("neutritionalInfo", ""))

        # Write the markdown file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))

        print(f"Converted {crumb_path} to {output_path}")

    except Exception as e:
        print(f"Error converting {crumb_path}: {e}")


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
    default_path = possible_paths[0]
    os.makedirs(default_path, exist_ok=True)
    return default_path


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
    default_path = possible_paths[0]
    os.makedirs(default_path, exist_ok=True)
    return default_path


def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments object
    """
    parser = argparse.ArgumentParser(
        description="Convert Crouton .crumb files to Obsidian markdown format."
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
        "-f",
        "--file",
        default=None,
        help="Process a single .crumb file instead of a directory.",
    )
    return parser.parse_args()


def main():
    """Main function to process .crumb files based on command-line arguments."""
    args = parse_args()

    # Determine input and output directories
    if args.file:
        # Process a single file
        if not os.path.isfile(args.file):
            print(f"Error: File not found: {args.file}")
            return

        input_dir = os.path.dirname(os.path.abspath(args.file))
        crumb_files = [args.file]
    else:
        # Process files in a directory
        input_dir = args.input if args.input else find_input_directory()

        if not os.path.isdir(input_dir):
            print(f"Error: Input directory not found: {input_dir}")
            return

        # Find .crumb files
        if args.recursive:
            # Recursive search
            crumb_files = []
            for root, _, files in os.walk(input_dir):
                for file in files:
                    if file.endswith(".crumb"):
                        crumb_files.append(os.path.join(root, file))
        else:
            # Non-recursive search
            crumb_files = glob.glob(os.path.join(input_dir, "*.crumb"))

    # Determine output directory
    output_dir = args.output if args.output else find_output_directory()

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    if not crumb_files:
        print("No .crumb files found.")
        return

    # Process each .crumb file
    for crumb_file in crumb_files:
        convert_crumb_to_md(crumb_file, output_dir)

    print(f"Processed {len(crumb_files)} recipe(s). Output saved to {output_dir}")


if __name__ == "__main__":
    main() 