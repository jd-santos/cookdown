#!/bin/bash
# Run tests specifically for Paprika-related functionality

# Change to the project directory
cd "$(dirname "$0")"

# Set up color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running Paprika-specific tests...${NC}"

# Parse command line arguments
coverage=false
verbose=false

for arg in "$@"; do
  case $arg in
    --coverage)
      coverage=true
      shift
      ;;
    --verbose|-v)
      verbose=true
      shift
      ;;
  esac
done

# Set up pytest options
PYTEST_OPTS=""
if [ "$verbose" = true ]; then
  PYTEST_OPTS="$PYTEST_OPTS -v"
fi

# Run tests with or without coverage
if [ "$coverage" = true ]; then
  echo -e "${YELLOW}Running tests with coverage...${NC}"
  python -m pytest tests/test_paprika.py tests/test_paprika_batch.py --cov=src/cookdown/parsers/paprika --cov=extract_paprika --cov-report=term $PYTEST_OPTS
else
  echo -e "${YELLOW}Running tests without coverage...${NC}"
  python -m pytest tests/test_paprika.py tests/test_paprika_batch.py $PYTEST_OPTS
fi

# Check the exit code
if [ $? -eq 0 ]; then
  echo -e "${GREEN}All Paprika tests passed!${NC}"
  exit 0
else
  echo -e "${RED}Some Paprika tests failed.${NC}"
  exit 1
fi 