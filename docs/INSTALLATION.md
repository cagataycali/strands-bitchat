# Installation Guide

## PyPI Installation (Recommended)

Install directly from PyPI:

```bash
pip install strands-bitchat
```

## Development Installation

For development or to install from source:

### 1. Clone the Repository
```bash
git clone https://github.com/cagataycali/strands-bitchat.git
cd strands-bitchat
```

### 2. Install in Development Mode
```bash
# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Or just the package
pip install -e .
```

### 3. Run Tests
```bash
pytest tests/
```

## Usage

### Command Line
After installation, you can run the agent directly:

```bash
strands-bitchat
```

### Python Import
```python
from strands import Agent
from strands_bitchat import bitchat

agent = Agent(tools=[bitchat])
agent("start bitchat")
```

## Requirements

- Python 3.8+
- Bluetooth Low Energy support
- Compatible with macOS, Linux, and Windows

## Dependencies

All dependencies are automatically installed:

- `strands-agents` - Core AI agent framework
- `strands-agents-tools` - Extended tool ecosystem  
- `bleak>=0.20.0` - Bluetooth Low Energy library
- `pybloom-live>=4.0.0` - Bloom filters for message deduplication
- `lz4>=4.3.0` - Fast compression
- `aioconsole>=0.6.0` - Async console input
- `cryptography>=41.0.0` - Cryptographic primitives

## Troubleshooting

### Bluetooth Permissions

**macOS:** Grant Bluetooth permission in System Preferences → Security & Privacy → Bluetooth

**Linux:** Ensure user is in `bluetooth` group:
```bash
sudo usermod -a -G bluetooth $USER
```

**Windows:** Enable Bluetooth in Device Manager

### Dependencies Issues

If you encounter dependency issues, try:

```bash
pip install --upgrade pip setuptools wheel
pip install strands-bitchat --force-reinstall
```