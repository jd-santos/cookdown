"""
Tests for the Paprika parser and extractor functionality.

These tests verify that the system correctly processes Paprika recipe files
in both .paprikarecipe and .paprikarecipes formats.
"""

import os
import json
import gzip
import shutil
import tempfile
import zipfile
import pytest
from pathlib import Path

from cookdown import convert, formatter
from cookdown.parsers import paprika
from cookdown.parsers.paprika import PaprikaParser
import extract_paprika


@pytest.fixture
def sample_paprika_recipe_data():
    """Return sample Paprika recipe data."""
    return {
        "name": "Test Paprika Recipe",
        "ingredients": "2 cups flour\n1 tablespoon sugar\n1/2 teaspoon salt",
        "directions": "PREPARATION:\nMix the ingredients.\nBake at 350°F for 30 minutes.",
        "notes": "This is a test recipe.",
        "nutritional_info": "Test nutrition info",
        "source": "https://example.com/test",
        "cook_time": "30 minutes",
        "servings": "2",
        "photo_data": None,  # In real data this would be base64 encoded
        "photo": "https://example.com/recipe.jpg",
        "categories": ["Dessert", "Baking"],
        "rating": 5,
        "difficulty": "Easy",
        "created": "2023-01-01T12:00:00Z",
        "uid": "01234567-89AB-CDEF-0123-456789ABCDEF"
    }


@pytest.fixture
def paprika_recipe_file(tmp_path, sample_paprika_recipe_data):
    """Create a .paprikarecipe file for testing."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    # Create a .paprikarecipe file (gzipped JSON)
    recipe_path = input_dir / "test_recipe.paprikarecipe"
    
    # Convert the sample data to JSON and then gzip it
    json_data = json.dumps(sample_paprika_recipe_data).encode('utf-8')
    with gzip.open(recipe_path, 'wb') as f:
        f.write(json_data)
    
    return {
        "temp_dir": tmp_path,
        "input_dir": input_dir,
        "recipe_path": recipe_path,
        "recipe_data": sample_paprika_recipe_data
    }


@pytest.fixture
def paprika_recipes_archive(tmp_path, sample_paprika_recipe_data):
    """Create a .paprikarecipes archive (ZIP with multiple .paprikarecipe files)."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    # First create two .paprikarecipe files
    recipe_data1 = sample_paprika_recipe_data
    recipe_data2 = dict(sample_paprika_recipe_data)
    recipe_data2["name"] = "Second Test Recipe"
    
    # Convert the sample data to JSON and then gzip it
    json_data1 = json.dumps(recipe_data1).encode('utf-8')
    json_data2 = json.dumps(recipe_data2).encode('utf-8')
    
    # Create a temporary directory to store the files before zipping
    temp_files_dir = tmp_path / "temp_files"
    temp_files_dir.mkdir()
    
    recipe_path1 = temp_files_dir / "test_recipe1.paprikarecipe"
    recipe_path2 = temp_files_dir / "test_recipe2.paprikarecipe"
    
    with gzip.open(recipe_path1, 'wb') as f:
        f.write(json_data1)
    
    with gzip.open(recipe_path2, 'wb') as f:
        f.write(json_data2)
    
    # Create a .paprikarecipes archive (ZIP file)
    archive_path = input_dir / "test_recipes.paprikarecipes"
    
    with zipfile.ZipFile(archive_path, 'w') as zip_file:
        zip_file.write(recipe_path1, arcname=recipe_path1.name)
        zip_file.write(recipe_path2, arcname=recipe_path2.name)
    
    return {
        "temp_dir": tmp_path,
        "input_dir": input_dir,
        "archive_path": archive_path,
        "recipe_files": [recipe_path1, recipe_path2],
        "recipe_data": [recipe_data1, recipe_data2]
    }


def test_paprika_parser_file_extraction(paprika_recipe_file):
    """Test that the PaprikaParser correctly extracts data from a .paprikarecipe file."""
    # Parse the .paprikarecipe file
    result = PaprikaParser.parse_file(str(paprika_recipe_file["recipe_path"]))
    
    # Verify the parsed data
    assert result["name"] == "Test Paprika Recipe"
    assert "ingredients" in result
    assert "directions" in result
    assert result["notes"] == "This is a test recipe."


def test_paprika_parser_archive_extraction(paprika_recipes_archive):
    """Test that the PaprikaParser correctly extracts data from a .paprikarecipes archive."""
    # Parse the .paprikarecipes archive
    result = PaprikaParser.parse_file(str(paprika_recipes_archive["archive_path"]))
    
    # Verify that the parser returns data from the first recipe in the archive
    assert "name" in result
    assert "ingredients" in result
    assert "directions" in result


def test_paprika_get_recipe_name(sample_paprika_recipe_data):
    """Test getting the recipe name from Paprika data."""
    name = PaprikaParser.get_recipe_name(sample_paprika_recipe_data)
    assert name == "Test Paprika Recipe"


def test_paprika_get_ingredients(sample_paprika_recipe_data):
    """Test getting ingredients from Paprika data."""
    ingredients = PaprikaParser.get_ingredients(sample_paprika_recipe_data)
    
    # Check that we have the expected number of ingredients
    assert len(ingredients) == 3
    
    # Check format of normalized ingredients
    assert ingredients[0]["text"] == "2 cups flour"
    assert ingredients[1]["text"] == "1 tablespoon sugar"
    assert ingredients[2]["text"] == "1/2 teaspoon salt"


def test_paprika_get_instructions(sample_paprika_recipe_data):
    """Test getting instructions from Paprika data."""
    instructions = PaprikaParser.get_instructions(sample_paprika_recipe_data)
    
    # Check that we have the expected number of instructions
    assert len(instructions) == 3
    
    # Check if section headers are properly identified
    assert instructions[0]["isSection"] == True
    assert instructions[0]["text"] == "PREPARATION:"
    
    # Check regular instructions
    assert instructions[1]["isSection"] == False
    assert instructions[1]["text"] == "Mix the ingredients."


def test_paprika_get_metadata(sample_paprika_recipe_data):
    """Test getting metadata from Paprika data."""
    metadata = PaprikaParser.get_metadata(sample_paprika_recipe_data)
    
    # Check essential metadata fields
    assert metadata["source"] == "https://example.com/test"
    assert metadata["servings"] == "2"
    assert "cook_time" in metadata
    assert "categories" in metadata


def test_extract_paprika_single_file(paprika_recipe_file, tmp_path):
    """Test the extract_paprika.py functionality for a single file."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Extract the .paprikarecipe file to JSON
    json_path = extract_paprika.extract_paprikarecipe_to_json(
        str(paprika_recipe_file["recipe_path"]), 
        str(output_dir)
    )
    
    # Verify the JSON file was created
    assert os.path.exists(json_path)
    
    # Verify the JSON content
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        assert json_data["name"] == "Test Paprika Recipe"


def test_extract_paprika_archive(paprika_recipes_archive, tmp_path):
    """Test the extract_paprika.py functionality for a .paprikarecipes archive."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    intermediate_dir = tmp_path / "intermediate"
    intermediate_dir.mkdir()
    
    # Extract the .paprikarecipes archive
    extracted_files = extract_paprika.extract_paprikarecipes_archive(
        str(paprika_recipes_archive["archive_path"]), 
        str(intermediate_dir)
    )
    
    # Verify extraction
    assert len(extracted_files) == 2
    
    # Test extraction to JSON
    for recipe_file in extracted_files:
        json_path = extract_paprika.extract_paprikarecipe_to_json(recipe_file, str(output_dir))
        assert os.path.exists(json_path)
        
        # Verify JSON content
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            assert "name" in json_data
            assert "ingredients" in json_data


def test_process_directory(paprika_recipes_archive, tmp_path):
    """Test processing a directory with Paprika files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Process the directory
    stats = extract_paprika.process_directory(
        str(paprika_recipes_archive["input_dir"]),
        str(output_dir),
        keep_intermediate=True
    )
    
    # Verify processing stats
    assert len(stats["archives_processed"]) == 1
    assert len(stats["json_files_created"]) == 2
    
    # Check that the output files exist
    json_files = list(Path(output_dir).glob("*.json"))
    assert len(json_files) == 2


def test_convert_paprika_to_md(paprika_recipe_file, tmp_path):
    """Test end-to-end conversion of a Paprika recipe to markdown."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Convert the recipe
    result = convert.convert_recipe_file(
        str(paprika_recipe_file["recipe_path"]),
        str(output_dir)
    )
    
    # Verify conversion
    assert result["success"] == True
    assert os.path.exists(result["output_path"])
    
    # Check the content of the markdown file
    with open(result["output_path"], 'r', encoding='utf-8') as f:
        content = f.read()
        assert "# Test Paprika Recipe" in content
        assert "## Ingredients" in content
        assert "## Instructions" in content
        assert "## Notes" in content 