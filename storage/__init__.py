"""
Storage module for ad scraper data persistence.

This module provides a pluggable storage system that allows easy switching
between different data storage methods (CSV, Google Sheets, databases, etc.)
without changing the core scraping logic.
"""

from .base import BaseStorage
from .csv_storage import CsvStorage

__all__ = ['BaseStorage', 'CsvStorage']