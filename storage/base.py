"""
Abstract base class for data storage implementations.

This module defines the interface that all storage implementations must follow,
enabling easy switching between different storage methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class BaseStorage(ABC):
    """
    Abstract base class for data storage implementations.
    
    This class defines the interface that all storage implementations must follow.
    It enables easy switching between different storage methods (CSV, Google Sheets,
    databases, etc.) without changing the core scraping logic.
    """
    
    def __init__(self, output_path: str, **kwargs):
        """
        Initialize the storage implementation.
        
        Args:
            output_path: Path where data should be stored
            **kwargs: Additional configuration parameters specific to the storage type
        """
        self.output_path = output_path
        self.config = kwargs
        self.is_initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the storage system.
        
        This method should set up any necessary resources, create files/tables,
        establish connections, etc. It should be called before any data operations.
        """
        pass
    
    @abstractmethod
    def save_ad_data(self, ad_data: Dict[str, Any]) -> bool:
        """
        Save a single ad's data to storage.
        
        Args:
            ad_data: Dictionary containing ad information with keys:
                - library_id: str - Unique identifier for the ad
                - start_date: str - When the ad started running
                - platforms: List[str] - Platforms where ad appears
                - thumbnail_url: str - URL of the main ad image
                - learn_more_url: str - URL of the ad's landing page
                - multiple_versions_images: List[str] - URLs of additional ad versions
                - scraped_at: datetime - When the data was collected
                - platform: str - Source platform (facebook, google, tiktok)
        
        Returns:
            bool: True if data was saved successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def save_batch_data(self, ads_data: List[Dict[str, Any]]) -> bool:
        """
        Save multiple ads' data to storage in a batch operation.
        
        Args:
            ads_data: List of dictionaries, each containing ad information
        
        Returns:
            bool: True if all data was saved successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def save_page_archive(self, html_content: str, filename: str) -> bool:
        """
        Save the raw HTML content of a scraped page for archival purposes.
        
        Args:
            html_content: Raw HTML content of the page
            filename: Name for the archive file
        
        Returns:
            bool: True if archive was saved successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_existing_library_ids(self) -> List[str]:
        """
        Get list of library IDs that have already been scraped.
        
        This method enables duplicate detection and incremental scraping.
        
        Returns:
            List[str]: List of library IDs that already exist in storage
        """
        pass
    
    @abstractmethod
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the stored data.
        
        Returns:
            Dict[str, Any]: Dictionary containing statistics like:
                - total_ads: int - Total number of ads stored
                - platforms: Dict[str, int] - Count of ads per platform
                - date_range: Dict[str, str] - First and last scraping dates
                - last_updated: datetime - When data was last updated
        """
        pass
    
    def validate_ad_data(self, ad_data: Dict[str, Any]) -> bool:
        """
        Validate that ad data contains required fields.
        
        Args:
            ad_data: Dictionary containing ad information
        
        Returns:
            bool: True if data is valid, False otherwise
        """
        required_fields = [
            'library_id', 'start_date', 'platforms', 'thumbnail_url',
            'learn_more_url', 'multiple_versions_images', 'scraped_at', 'platform'
        ]
        
        for field in required_fields:
            if field not in ad_data:
                return False
            
            # Check for empty values (except for multiple_versions_images which can be empty)
            if field != 'multiple_versions_images' and not ad_data[field]:
                return False
        
        return True
    
    def prepare_ad_data(self, ad_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare and normalize ad data before storage.
        
        Args:
            ad_data: Raw ad data dictionary
        
        Returns:
            Dict[str, Any]: Normalized ad data ready for storage
        """
        prepared_data = ad_data.copy()
        
        # Ensure scraped_at is set
        if 'scraped_at' not in prepared_data:
            prepared_data['scraped_at'] = datetime.now()
        
        # Normalize platforms to list
        if isinstance(prepared_data.get('platforms'), str):
            prepared_data['platforms'] = [prepared_data['platforms']]
        
        # Ensure multiple_versions_images is a list
        if not isinstance(prepared_data.get('multiple_versions_images'), list):
            prepared_data['multiple_versions_images'] = []
        
        # Remove any None values
        prepared_data = {k: v for k, v in prepared_data.items() if v is not None}
        
        return prepared_data
    
    def close(self) -> None:
        """
        Close any open connections or resources.
        
        This method should be called when scraping is complete to ensure
        proper cleanup of resources.
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()