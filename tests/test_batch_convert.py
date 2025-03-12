"""
Tests for the batch conversion functionality.

These tests verify that the system correctly processes multiple recipe files
in batch mode, with proper parallelization and error handling.
"""

import os
import json
import shutil
import tempfile
import pytest
from unittest import mock
from pathlib import Path

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


@pytest.fixture
def test_files_setup():
    """Set up test environment with multiple recipe files."""
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    input_dir = os.path.join(temp_dir, "input")
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
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
        
        recipe_path = os.path.join(input_dir, f"recipe_{i+1}.crumb")
        with open(recipe_path, "w", encoding="utf-8") as f:
            json.dump(recipe, f)
    
    # Yield the directories to the test
    yield {
        "temp_dir": temp_dir,
        "input_dir": input_dir,
        "output_dir": output_dir
    }
    
    # Clean up after the test (equivalent to tearDown)
    shutil.rmtree(temp_dir)


def test_find_recipe_files(test_files_setup):
    """Test finding recipe files in a directory."""
    input_dir = test_files_setup["input_dir"]
    
    # Non-recursive search
    files = batch.find_recipe_files(input_dir, recursive=False, extensions=["crumb"])
    assert len(files) == 3
    
    # Create a subdirectory with another file
    subdir = os.path.join(input_dir, "subdir")
    os.makedirs(subdir, exist_ok=True)
    with open(os.path.join(subdir, "recipe_4.crumb"), "w", encoding="utf-8") as f:
        f.write("{}")
    
    # Non-recursive should still find only 3
    files = batch.find_recipe_files(input_dir, recursive=False, extensions=["crumb"])
    assert len(files) == 3
    
    # Recursive should find 4
    files = batch.find_recipe_files(input_dir, recursive=True, extensions=["crumb"])
    assert len(files) == 4


@pytest.mark.parametrize("success_case", [True, False])
@mock.patch("subprocess.run")
def test_convert_file(mock_run, test_files_setup, success_case):
    """Test converting a single file."""
    input_dir = test_files_setup["input_dir"]
    output_dir = test_files_setup["output_dir"]
    
    # Configure the mock based on success or failure case
    mock_process = mock.Mock()
    
    if success_case:
        # Set up the mock subprocess.run to return success
        mock_process.returncode = 0
        mock_process.stdout = "Converted successfully"
        mock_process.stderr = ""
        expected_success = True
        expected_output = "Converted successfully"
    else:
        # Test failed conversion with a proper CommandError
        error_message = "Error processing file"
        mock_process.returncode = 1
        mock_process.stderr = error_message
        expected_success = False
        expected_output = error_message
    
    mock_run.return_value = mock_process
    
    # Test conversion
    success, file_path, output, conversion_time = batch.convert_file(
        os.path.join(input_dir, "recipe_1.crumb"),
        output_dir,
        use_subprocess=True
    )
    
    assert success == expected_success
    assert output == expected_output
    assert isinstance(conversion_time, float)  # Verify conversion time is returned


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