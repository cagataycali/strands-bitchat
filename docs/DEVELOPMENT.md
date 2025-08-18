# Development Guide

## Building the Package

### Prerequisites

Install build dependencies:
```bash
pip install --upgrade pip setuptools wheel build twine
```

### Build Process

1. **Clean build artifacts:**
   ```bash
   python build_and_publish.py --clean-only
   ```

2. **Build and check package:**
   ```bash
   python build_and_publish.py --check
   ```

3. **Test upload to Test PyPI:**
   ```bash
   python build_and_publish.py --test
   ```

4. **Upload to production PyPI:**
   ```bash
   python build_and_publish.py --prod
   ```

## Manual Build Commands

If you prefer manual control:

### Build Package
```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info/ src/*.egg-info/

# Build package
python -m build

# Check package
python -m twine check dist/*
```

### Upload to PyPI

#### Test PyPI (recommended first)
```bash
python -m twine upload --repository testpypi dist/*
```

#### Production PyPI
```bash
python -m twine upload dist/*
```

## Testing the Package

### Local Testing
```bash
# Install in development mode
pip install -e .[dev]

# Run tests
pytest tests/

# Test import
python -c "from src.tools.bitchat import bitchat; print('✅ Import successful')"
```

### Test PyPI Installation
```bash
# Install from test PyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ strands-bitchat

# Test CLI
strands-bitchat

# Test import
python -c "from strands_bitchat import bitchat; print('✅ Package working')"
```

## Version Management

Update version in these files:
- `setup.py` (version parameter)
- `pyproject.toml` (version field)
- `src/__init__.py` (__version__ variable)

## Package Structure

```
strands-bitchat/
├── src/
│   ├── __init__.py
│   └── tools/
│       ├── __init__.py
│       └── bitchat.py          # Main BitChat tool
├── tests/
│   ├── __init__.py
│   └── test_bitchat.py
├── docs/
│   ├── INSTALLATION.md
│   └── DEVELOPMENT.md
├── agent.py                    # Main CLI entry point
├── setup.py                    # Setup configuration
├── pyproject.toml             # Modern Python packaging
├── requirements.txt           # Dependencies
├── MANIFEST.in               # Package manifest
├── LICENSE                   # MIT License
├── README.md                 # Main documentation
└── build_and_publish.py      # Build automation script
```

## Quality Checks

### Code Formatting
```bash
# Format code
black .

# Check formatting
black --check .
```

### Type Checking
```bash
mypy src/
```

### Linting
```bash
flake8 src/
```

## Release Checklist

- [ ] Update version numbers
- [ ] Update CHANGELOG.md
- [ ] Run tests: `pytest tests/`
- [ ] Build package: `python build_and_publish.py --check`
- [ ] Test on Test PyPI: `python build_and_publish.py --test`
- [ ] Test installation from Test PyPI
- [ ] Upload to production: `python build_and_publish.py --prod`
- [ ] Verify on PyPI: https://pypi.org/project/strands-bitchat/
- [ ] Test installation from PyPI: `pip install strands-bitchat`
- [ ] Create GitHub release tag

## Troubleshooting

### Build Issues

**Missing files in package:**
- Check `MANIFEST.in`
- Verify `package_data` in `setup.py`

**Import errors:**
- Ensure `__init__.py` files exist
- Check module paths in `setup.py`

**Permission errors:**
- Use API tokens for PyPI upload
- Configure `.pypirc` file

### PyPI Upload Issues

**Authentication:**
```bash
# Configure PyPI credentials
pip install keyring
python -m twine upload dist/* --username __token__ --password YOUR_API_TOKEN
```

**Duplicate version:**
- Increment version number
- Cannot re-upload same version to PyPI

## API Tokens

Create API tokens at:
- Test PyPI: https://test.pypi.org/manage/account/token/
- Production PyPI: https://pypi.org/manage/account/token/

Configure in `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = your-production-token

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = your-test-token
```