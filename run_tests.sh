#!/bin/bash
# Script to run the test suite for Cookdown

# Stop on errors
set -e

# Explain what this script does
echo "Cookdown Test Runner"
echo "===================="
echo "This script will run the test suite for the Cookdown recipe converter."
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest not found. Installing development dependencies..."
    pip install -e ".[dev]"
else
    echo "pytest found, continuing..."
fi

# Allow for different test modes
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: ./run_tests.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  --basic      Run basic tests without coverage (default)"
    echo "  --coverage   Run tests with coverage report"
    echo "  --verbose    Run tests with verbose output"
    echo "  --help       Display this help message"
    exit 0
fi

# Run the appropriate tests
if [ "$1" == "--coverage" ]; then
    echo "Running tests with coverage report..."
    pytest --cov=. --cov-report=term --cov-report=html
    echo ""
    echo "Coverage report generated in 'htmlcov' directory."
    echo "Open 'htmlcov/index.html' in your browser to view detailed coverage report."
elif [ "$1" == "--verbose" ]; then
    echo "Running tests with verbose output..."
    pytest -v
else
    echo "Running basic tests..."
    pytest
fi

# Final message
echo ""
echo "Tests completed!" 