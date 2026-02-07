# Contributing to PDF Context Narrator

Thank you for your interest in contributing to PDF Context Narrator! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- pip (Python package manager)

### Quick Setup

Use the provided quickstart script:

```bash
./quickstart.sh
```

Or manually:

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black ruff mypy

# Copy environment template
cp .env.example .env
```

## Project Structure

```
pdf_context_narrator/
├── src/pdf_context_narrator/  # Main application code
│   ├── cli.py                 # CLI interface
│   ├── config.py              # Configuration management
│   └── logger.py              # Logging setup
├── tests/                     # Test files
├── configs/                   # Configuration files
└── docs/                      # Documentation
```

## Running the Application

### Development Mode

```bash
# Run with PYTHONPATH
PYTHONPATH=src:$PYTHONPATH python -m pdf_context_narrator --help

# Or install in development mode
pip install -e .
pdf-context-narrator --help
```

## Testing

### Running Tests

```bash
# Run all tests
PYTHONPATH=src:$PYTHONPATH pytest tests/

# Run with coverage
PYTHONPATH=src:$PYTHONPATH pytest --cov=pdf_context_narrator tests/

# Run specific test file
PYTHONPATH=src:$PYTHONPATH pytest tests/test_cli.py -v

# Run with verbose output
PYTHONPATH=src:$PYTHONPATH pytest tests/ -v
```

### Writing Tests

- Place test files in the `tests/` directory
- Name test files with `test_` prefix (e.g., `test_cli.py`)
- Name test functions with `test_` prefix (e.g., `test_ingest_command`)
- Use descriptive docstrings for test functions
- Follow existing test patterns in the repository

Example test:

```python
def test_new_feature():
    """Test description of what this test verifies."""
    # Arrange
    # ... setup code
    
    # Act
    # ... code to execute
    
    # Assert
    assert expected == actual
```

## Code Quality

### Formatting

We use Black for code formatting:

```bash
# Format all Python files
black src/ tests/

# Check formatting without making changes
black --check src/ tests/
```

### Linting

We use Ruff for linting:

```bash
# Lint the code
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/
```

### Type Checking

We use mypy for type checking:

```bash
# Run type checker
mypy src/
```

## Code Style Guidelines

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write descriptive docstrings for functions and classes
- Keep functions focused and single-purpose
- Maximum line length: 100 characters
- Use meaningful variable names

## Git Workflow

### Branch Naming

- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Documentation: `docs/description`

### Commit Messages

Write clear, descriptive commit messages:

```
Add feature X to support Y

- Detailed explanation of what changed
- Why the change was necessary
- Any breaking changes or important notes
```

### Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request

## Adding New Features

### Adding a New CLI Command

1. Define the command in `src/pdf_context_narrator/cli.py`:

```python
@app.command()
def new_command(
    arg: str = typer.Argument(..., help="Argument description"),
    option: str = typer.Option("default", help="Option description"),
) -> None:
    """
    Command description.
    """
    logger.info(f"Executing new_command with {arg}")
    # Implementation here
```

2. Add tests in `tests/test_cli.py`:

```python
def test_new_command():
    """Test the new_command."""
    result = runner.invoke(app, ["new_command", "test_arg"])
    assert result.exit_code == 0
    assert "expected output" in result.stdout
```

3. Update the README with usage examples

### Adding Configuration Options

1. Add the setting in `src/pdf_context_narrator/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings
    new_setting: str = "default_value"
```

2. Add to `.env.example`:

```
PDF_CN_NEW_SETTING=default_value
```

3. Update documentation

## Documentation

- Keep the README.md up to date
- Add docstrings to all public functions and classes
- Update CONTRIBUTING.md for new development processes
- Add examples for new features

## Release Process

(To be defined as the project matures)

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Provide detailed information for bug reports

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue for any questions about contributing!
