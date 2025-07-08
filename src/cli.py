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
    ContextAwareClassifier,
    LocalFileStorage,
    OutputFormat,
    OutputFormatters,
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


@app.command("crawl")  # type: ignore[misc]
def crawl_command(
    url: str = typer.Argument(..., help="Starting URL for crawling"),
    max_pages: int = typer.Option(
        5, "--max-pages", "-m", help="Maximum number of pages to crawl"
    ),
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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output"),
) -> None:
    """
    Crawl multiple pages and categorize links.
    """
    # Configure logging
    setup_logging(level="DEBUG" if verbose else "INFO")

    # Show startup banner
    _print_banner()

    # Run crawling
    try:
        result: ExtractionResult = asyncio.run(_crawl(url, max_pages))

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
    link_classifier = ContextAwareClassifier()  # New implementation
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
    result, _ = await service.extract_and_classify(
        url, save_result
    )  # Unpack result and ignore content

    # Handle assets after extraction completed
    await _handle_assets(result, http_client, output_dir)

    return result


async def _crawl(url: str, max_pages: int) -> ExtractionResult:
    """Helper function to perform multi-page crawling"""
    # Create components
    http_client = AsyncHttpClient()
    link_parser = BeautifulSoupLinkParser()
    link_classifier = ContextAwareClassifier()
    storage = LocalFileStorage()

    # Ensure output directory exists
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch content and save raw HTML for inspection
    logger.debug("attempting_to_fetch_raw_html", url=url)
    raw_html_content = await http_client.extract_content(url)
    raw_html_path = output_dir / "raw_page_content.html"
    raw_html_path.write_text(raw_html_content)
    logger.info("raw_html_saved_successfully", path=str(raw_html_path), url=url)

    # Create service
    service = ExtractionService(
        content_extractor=http_client,
        link_parser=link_parser,
        link_classifier=link_classifier,
        result_storage=storage,
    )

    # Perform crawling
    result = await service.crawl_and_extract(url, max_pages)

    # Handle assets for aggregated result
    await _handle_assets(result, http_client, output_dir)

    return result


# ---------------------------------------------------------------------------
# Asset utilities
# ---------------------------------------------------------------------------


async def _handle_assets(
    result: ExtractionResult, http_client: AsyncHttpClient, output_dir: Path
) -> None:
    """Download PDFs and write YouTube link JSON for a given extraction result."""

    # 1. Download PDFs
    pdf_dir = output_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    unique_pdfs: dict[str, str] = {}
    for link in result.pdf_links:
        url_str = str(link.url)
        if url_str not in unique_pdfs:
            # Use link text as filename when possible; otherwise derive from URL
            filename = _derive_filename(link.link_text, url_str)
            unique_pdfs[url_str] = filename

    if unique_pdfs:
        import httpx  # Lazy import to avoid overhead if no PDFs

        logger.info("downloading_pdfs", count=len(unique_pdfs))
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            for url_str, filename in unique_pdfs.items():
                dest_path = pdf_dir / filename
                if dest_path.exists():
                    logger.debug("pdf_already_downloaded", path=str(dest_path))
                    continue
                try:
                    resp = await client.get(url_str)
                    resp.raise_for_status()
                    dest_path.write_bytes(resp.content)
                    logger.debug("pdf_downloaded", url=url_str, path=str(dest_path))
                except Exception as e:
                    logger.warning("pdf_download_failed", url=url_str, error=str(e))

    # 2. Save YouTube links as JSON
    youtube_urls = sorted({str(link.url) for link in result.youtube_links})
    if youtube_urls:
        import json

        json_path = output_dir / "youtube_links.json"
        json_path.write_text(json.dumps(youtube_urls, indent=2))
        logger.info("youtube_links_saved", path=str(json_path), count=len(youtube_urls))


def _derive_filename(link_text: str, url_str: str) -> str:
    """Derive a safe filename for the PDF to be saved."""
    import re
    from urllib.parse import urlparse

    # Prefer link text if it ends with .pdf
    candidate = link_text.strip()
    if not candidate.lower().endswith(".pdf"):
        # Fallback to last part of URL path
        path_part = urlparse(url_str).path.rsplit("/", 1)[-1]
        candidate = path_part or "downloaded.pdf"

    # Sanitize filename (remove query params etc.)
    candidate = re.sub(r"[\?&#].*$", "", candidate)
    # Replace forbidden chars
    candidate = re.sub(r"[^A-Za-z0-9._-]", "_", candidate)
    return candidate


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
    url: str = "https://tutorial.nlp-tlp.org/ai-engineer-bootcamp",
) -> None:
    console.print(Panel("[bold green]🔍 Running extraction example...[/bold green]"))

    # Use the _crawl helper function for the demo
    try:
        result = await _crawl(url, max_pages=100)  # Crawl deeper for demo

        # Debug output - show sample links (already done in _crawl output)
        console.print("\n[bold]Debug: Sample Links Found (from crawl)[/bold]")
        for i, link in enumerate(result.get_all_links()[:10]):
            console.print(
                f"  {i+1}. [{link.link_type.value}] {link.link_text[:50]}... -> {str(link.url)[:80]}..."
            )

        formatters = OutputFormatters()
        formatted_text = formatters.format_result(result, OutputFormat.TEXT)
        console.print(formatted_text)

    except Exception as e:
        console.print(f"\n❌ [bold red]Error:[/bold red] {e}")
        console.print_exception()


def main() -> None:
    """Main entry point for the application"""
    app()
