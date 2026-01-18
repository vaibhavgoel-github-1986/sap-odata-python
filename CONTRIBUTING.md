# Contributing to sap-odata-python

Thank you for your interest in contributing to sap-odata-python! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected behavior** vs **actual behavior**
- **Environment details** (Python version, OS, SAP system version)
- **Code samples** if applicable
- **Error messages** and stack traces

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- **Use case** - Why is this enhancement needed?
- **Proposed solution** - How should it work?
- **Alternatives considered** - What other solutions did you consider?

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
3. **Make your changes** following the coding standards
4. **Add tests** for any new functionality
5. **Run the test suite**:
   ```bash
   pytest
   ```
6. **Run linters**:
   ```bash
   black src tests
   isort src tests
   flake8 src tests
   mypy src
   ```
7. **Update documentation** if needed
8. **Commit your changes** with a clear commit message
9. **Push to your fork** and submit a pull request

## Development Setup

### Prerequisites

- Python 3.9+
- pip
- git

### Setting Up Your Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/sap-odata-python.git
cd sap-odata-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=sap_odata --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run specific test
pytest tests/test_client.py::test_connect
```

### Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black src tests
isort src tests

# Check linting
flake8 src tests

# Type checking
mypy src
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all public functions
- Maximum line length: 100 characters
- Use docstrings for all public modules, classes, and functions

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description of the function.

    Longer description if needed, explaining the function's
    behavior in more detail.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of the return value.

    Raises:
        ValueError: When param1 is empty.
        ConnectionError: When unable to connect.

    Example:
        >>> function_name("hello", 42)
        True
    """
    pass
```

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests when relevant

Examples:
- `feat: Add batch operation support`
- `fix: Handle empty response in V4 services`
- `docs: Update README with V2 examples`
- `test: Add tests for metadata parsing`

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test additions or changes

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Name test functions with `test_` prefix
- Use descriptive test names
- Test both success and failure cases
- Use `responses` library to mock HTTP requests

```python
import pytest
import responses
from sap_odata import ODataClient

class TestODataClient:
    """Tests for ODataClient class."""

    @responses.activate
    def test_connect_success(self):
        """Test successful connection to SAP system."""
        responses.add(
            responses.GET,
            "https://sap.example.com/sap/opu/odata/sap/SERVICE/$metadata",
            body="<edmx:Edmx>...</edmx:Edmx>",
            status=200,
        )
        
        client = ODataClient(
            host="https://sap.example.com",
            username="user",
            password="pass",
        )
        assert client.is_connected
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public APIs
- Update CHANGELOG.md for notable changes
- Add examples for new features

## Release Process

Releases are handled by maintainers. The process:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag
4. Push to trigger CI/CD pipeline
5. PyPI package is automatically published

## Questions?

Feel free to open an issue for any questions about contributing!
