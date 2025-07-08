#!/usr/bin/env python3
"""
Verification script to check if the project is properly set up.
"""
import sys
import importlib
from pathlib import Path


def check_imports():
    """Check if all required modules can be imported."""
    print("🔍 Checking imports...")
    print("  ⚠️  Note: Import checks require dependencies to be installed")
    print("  💡 Run 'make setup' to install dependencies first")

    modules_to_check = [
        "src.core",
        "src.core.models",
        "src.core.interfaces",
        "src.core.service",
        "src.infrastructure",
        "src.infrastructure.http_client",
        "src.infrastructure.html_parser",
        "src.infrastructure.link_classifier",
        "src.infrastructure.formatters",
        "src.infrastructure.local_storage",
        "src.settings",
        "src.logging",
    ]

    failed_imports = []

    for module in modules_to_check:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ⚠️  {module}: {e}")
            failed_imports.append(module)

    return failed_imports


def check_files():
    """Check if all required files exist."""
    print("\n📁 Checking file structure...")

    required_files = [
        "pyproject.toml",
        "Makefile",
        "README.md",
        "src/__init__.py",
        "src/core/__init__.py",
        "src/infrastructure/__init__.py",
        "src/api/__init__.py",
        "src/functions/__init__.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "docker/Dockerfile",
        "docker/docker-compose.yml",
        "azure-functions/host.json",
    ]

    missing_files = []

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)

    return missing_files


def check_directories():
    """Check if all required directories exist."""
    print("\n📂 Checking directory structure...")

    required_dirs = [
        "src",
        "src/core",
        "src/infrastructure",
        "src/api",
        "src/functions",
        "tests",
        "tests/unit",
        "tests/integration",
        "docker",
        "azure-functions",
        "docs",
        "scripts",
    ]

    missing_dirs = []

    for dir_path in required_dirs:
        if Path(dir_path).is_dir():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/")
            missing_dirs.append(dir_path)

    return missing_dirs


def main():
    """Main verification function."""
    print("🚀 Web Content Extractor - Setup Verification")
    print("=" * 50)

    # Check imports
    failed_imports = check_imports()

    # Check files
    missing_files = check_files()

    # Check directories
    missing_dirs = check_directories()

    # Summary
    print("\n📊 Summary:")
    print("=" * 50)

    if not missing_files and not missing_dirs:
        print("🎉 Project structure is properly set up!")
        if failed_imports:
            print("⚠️  Import checks failed (expected if dependencies not installed)")
        print("\nNext steps:")
        print("  1. Run 'make setup' to install dependencies")
        print("  2. Run 'make verify' to verify after installation")
        print("  3. Run 'make test' to run the test suite")
        print("  4. Run 'make run' to test the application")
        return 0
    else:
        print("❌ Some issues found:")

        if missing_files:
            print(f"  - {len(missing_files)} missing files")

        if missing_dirs:
            print(f"  - {len(missing_dirs)} missing directories")

        print("\nPlease fix these issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
