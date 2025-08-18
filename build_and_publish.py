#!/usr/bin/env python3
"""
Build and publish script for strands-bitchat package

Usage:
    python build_and_publish.py --check    # Check package without uploading
    python build_and_publish.py --test     # Upload to test PyPI
    python build_and_publish.py --prod     # Upload to production PyPI
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)


def clean_build():
    """Clean up build artifacts."""
    print("🧹 Cleaning up build artifacts...")

    dirs_to_remove = ["build", "dist", "src/*.egg-info", "*.egg-info"]

    for pattern in dirs_to_remove:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                print(f"Removing directory: {path}")
                shutil.rmtree(path)
            elif path.is_file():
                print(f"Removing file: {path}")
                path.unlink()


def install_build_deps():
    """Install build dependencies."""
    print("📦 Installing build dependencies...")
    run_command("pip install --upgrade pip setuptools wheel build twine")


def build_package():
    """Build the package."""
    print("🔨 Building package...")
    run_command("python -m build")

    # Check if build artifacts exist
    dist_files = list(Path("dist").glob("*"))
    if not dist_files:
        print("❌ No distribution files found in dist/")
        sys.exit(1)

    print("✅ Build completed successfully!")
    print("📦 Distribution files:")
    for file in dist_files:
        print(f"  - {file}")


def check_package():
    """Check the package with twine."""
    print("🔍 Checking package with twine...")
    run_command("python -m twine check dist/*")
    print("✅ Package check passed!")


def upload_to_test_pypi():
    """Upload to test PyPI."""
    print("🚀 Uploading to Test PyPI...")
    print("You'll need to enter your Test PyPI credentials.")
    run_command("python -m twine upload --repository testpypi dist/*")
    print("✅ Uploaded to Test PyPI!")
    print("🔗 View at: https://test.pypi.org/project/strands-bitchat/")


def upload_to_pypi():
    """Upload to production PyPI."""
    print("🚀 Uploading to PyPI...")
    print("You'll need to enter your PyPI credentials.")

    # Ask for confirmation
    response = input("Are you sure you want to upload to production PyPI? (yes/no): ")
    if response.lower() != "yes":
        print("❌ Upload cancelled.")
        sys.exit(0)

    run_command("python -m twine upload dist/*")
    print("✅ Uploaded to PyPI!")
    print("🔗 View at: https://pypi.org/project/strands-bitchat/")


def test_installation():
    """Test installation of the package."""
    print("🧪 Testing package installation...")

    # Try to install from test PyPI
    print("Testing installation from Test PyPI...")
    run_command(
        "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ strands-bitchat",
        check=False,
    )

    # Test import
    try:
        import src.tools.bitchat

        print("✅ Package import test passed!")
    except ImportError as e:
        print(f"❌ Package import test failed: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Build and publish strands-bitchat package"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check package without uploading"
    )
    parser.add_argument("--test", action="store_true", help="Upload to test PyPI")
    parser.add_argument("--prod", action="store_true", help="Upload to production PyPI")
    parser.add_argument(
        "--clean-only", action="store_true", help="Only clean build artifacts"
    )

    args = parser.parse_args()

    if args.clean_only:
        clean_build()
        return

    print("🔐 BitChat Strands Agent - Build & Publish")
    print("==========================================")

    # Clean up previous builds
    clean_build()

    # Install dependencies
    install_build_deps()

    # Build package
    build_package()

    # Check package
    check_package()

    if args.check:
        print("✅ Package check completed successfully!")
        return

    if args.test:
        upload_to_test_pypi()
        test_installation()
    elif args.prod:
        upload_to_pypi()
    else:
        print("📋 Package built and checked successfully!")
        print("Next steps:")
        print("  --check : Check package only")
        print("  --test  : Upload to Test PyPI")
        print("  --prod  : Upload to production PyPI")


if __name__ == "__main__":
    main()
