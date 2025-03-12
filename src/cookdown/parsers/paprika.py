"""
Parser for Paprika recipe files.

This module provides a parser for Paprika's .paprikarecipe format
and handles the extraction of .paprikarecipes archives.
"""

import os
import json
import gzip
import zipfile
import tempfile
import shutil
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base import RecipeParser
from . import register_parser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('paprika_parser')


class PaprikaParser(RecipeParser):
    """Parser for Paprika recipe files."""
    
    @classmethod
    def parse_file(cls, filepath: str) -> Dict[str, Any]:
        """
        Parse a .paprikarecipe file into a standardized dictionary format.
        
        This method handles both:
        - Direct .paprikarecipe files (gzipped JSON)
        - .paprikarecipes archives (ZIP files containing multiple .paprikarecipe files)
        
        Args:
            filepath: Path to the .paprikarecipe or .paprikarecipes file
            
        Returns:
            Dictionary containing the parsed recipe data
        """
        # Handle file based on extension
        ext = cls.get_file_extension(filepath)
        
        if ext == "paprikarecipe":
            # Single recipe file (gzipped JSON)
            return cls._extract_paprikarecipe(filepath)
        
        elif ext == "paprikarecipes":
            # Archive of recipes - extract all and return the first one
            # Note: For batch conversion, the main converter will find and process all files
            recipes_dir = cls._extract_paprikarecipes_archive(filepath)
            
            # Find all extracted .paprikarecipe files
            recipe_files = list(Path(recipes_dir).glob("*.paprikarecipe"))
            if not recipe_files:
                raise ValueError(f"No recipe files found in archive: {filepath}")
            
            # Parse the first recipe file (batch processing will handle the rest)
            recipe_data = cls._extract_paprikarecipe(str(recipe_files[0]))
            
            # Clean up temporary directory
            shutil.rmtree(recipes_dir)
            
            return recipe_data
    
    @classmethod
    def _extract_paprikarecipes_archive(cls, archive_path: str) -> str:
        """
        Extract a .paprikarecipes archive to a temporary directory.
        
        Args:
            archive_path: Path to the .paprikarecipes archive
            
        Returns:
            Path to the directory containing extracted .paprikarecipe files
        """
        logger.info(f"Extracting archive: {archive_path}")
        
        # Create a temporary directory for extraction
        temp_dir = tempfile.mkdtemp(prefix="paprika_")
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Get list of files in the archive
                recipe_files = [f for f in zip_ref.namelist() if f.endswith('.paprikarecipe')]
                logger.info(f"Archive contains {len(recipe_files)} recipe files")
                
                # Extract each recipe file
                for recipe_file in recipe_files:
                    zip_ref.extract(recipe_file, temp_dir)
                    logger.debug(f"Extracted: {recipe_file}")
        except Exception as e:
            shutil.rmtree(temp_dir)
            raise ValueError(f"Failed to extract archive {archive_path}: {e}")
        
        return temp_dir
    
    @classmethod
    def _extract_paprikarecipe(cls, recipe_path: str) -> Dict[str, Any]:
        """
        Extract a single .paprikarecipe file to JSON.
        
        Args:
            recipe_path: Path to the .paprikarecipe file
            
        Returns:
            Dictionary containing the parsed JSON data
        """
        logger.debug(f"Extracting: {recipe_path}")
        
        try:
            # Open and decompress the gzipped file
            with gzip.open(recipe_path, 'rb') as f_in:
                # Read and decode the JSON data
                json_data = f_in.read().decode('utf-8')
                
                # Parse JSON
                recipe_data = json.loads(json_data)
                return recipe_data
                
        except Exception as e:
            raise ValueError(f"Failed to extract {recipe_path}: {e}")
    
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
        # Get ingredients text and split by newlines
        ingredients_text = recipe_data.get("ingredients", "")
        ingredient_lines = ingredients_text.split('\n')
        
        normalized_ingredients = []
        
        for line in ingredient_lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to parse ingredient line into amount, unit, and name
            # Most Paprika ingredients are formatted as: "1 cup flour"
            parts = line.split(' ', 2)
            
            if len(parts) >= 3 and parts[0].replace('.', '', 1).isdigit():
                # Found amount and unit
                amount = parts[0]
                unit = parts[1]
                name = parts[2]
            elif len(parts) >= 2 and parts[0].replace('.', '', 1).isdigit():
                # Found amount but no unit
                amount = parts[0]
                unit = ""
                name = parts[1]
            else:
                # No clear amount/unit structure
                amount = ""
                unit = ""
                name = line
            
            normalized_ingredients.append({
                "name": name,
                "amount": amount,
                "unit": unit,
                "raw": line  # Keep the raw line for reference
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
        # Get directions text and split by newlines
        directions_text = recipe_data.get("directions", "")
        direction_lines = directions_text.split('\n')
        
        normalized_steps = []
        
        # Process each line as a step
        for line in direction_lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if the line looks like a section header
            is_section = False
            section_name = None
            
            # Paprika often has section headers in all caps or with trailing colons
            if line.isupper() or line.endswith(':'):
                is_section = True
                section_name = line.rstrip(':')
                
                # Add as a section header
                normalized_steps.append({
                    "text": "",
                    "is_section": True,
                    "section_name": section_name,
                    "raw": line
                })
            else:
                # Regular instruction step
                normalized_steps.append({
                    "text": line,
                    "is_section": False,
                    "section_name": None,
                    "raw": line
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
        safe_name = recipe_name.replace(' ', '_').replace('/', '_')
        
        # Paprika stores images in the 'photo_data' field as base64
        photo_data = recipe_data.get("photo_data", "")
        if photo_data:
            images.append({
                "data": photo_data,
                "filename": f"{safe_name}.jpg",
                "format": "base64"
            })
        
        # Paprika may also have a 'photo' field with a URL
        photo_url = recipe_data.get("photo", "")
        if photo_url and not photo_data:
            # Just store the URL reference
            images.append({
                "url": photo_url,
                "filename": f"{safe_name}.jpg",
                "format": "url"
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
        # Extract categories as tags
        categories = recipe_data.get("categories", "").split(',')
        tags = [cat.strip() for cat in categories if cat.strip()]
        
        # Calculate total time
        prep_time = int(recipe_data.get("prep_time", "0") or "0")
        cook_time = int(recipe_data.get("cook_time", "0") or "0")
        total_time = prep_time + cook_time
        
        return {
            "source_url": recipe_data.get("source_url", ""),
            "cook_time": f"{cook_time} minutes" if cook_time else "",
            "prep_time": f"{prep_time} minutes" if prep_time else "",
            "total_time": f"{total_time} minutes" if total_time else "",
            "servings": recipe_data.get("servings", ""),
            "notes": recipe_data.get("notes", ""),
            "nutrition_info": recipe_data.get("nutritional_info", ""),
            "rating": recipe_data.get("rating", 0),
            "difficulty": recipe_data.get("difficulty", ""),
            "tags": tags,
            "source": recipe_data.get("source", ""),
            "created": recipe_data.get("created", ""),
            "uid": recipe_data.get("uid", ""),
        }


# Register this parser for Paprika file extensions
register_parser(["paprikarecipe", "paprikarecipes"], PaprikaParser) 