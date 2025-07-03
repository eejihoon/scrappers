"""
Scrapers module for multi-platform ad library scraping.

This module provides a pluggable scraper system that allows easy addition
of new platforms while maintaining a consistent interface and shared
functionality.
"""

from .base import BaseScraper
from .facebook_scraper import FacebookScraper

__all__ = ['BaseScraper', 'FacebookScraper']