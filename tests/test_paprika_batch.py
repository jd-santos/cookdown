"""
Tests for batch processing of Paprika recipe files.

These tests verify that the batch processing system correctly handles
Paprika recipe files in both .paprikarecipe and .paprikarecipes formats.
"""

import os
import json
import gzip
import zipfile
import pytest
import shutil
from pathlib import Path

from cookdown import batch
from cookdown.parsers import paprika


@pytest.fixture
def batch_paprika_setup(tmp_path):
    """Set up test environment with multiple Paprika recipe files."""
    # Create directories
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    
    # Create sample recipe data
    sample_recipes = [
        {
            "name": f"Paprika Recipe {i}",
            "ingredients": f"{i} cups flour\n{i} tablespoon sugar",
            "directions": f"Step {i}. Mix ingredients.\nStep {i+1}. Bake at 350°F.",
            "notes": f"Test recipe {i}",
            "servings": f"{i}",
            "source": f"https://example.com/recipe{i}"
        }
        for i in range(1, 4)  # Create 3 recipes
    ]
    
    # Create individual .paprikarecipe files
    recipe_files = []
    for i, recipe_data in enumerate(sample_recipes):
        recipe_path = input_dir / f"recipe{i+1}.paprikarecipe"
        json_data = json.dumps(recipe_data).encode('utf-8')
        with gzip.open(recipe_path, 'wb') as f:
            f.write(json_data)
        recipe_files.append(recipe_path)
    
    # Create a .paprikarecipes archive with two more recipes
    archive_recipes = [
        {
            "name": f"Archive Recipe {i}",
            "ingredients": f"{i} cups flour\n{i} tablespoon sugar",
            "directions": f"Step {i}. Mix ingredients.\nStep {i+1}. Bake at 350°F.",
            "notes": f"Archive recipe {i}",
            "servings": f"{i}",
            "source": f"https://example.com/archive{i}"
        }
        for i in range(1, 3)  # Create 2 archive recipes
    ]
    
    # Temporary directory for creating archive files
    temp_files_dir = tmp_path / "temp_files"
    temp_files_dir.mkdir()
    
    archive_files = []
    for i, recipe_data in enumerate(archive_recipes):
        recipe_path = temp_files_dir / f"archive_recipe{i+1}.paprikarecipe"
        json_data = json.dumps(recipe_data).encode('utf-8')
        with gzip.open(recipe_path, 'wb') as f:
            f.write(json_data)
        archive_files.append(recipe_path)
    
    # Create the archive
    archive_path = input_dir / "recipes.paprikarecipes"
    with zipfile.ZipFile(archive_path, 'w') as zip_file:
        for file_path in archive_files:
            zip_file.write(file_path, arcname=file_path.name)
    
    # Return the test setup
    result = {
        "temp_dir": tmp_path,
        "input_dir": input_dir,
        "output_dir": output_dir,
        "recipe_files": recipe_files,
        "archive_path": archive_path,
        "archive_files": archive_files,
        "sample_recipes": sample_recipes,
        "archive_recipes": archive_recipes
    }
    
    yield result
    
    # Clean up temp files
    if temp_files_dir.exists():
        shutil.rmtree(temp_files_dir)


def test_batch_convert_paprika_files(batch_paprika_setup):
    """Test batch conversion of Paprika recipe files."""
    # Run batch conversion
    result = batch.batch_convert(
        input_dir=str(batch_paprika_setup["input_dir"]),
        output_dir=str(batch_paprika_setup["output_dir"]),
        recursive=False,
        max_workers=2
    )
    
    # We should have 5 total recipes: 3 individual files + 2 from the archive
    assert result["total"] == 5, f"Expected 5 recipes, got {result['total']}"
    assert result["successful"] == 5, f"Expected 5 successful conversions, got {result['successful']}"
    assert result["failed"] == 0, f"Expected 0 failed conversions, got {result['failed']}"
    
    # Check that output files were created
    output_files = list(Path(batch_paprika_setup["output_dir"]).glob("*.md"))
    assert len(output_files) == 5, f"Expected 5 output files, got {len(output_files)}"
    
    # Check that all recipe names are in the output files
    found_recipes = set()
    for output_file in output_files:
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for individual recipes
            for recipe in batch_paprika_setup["sample_recipes"]:
                if f"# {recipe['name']}" in content:
                    found_recipes.add(recipe['name'])
            # Check for archive recipes
            for recipe in batch_paprika_setup["archive_recipes"]:
                if f"# {recipe['name']}" in content:
                    found_recipes.add(recipe['name'])
    
    # All 5 recipe names should be found
    expected_names = set([r["name"] for r in batch_paprika_setup["sample_recipes"]] + 
                          [r["name"] for r in batch_paprika_setup["archive_recipes"]])
    assert found_recipes == expected_names, f"Expected recipes {expected_names}, found {found_recipes}"


def test_batch_paprika_filter_by_extension(batch_paprika_setup):
    """Test batch conversion with extension filtering."""
    # Run batch conversion with .paprikarecipe extension only
    result = batch.batch_convert(
        input_dir=str(batch_paprika_setup["input_dir"]),
        output_dir=str(batch_paprika_setup["output_dir"]),
        recursive=False,
        max_workers=2,
        extensions=["paprikarecipe"]  # Only process .paprikarecipe files
    )
    
    # We should have 3 recipes from individual files
    assert result["total"] == 3, f"Expected 3 recipes, got {result['total']}"
    assert result["successful"] == 3, f"Expected 3 successful conversions, got {result['successful']}"
    
    # Check output files
    output_files = list(Path(batch_paprika_setup["output_dir"]).glob("*.md"))
    assert len(output_files) == 3, f"Expected 3 output files, got {len(output_files)}"


def test_batch_paprika_filter_by_paprikarecipes(batch_paprika_setup):
    """Test batch conversion with .paprikarecipes extension only."""
    # Run batch conversion with .paprikarecipes extension only
    result = batch.batch_convert(
        input_dir=str(batch_paprika_setup["input_dir"]),
        output_dir=str(batch_paprika_setup["output_dir"]),
        recursive=False,
        max_workers=2,
        extensions=["paprikarecipes"]  # Only process .paprikarecipes archives
    )
    
    # We should have 2 recipes from the archive
    assert result["total"] == 2, f"Expected 2 recipes, got {result['total']}"
    assert result["successful"] == 2, f"Expected 2 successful conversions, got {result['successful']}"
    
    # Check output files
    output_files = list(Path(batch_paprika_setup["output_dir"]).glob("*.md"))
    assert len(output_files) == 2, f"Expected 2 output files, got {len(output_files)}"


def test_batch_subprocess_mode(batch_paprika_setup):
    """Test batch conversion using subprocess mode."""
    # Run batch conversion in subprocess mode
    result = batch.batch_convert(
        input_dir=str(batch_paprika_setup["input_dir"]),
        output_dir=str(batch_paprika_setup["output_dir"]),
        recursive=False,
        max_workers=2,
        use_subprocess=True  # Use subprocess mode
    )
    
    # We should have 5 total recipes
    assert result["total"] == 5, f"Expected 5 recipes, got {result['total']}"
    assert result["successful"] == 5, f"Expected 5 successful conversions, got {result['successful']}"
    
    # Check output files
    output_files = list(Path(batch_paprika_setup["output_dir"]).glob("*.md"))
    assert len(output_files) == 5, f"Expected 5 output files, got {len(output_files)}" 