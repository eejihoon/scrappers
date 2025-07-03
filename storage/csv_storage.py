"""
CSV-based storage implementation for ad scraper data.

This module provides a CSV-based storage system that saves ad data to CSV files
and HTML archives to separate files. It implements the BaseStorage interface
and provides efficient data persistence suitable for small to medium datasets.
"""

import csv
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base import BaseStorage
from config import config


class CsvStorage(BaseStorage):
    """
    CSV-based storage implementation for ad scraper data.
    
    This class saves ad data to CSV files with automatic header management
    and HTML archiving capabilities. It's designed for local storage and
    easy data analysis with spreadsheet applications.
    """
    
    def __init__(self, output_path: str, **kwargs):
        """
        Initialize CSV storage.
        
        Args:
            output_path: Base path for output files
            **kwargs: Additional configuration:
                - csv_filename: str - Name of the CSV file (default: 'ad_data.csv')
                - archive_html: bool - Whether to save HTML archives (default: True)
                - encoding: str - File encoding (default: 'utf-8')
        """
        super().__init__(output_path, **kwargs)
        self.csv_filename = kwargs.get('csv_filename', 'ad_data.csv')
        self.archive_html = kwargs.get('archive_html', True)
        self.encoding = kwargs.get('encoding', 'utf-8')
        
        # CSV file paths
        self.csv_path = os.path.join(output_path, self.csv_filename)
        self.html_archive_dir = os.path.join(output_path, 'html_archives')
        
        # CSV headers
        self.csv_headers = [
            'library_id',
            'start_date',
            'platforms',
            'thumbnail_url',
            'learn_more_url',
            'multiple_versions_images',
            'scraped_at',
            'platform',
            'additional_data'
        ]
    
    def initialize(self) -> None:
        """
        Initialize the CSV storage system.
        
        Creates necessary directories and sets up CSV file with headers if needed.
        """
        try:
            # Create output directory
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
            
            # Create HTML archive directory if needed
            if self.archive_html:
                os.makedirs(self.html_archive_dir, exist_ok=True)
            
            # Create CSV file with headers if it doesn't exist
            if not os.path.exists(self.csv_path):
                with open(self.csv_path, 'w', newline='', encoding=self.encoding) as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                    writer.writeheader()
            
            self.is_initialized = True
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize CSV storage: {str(e)}")
    
    def save_ad_data(self, ad_data: Dict[str, Any]) -> bool:
        """
        Save a single ad's data to the CSV file.
        
        Args:
            ad_data: Dictionary containing ad information
        
        Returns:
            bool: True if data was saved successfully, False otherwise
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            # Validate and prepare data
            if not self.validate_ad_data(ad_data):
                return False
            
            prepared_data = self.prepare_ad_data(ad_data)
            
            # Convert complex fields to JSON strings for CSV storage
            csv_row = self._prepare_csv_row(prepared_data)
            
            # Append to CSV file
            with open(self.csv_path, 'a', newline='', encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writerow(csv_row)
            
            return True
            
        except Exception as e:
            print(f"Error saving ad data: {str(e)}")
            return False
    
    def save_batch_data(self, ads_data: List[Dict[str, Any]]) -> bool:
        """
        Save multiple ads' data to the CSV file in a batch operation.
        
        Args:
            ads_data: List of dictionaries containing ad information
        
        Returns:
            bool: True if all data was saved successfully, False otherwise
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            # Validate and prepare all data first
            prepared_rows = []
            for ad_data in ads_data:
                if not self.validate_ad_data(ad_data):
                    continue
                
                prepared_data = self.prepare_ad_data(ad_data)
                csv_row = self._prepare_csv_row(prepared_data)
                prepared_rows.append(csv_row)
            
            # Write all rows to CSV file
            with open(self.csv_path, 'a', newline='', encoding=self.encoding) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writerows(prepared_rows)
            
            return True
            
        except Exception as e:
            print(f"Error saving batch data: {str(e)}")
            return False
    
    def save_page_archive(self, html_content: str, filename: str) -> bool:
        """
        Save the raw HTML content of a scraped page.
        
        Args:
            html_content: Raw HTML content of the page
            filename: Name for the archive file
        
        Returns:
            bool: True if archive was saved successfully, False otherwise
        """
        if not self.archive_html:
            return True
        
        try:
            # Ensure filename has .html extension
            if not filename.endswith('.html'):
                filename += '.html'
            
            html_path = os.path.join(self.html_archive_dir, filename)
            
            with open(html_path, 'w', encoding=self.encoding) as htmlfile:
                htmlfile.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"Error saving HTML archive: {str(e)}")
            return False
    
    def get_existing_library_ids(self) -> List[str]:
        """
        Get list of library IDs that have already been scraped.
        
        Returns:
            List[str]: List of library IDs that already exist in storage
        """
        if not os.path.exists(self.csv_path):
            return []
        
        try:
            library_ids = []
            with open(self.csv_path, 'r', encoding=self.encoding) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('library_id'):
                        library_ids.append(row['library_id'])
            
            return library_ids
            
        except Exception as e:
            print(f"Error reading existing library IDs: {str(e)}")
            return []
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the stored data.
        
        Returns:
            Dict[str, Any]: Dictionary containing statistics about stored data
        """
        if not os.path.exists(self.csv_path):
            return {
                'total_ads': 0,
                'platforms': {},
                'date_range': {},
                'last_updated': None
            }
        
        try:
            stats = {
                'total_ads': 0,
                'platforms': {},
                'date_range': {},
                'last_updated': None
            }
            
            scraped_dates = []
            
            with open(self.csv_path, 'r', encoding=self.encoding) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    stats['total_ads'] += 1
                    
                    # Count platforms
                    platform = row.get('platform', 'unknown')
                    stats['platforms'][platform] = stats['platforms'].get(platform, 0) + 1
                    
                    # Track scraping dates
                    scraped_at = row.get('scraped_at')
                    if scraped_at:
                        scraped_dates.append(scraped_at)
            
            # Determine date range
            if scraped_dates:
                scraped_dates.sort()
                stats['date_range'] = {
                    'first_scraped': scraped_dates[0],
                    'last_scraped': scraped_dates[-1]
                }
                stats['last_updated'] = scraped_dates[-1]
            
            return stats
            
        except Exception as e:
            print(f"Error calculating statistics: {str(e)}")
            return {
                'total_ads': 0,
                'platforms': {},
                'date_range': {},
                'last_updated': None
            }
    
    def _prepare_csv_row(self, ad_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Prepare ad data for CSV storage by converting complex types to strings.
        
        Args:
            ad_data: Prepared ad data dictionary
        
        Returns:
            Dict[str, str]: CSV-ready row data
        """
        csv_row = {}
        
        for header in self.csv_headers:
            if header in ad_data:
                value = ad_data[header]
                
                # Convert lists and dicts to JSON strings
                if isinstance(value, (list, dict)):
                    csv_row[header] = json.dumps(value)
                elif isinstance(value, datetime):
                    csv_row[header] = value.isoformat()
                else:
                    csv_row[header] = str(value)
            else:
                csv_row[header] = ''
        
        # Store any additional data not in standard headers
        additional_data = {k: v for k, v in ad_data.items() if k not in self.csv_headers}
        if additional_data:
            csv_row['additional_data'] = json.dumps(additional_data)
        
        return csv_row
    
    def close(self) -> None:
        """
        Close any open resources.
        
        For CSV storage, this is a no-op as we don't maintain persistent connections.
        """
        pass