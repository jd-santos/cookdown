"""
Tests for the conversion functionality.

These tests verify that the system correctly converts recipe files to
Obsidian-compatible markdown format.
"""

import os
import json
import shutil
import tempfile
import pytest
from pathlib import Path

from cookdown import convert, formatter
from cookdown.parsers import crumb


@pytest.fixture
def sample_recipe_setup():
    """Set up test environment with sample recipe data."""
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    input_dir = os.path.join(temp_dir, "input")
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Create sample recipe data
    sample_recipe = {
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
    
    sample_recipe_path = os.path.join(input_dir, "test_recipe.crumb")
    with open(sample_recipe_path, "w", encoding="utf-8") as f:
        json.dump(sample_recipe, f)
    
    # Return test data to the test function
    yield {
        "temp_dir": temp_dir,
        "input_dir": input_dir,
        "output_dir": output_dir,
        "sample_recipe": sample_recipe,
        "sample_recipe_path": sample_recipe_path
    }
    
    # Clean up after test
    shutil.rmtree(temp_dir)


def test_read_crumb_file(sample_recipe_setup):
    """Test reading a .crumb file."""
    result = crumb.CrumbParser.parse_file(sample_recipe_setup["sample_recipe_path"])
    assert result["name"] == "Test Recipe"
    assert len(result["ingredients"]) == 2


def test_format_ingredients(sample_recipe_setup):
    """Test formatting ingredients."""
    normalized_ingredients = crumb.CrumbParser.get_ingredients(sample_recipe_setup["sample_recipe"])
    result = formatter.format_ingredients(normalized_ingredients)
    
    assert len(result) == 2
    assert "2 cups flour" in result
    assert "1 tablespoon sugar" in result


def test_format_steps(sample_recipe_setup):
    """Test formatting recipe steps."""
    normalized_instructions = crumb.CrumbParser.get_instructions(sample_recipe_setup["sample_recipe"])
    result = formatter.format_instructions(normalized_instructions)
    
    expected_lines = [
        "### Preparation",
        "1. Mix the ingredients",
        "1. Bake at 350°F for 30 minutes"
    ]
    
    for line in expected_lines:
        assert line in result


def test_convert_crumb_to_md(sample_recipe_setup):
    """Test converting a .crumb file to markdown."""
    # Convert the test recipe
    formatter.convert_to_markdown(
        sample_recipe_setup["sample_recipe_path"], 
        sample_recipe_setup["output_dir"],
        crumb.CrumbParser
    )
    
    # Check that the output file exists
    expected_output = os.path.join(sample_recipe_setup["output_dir"], "Test_Recipe.md")
    assert os.path.exists(expected_output)
    
    # Verify content of the output file
    with open(expected_output, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check that important sections exist
    assert "---" in content  # YAML frontmatter
    assert "tags:" in content
    assert "ingredients:" in content
    assert "## Directions" in content
    assert "Mix the ingredients" in content
    assert "Bake at 350°F for 30 minutes" in content


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