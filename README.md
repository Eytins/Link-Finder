# Articulate Course URL Scanner

A powerful command-line tool to extract and verify URLs from Articulate Rise courses. This tool recursively scans course lessons, extracts all external links, and verifies their accessibility.

## Features

- 🔍 **Recursive Scanning**: Automatically discovers and scans linked Articulate courses
- ✅ **URL Verification**: Validates each URL and reports its status (working, broken, redirected)
- ⚡ **Parallel Processing**: Fast URL verification using concurrent requests
- 🎯 **Detailed Reports**: Comprehensive output showing URL status, location, and HTTP codes
- 🔧 **Flexible Options**: Customizable recursion depth, verification settings, and more

## Prerequisites

Before installation, ensure you have:

1. **Python 3.8 or higher**
   ```bash
   python --version
   ```

2. **Chrome Browser** installed on your system

3. **ChromeDriver** compatible with your Chrome version
   - Download from: https://chromedriver.chromium.org/downloads
   - Or install via package manager:
     ```bash
     # macOS
     brew install chromedriver
     
     # Ubuntu/Debian
     sudo apt-get install chromium-chromedriver
     
     # Windows (using Chocolatey)
     choco install chromedriver
     ```

## Installation

### Option 1: Install from Source (Recommended for Local Development)

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/Eytins/Link-Finder
   cd articulate_scanner
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # Activate on macOS/Linux
   source venv/bin/activate
   
   # Activate on Windows
   venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e .
   ```

   This installs the package in "editable" mode, allowing you to make changes to the code.

### Option 2: Install as a Package

1. **Navigate to the project directory**
   ```bash
   cd articulate-scanner
   ```

2. **Install using pip**
   ```bash
   pip install .
   ```

## Usage

### Basic Usage

Scan a course and verify all URLs:

```bash
articulate-scanner https://rise.articulate.com/share/your-course-id
```

### Options

```bash
articulate-scanner [OPTIONS] URL

Positional Arguments:
  url                   Articulate Rise course URL to scan

Options:
  -h, --help            Show help message and exit
  --max-depth N         Maximum recursion depth for linked courses (default: 2)
  --no-verify           Skip URL verification step
  --no-headless         Run browser in visible mode (not headless)
  --max-workers N       Maximum parallel workers for verification (default: 10)
  --quiet               Suppress progress messages
  --version             Show version number and exit
```
