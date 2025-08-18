#!/usr/bin/env python3
"""
Setup script for strands-bitchat - Decentralized P2P Encrypted Chat Agent
"""

from setuptools import setup, find_packages


# Read the README file for long description
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "Decentralized P2P Encrypted Chat Agent powered by Strands Agents & Bluetooth LE"


# Read requirements from requirements.txt
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [
                line.strip() for line in fh if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        return [
            "strands-agents",
            "strands-agents[ollama]",
            "strands-agents-tools",
            "bleak>=0.20.0",
            "pybloom-live>=4.0.0",
            "lz4>=4.3.0",
            "aioconsole>=0.6.0",
            "cryptography>=41.0.0",
        ]


setup(
    name="strands-bitchat",
    version="1.0.6",
    author="Cagatay Cali",
    author_email="cagataycali@icloud.com",
    description="Decentralized P2P Encrypted Chat Agent powered by Strands Agents & Bluetooth LE",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/cagataycali/strands-bitchat",
    project_urls={
        "Bug Tracker": "https://github.com/cagataycali/strands-bitchat/issues",
        "Documentation": "https://github.com/cagataycali/strands-bitchat#readme",
        "Source Code": "https://github.com/cagataycali/strands-bitchat",
    },
    packages=find_packages(),
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml", "*.json"],
        "strands_bitchat": ["**/*.py"],
        "strands_bitchat.tools": ["*.py"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Internet",
        "Topic :: Security :: Cryptography",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "twine>=4.0.0",
            "build>=0.8.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "strands-bitchat=agent:main",
        ],
        "strands_tools": [
            "bitchat=src.tools.bitchat:bitchat",
        ],
    },
    keywords=[
        "strands-agents",
        "ai-agent",
        "bitchat",
        "p2p",
        "bluetooth",
        "encryption",
        "mesh-network",
        "decentralized",
        "privacy",
        "secure-chat",
        "noise-protocol",
        "ble",
        "agent-to-agent",
        "offline-communication",
    ],
    zip_safe=False,
    platforms=["any"],
    license="MIT",
    maintainer="Cagatay Cali",
    maintainer_email="cagataycali@icloud.com",
)
