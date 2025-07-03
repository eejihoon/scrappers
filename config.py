import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Config:
    """Configuration class for the ad scraper project."""
    
    # Base URLs for different platforms
    FACEBOOK_AD_LIBRARY_URL: str = "https://www.facebook.com/ads/library"
    GOOGLE_AD_TRANSPARENCY_URL: str = "https://adstransparency.google.com"
    TIKTOK_CREATIVE_CENTER_URL: str = "https://ads.tiktok.com/business/creativecenter"
    
    # Output directories
    OUTPUT_DIR: str = "output"
    CSV_DIR: str = "csv_files"
    HTML_DIR: str = "html_archives"
    
    # Selenium configuration
    SELENIUM_TIMEOUT: int = 10
    PAGE_LOAD_TIMEOUT: int = 30
    SCROLL_PAUSE_TIME: float = 2.0
    MAX_SCROLL_ATTEMPTS: int = 50
    
    # Browser settings
    HEADLESS: bool = False
    WINDOW_SIZE: tuple = (1920, 1080)
    
    # Data collection settings
    MAX_ADS_TO_SCRAPE: int = None  # None means no limit
    
    def __post_init__(self):
        """Create necessary directories after initialization."""
        self.setup_directories()
    
    def setup_directories(self):
        """Create output directories if they don't exist."""
        base_path = os.path.join(os.getcwd(), self.OUTPUT_DIR)
        csv_path = os.path.join(base_path, self.CSV_DIR)
        html_path = os.path.join(base_path, self.HTML_DIR)
        
        os.makedirs(csv_path, exist_ok=True)
        os.makedirs(html_path, exist_ok=True)
    
    def get_csv_path(self, filename: str) -> str:
        """Get full path for CSV file."""
        return os.path.join(self.OUTPUT_DIR, self.CSV_DIR, filename)
    
    def get_html_path(self, filename: str) -> str:
        """Get full path for HTML file."""
        return os.path.join(self.OUTPUT_DIR, self.HTML_DIR, filename)

# Global configuration instance
config = Config()