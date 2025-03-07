# Crouton Recipe Converter

This tool converts Crouton recipe (.crumb) files to Obsidian-compatible markdown format.

## Features

- Converts Crouton's .crumb JSON files to Obsidian markdown with YAML frontmatter
- Preserves all recipe details including ingredients, steps, and nutritional information
- Extracts and saves images from base64-encoded data
- Maintains original formatting and organization of recipes
- Handles recipe sections and formatting
- Supports batch processing with parallel execution

## Prerequisites

- Python 3.6 or higher

## Project Structure

```
cookdown/
├── src/
│   └── cookdown/       # Main package
│       ├── __init__.py
│       ├── convert.py  # Single file converter
│       └── batch.py    # Batch processor
├── tests/             # Test suite
├── data/              # Data directories
│   ├── input/         # Place .crumb files here
│   └── output/        # Converted files go here
├── examples/          # Example templates
├── pyproject.toml     # Project configuration
└── README.md          # This file
```

## Installation

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cookdown.git
cd cookdown

# Install in development mode
pip install -e .
```

### Usage After Installation

Once installed, you can use the command-line tools:

```bash
# Convert a single file
crumb-convert -f "data/input/recipe.crumb"

# Batch convert all recipes
crumb-batch
```

## Usage Without Installation

You can also run the scripts directly:

```bash
# Convert a single file
python -m cookdown.convert -f "data/input/recipe.crumb"

# Batch convert all recipes
python -m cookdown.batch
```

## Command-Line Options

### Single File Conversion

```bash
crumb-convert [-h] [-i INPUT] [-o OUTPUT] [-r] [-f FILE]
```

Arguments:
- `-h, --help`: Show help message
- `-i, --input`: Input directory containing .crumb files (defaults to 'data/input' subdirectory)
- `-o, --output`: Output directory for markdown files (defaults to 'data/output' subdirectory)
- `-r, --recursive`: Search recursively for .crumb files in input directory
- `-f, --file`: Process a single .crumb file instead of a directory

### Batch Conversion

```bash
crumb-batch [-h] [-i INPUT] [-o OUTPUT] [-r] [-p PARALLEL] [-s]
```

Arguments:
- `-h, --help`: Show help message
- `-i, --input`: Input directory containing .crumb files (defaults to 'data/input' subdirectory)
- `-o, --output`: Output directory for markdown files (defaults to 'data/output' subdirectory)
- `-r, --recursive`: Search recursively for .crumb files in input directory
- `-p, --parallel`: Maximum number of parallel conversions (default is 4)
- `-s, --subprocess`: Use subprocess to call the converter script instead of direct function call

## Examples

Process all .crumb files in the input directory:
```bash
crumb-batch
```

Process files in a custom directory recursively with higher parallelism:
```bash
crumb-batch -i /path/to/crumb_files -r -p 8
```

Convert a single file with specific output location:
```bash
crumb-convert -f data/input/recipe.crumb -o /path/to/obsidian/recipes
```

## Testing

The project includes a comprehensive test suite using pytest. To run the tests:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run the basic test suite
pytest

# Run tests with coverage report
pytest --cov=src --cov-report=term --cov-report=html
```

For convenience, you can also use the included script:

```bash
./run_tests.sh        # Basic tests
./run_tests.sh --coverage  # Tests with coverage report
./run_tests.sh --verbose   # Verbose test output
```

### Test Structure

- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test the end-to-end conversion process
- **Image Handling Tests**: Specifically test the base64 image decoding functionality

## Output Format

The conversion creates:
- Markdown files for each recipe in the output directory with YAML frontmatter
- An `images` subdirectory containing extracted images from the recipes

## Handling Images

The script extracts and decodes base64-encoded images from the .crumb files. For truncated base64 strings (as might appear in conversation contexts), the script will skip these images with a warning message.

## Customization

You can modify the package to:
- Change the output directory structure
- Adjust the formatting of recipe steps
- Customize the YAML frontmatter fields
- Add additional metadata processing

## License

This project is open source and available under the MIT License. 