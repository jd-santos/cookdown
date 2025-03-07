"""
Tests for the batch_convert.py script.

These tests verify that the script correctly processes multiple .crumb files
in batch mode, with proper parallelization and error handling.
"""

import os
import json
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import pytest

import batch_convert


@pytest.fixture
def mock_recipe_directory(tmp_path):
    """Create a directory with multiple mock recipe files for testing."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    
    # Create three sample recipes
    recipes = []
    for i in range(3):
        recipe = {
            "name": f"Test Recipe {i+1}",
            "ingredients": [
                {
                    "order": 0,
                    "ingredient": {"name": f"Ingredient {i+1}"},
                    "quantity": {"amount": i+1, "quantityType": "cup"}
                }
            ],
            "steps": [
                {
                    "order": 0,
                    "step": f"Step {i+1}",
                    "isSection": False
                }
            ],
            "notes": f"Notes {i+1}",
            "neutritionalInfo": "",
            "webLink": "",
            "cookingDuration": 30,
            "serves": 2,
            "images": []
        }
        
        recipe_path = input_dir / f"recipe_{i+1}.crumb"
        recipe_path.write_text(json.dumps(recipe))
        recipes.append({"path": recipe_path, "content": recipe})
    
    return {
        "path": input_dir,
        "recipes": recipes,
        "tmp_dir": tmp_path
    }


class TestBatchConvert(unittest.TestCase):
    """Test cases for the batch_convert.py script."""

    def setUp(self):
        """Set up temporary directories for testing."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create sample recipe files
        for i in range(3):
            recipe = {
                "name": f"Test Recipe {i+1}",
                "ingredients": [
                    {
                        "order": 0,
                        "ingredient": {"name": f"Ingredient {i+1}"},
                        "quantity": {"amount": i+1, "quantityType": "cup"}
                    }
                ],
                "steps": [
                    {
                        "order": 0,
                        "step": f"Step {i+1}",
                        "isSection": False
                    }
                ],
                "notes": f"Notes {i+1}",
                "neutritionalInfo": "",
                "webLink": "",
                "cookingDuration": 30,
                "serves": 2,
                "images": []
            }
            
            recipe_path = os.path.join(self.input_dir, f"recipe_{i+1}.crumb")
            with open(recipe_path, "w", encoding="utf-8") as f:
                json.dump(recipe, f)

    def tearDown(self):
        """Clean up temporary directories after testing."""
        shutil.rmtree(self.temp_dir)

    def test_find_crumb_files(self):
        """Test finding .crumb files in a directory."""
        # Non-recursive search
        files = batch_convert.find_crumb_files(self.input_dir, recursive=False)
        self.assertEqual(len(files), 3)
        
        # Create a subdirectory with another file
        subdir = os.path.join(self.input_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        with open(os.path.join(subdir, "recipe_4.crumb"), "w", encoding="utf-8") as f:
            f.write("{}")
        
        # Non-recursive should still find only 3
        files = batch_convert.find_crumb_files(self.input_dir, recursive=False)
        self.assertEqual(len(files), 3)
        
        # Recursive should find 4
        files = batch_convert.find_crumb_files(self.input_dir, recursive=True)
        self.assertEqual(len(files), 4)

    @mock.patch("subprocess.run")
    def test_convert_file(self, mock_run):
        """Test converting a single file."""
        # Set up the mock subprocess.run to return success
        mock_run.return_value = mock.Mock(stdout="Success", stderr="")
        
        # Test successful conversion
        success, file_path, output = batch_convert.convert_file(
            os.path.join(self.input_dir, "recipe_1.crumb"),
            self.output_dir,
            "crumb_to_md.py"
        )
        
        self.assertTrue(success)
        self.assertEqual(output, "Success")
        
        # Verify subprocess.run was called with the correct arguments
        mock_run.assert_called_once_with(
            ["python3", "crumb_to_md.py", "-f", os.path.join(self.input_dir, "recipe_1.crumb"), "-o", self.output_dir],
            capture_output=True, text=True, check=True
        )
        
        # Test failure
        mock_run.reset_mock()
        mock_run.side_effect = subprocess.CalledProcessError(1, [], stderr="Error")
        
        success, file_path, output = batch_convert.convert_file(
            os.path.join(self.input_dir, "recipe_1.crumb"),
            self.output_dir,
            "crumb_to_md.py"
        )
        
        self.assertFalse(success)
        self.assertEqual(output, "Error")


def test_process_files_with_pytest(mock_recipe_directory):
    """Test processing multiple files with pytest fixtures."""
    output_dir = mock_recipe_directory["tmp_dir"] / "output"
    output_dir.mkdir()
    
    # Create a mock converter script for testing
    converter_script = mock_recipe_directory["tmp_dir"] / "mock_converter.py"
    
    # Use mocking to avoid actually running the subprocess
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(stdout="Success", stderr="")
        
        # Get the list of files
        crumb_files = [str(recipe["path"]) for recipe in mock_recipe_directory["recipes"]]
        
        # Process the files
        success_count, error_count = batch_convert.process_files(
            crumb_files, 
            str(output_dir), 
            str(converter_script), 
            max_workers=2
        )
        
        # Check the results
        assert success_count == 3
        assert error_count == 0
        assert mock_run.call_count == 3


def test_main_function(mock_recipe_directory):
    """Test the main function with mocked arguments."""
    with mock.patch("argparse.ArgumentParser.parse_args") as mock_args:
        # Mock the arguments
        mock_args.return_value = mock.Mock(
            input=str(mock_recipe_directory["path"]),
            output=str(mock_recipe_directory["tmp_dir"] / "output"),
            recursive=False,
            parallel=2
        )
        
        # Mock the actual conversion to avoid subprocess calls
        with mock.patch("batch_convert.process_files") as mock_process:
            mock_process.return_value = (3, 0)  # 3 successful, 0 errors
            
            # Run the main function
            batch_convert.main()
            
            # Check that process_files was called with the correct arguments
            mock_process.assert_called_once()
            
            # First argument should be the list of crumb files
            args, kwargs = mock_process.call_args
            assert len(args[0]) == 3  # Should find 3 files
            assert kwargs["max_workers"] == 2 