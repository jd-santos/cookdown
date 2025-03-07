"""
Tests for image handling functionality in the recipe converter.

These tests specifically focus on the base64 image decoding and saving
functionality, which is a key feature of the converter.
"""

import os
import json
import pytest
from pathlib import Path

import crumb_to_md


def test_save_image(sample_base64_image, tmp_path):
    """Test saving a base64-encoded image to a file."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Save the test image
    image_path = crumb_to_md.save_image(
        sample_base64_image, 
        "Test_Recipe", 
        0, 
        str(output_dir)
    )
    
    # Check that the image file was created
    expected_path = "images/Test_Recipe_0.jpg"
    assert image_path == expected_path
    
    # Check that the file exists on disk
    full_path = output_dir / "images" / "Test_Recipe_0.jpg"
    assert full_path.exists()
    assert full_path.stat().st_size > 0  # File should not be empty


def test_save_image_invalid_base64(tmp_path):
    """Test handling of invalid base64 data."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Try to save invalid base64 data
    image_path = crumb_to_md.save_image(
        "invalid base64 data", 
        "Test_Recipe", 
        0, 
        str(output_dir)
    )
    
    # Should return empty string on error
    assert image_path == ""
    
    # Check that no file was created
    image_dir = output_dir / "images"
    if image_dir.exists():
        assert len(list(image_dir.iterdir())) == 0


def test_recipe_with_image(sample_crumb_with_image):
    """Test converting a recipe with an image."""
    # Set up paths
    input_path = sample_crumb_with_image["path"]
    output_dir = sample_crumb_with_image["tmp_dir"] / "output"
    output_dir.mkdir()
    
    # Convert the recipe
    crumb_to_md.convert_crumb_to_md(str(input_path), str(output_dir))
    
    # Check that the markdown file was created
    output_md = output_dir / "Sample Test Recipe.md"
    assert output_md.exists()
    
    # Check that the image was extracted
    images_dir = output_dir / "images"
    assert images_dir.exists()
    assert len(list(images_dir.iterdir())) == 1
    
    # Check that the markdown references the image
    content = output_md.read_text()
    assert "photos:" in content
    assert "  - images/" in content


def test_truncated_image_data(tmp_path, sample_crumb_data):
    """Test handling of truncated base64 image data."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create recipe with truncated image data
    truncated_data = sample_crumb_data.copy()
    truncated_data["images"] = ["iVBORw0KGgoAAAANSUhEUgAA(base64 encoding truncated for LLM context)"]
    
    recipe_path = input_dir / "truncated_image.crumb"
    recipe_path.write_text(json.dumps(truncated_data))
    
    # Convert the recipe
    crumb_to_md.convert_crumb_to_md(str(recipe_path), str(output_dir))
    
    # Check that the markdown file was created without images
    output_md = output_dir / "Sample Test Recipe.md"
    assert output_md.exists()
    
    # The photos field should be empty since the image couldn't be processed
    content = output_md.read_text()
    assert "photos:" in content
    
    # Check if there are any entries under photos
    photo_line_idx = content.split("\n").index("photos:")
    next_line = content.split("\n")[photo_line_idx + 1]
    assert not next_line.strip().startswith("  - ")  # No photo entries
    
    # No images directory should be created
    images_dir = output_dir / "images"
    assert not images_dir.exists() or len(list(images_dir.iterdir())) == 0 