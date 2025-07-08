import re
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    Validate if the string is a properly formatted URL
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_pdf_link(url: str) -> bool:
    """
    Check if URL points to a PDF file
    """
    pdf_pattern = re.compile(r'\.pdf$', re.IGNORECASE)
    return bool(pdf_pattern.search(url))


def is_youtube_link(url: str) -> bool:
    """
    Check if URL points to a YouTube video
    """
    youtube_patterns = [
        re.compile(r'youtube\.com/watch\?v=', re.IGNORECASE),
        re.compile(r'youtu\.be/', re.IGNORECASE),
        re.compile(r'youtube\.com/embed/', re.IGNORECASE)
    ]

    for pattern in youtube_patterns:
        if pattern.search(url):
            return True

    return False
