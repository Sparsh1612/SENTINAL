#!/usr/bin/env python3
"""
Setup script for Sentinel Fraud Detection System
"""

from setuptools import setup, find_packages
from pathlib import Path
import re

# Read the README file
def read_readme():
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8")
    return "Sentinel - Credit Card Fraud Detection System"

# Read requirements
def read_requirements():
    requirements_path = Path(__file__).parent / "requirements.txt"
    if requirements_path.exists():
        return [line.strip() for line in requirements_path.read_text().splitlines() 
                if line.strip() and not line.startswith("#")]
    return []

# Get version from __init__.py
def get_version():
    init_path = Path(__file__).parent / "backend" / "__init__.py"
    if init_path.exists():
        content = init_path.read_text(encoding="utf-8")
        version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', content, re.M)
        if version_match:
            return version_match.group(1)
    return "1.0.0"

# Package configuration
setup(
    name="sentinel-fraud-detection",
    version=get_version(),
    author="Sparsh",
    author_email="sparsh@example.com",
    description="Enterprise-grade credit card fraud detection system with explainable AI",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/sentinel",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/sentinel/issues",
        "Documentation": "https://github.com/your-org/sentinel/docs",
        "Source Code": "https://github.com/your-org/sentinel",
    },
    packages=find_packages(include=[
        "backend*",
        "cli*",
        "plugins*"
    ], exclude=[
        "data*",
        "frontend*",
        "tests*",
        "docs*"
    ]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: Security",
        "Topic :: Database",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "httpx>=0.25.0",
            "factory-boy>=3.2.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
            "sphinx-autodoc-typehints>=1.23.0",
        ],
        "production": [
            "gunicorn>=21.0.0",
            "uvicorn[standard]>=0.24.0",
            "prometheus-client>=0.19.0",
            "structlog>=23.0.0",
        ],
        "ml": [
            "tensorflow>=2.15.0",
            "torch>=2.1.0",
            "scikit-learn>=1.3.0",
            "xgboost>=2.0.0",
            "lightgbm>=4.0.0",
            "optuna>=3.0.0",
        ],
        "streaming": [
            "kafka-python>=2.0.0",
            "confluent-kafka>=2.0.0",
            "aiokafka>=0.8.0",
        ],
        "monitoring": [
            "prometheus-client>=0.19.0",
            "grafana-api>=1.0.0",
            "elasticsearch>=8.0.0",
            "opentelemetry-api>=1.20.0",
            "opentelemetry-sdk>=1.20.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "sentinel=cli.main:main",
            "sentinel-api=backend.main:main",
            "sentinel-cli=cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "backend": [
            "*.py",
            "api/*.py",
            "core/*.py",
            "models/*.py",
            "schemas/*.py",
            "streaming/*.py",
            "utils/*.py",
        ],
        "cli": [
            "*.py",
            "commands/*.py",
        ],
        "plugins": [
            "*.py",
            "examples/*.py",
        ],
    },
    data_files=[
        ("config", ["backend/config.py"]),
        ("data/models", []),
        ("data/processed", []),
        ("data/raw", []),
        ("docs", [
            "docs/API.md",
            "docs/ARCHITECTURE.md",
            "docs/DEPLOYMENT.md",
            "docs/PLUGINS.md",
        ]),
        ("tests", [
            "tests/__init__.py",
            "tests/test_api/__init__.py",
            "tests/test_core/__init__.py",
            "tests/test_models/__init__.py",
        ]),
    ],
    zip_safe=False,
    keywords=[
        "fraud-detection",
        "credit-card",
        "machine-learning",
        "ai",
        "security",
        "fintech",
        "risk-management",
        "anomaly-detection",
        "explainable-ai",
        "real-time",
        "streaming",
        "api",
        "dashboard",
        "monitoring",
    ],
    platforms=["any"],
    license="MIT",
    maintainer="Sparsh",
    maintainer_email="sparsh@example.com",
    download_url="https://github.com/your-org/sentinel/archive/refs/tags/v1.0.0.tar.gz",
    provides=["sentinel"],
    requires_python=">=3.8",
    setup_requires=[
        "setuptools>=45.0.0",
        "wheel>=0.37.0",
    ],
    test_suite="tests",
    tests_require=[
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
    ],
    options={
        "bdist_wheel": {
            "universal": True,
        },
    },
    # Additional metadata
    metadata_version="2.1",
    summary="Enterprise-grade credit card fraud detection system",
    home_page="https://github.com/your-org/sentinel",
    project_url={
        "Homepage": "https://github.com/your-org/sentinel",
        "Documentation": "https://github.com/your-org/sentinel/docs",
        "Repository": "https://github.com/your-org/sentinel",
        "Issues": "https://github.com/your-org/sentinel/issues",
        "Changelog": "https://github.com/your-org/sentinel/blob/main/CHANGELOG.md",
    },
)

if __name__ == "__main__":
    setup()
