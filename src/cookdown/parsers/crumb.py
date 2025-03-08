"""
Parser for Crouton .crumb recipe files.

This module provides a parser for Crouton's .crumb JSON recipe format.
"""

import json
import base64
import re
from typing import Dict, List, Any

from .base import RecipeParser
from . import register_parser


class CrumbParser(RecipeParser):
    """Parser for Crouton .crumb recipe files."""
    
    @classmethod
    def parse_file(cls, filepath: str) -> Dict[str, Any]:
        """
        Parse a .crumb file into a standardized dictionary format.
        
        Args:
            filepath: Path to the .crumb file
            
        Returns:
            Dictionary containing the parsed recipe data
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.loads(f.read())
    
    @classmethod
    def get_recipe_name(cls, recipe_data: Dict[str, Any]) -> str:
        """
        Extract the recipe name from the parsed data.
        
        Args:
            recipe_data: Parsed recipe data
            
        Returns:
            Recipe name
        """
        return recipe_data.get("name", "Unnamed Recipe")
    
    @classmethod
    def get_ingredients(cls, recipe_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and normalize the list of ingredients from the parsed data.
        
        Args:
            recipe_data: Parsed recipe data
            
        Returns:
            List of normalized ingredient dictionaries
        """
        raw_ingredients = recipe_data.get("ingredients", [])
        normalized_ingredients = []
        
        # Sort ingredients by order
        sorted_ingredients = sorted(raw_ingredients, key=lambda x: x.get("order", 0))
        
        for item in sorted_ingredients:
            ingredient_name = item.get("ingredient", {}).get("name", "")
            quantity_info = item.get("quantity", {})
            amount = quantity_info.get("amount", "")
            quantity_type = quantity_info.get("quantityType", "")
            
            normalized_ingredients.append({
                "name": ingredient_name,
                "amount": amount,
                "unit": quantity_type,
                "raw": item  # Keep the raw data for format-specific details
            })
        
        return normalized_ingredients
    
    @classmethod
    def get_instructions(cls, recipe_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and normalize the list of instructions from the parsed data.
        
        Args:
            recipe_data: Parsed recipe data
            
        Returns:
            List of normalized instruction dictionaries
        """
        raw_steps = recipe_data.get("steps", [])
        normalized_steps = []
        
        # Sort steps by order
        sorted_steps = sorted(raw_steps, key=lambda x: x.get("order", 0))
        
        for step in sorted_steps:
            step_text = step.get("step", "")
            is_section = step.get("isSection", False)
            
            # Check if the step starts with a section marker
            section_name = None
            section_pattern = r"^\*\*(.*?)\*\*\s*"
            section_match = re.match(section_pattern, step_text)
            
            if section_match:
                section_name = section_match.group(1)
                step_text = re.sub(section_pattern, "", step_text)
            
            normalized_steps.append({
                "text": step_text,
                "is_section": is_section or section_name is not None,
                "section_name": section_name,
                "raw": step  # Keep the raw data for format-specific details
            })
        
        return normalized_steps
    
    @classmethod
    def get_images(cls, recipe_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract image data from the parsed data.
        
        Args:
            recipe_data: Parsed recipe data
            
        Returns:
            List of image dictionaries with 'data' and 'filename' keys
        """
        images = []
        recipe_name = cls.get_recipe_name(recipe_data)
        safe_name = re.sub(r"[^a-zA-Z0-9]", "_", recipe_name)
        
        for i, image_data in enumerate(recipe_data.get("images", [])):
            if image_data and "truncated for LLM context" not in image_data:
                images.append({
                    "data": image_data,
                    "filename": f"{safe_name}_{i}.jpg",
                    "format": "base64"
                })
        
        return images
    
    @classmethod
    def get_metadata(cls, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from the parsed data.
        
        Args:
            recipe_data: Parsed recipe data
            
        Returns:
            Dictionary of metadata values
        """
        return {
            "source_url": recipe_data.get("webLink", ""),
            "cook_time": f"{recipe_data.get('cookingDuration', 0)} minutes",
            "servings": recipe_data.get("serves", ""),
            "notes": recipe_data.get("notes", ""),
            "nutrition_info": recipe_data.get("neutritionalInfo", ""),
            "prep_time": f"{recipe_data.get('prepDuration', 0)} minutes",
            "total_time": f"{recipe_data.get('prepDuration', 0) + recipe_data.get('cookingDuration', 0)} minutes",
            "rating": recipe_data.get("rating", 0),
            "difficulty": "",  # Not directly available in .crumb format
        }


# Register this parser for the .crumb extension
register_parser(["crumb"], CrumbParser) 