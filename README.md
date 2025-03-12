# Cookdown Recipe Converter

This tool converts recipe files from various formats to Obsidian-compatible markdown format.

## Features

- Converts various recipe formats to Obsidian markdown with YAML frontmatter
- Currently supports:
  - Crouton's .crumb JSON files
  - Paprika's .paprikarecipe (gzipped JSON) and .paprikarecipes (ZIP archives) files
  - (More formats coming soon)
- Preserves all recipe details including ingredients, steps, and nutritional information
- Extracts and saves images from base64-encoded data
- Maintains original formatting and organization of recipes
- Handles recipe sections and formatting
- Supports batch processing with parallel execution
- Extensible architecture for adding support for more recipe formats

## Prerequisites

- Python 3.6 or higher

## Project Structure

```
cookdown/
├── src/
│   └── cookdown/            # Main package
│       ├── __init__.py
│       ├── parsers/         # Format-specific parsers
│       │   ├── __init__.py  # Parser registry
│       │   ├── base.py      # Base parser interface
│       │   ├── crumb.py     # Crouton parser
│       │   └── paprika.py   # Paprika parser
│       ├── formatter.py     # Formatting logic
│       ├── convert.py       # Single file converter
│       └── batch.py         # Batch processor
├── tests/                   # Test suite
│   ├── test_convert.py      # Basic conversion tests
│   ├── test_batch_convert.py # Batch conversion tests
│   ├── test_image_handling.py # Image processing tests
│   ├── test_paprika.py      # Paprika parser tests
│   └── test_paprika_batch.py # Paprika batch tests
├── data/                    # Data directories
│   ├── input/               # Place recipe files here
│   └── output/              # Converted files go here
├── examples/                # Example templates
├── extract_paprika.py       # Standalone Paprika extractor
├── run_paprika_tests.sh     # Script for running Paprika tests
├── pyproject.toml           # Project configuration
└── README.md                # This file
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
recipe-convert -f "data/input/recipe.crumb"

# Convert a Paprika recipe
recipe-convert -f "data/input/recipe.paprikarecipe"

# Batch convert all recipes
recipe-batch
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
recipe-convert [-h] [-i INPUT] [-o OUTPUT] [-r] [-f FILE] [-l]
```

Arguments:
- `-h, --help`: Show help message
- `-i, --input`: Input directory containing recipe files (defaults to 'data/input' subdirectory)
- `-o, --output`: Output directory for markdown files (defaults to 'data/output' subdirectory)
- `-r, --recursive`: Search recursively for recipe files in input directory
- `-f, --file`: Process a single recipe file
- `-l, --list-formats`: List supported file formats

### Batch Conversion

```bash
recipe-batch [-h] [-i INPUT] [-o OUTPUT] [-r] [-p PARALLEL] [-s] [-e EXTENSIONS [EXTENSIONS ...]] [-l]
```

Arguments:
- `-h, --help`: Show help message
- `-i, --input`: Input directory containing recipe files (defaults to 'data/input' subdirectory)
- `-o, --output`: Output directory for markdown files (defaults to 'data/output' subdirectory)
- `-r, --recursive`: Search recursively for recipe files in input directory
- `-p, --parallel`: Maximum number of parallel conversions (default is 4)
- `-s, --subprocess`: Use subprocess to call the converter script instead of direct function call
- `-e, --extensions`: List of file extensions to process (default: all supported extensions)
- `-l, --list-formats`: List supported file formats

### Paprika Extraction

For just extracting Paprika recipe files to JSON (without converting to markdown), you can use the standalone extractor:

```bash
./extract_paprika.py [-h] [-o OUTPUT] [-k] [-v] INPUT
```

Arguments:
- `INPUT`: Directory containing Paprika recipe files or a specific .paprikarecipe(s) file
- `-h, --help`: Show help message
- `-o, --output`: Directory to save extracted JSON files (default: input_dir/json)
- `-k, --keep-intermediate`: Keep intermediate .paprikarecipe files extracted from archives
- `-v, --verbose`: Enable verbose logging

## Examples

Process all recipe files in the input directory:
```bash
recipe-batch
```

Process files in a custom directory recursively with higher parallelism:
```bash
recipe-batch -i /path/to/recipe_files -r -p 8
```

Convert a single file with specific output location:
```bash
recipe-convert -f data/input/recipe.crumb -o /path/to/obsidian/recipes
```

Extract a Paprika recipe archive to JSON:
```bash
./extract_paprika.py data/input/recipes.paprikarecipes
```

Extract a single Paprika recipe file to JSON:
```bash
./extract_paprika.py data/input/recipe.paprikarecipe -o /path/to/output
```

List supported formats:
```bash
recipe-convert -l
```

## Adding Support for New Formats

Cookdown uses a modular architecture that makes it easy to add support for new recipe formats:

1. Create a new parser in the `src/cookdown/parsers/` directory (e.g., `mealmaster.py` for .mmf files)
2. Implement the `RecipeParser` interface defined in `base.py`
3. Register your parser with the appropriate file extension using the `register_parser` function

See the `crumb.py` or `paprika.py` parsers for complete examples.

## How It Works

The Cookdown tool processes recipe files through a pipeline of operations:

1. **Input Detection** (`convert.py`): 
   - The `convert_recipe_file()` function examines the file extension of the input recipe file (e.g., `.crumb`, `.paprikarecipe`).
   - Calls `RecipeParser.get_file_extension()` to extract the extension.

2. **Parser Selection** (`parsers/__init__.py`): 
   - The `get_parser_for_extension()` function selects the appropriate parser class from the registry.
   - The parser registry (`_PARSERS` dictionary) maps file extensions to parser classes.
   - Each parser is registered using the `register_parser()` function when the module is imported.

3. **Parsing** (`parsers/crumb.py`, `parsers/paprika.py`, and other format-specific parsers): 
   - The selected parser's `parse_file()` method reads the input file.
   - Parser extracts structured data using format-specific methods:
     - `get_recipe_name()`: Extracts the recipe title
     - `get_ingredients()`: Extracts and normalizes the ingredients list
     - `get_instructions()`: Extracts and normalizes cooking steps
     - `get_images()`: Extracts image data
     - `get_metadata()`: Extracts additional recipe metadata
   - All data is normalized to a common structure regardless of input format.

4. **Formatting** (`formatter.py`): 
   - The `convert_to_markdown()` function orchestrates the conversion process.
   - Helper functions process each part of the recipe:
     - `format_ingredients()`: Converts normalized ingredient data to text
     - `format_instructions()`: Structures the cooking steps into markdown
   - YAML frontmatter is generated from recipe metadata.

5. **Image Processing** (`formatter.py`):
   - The `save_image()` function extracts and decodes images from the parsed data.
   - Images are saved to the output directory's `images` subdirectory.
   - Image references are added to the markdown frontmatter.

6. **Output Generation** (`formatter.py`):
   - Final markdown content is assembled by the `convert_to_markdown()` function.
   - The markdown file is written to the output directory with the recipe name.

To add support for a new format, you only need to implement a new parser class that follows the `RecipeParser` interface - the rest of the pipeline remains unchanged.

### Paprika Format Handling

The Paprika parser handles two types of files:

1. **Individual Recipe Files** (`.paprikarecipe`):
   - These are gzipped JSON files containing a single recipe
   - Extracted using gzip and json modules
   
2. **Recipe Archives** (`.paprikarecipes`):
   - These are ZIP archives containing multiple `.paprikarecipe` files
   - Extracted first to individual `.paprikarecipe` files using the zipfile module
   - Then each extracted file is processed as above

The standalone `extract_paprika.py` script provides a way to extract these formats to plain JSON files, which can be useful for debugging or further processing outside of the Cookdown conversion pipeline. The script can handle both individual files and directories containing multiple Paprika recipe files.

Both the PaprikaParser and the extract_paprika.py script are comprehensively tested with dedicated test files (test_paprika.py and test_paprika_batch.py).

### Data Flow Diagram

```
Input Recipe File (.crumb, .paprikarecipe, .paprikarecipes, etc.)
         │
         ▼
┌─────────────────────────────────────┐
│ Parser Registry                     │
│ (get_parser_for_extension)          │──► Select parser based on extension
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Format-specific Parser              │
│ (CrumbParser, PaprikaParser, etc.)  │──► Extract & normalize recipe data
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Formatter                           │
│ (format_ingredients, instructions)  │──► Convert to Markdown with YAML
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Image Processor                     │
│ (save_image)                        │──► Extract and save images
└─────────────────────────────────────┘
         │
         ▼
Output Markdown File + Images
```

For batch processing, the `batch.py` module provides parallel processing capabilities through the `batch_convert()` function, which distributes conversion tasks across multiple threads for efficiency.

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

For convenience, you can also use the included scripts:

```bash
./run_tests.sh        # Basic tests
./run_tests.sh --coverage  # Tests with coverage report
./run_tests.sh --verbose   # Verbose test output

# For testing specifically the Paprika functionality
./run_paprika_tests.sh     # Run only Paprika-related tests
./run_paprika_tests.sh --coverage  # Paprika tests with coverage
./run_paprika_tests.sh --verbose   # Verbose Paprika test output
```

### Test Structure

- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test the end-to-end conversion process
- **Image Handling Tests**: Specifically test the base64 image decoding functionality
- **Paprika Format Tests**: Test both `.paprikarecipe` and `.paprikarecipes` handling

## Output Format

The conversion creates:
- Markdown files for each recipe in the output directory with YAML frontmatter
- An `images` subdirectory containing extracted images from the recipes

## Handling Images

The script extracts and decodes images from the recipe files. For truncated base64 strings (as might appear in conversation contexts), the script will skip these images with a warning message.

## Customization

You can modify the package to:
- Change the output directory structure
- Adjust the formatting of recipe steps
- Customize the YAML frontmatter fields
- Add additional metadata processing

## License

This project is open source and available under the MIT License. 