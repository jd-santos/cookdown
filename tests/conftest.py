"""
Configuration file for pytest.

This file sets up the test environment and adds the src directory to the Python path.
"""

import os
import sys
import json
import base64
import pytest
from pathlib import Path

# Add the src directory to the Python path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_dir)


@pytest.fixture
def sample_crumb_data():
    """Return a sample recipe data dictionary for use in tests."""
    return {
        "name": "Sample Test Recipe",
        "ingredients": [
            {
                "order": 0,
                "ingredient": {"name": "Sample Ingredient 1"},
                "quantity": {"amount": 2, "quantityType": "cup"}
            },
            {
                "order": 1,
                "ingredient": {"name": "Sample Ingredient 2"},
                "quantity": {"amount": 1, "quantityType": "teaspoon"}
            }
        ],
        "steps": [
            {
                "order": 0,
                "step": "**Preparation**\nFirst sample step",
                "isSection": False
            },
            {
                "order": 1,
                "step": "Second sample step",
                "isSection": False
            },
            {
                "order": 2,
                "step": "**Cooking**\nThird sample step",
                "isSection": False
            }
        ],
        "notes": "Sample notes for testing",
        "neutritionalInfo": "Sample nutritional info",
        "webLink": "https://example.com/sample",
        "cookingDuration": 45,
        "serves": 4,
        "images": []
    }


@pytest.fixture
def sample_crumb_file(tmp_path, sample_crumb_data):
    """Create a temporary .crumb file from the sample data."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    recipe_path = input_dir / "sample_recipe.crumb"
    recipe_path.write_text(json.dumps(sample_crumb_data))
    
    return {
        "path": recipe_path,
        "content": sample_crumb_data,
        "tmp_dir": tmp_path
    }


@pytest.fixture
def sample_base64_image():
    """
    Return a small valid base64-encoded image for testing.
    
    This is a 1x1 pixel transparent PNG image.
    """
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="


@pytest.fixture
def sample_crumb_with_image(tmp_path, sample_crumb_data, sample_base64_image):
    """Create a temporary .crumb file with a base64-encoded image."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    # Add the image to the recipe data
    sample_data_with_image = sample_crumb_data.copy()
    sample_data_with_image["images"] = [sample_base64_image]
    
    recipe_path = input_dir / "recipe_with_image.crumb"
    recipe_path.write_text(json.dumps(sample_data_with_image))
    
    return {
        "path": recipe_path,
        "content": sample_data_with_image,
        "tmp_dir": tmp_path
    }


@pytest.fixture
def expected_output_structure():
    """Sample structure of the expected output markdown file."""
    return {
        "frontmatter": [
            "---",
            "food-labels:",
            "created:",
            "updated:",
            "tags:",
            "  - food/recipe",
            "photos:",
            "source:",
            "source-url: https://example.com/sample",
            "cook-time: 45 minutes",
            "difficulty:",
            "servings: 4",
            "ingredients:",
            "  - 2 cups Sample Ingredient 1",
            "  - 1 teaspoon Sample Ingredient 2",
            "---"
        ],
        "sections": [
            "## Directions",
            "### Preparation",
            "1. First sample step",
            "1. Second sample step",
            "### Cooking",
            "1. Third sample step",
            "## Notes",
            "Sample notes for testing",
            "## Nutrition Info",
            "Sample nutritional info"
        ]
    } 