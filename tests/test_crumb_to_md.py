"""
Tests for the crumb_to_md.py script.

These tests verify that the script correctly converts .crumb files to
Obsidian-compatible markdown format.
"""

import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pytest

import crumb_to_md


class TestCrumbToMd(unittest.TestCase):
    """Test cases for the crumb_to_md.py script."""

    def setUp(self):
        """Set up temporary directories for testing."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        # Copy test data to temporary input directory
        test_data_dir = os.path.join(os.path.dirname(__file__), "data")
        
        # Create a sample test crumb file
        self.sample_recipe = {
            "name": "Test Recipe",
            "ingredients": [
                {
                    "order": 0,
                    "ingredient": {"name": "Test Ingredient 1"},
                    "quantity": {"amount": 2, "quantityType": "cup"}
                },
                {
                    "order": 1,
                    "ingredient": {"name": "Test Ingredient 2"},
                    "quantity": {"amount": 1, "quantityType": "teaspoon"}
                }
            ],
            "steps": [
                {
                    "order": 0,
                    "step": "**Section 1**\nFirst test step",
                    "isSection": False
                },
                {
                    "order": 1,
                    "step": "Second test step",
                    "isSection": False
                }
            ],
            "notes": "Test notes",
            "neutritionalInfo": "Test nutritional info",
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
        result = crumb_to_md.read_crumb_file(self.sample_recipe_path)
        self.assertEqual(result["name"], "Test Recipe")
        self.assertEqual(len(result["ingredients"]), 2)
        self.assertEqual(len(result["steps"]), 2)

    def test_format_ingredients(self):
        """Test formatting ingredients."""
        ingredients = self.sample_recipe["ingredients"]
        result = crumb_to_md.format_ingredients(ingredients)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "2 cups Test Ingredient 1")
        self.assertEqual(result[1], "1 teaspoon Test Ingredient 2")

    def test_format_steps(self):
        """Test formatting recipe steps."""
        steps = self.sample_recipe["steps"]
        result = crumb_to_md.format_steps(steps)
        
        expected_lines = [
            "### Section 1",
            "1. First test step",
            "1. Second test step"
        ]
        
        self.assertEqual(result.split("\n"), expected_lines)

    def test_convert_crumb_to_md(self):
        """Test converting a .crumb file to markdown."""
        # Convert the test recipe
        crumb_to_md.convert_crumb_to_md(self.sample_recipe_path, self.output_dir)
        
        # Check that the output file exists
        output_path = os.path.join(self.output_dir, "Test Recipe.md")
        self.assertTrue(os.path.exists(output_path))
        
        # Read the output file
        with open(output_path, "r", encoding="utf-8") as f:
            output_content = f.read()
        
        # Check that key elements are in the output
        self.assertIn("## Directions", output_content)
        self.assertIn("### Section 1", output_content)
        self.assertIn("1. First test step", output_content)
        self.assertIn("1. Second test step", output_content)
        self.assertIn("## Notes", output_content)
        self.assertIn("Test notes", output_content)
        self.assertIn("## Nutrition Info", output_content)
        self.assertIn("Test nutritional info", output_content)
        
        # Check YAML frontmatter
        self.assertIn("ingredients:", output_content)
        self.assertIn("  - 2 cups Test Ingredient 1", output_content)
        self.assertIn("  - 1 teaspoon Test Ingredient 2", output_content)
        self.assertIn("cook-time: 30 minutes", output_content)
        self.assertIn("servings: 2", output_content)
        self.assertIn("source-url: https://example.com/test", output_content)


@pytest.fixture
def mock_recipe_file(tmp_path):
    """Create a mock recipe file for testing."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    recipe = {
        "name": "Pytest Recipe",
        "ingredients": [
            {
                "order": 0,
                "ingredient": {"name": "Pytest Ingredient"},
                "quantity": {"amount": 1, "quantityType": "unit"}
            }
        ],
        "steps": [
            {
                "order": 0,
                "step": "Pytest Step",
                "isSection": False
            }
        ],
        "notes": "Pytest Notes",
        "neutritionalInfo": "",
        "webLink": "",
        "cookingDuration": 0,
        "serves": 1,
        "images": []
    }
    
    recipe_path = input_dir / "pytest_recipe.crumb"
    recipe_path.write_text(json.dumps(recipe))
    
    return {
        "path": recipe_path,
        "content": recipe,
        "tmp_dir": tmp_path
    }


def test_convert_with_pytest(mock_recipe_file):
    """Test conversion using pytest fixtures."""
    output_dir = mock_recipe_file["tmp_dir"] / "output"
    output_dir.mkdir()
    
    # Convert the recipe
    crumb_to_md.convert_crumb_to_md(str(mock_recipe_file["path"]), str(output_dir))
    
    # Check the output
    output_file = output_dir / "Pytest Recipe.md"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "Pytest Ingredient" in content
    assert "Pytest Step" in content
    assert "Pytest Notes" in content 