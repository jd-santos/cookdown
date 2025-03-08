"""
Formatter for converting parsed recipe data to Obsidian markdown.

This module provides functions to format recipe data into Obsidian-compatible markdown.
"""

import os
import base64
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from cookdown.parsers import RecipeParser


def format_ingredients(ingredients: List[Dict[str, Any]]) -> List[str]:
    """
    Format normalized ingredients into a list of strings.
    
    Args:
        ingredients: List of normalized ingredient dictionaries
        
    Returns:
        List of formatted ingredient strings
    """
    result = []

    for item in ingredients:
        ingredient_name = item["name"]
        amount = item["amount"]
        unit = item["unit"]

        # Format the ingredient string
        if amount and unit:
            # Convert to lowercase for consistency
            unit_lower = unit.lower()
            # Handle plural forms
            if (
                amount > 1
                and unit_lower != "pound"
                and not unit_lower.endswith("s")
            ):
                unit_lower += "s"
            ingredient_str = f"{amount} {unit_lower} {ingredient_name}"
        else:
            ingredient_str = ingredient_name

        result.append(ingredient_str)

    return result


def format_instructions(instructions: List[Dict[str, Any]]) -> str:
    """
    Format recipe instructions into markdown.
    
    Args:
        instructions: List of normalized instruction dictionaries
        
    Returns:
        Formatted markdown string with instructions
    """
    formatted_steps = []
    
    for step in instructions:
        step_text = step["text"]
        is_section = step["is_section"]
        section_name = step["section_name"]
        
        if section_name:
            # This is a section header
            formatted_steps.append(f"### {section_name}")
        
        # Add the step content as a numbered list item
        formatted_steps.append(f"1. {step_text}")
    
    return "\n".join(formatted_steps)


def save_image(image_data: Dict[str, Any], output_dir: str) -> str:
    """
    Save image data to a file.
    
    Args:
        image_data: Dictionary with image data
        output_dir: Directory to save the image
        
    Returns:
        Relative path to the saved image
    """
    # Create images directory if it doesn't exist
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    image_filename = image_data["filename"]
    image_path = os.path.join(images_dir, image_filename)

    try:
        if image_data["format"] == "base64":
            image_bytes = base64.b64decode(image_data["data"])
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            return f"images/{image_filename}"
    except Exception as e:
        print(f"Warning: Could not save image {image_filename}: {e}")
    
    return ""


def convert_to_markdown(
    filepath: str, 
    output_dir: str, 
    parser_class: Optional[type] = None
) -> str:
    """
    Convert a recipe file to Obsidian markdown format using the appropriate parser.
    
    Args:
        filepath: Path to the recipe file
        output_dir: Directory where the markdown file will be saved
        parser_class: Optional parser class to use (if not specified, will try to detect)
        
    Returns:
        Path to the created markdown file
    """
    try:
        # Make sure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # If parser_class is not provided, try to detect from file extension
        if parser_class is None:
            from cookdown.parsers import get_parser_for_extension
            ext = RecipeParser.get_file_extension(filepath)
            parser_class = get_parser_for_extension(ext)
            
            if parser_class is None:
                raise ValueError(f"No parser found for file extension: {ext}")
        
        # Parse the recipe file
        recipe_data = parser_class.parse_file(filepath)
        
        # Extract recipe information
        recipe_name = parser_class.get_recipe_name(recipe_data)
        normalized_ingredients = parser_class.get_ingredients(recipe_data)
        normalized_instructions = parser_class.get_instructions(recipe_data)
        image_data_list = parser_class.get_images(recipe_data)
        metadata = parser_class.get_metadata(recipe_data)
        
        # Create safe filename
        safe_name = re.sub(r"[^a-zA-Z0-9]", "_", recipe_name)
        safe_filename = f"{safe_name}.md"
        output_path = os.path.join(output_dir, safe_filename)
        
        # Format ingredients
        ingredients_list = format_ingredients(normalized_ingredients)
        
        # Format directions (steps)
        directions = format_instructions(normalized_instructions)
        
        # Process images
        image_paths = []
        for image_data in image_data_list:
            image_path = save_image(image_data, output_dir)
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
            "source-url": metadata.get("source_url", ""),
            "cook-time": metadata.get("cook_time", ""),
            "difficulty": metadata.get("difficulty", ""),
            "servings": metadata.get("servings", ""),
            "ingredients": ingredients_list,
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
        md_content.append(f"\n# {recipe_name}")
        md_content.append("\n## Directions")
        md_content.append(directions)
        md_content.append("\n## Notes")
        md_content.append(metadata.get("notes", ""))
        md_content.append("\n## Nutrition Info")
        md_content.append(metadata.get("nutrition_info", ""))
        
        # Write the markdown file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        
        print(f"Converted {filepath} to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error converting {filepath}: {e}")
        raise 