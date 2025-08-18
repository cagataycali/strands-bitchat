"""
Tests for the BitChat tool
"""

import pytest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_bitchat_import():
    """Test that we can import the bitchat tool."""
    try:
        from tools.bitchat import bitchat

        assert bitchat is not None
        print("✅ BitChat tool imported successfully")
    except ImportError as e:
        pytest.skip(f"BitChat dependencies not available: {e}")


def test_bitchat_tool_signature():
    """Test that the bitchat tool has the expected signature."""
    try:
        from tools.bitchat import bitchat

        # Test that it's callable
        assert callable(bitchat)

        # Test basic status call (should not require BitChat to be running)
        result = bitchat(action="status")
        assert isinstance(result, dict)
        assert "status" in result
        assert "content" in result

        print("✅ BitChat tool signature test passed")
    except ImportError as e:
        pytest.skip(f"BitChat dependencies not available: {e}")


def test_bitchat_invalid_action():
    """Test that invalid actions are handled properly."""
    try:
        from tools.bitchat import bitchat

        result = bitchat(action="invalid_action")
        assert result["status"] == "error"
        assert (
            "❌ BitChat is not running. Use action='start' first."
            in result["content"][0]["text"]
        )

        print("✅ BitChat invalid action handling test passed")
    except ImportError as e:
        pytest.skip(f"BitChat dependencies not available: {e}")


def test_package_metadata():
    """Test package metadata."""
    try:
        import src

        assert hasattr(src, "__version__")
        assert hasattr(src, "__author__")
        assert src.__version__ == "1.0.0"
        assert src.__author__ == "Cagatay Cali"

        print("✅ Package metadata test passed")
    except ImportError as e:
        pytest.skip(f"Package not available: {e}")


if __name__ == "__main__":
    print("🧪 Running BitChat tests...")

    test_bitchat_import()
    test_bitchat_tool_signature()
    test_bitchat_invalid_action()
    test_package_metadata()

    print("✅ All tests passed!")
