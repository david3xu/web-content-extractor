"""
Command-line interface for web content extraction.
"""
import asyncio
from typing import Optional, List
from pathlib import Path
import sys
import os

import structlog
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

from src.core import ExtractionService
from src.infrastructure import (
    AsyncHttpClient, BeautifulSoupLinkParser, RegexLinkClassifier,
    OutputFormatters, OutputFormat, LocalFileStorage
)
from src.settings import settings
from src.logging import setup_logging

# Initialize logger
logger = structlog.get_logger(__name__)

# Create Typer app
app = typer.Typer(
    help="Web Content Extractor - Extract and categorize links from web pages",
    add_completion=False,
)

# Create console
console = Console()


@app.command("extract")
def extract_command(
    url: str = typer.Argument(..., help="URL to extract content from"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.TEXT, "--format", "-f",
        help="Output format (json, text, markdown, csv)"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o",
        help="Output file path (default: prints to console)"
    ),
    save_result: bool = typer.Option(
        False, "--save", "-s",
        help="Save extraction result to storage"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show verbose output"
    )
) -> None:
    """
    Extract and categorize links from a web page.
    """
    # Configure logging
    setup_logging(level="DEBUG" if verbose else "INFO")

    # Show startup banner
    _print_banner()

    # Run extraction
    try:
        result = asyncio.run(_extract(url, save_result))

        # Format result
        formatters = OutputFormatters()
        formatted_output = formatters.format_result(result, output_format)

        # Output result
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(formatted_output)
            console.print(f"\n✅ Result saved to [bold]{output_file}[/bold]")
        else:
            if output_format == OutputFormat.JSON:
                console.print(Syntax(formatted_output, "json", theme="monokai"))
            elif output_format == OutputFormat.MARKDOWN:
                console.print(Syntax(formatted_output, "markdown", theme="monokai"))
            else:
                console.print(formatted_output)

    except Exception as e:
        console.print(f"\n❌ [bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command("batch")
def batch_command(
    urls: List[str] = typer.Argument(..., help="URLs to extract content from"),
    output_dir: Path = typer.Option(
        settings.output_directory, "--output-dir", "-o",
        help="Directory to save results"
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON, "--format", "-f",
        help="Output format (json, text, markdown, csv)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show verbose output"
    )
) -> None:
    """
    Extract and categorize links from multiple web pages.
    """
    # Configure logging
    setup_logging(level="DEBUG" if verbose else "INFO")

    # Show startup banner
    _print_banner()

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process URLs
    results = []
    failed = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for url in urls:
            task = progress.add_task(f"Processing {url}...", total=None)

            try:
                result = asyncio.run(_extract(url, True))
                results.append(result)
                progress.update(task, description=f"✅ Processed {url}")

            except Exception as e:
                progress.update(task, description=f"❌ Failed {url}")
                failed.append((url, str(e)))
                logger.error("batch_processing_error", url=url, error=str(e))

    # Show summary
    console.print(f"\n✅ Processed {len(results)} URLs successfully")
    if failed:
        console.print(f"❌ Failed to process {len(failed)} URLs")
        for url, error in failed:
            console.print(f"  - [bold red]{url}[/bold red]: {error}")


@app.command("serve")
def serve_command(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload server on code changes"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
) -> None:
    """
    Start API server for web content extraction.
    """
    # Configure logging
    setup_logging(level="DEBUG" if verbose else "INFO")

    try:
        import uvicorn
        from src.api import create_app
    except ImportError:
        console.print("[bold red]Error:[/bold red] API dependencies not installed.")
        console.print("Install API dependencies with: [bold]pip install web-content-extractor[api][/bold]")
        sys.exit(1)

    # Print banner
    _print_banner()
    console.print(f"[bold]🚀 Starting API server at http://{host}:{port}[/bold]\n")

    # Start server
    uvicorn.run(
        "src.api:create_app",
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if verbose else "info",
    )


@app.command("version")
def version_command() -> None:
    """Show version information."""
    from importlib.metadata import version
    try:
        pkg_version = version("web-content-extractor")
    except:
        pkg_version = "unknown"

    console.print(f"Web Content Extractor v{pkg_version}")
    console.print(f"Python {sys.version}")


async def _extract(url: str, save_result: bool = False):
    """Helper function to perform extraction"""
    # Create components
    http_client = AsyncHttpClient()
    link_parser = BeautifulSoupLinkParser()
    link_classifier = RegexLinkClassifier()
    storage = LocalFileStorage()

    # Create service
    service = ExtractionService(
        content_extractor=http_client,
        link_parser=link_parser,
        link_classifier=link_classifier,
        result_storage=storage if save_result else None
    )

    # Perform extraction
    return await service.extract_and_classify(url, save_result)


def _print_banner():
    """Print application banner"""
    console.print(Panel.fit(
        "[bold blue]Web Content Extractor[/bold blue]\n"
        "[dim]Extract and categorize links from web pages[/dim]",
        border_style="blue"
    ))


async def demo():
    """Run a demo extraction"""
    demo_url = "https://www.python.org"
    result = await _extract(demo_url)

    # Print summary table
    table = Table(title=f"Extraction Results for {demo_url}")
    table.add_column("Type", style="cyan")
    table.add_column("Count", style="magenta")

    table.add_row("PDF Links", str(len(result.pdf_links)))
    table.add_row("YouTube Links", str(len(result.youtube_links)))
    table.add_row("Other Links", str(len(result.other_links)))
    table.add_row("Total Links", str(result.total_links))

    console.print(table)

    return result


def main():
    """Main entry point for the application"""
    app()
