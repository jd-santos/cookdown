"""
Recipe parsers for different file formats.

This module provides a registry of parsers for different recipe file formats.
"""

from typing import Dict, Type, List, Optional
from .base import RecipeParser

# Registry of parsers by file extension
_PARSERS: Dict[str, Type[RecipeParser]] = {}

def register_parser(extensions: List[str], parser_class: Type[RecipeParser]) -> None:
    """
    Register a parser class for the given file extensions.
    
    Args:
        extensions: List of file extensions this parser handles (without the dot)
        parser_class: The parser class to register
    """
    for ext in extensions:
        _PARSERS[ext.lower()] = parser_class

def get_parser_for_extension(extension: str) -> Optional[Type[RecipeParser]]:
    """
    Get the appropriate parser class for a file extension.
    
    Args:
        extension: File extension (without the dot)
        
    Returns:
        Parser class for the extension, or None if no parser is registered
    """
    return _PARSERS.get(extension.lower())

def get_supported_extensions() -> List[str]:
    """
    Get a list of all supported file extensions.
    
    Returns:
        List of supported file extensions
    """
    return list(_PARSERS.keys())

# Import all parsers to register them
from .crumb import CrumbParser

# This makes the imports available directly from the parsers module
__all__ = [
    'RecipeParser',
    'register_parser',
    'get_parser_for_extension',
    'get_supported_extensions',
    'CrumbParser',
] 