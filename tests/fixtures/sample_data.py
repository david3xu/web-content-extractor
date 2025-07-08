from src.models.extraction_models import ExtractedLink, LinkType, ExtractionMetadata, LinkCategorizationResult
from datetime import datetime


# Sample HTML content
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Sample Test Page</title>
</head>
<body>
    <h1>Sample Page for Testing</h1>
    <div>
        <p>This is a sample page with various links for testing purposes.</p>
        <ul>
            <li><a href="https://example.com/document.pdf">Sample PDF Document</a></li>
            <li><a href="https://example.com/another-doc.pdf">Another PDF</a></li>
            <li><a href="https://youtube.com/watch?v=abcdef">YouTube Video</a></li>
            <li><a href="https://youtu.be/123456">Short YouTube Link</a></li>
            <li><a href="https://example.com/page.html">Regular Web Page</a></li>
            <li><a href="https://example.com/another-page">Another Page</a></li>
            <li><a href="/relative-link">Relative Link</a></li>
        </ul>
    </div>
</body>
</html>
"""

# Sample extracted links
SAMPLE_LINKS = [
    ("https://example.com/document.pdf", "Sample PDF Document"),
    ("https://example.com/another-doc.pdf", "Another PDF"),
    ("https://youtube.com/watch?v=abcdef", "YouTube Video"),
    ("https://youtu.be/123456", "Short YouTube Link"),
    ("https://example.com/page.html", "Regular Web Page"),
    ("https://example.com/another-page", "Another Page"),
    ("https://example.com/relative-link", "Relative Link")
]

# Sample extracted link objects
SAMPLE_EXTRACTED_LINKS = [
    ExtractedLink(url="https://example.com/document.pdf", link_text="Sample PDF Document", link_type=LinkType.PDF),
    ExtractedLink(url="https://example.com/another-doc.pdf", link_text="Another PDF", link_type=LinkType.PDF),
    ExtractedLink(url="https://youtube.com/watch?v=abcdef", link_text="YouTube Video", link_type=LinkType.YOUTUBE),
    ExtractedLink(url="https://youtu.be/123456", link_text="Short YouTube Link", link_type=LinkType.YOUTUBE),
    ExtractedLink(url="https://example.com/page.html", link_text="Regular Web Page", link_type=LinkType.OTHER),
    ExtractedLink(url="https://example.com/another-page", link_text="Another Page", link_type=LinkType.OTHER),
    ExtractedLink(url="https://example.com/relative-link", link_text="Relative Link", link_type=LinkType.OTHER),
]

# Sample PDF links
SAMPLE_PDF_LINKS = [
    ExtractedLink(url="https://example.com/document.pdf", link_text="Sample PDF Document", link_type=LinkType.PDF),
    ExtractedLink(url="https://example.com/another-doc.pdf", link_text="Another PDF", link_type=LinkType.PDF)
]

# Sample YouTube links
SAMPLE_YOUTUBE_LINKS = [
    ExtractedLink(url="https://youtube.com/watch?v=abcdef", link_text="YouTube Video", link_type=LinkType.YOUTUBE),
    ExtractedLink(url="https://youtu.be/123456", link_text="Short YouTube Link", link_type=LinkType.YOUTUBE)
]

# Sample other links
SAMPLE_OTHER_LINKS = [
    ExtractedLink(url="https://example.com/page.html", link_text="Regular Web Page", link_type=LinkType.OTHER),
    ExtractedLink(url="https://example.com/another-page", link_text="Another Page", link_type=LinkType.OTHER),
    ExtractedLink(url="https://example.com/relative-link", link_text="Relative Link", link_type=LinkType.OTHER)
]

# Sample metadata
SAMPLE_METADATA = ExtractionMetadata(
    total_links_found=7,
    pdf_count=2,
    youtube_count=2,
    processing_time_seconds=0.5,
    page_title="Sample Test Page",
    extraction_timestamp=datetime(2023, 6, 1, 12, 0, 0)
)

# Sample categorization result
SAMPLE_CATEGORIZATION_RESULT = LinkCategorizationResult(
    source_url="https://example.com",
    pdf_links=SAMPLE_PDF_LINKS,
    youtube_links=SAMPLE_YOUTUBE_LINKS,
    other_links=SAMPLE_OTHER_LINKS,
    metadata=SAMPLE_METADATA
)

# Sample JSON output
SAMPLE_JSON_OUTPUT = """{
  "source_url": "https://example.com",
  "extraction_timestamp": "2023-06-01T12:00:00",
  "summary": {
    "total_links": 7,
    "pdf_count": 2,
    "youtube_count": 2,
    "other_count": 3
  },
  "pdf_links": [
    {
      "url": "https://example.com/document.pdf",
      "text": "Sample PDF Document",
      "type": "pdf",
      "is_valid": true
    },
    {
      "url": "https://example.com/another-doc.pdf",
      "text": "Another PDF",
      "type": "pdf",
      "is_valid": true
    }
  ],
  "youtube_links": [
    {
      "url": "https://youtube.com/watch?v=abcdef",
      "text": "YouTube Video",
      "type": "youtube",
      "is_valid": true
    },
    {
      "url": "https://youtu.be/123456",
      "text": "Short YouTube Link",
      "type": "youtube",
      "is_valid": true
    }
  ],
  "other_links": [
    {
      "url": "https://example.com/page.html",
      "text": "Regular Web Page",
      "type": "other",
      "is_valid": true
    },
    {
      "url": "https://example.com/another-page",
      "text": "Another Page",
      "type": "other",
      "is_valid": true
    },
    {
      "url": "https://example.com/relative-link",
      "text": "Relative Link",
      "type": "other",
      "is_valid": true
    }
  ],
  "metadata": {
    "total_links_found": 7,
    "pdf_count": 2,
    "youtube_count": 2,
    "processing_time_seconds": 0.5,
    "page_title": "Sample Test Page",
    "extraction_timestamp": "2023-06-01T12:00:00"
  }
}"""
