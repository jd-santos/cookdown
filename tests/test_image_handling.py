"""
Tests for image handling functionality in the recipe converter.

These tests specifically focus on the base64 image decoding and saving
functionality, which is a key feature of the converter.
"""

import os
import json
import pytest
from pathlib import Path

from cookdown import formatter
from cookdown.parsers import crumb


def test_save_image(sample_base64_image, tmp_path):
    """Test saving a base64-encoded image to a file."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Save the test image
    image_data = {
        "data": sample_base64_image,
        "filename": "Test_Recipe_0.jpg",
        "format": "base64"
    }
    
    image_path = formatter.save_image(
        image_data,
        str(output_dir)
    )
    
    # Check that the image file was created
    expected_path = "images/Test_Recipe_0.jpg"
    assert image_path == expected_path
    
    full_path = output_dir / "images" / "Test_Recipe_0.jpg"
    assert full_path.exists()
    
    # Check that the file is a valid image (has some content)
    assert full_path.stat().st_size > 0


def test_save_image_invalid_base64(tmp_path):
    """Test handling of invalid base64 data."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Invalid base64 data
    image_data = {
        "data": "not-valid-base64!",
        "filename": "invalid.jpg",
        "format": "base64"
    }
    
    # Should return empty string on error
    image_path = formatter.save_image(
        image_data,
        str(output_dir)
    )
    
    assert image_path == ""


def test_recipe_with_image(sample_crumb_with_image):
    """Test converting a recipe that contains an image."""
    tmp_dir = sample_crumb_with_image["tmp_dir"]
    recipe_path = sample_crumb_with_image["path"]
    output_dir = tmp_dir / "output"
    output_dir.mkdir()
    
    # Convert the recipe with image
    formatter.convert_to_markdown(
        str(recipe_path),
        str(output_dir),
        crumb.CrumbParser
    )
    
    # Check output markdown file
    recipe_name = sample_crumb_with_image["content"]["name"].replace(" ", "_")
    md_path = output_dir / f"{recipe_name}.md"
    assert md_path.exists()
    
    # Check that the image was saved
    images_dir = output_dir / "images"
    assert images_dir.exists()
    assert any(images_dir.iterdir())
    
    # Check the markdown file content
    content = md_path.read_text()
    assert "photos:" in content  # Should have photos in frontmatter
    assert "images/" in content  # Should reference the image


def test_truncated_image_data(tmp_path, sample_crumb_data):
    """Test handling of truncated image data."""
    # Create recipe with truncated image data
    recipe_dir = tmp_path / "recipes"
    recipe_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Modify sample data to include truncated image data
    modified_data = sample_crumb_data.copy()
    modified_data["images"] = ["truncated for LLM context"]
    
    # Write to file
    recipe_path = recipe_dir / "truncated_image.crumb"
    with open(recipe_path, "w") as f:
        json.dump(modified_data, f)
    
    # Process the recipe
    formatter.convert_to_markdown(
        str(recipe_path),
        str(output_dir),
        crumb.CrumbParser
    )
    
    # Check output - should succeed but without images
    recipe_name = modified_data["name"].replace(" ", "_")
    md_path = output_dir / f"{recipe_name}.md"
    assert md_path.exists()
    
    # Check content - should not have any image references
    content = md_path.read_text()
    assert "photos:" in content
    
    # Should not contain any image references
    assert not any(line.strip().startswith("- images/") for line in content.split("\n"))
    
    # No images directory should be created if there are no valid images
    # (or if created, should be empty)
    images_dir = output_dir / "images"
    if images_dir.exists():
        assert len(list(images_dir.iterdir())) == 0 