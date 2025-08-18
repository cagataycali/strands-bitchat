"""
Tests for the BitChat tool
"""

import pytest


def test_bitchat_import():
    """Test that we can import the bitchat tool."""
    try:
        from strands_bitchat import bitchat

        assert bitchat is not None
        print("✅ BitChat tool imported successfully")
    except ImportError as e:
        pytest.skip(f"BitChat dependencies not available: {e}")


def test_bitchat_tool_signature():
    """Test that the bitchat tool has the expected signature."""
    try:
        from strands_bitchat import bitchat

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
        from strands_bitchat import bitchat

        result = bitchat(action="invalid_action")
        assert result["status"] == "error"
        assert (
            "❌ BitChat is not running. Use action='start' first."
            in result["content"][0]["text"]
        )

        print("✅ BitChat invalid action handling test passed")
    except ImportError as e:
        pytest.skip(f"BitChat dependencies not available: {e}")


def test_package():
    """Test package"""
    try:
        import strands_bitchat
    except ImportError as e:
        pytest.skip(f"Package not available: {e}")


if __name__ == "__main__":
    print("🧪 Running BitChat tests...")

    test_bitchat_import()
    test_bitchat_tool_signature()
    test_bitchat_invalid_action()
    test_package()

    print("✅ All tests passed!")
