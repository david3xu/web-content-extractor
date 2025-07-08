"""
Command-line interface for web content extraction.
"""
import asyncio
import sys
from pathlib import Path

import structlog
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

from src.core import ExtractionService
from src.core.exceptions import ContextualExtractionError
from src.core.models import ExtractionResult
from src.infrastructure import (
    AsyncHttpClient,
    BeautifulSoupLinkParser,
    LocalFileStorage,
    OutputFormat,
    OutputFormatters,
    RegexLinkClassifier,
)
from src.logging import setup_logging
from src.settings import settings

# Initialize logger
logger = structlog.get_logger(__name__)

# Create Typer app
app = typer.Typer(
    help="Web Content Extractor - Extract and categorize links from web pages",
    add_completion=False,
)

# Create console
console = Console()


@app.command("extract")  # type: ignore[misc]
def extract_command(
    url: str = typer.Argument(..., help="URL to extract content from"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.TEXT,
        "--format",
        "-f",
        help="Output format (json, text, markdown, csv)",
    ),
    output_file: Path
    | None = typer.Option(
        None, "--output", "-o", help="Output file path (default: prints to console)"
    ),
    save_result: bool = typer.Option(
        False, "--save", "-s", help="Save extraction result to storage"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
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
        result: ExtractionResult = asyncio.run(_extract(url, save_result))

        # Format result
        formatters = OutputFormatters()
        formatted_output: str = formatters.format_result(result, output_format)

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

    except ContextualExtractionError as e:
        console.print(f"\n❌ [bold red]Extraction Error:[/bold red] {e}")
        if verbose:
            debug_info = e.get_debug_info()
            console.print(
                f"🔍 [dim]Correlation ID: {debug_info['context']['correlation_id']}[/dim]"
            )
            console.print(
                f"🔍 [dim]Elapsed time: {debug_info['context']['elapsed_time']:.2f}s[/dim]"
            )
        sys.exit(1)
    except Exception as e:  # Catch all other unexpected exceptions
        console.print(f"\n❌ [bold red]An unexpected error occurred:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@app.command("batch")  # type: ignore[misc]
def batch_command(
    urls: list[str] = typer.Argument(..., help="URLs to extract content from"),
    output_dir: Path = typer.Option(
        settings.output_directory,
        "--output-dir",
        "-o",
        help="Directory to save results",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.JSON,
        "--format",
        "-f",
        help="Output format (json, text, markdown, csv)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
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
    results: list[ExtractionResult] = []
    failed: list[tuple[str, str]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
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


@app.command("serve")  # type: ignore[misc]
def serve_command(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(
        False, "--reload", help="Auto-reload server on code changes"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
) -> None:
    """
    Start API server for web content extraction.
    """
    # Configure logging
    setup_logging(level="DEBUG" if verbose else "INFO")

    try:
        import uvicorn

        from src.api.app import create_app  # Import create_app

    except ImportError:
        console.print("[bold red]Error:[/bold red] API dependencies not installed.")
        console.print(
            "Install API dependencies with: [bold]pip install web-content-extractor[api][/bold]"
        )
        sys.exit(1)

    # Print banner
    _print_banner()
    console.print(f"[bold]🚀 Starting API server at http://{host}:{port}[/bold]\n")

    # Start server
    uvicorn.run(
        create_app(),  # Call create_app to get the FastAPI app instance
        host=host,
        port=port,
        reload=reload,
        log_level="debug" if verbose else "info",
    )


@app.command("version")  # type: ignore[misc]
def version_command() -> None:
    """Show version information."""
    from importlib.metadata import version

    try:
        pkg_version: str = version("web-content-extractor")
    except Exception:  # Catch specific exception if possible, or leave as is if not.
        pkg_version = "unknown"

    console.print(f"Web Content Extractor v{pkg_version}")
    console.print(f"Python {sys.version}")


async def _extract(url: str, save_result: bool = False) -> ExtractionResult:
    """Helper function to perform extraction"""
    # Create components
    http_client = AsyncHttpClient()
    link_parser = BeautifulSoupLinkParser()
    link_classifier = RegexLinkClassifier()
    storage = LocalFileStorage()

    # Ensure output directory exists
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch content and save raw HTML for inspection
    logger.debug("attempting_to_fetch_raw_html", url=url)
    # The 'get' method should be part of ContentExtractor interface if used,
    # but AsyncHttpClient implements ContentExtractor, which has extract_content
    # It seems 'get' is an internal method or not part of the protocol.
    # Let's use extract_content instead, which is part of the ContentExtractor protocol.
    raw_html_content = await http_client.extract_content(url)
    raw_html_path = output_dir / "raw_page_content.html"
    raw_html_path.write_text(raw_html_content)
    logger.info("raw_html_saved_successfully", path=str(raw_html_path), url=url)

    # Create service
    service = ExtractionService(
        content_extractor=http_client,
        link_parser=link_parser,
        link_classifier=link_classifier,
        result_storage=storage if save_result else None,
    )

    # Perform extraction
    return await service.extract_and_classify(url, save_result)


def _print_banner() -> None:
    """Print application banner"""
    console.print(
        Panel.fit(
            "[bold blue]Web Content Extractor[/bold blue]\n"
            "[dim]Extract and categorize links from web pages[/dim]",
            border_style="blue",
        )
    )


async def demo(
    url: str = "https://www.python.org",
) -> None:  # Default URL for demonstration
    """Demonstrates the full extraction and classification process."""
    console.print(Panel("[bold green]🔍 Running extraction example...[/bold green]"))

    service = ExtractionService(
        content_extractor=AsyncHttpClient(),
        link_parser=BeautifulSoupLinkParser(),
        link_classifier=RegexLinkClassifier(),
        result_storage=LocalFileStorage(),
    )

    try:
        result = await service.extract_and_classify(url, save_result=True)

        formatters = OutputFormatters()
        formatted_text = formatters.format_result(result, OutputFormat.TEXT)

        console.print(formatted_text)
        if result.metadata:
            console.print(
                f"\n✅ Result saved to [bold]{result.metadata.correlation_id}.json[/bold]"
            )
        else:
            console.print(
                "\n✅ Extraction completed, but no metadata found to save result."
            )

    except ContextualExtractionError as e:
        console.print(f"\n❌ [bold red]Extraction Error:[/bold red] {e}")
        debug_info = e.get_debug_info()
        console.print(
            f"🔍 [dim]Correlation ID: {debug_info['context']['correlation_id']}[/dim]"
        )
        console.print(
            f"🔍 [dim]Elapsed time: {debug_info['context']['elapsed_time']:.2f}s[/dim]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"\n❌ [bold red]Error:[/bold red] {e}")
        console.print_exception()
        sys.exit(1)


def main() -> None:
    """Main entry point for the application"""
    app()
