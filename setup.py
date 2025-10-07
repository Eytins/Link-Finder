"""Setup configuration for Articulate Course URL Scanner."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="articulate-scanner",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Extract and verify URLs from Articulate Rise courses",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/articulate-scanner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "selenium>=4.0.0",
        "beautifulsoup4>=4.9.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "articulate-scanner=articulate_scanner.cli:main",
        ],
    },
)
