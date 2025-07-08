#!/usr/bin/env python3

import argparse
import sys
import json
from pathlib import Path
import http.server
import socketserver
import threading
from .config.settings import Settings
from .extractors.web_content_extractor import WebContentExtractor
from .models.exceptions import WebExtractionError


def main():
    parser = argparse.ArgumentParser(description='Extract and categorize web content links')
    parser.add_argument('url', nargs='?', help='URL to extract content from')
    parser.add_argument('--format', choices=['json', 'console'], default='json',
                       help='Output format (default: json)')
    parser.add_argument('--output-file', action='store_true',
                       help='Save output to file')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--serve', action='store_true',
                       help='Start a local HTTP server on port 8000')
    parser.add_argument('--port', type=int, default=8000,
                       help='Port for the HTTP server (default: 8000)')

    args = parser.parse_args()

    # If serve flag is set, start HTTP server
    if args.serve:
        start_server(args.port)
        return

    # Regular CLI mode - extract from URL
    if not args.url:
        parser.print_help()
        sys.exit(1)

    try:
        # Load configuration
        settings = Settings(args.config) if args.config else Settings()

        # Initialize extractor
        extractor = WebContentExtractor(
            timeout=settings.request_timeout,
            max_retries=settings.max_retry_attempts,
            user_agent=settings.user_agent,
            output_directory=settings.output_directory
        )

        # Extract and process
        if args.output_file:
            file_path = extractor.extract_and_export(
                args.url,
                output_format=args.format,
                export_to_file=True
            )
            print(f"Results exported to: {file_path}")
        else:
            output = extractor.extract_and_export(
                args.url,
                output_format=args.format,
                export_to_file=False
            )
            print(output)

        extractor.close()

    except WebExtractionError as e:
        print(f"Extraction error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


class HttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            health_data = {
                "status": "healthy",
                "service": "web-content-extractor"
            }
            self.wfile.write(json.dumps(health_data).encode())
            return

        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())


def start_server(port=8000):
    handler = HttpRequestHandler

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Server running at http://localhost:{port}/")
        print(f"Health check: http://localhost:{port}/health")
        print("Press Ctrl+C to stop")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()


if __name__ == "__main__":
    main()
