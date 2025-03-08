"""
Tests for the batch conversion functionality.

These tests verify that the system correctly processes multiple recipe files
in batch mode, with proper parallelization and error handling.
"""

import os
import json
import shutil
import tempfile
import unittest
import subprocess
from unittest import mock
from pathlib import Path

import pytest

from cookdown import batch
from cookdown.parsers import get_supported_extensions


@pytest.fixture
def mock_recipe_directory(tmp_path):
    """Create a mock directory with multiple recipe files."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Create multiple recipe files
    for i in range(3):
        recipe = {
            "name": f"Test Recipe {i+1}",
            "ingredients": [
                {
                    "order": 0,
                    "ingredient": {"name": f"Ingredient {i+1}"},
                    "quantity": {"amount": 1, "quantityType": "cup"}
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
        with open(recipe_path, "w") as f:
            json.dump(recipe, f)
    
    return {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "tmp_path": tmp_path
    }


class TestBatchConvert(unittest.TestCase):
    """Test cases for the batch conversion functionality."""
    
    def setUp(self):
        """Set up test environment with multiple recipe files."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.temp_dir, "input")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create multiple sample recipe files
        for i in range(3):
            recipe = {
                "name": f"Recipe {i+1}",
                "ingredients": [
                    {
                        "order": 0,
                        "ingredient": {"name": f"Ingredient {i+1}"},
                        "quantity": {"amount": 1, "quantityType": "cup"}
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
    
    def test_find_recipe_files(self):
        """Test finding recipe files in a directory."""
        # Non-recursive search
        files = batch.find_recipe_files(self.input_dir, recursive=False, extensions=["crumb"])
        self.assertEqual(len(files), 3)
        
        # Create a subdirectory with another file
        subdir = os.path.join(self.input_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        with open(os.path.join(subdir, "recipe_4.crumb"), "w", encoding="utf-8") as f:
            f.write("{}")
        
        # Non-recursive should still find only 3
        files = batch.find_recipe_files(self.input_dir, recursive=False, extensions=["crumb"])
        self.assertEqual(len(files), 3)
        
        # Recursive should find 4
        files = batch.find_recipe_files(self.input_dir, recursive=True, extensions=["crumb"])
        self.assertEqual(len(files), 4)
    
    @mock.patch("subprocess.run")
    def test_convert_file(self, mock_run):
        """Test converting a single file."""
        # Set up the mock subprocess.run to return success
        mock_process = mock.Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Converted successfully"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        # Test successful conversion
        success, file_path, output = batch.convert_file(
            os.path.join(self.input_dir, "recipe_1.crumb"),
            self.output_dir,
            use_subprocess=True
        )
        
        self.assertTrue(success)
        self.assertEqual(output, "Converted successfully")
        
        # Test failed conversion with a proper CommandError
        error_message = "Error processing file"
        mock_process = mock.Mock()
        mock_process.returncode = 1
        mock_process.stderr = error_message
        mock_run.return_value = mock_process
        mock_run.side_effect = None  # Remove previous side effect
        
        success, file_path, output = batch.convert_file(
            os.path.join(self.input_dir, "recipe_1.crumb"),
            self.output_dir,
            use_subprocess=True
        )
        
        self.assertFalse(success)
        self.assertEqual(output, error_message)


def test_batch_convert_with_pytest(mock_recipe_directory):
    """Test batch conversion using pytest fixtures."""
    input_dir = mock_recipe_directory["input_dir"]
    output_dir = mock_recipe_directory["output_dir"]
    
    # Run batch conversion
    results = batch.batch_convert(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        recursive=False,
        max_workers=2,
        use_subprocess=False,
        extensions=["crumb"]
    )
    
    # Check that all files were processed
    assert len(results) == 3
    # Check that all conversions were successful
    assert all(result[0] for result in results)
    
    # Check output directory has the converted files
    output_files = list(output_dir.glob("*.md"))
    assert len(output_files) == 3


@mock.patch("cookdown.batch.batch_convert")
@mock.patch("cookdown.batch.argparse.ArgumentParser.parse_args")
def test_main_function(mock_parse_args, mock_batch_convert):
    """Test the main function."""
    # Set up the mock args
    mock_args = mock.Mock()
    mock_args.input = None
    mock_args.output = None
    mock_args.recursive = False
    mock_args.parallel = 4
    mock_args.subprocess = False
    mock_args.extensions = None
    mock_args.list_formats = False
    mock_parse_args.return_value = mock_args
    
    # Set up the batch_convert mock
    mock_batch_convert.return_value = [
        (True, "file1.crumb", "output1"), 
        (True, "file2.crumb", "output2"), 
        (True, "file3.crumb", "output3")
    ]
    
    # Run the main function
    batch.main()
    
    # Check that batch_convert was called
    mock_batch_convert.assert_called_once() 