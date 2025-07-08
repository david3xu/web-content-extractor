"""
API package for web content extraction service.
"""
from .app import app, create_app

__all__ = ["create_app", "app"]
