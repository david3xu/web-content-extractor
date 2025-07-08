#!/usr/bin/env python3
"""
Setup fix script for Web Content Extractor.
Helps resolve common installation and setup issues.
"""
import subprocess  # nosec
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )  # nosec
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def check_poetry_installed() -> bool:
    """Check if Poetry is installed."""
    try:
        subprocess.run(
            ["poetry", "--version"], check=True, capture_output=True
        )  # nosec
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_pre_commit_installed() -> bool:
    """Check if pre-commit is available in Poetry environment."""
    try:
        subprocess.run(
            ["poetry", "run", "pre-commit", "--version"],
            check=True,
            capture_output=True,
        )  # nosec
        return True
    except subprocess.CalledProcessError:
        return False


def main() -> None:
    """Main fix function."""
    print("🔧 Web Content Extractor - Setup Fix Script")
    print("=" * 50)

    # Check if we're in the project directory
    if not Path("pyproject.toml").exists():
        print(
            "❌ Error: pyproject.toml not found. Please run this script from the project root directory."
        )
        sys.exit(1)

    # Step 1: Check Poetry installation
    if not check_poetry_installed():
        print("📦 Installing Poetry...")
        if not run_command("pip install poetry", "Installing Poetry"):
            print(
                "❌ Failed to install Poetry. Please install it manually: pip install poetry"
            )
            sys.exit(1)

    # Step 2: Install dependencies with dev group
    print("\n📦 Installing project dependencies...")
    if not run_command("poetry install --with dev", "Installing dependencies"):
        print("❌ Failed to install dependencies. Trying alternative approach...")

        # Try clearing cache and reinstalling
        run_command("poetry cache clear --all pypi", "Clearing Poetry cache")
        if not run_command(
            "poetry install --with dev --no-cache", "Reinstalling dependencies"
        ):
            print(
                "❌ Failed to install dependencies. Please check your Python environment."
            )
            sys.exit(1)

    # Step 3: Check pre-commit installation
    if not check_pre_commit_installed():
        print("\n🔧 Installing pre-commit...")
        if not run_command(
            "poetry run pip install pre-commit", "Installing pre-commit"
        ):
            print("❌ Failed to install pre-commit. Continuing without it...")
        else:
            # Install pre-commit hooks
            run_command("poetry run pre-commit install", "Installing pre-commit hooks")

    # Step 4: Create necessary directories
    print("\n📁 Creating directories...")
    for directory in ["output", "logs"]:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")

    # Step 5: Verify setup
    print("\n🔍 Verifying setup...")
    if run_command(
        "poetry run python -c 'import src; print(\"✅ Import successful\")'",
        "Testing imports",
    ):
        print("✅ Setup verification completed successfully")
    else:
        print("❌ Setup verification failed. Please check the error messages above.")
        sys.exit(1)

    print("\n🎉 Setup fix completed successfully!")
    print("\nNext steps:")
    print("1. Run 'make run' to test the extraction")
    print("2. Run 'make test' to run the test suite")
    print("3. Run 'web-extractor --help' to see available commands")


if __name__ == "__main__":
    main()
