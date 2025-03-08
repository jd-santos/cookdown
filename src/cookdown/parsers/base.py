"""
Base class for recipe parsers.

This module defines the base interface that all recipe parsers must implement.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path


class RecipeParser(ABC):
    """Base class for recipe file parsers."""
    
    @classmethod
    @abstractmethod
    def parse_file(cls, filepath: str) -> Dict[str, Any]:
        """
        Parse a recipe file into a standardized dictionary format.
        
        Args:
            filepath: Path to the recipe file
            
        Returns:
            Dictionary containing the standardized recipe data
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_recipe_name(cls, recipe_data: Dict[str, Any]) -> str:
        """
        Extract the recipe name from the parsed data.
        
        Args:
            recipe_data: Parsed recipe data
            
        Returns:
            Recipe name
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_ingredients(cls, recipe_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract the list of ingredients from the parsed data.
        
        Args:
            recipe_data: Parsed recipe data
            
        Returns:
            List of ingredient dictionaries
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_instructions(cls, recipe_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract the list of instructions from the parsed data.
        
        Args:
            recipe_data: Parsed recipe data
            
        Returns:
            List of instruction dictionaries
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_images(cls, recipe_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract image data from the parsed data.
        
        Args:
            recipe_data: Parsed recipe data
            
        Returns:
            List of image dictionaries, each containing at least 'data' and 'filename' keys
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_metadata(cls, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from the parsed data.
        
        Args:
            recipe_data: Parsed recipe data
            
        Returns:
            Dictionary of metadata values
        """
        pass
    
    @staticmethod
    def get_file_extension(filepath: str) -> str:
        """
        Get the file extension from a filepath.
        
        Args:
            filepath: Path to the file
            
        Returns:
            File extension without the dot
        """
        return os.path.splitext(filepath)[1][1:] 