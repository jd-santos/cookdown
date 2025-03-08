"""
Tests for the conversion functionality.

These tests verify that the system correctly converts recipe files to
Obsidian-compatible markdown format.
"""

import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pytest

from cookdown import convert, formatter
from cookdown.parsers import crumb


class TestConvert(unittest.TestCase):
    """Test cases for the conversion functionality."""
    
    def setUp(self):
        """Set up test environment with sample recipe data."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create sample recipe data
        self.sample_recipe = {
            "name": "Test Recipe",
            "ingredients": [
                {
                    "order": 1,
                    "ingredient": {"name": "flour"},
                    "quantity": {"amount": 2, "quantityType": "cup"}
                },
                {
                    "order": 2,
                    "ingredient": {"name": "sugar"},
                    "quantity": {"amount": 1, "quantityType": "tablespoon"}
                }
            ],
            "steps": [
                {
                    "order": 1,
                    "step": "**Preparation**",
                    "isSection": True
                },
                {
                    "order": 2,
                    "step": "Mix the ingredients",
                    "isSection": False
                },
                {
                    "order": 3,
                    "step": "Bake at 350°F for 30 minutes",
                    "isSection": False
                }
            ],
            "notes": "This is a test recipe.",
            "neutritionalInfo": "Test nutrition info",
            "webLink": "https://example.com/test",
            "cookingDuration": 30,
            "serves": 2,
            "images": []
        }
        
        self.sample_recipe_path = os.path.join(self.input_dir, "test_recipe.crumb")
        with open(self.sample_recipe_path, "w", encoding="utf-8") as f:
            json.dump(self.sample_recipe, f)
    
    def tearDown(self):
        """Clean up temporary directories after testing."""
        shutil.rmtree(self.temp_dir)

    def test_read_crumb_file(self):
        """Test reading a .crumb file."""
        result = crumb.CrumbParser.parse_file(self.sample_recipe_path)
        self.assertEqual(result["name"], "Test Recipe")
        self.assertEqual(len(result["ingredients"]), 2)

    def test_format_ingredients(self):
        """Test formatting ingredients."""
        normalized_ingredients = crumb.CrumbParser.get_ingredients(self.sample_recipe)
        result = formatter.format_ingredients(normalized_ingredients)
        
        self.assertEqual(len(result), 2)
        self.assertIn("2 cups flour", result)
        self.assertIn("1 tablespoon sugar", result)

    def test_format_steps(self):
        """Test formatting recipe steps."""
        normalized_instructions = crumb.CrumbParser.get_instructions(self.sample_recipe)
        result = formatter.format_instructions(normalized_instructions)
        
        expected_lines = [
            "### Preparation",
            "1. Mix the ingredients",
            "1. Bake at 350°F for 30 minutes"
        ]
        
        for line in expected_lines:
            self.assertIn(line, result)

    def test_convert_crumb_to_md(self):
        """Test converting a .crumb file to markdown."""
        # Convert the test recipe
        formatter.convert_to_markdown(
            self.sample_recipe_path, 
            self.output_dir,
            crumb.CrumbParser
        )
        
        # Check that the output file exists
        expected_output = os.path.join(self.output_dir, "Test_Recipe.md")
        self.assertTrue(os.path.exists(expected_output))
        
        # Verify content of the output file
        with open(expected_output, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Check that important sections exist
        self.assertIn("---", content)  # YAML frontmatter
        self.assertIn("tags:", content)
        self.assertIn("ingredients:", content)
        self.assertIn("## Directions", content)
        self.assertIn("Mix the ingredients", content)
        self.assertIn("Bake at 350°F for 30 minutes", content)


@pytest.fixture
def mock_recipe_file(tmp_path):
    """Create a mock recipe file for testing."""
    recipe_dir = tmp_path / "recipes"
    recipe_dir.mkdir()
    
    recipe_content = {
        "name": "Pytest Recipe",
        "ingredients": [
            {
                "order": 1,
                "ingredient": {"name": "Pytest Ingredient"},
                "quantity": {"amount": 1, "quantityType": "cup"}
            }
        ],
        "steps": [
            {
                "order": 1,
                "step": "**Pytest Section**",
                "isSection": True
            },
            {
                "order": 2,
                "step": "Test step 1",
                "isSection": False
            }
        ],
        "notes": "Test notes",
        "neutritionalInfo": "",
        "webLink": "",
        "cookingDuration": 0,
        "serves": "",
        "images": []
    }
    
    recipe_path = recipe_dir / "pytest_recipe.crumb"
    with open(recipe_path, "w") as f:
        json.dump(recipe_content, f)
    
    return {
        "content": recipe_content,
        "path": recipe_path,
        "tmp_dir": tmp_path
    }


def test_convert_with_pytest(mock_recipe_file):
    """Test conversion using pytest fixtures."""
    output_dir = mock_recipe_file["tmp_dir"] / "output"
    output_dir.mkdir()
    
    # Convert the recipe
    formatter.convert_to_markdown(
        str(mock_recipe_file["path"]),
        str(output_dir),
        crumb.CrumbParser
    )
    
    # Check the output
    output_file = output_dir / "Pytest_Recipe.md"
    assert output_file.exists()
    
    # Verify content
    content = output_file.read_text()
    assert "Pytest Ingredient" in content
    assert "Pytest Section" in content
    assert "Test step 1" in content 