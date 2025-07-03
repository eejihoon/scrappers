"""
Abstract base class for platform-specific scrapers.

This module defines the interface that all scraper implementations must follow,
enabling a consistent approach to scraping different ad platforms while
allowing for platform-specific customizations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Generator
from datetime import datetime
import time
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from config import config


class BaseScraper(ABC):
    """
    Abstract base class for platform-specific scrapers.
    
    This class provides common functionality for web scraping using Selenium
    and defines the interface that all platform-specific scrapers must implement.
    It handles browser setup, page navigation, and common scraping patterns.
    """
    
    def __init__(self, platform_name: str, base_url: str, **kwargs):
        """
        Initialize the scraper.
        
        Args:
            platform_name: Name of the platform (e.g., 'facebook', 'google')
            base_url: Base URL for the platform's ad library
            **kwargs: Additional configuration parameters
        """
        self.platform_name = platform_name
        self.base_url = base_url
        self.config = kwargs
        
        # Selenium components
        self.driver = None
        self.wait = None
        
        # Scraping state
        self.is_initialized = False
        self.total_scraped = 0
        self.errors = []
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{platform_name}")
        
    def initialize(self) -> None:
        """
        Initialize the scraper with browser setup.
        
        Sets up the Selenium WebDriver with appropriate options and
        prepares the scraper for data collection.
        """
        try:
            # Setup Chrome options
            chrome_options = Options()
            
            if config.HEADLESS:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument(f'--window-size={config.WINDOW_SIZE[0]},{config.WINDOW_SIZE[1]}')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize WebDriver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Setup wait
            self.wait = WebDriverWait(self.driver, config.SELENIUM_TIMEOUT)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
            
            self.is_initialized = True
            self.logger.info(f"Initialized {self.platform_name} scraper")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scraper: {str(e)}")
            raise RuntimeError(f"Failed to initialize {self.platform_name} scraper: {str(e)}")
    
    @abstractmethod
    def scrape_ads(self, search_params: Dict[str, Any] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Scrape ads from the platform.
        
        This method should be implemented by each platform-specific scraper
        to handle the actual data extraction process.
        
        Args:
            search_params: Platform-specific search parameters
        
        Yields:
            Dict[str, Any]: Ad data dictionaries containing:
                - library_id: str - Unique identifier for the ad
                - start_date: str - When the ad started running
                - platforms: List[str] - Platforms where ad appears
                - thumbnail_url: str - URL of the main ad image
                - learn_more_url: str - URL of the ad's landing page
                - multiple_versions_images: List[str] - URLs of additional versions
                - scraped_at: datetime - When the data was collected
                - platform: str - Source platform name
        """
        pass
    
    @abstractmethod
    def get_page_source(self) -> str:
        """
        Get the current page source for archiving.
        
        Returns:
            str: HTML source code of the current page
        """
        pass
    
    def navigate_to_page(self, url: str) -> bool:
        """
        Navigate to a specific URL.
        
        Args:
            url: URL to navigate to
        
        Returns:
            bool: True if navigation successful, False otherwise
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            self.driver.get(url)
            self.logger.info(f"Navigated to: {url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {str(e)}")
            self.errors.append(f"Navigation error: {str(e)}")
            return False
    
    def scroll_to_bottom(self, max_scrolls: int = None) -> int:
        """
        Scroll to the bottom of the page to load all content.
        
        Args:
            max_scrolls: Maximum number of scroll attempts
        
        Returns:
            int: Number of scrolls performed
        """
        if max_scrolls is None:
            max_scrolls = config.MAX_SCROLL_ATTEMPTS
        
        scroll_count = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while scroll_count < max_scrolls:
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            time.sleep(config.SCROLL_PAUSE_TIME)
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            
            last_height = new_height
            scroll_count += 1
            
            self.logger.debug(f"Scroll {scroll_count}: New height = {new_height}")
        
        self.logger.info(f"Completed scrolling after {scroll_count} scrolls")
        return scroll_count
    
    def wait_for_element(self, by: By, value: str, timeout: int = None) -> bool:
        """
        Wait for an element to be present on the page.
        
        Args:
            by: Selenium By locator type
            value: Locator value
            timeout: Maximum time to wait in seconds
        
        Returns:
            bool: True if element found, False otherwise
        """
        if timeout is None:
            timeout = config.SELENIUM_TIMEOUT
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((by, value)))
            return True
            
        except TimeoutException:
            self.logger.warning(f"Element not found: {by} = {value}")
            return False
    
    def safe_find_element(self, by: By, value: str, parent_element=None) -> Optional[Any]:
        """
        Safely find an element without raising exceptions.
        
        Args:
            by: Selenium By locator type
            value: Locator value
            parent_element: Parent element to search within
        
        Returns:
            WebElement or None if not found
        """
        try:
            if parent_element:
                return parent_element.find_element(by, value)
            else:
                return self.driver.find_element(by, value)
                
        except NoSuchElementException:
            return None
    
    def safe_find_elements(self, by: By, value: str, parent_element=None) -> List[Any]:
        """
        Safely find multiple elements without raising exceptions.
        
        Args:
            by: Selenium By locator type
            value: Locator value
            parent_element: Parent element to search within
        
        Returns:
            List of WebElements (empty list if none found)
        """
        try:
            if parent_element:
                return parent_element.find_elements(by, value)
            else:
                return self.driver.find_elements(by, value)
                
        except NoSuchElementException:
            return []
    
    def safe_click(self, element) -> bool:
        """
        Safely click an element with error handling.
        
        Args:
            element: WebElement to click
        
        Returns:
            bool: True if click successful, False otherwise
        """
        try:
            element.click()
            return True
            
        except Exception as e:
            self.logger.warning(f"Failed to click element: {str(e)}")
            return False
    
    def get_element_text(self, element) -> str:
        """
        Safely get text from an element.
        
        Args:
            element: WebElement to get text from
        
        Returns:
            str: Element text or empty string if failed
        """
        try:
            return element.text.strip()
        except:
            return ""
    
    def get_element_attribute(self, element, attribute: str) -> str:
        """
        Safely get an attribute from an element.
        
        Args:
            element: WebElement to get attribute from
            attribute: Attribute name
        
        Returns:
            str: Attribute value or empty string if failed
        """
        try:
            return element.get_attribute(attribute) or ""
        except:
            return ""
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current scraping session.
        
        Returns:
            Dict[str, Any]: Statistics about the scraping session
        """
        return {
            'platform': self.platform_name,
            'total_scraped': self.total_scraped,
            'errors': len(self.errors),
            'error_details': self.errors,
            'is_initialized': self.is_initialized
        }
    
    def close(self) -> None:
        """
        Close the browser and clean up resources.
        """
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info(f"Closed {self.platform_name} scraper")
            except:
                pass
        
        self.driver = None
        self.wait = None
        self.is_initialized = False
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()