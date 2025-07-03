"""
Facebook Ad Library scraper implementation.

This module implements the Facebook-specific scraper for collecting ad data
from Facebook's Ad Library. It handles the dynamic loading of content,
detailed ad information extraction, and pagination.
"""

import time
import re
from typing import Dict, List, Any, Optional, Generator
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base import BaseScraper
from ad_selectors import FacebookSelectors
from config import config


class FacebookScraper(BaseScraper):
    """
    Facebook Ad Library scraper implementation.
    
    This scraper handles the Facebook Ad Library interface, including:
    - Dynamic content loading through scrolling
    - Ad card information extraction
    - Detailed ad version collection
    - Robust error handling for UI changes
    """
    
    def __init__(self, **kwargs):
        """
        Initialize Facebook scraper.
        
        Args:
            **kwargs: Additional configuration parameters
        """
        super().__init__(
            platform_name='facebook',
            base_url=config.FACEBOOK_AD_LIBRARY_URL,
            **kwargs
        )
        self.selectors = FacebookSelectors()
        self.processed_library_ids = set()
    
    def scrape_ads(self, search_params: Dict[str, Any] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Scrape ads from Facebook Ad Library.
        
        Args:
            search_params: Dictionary containing search parameters:
                - country: str - Country code (default: 'US')
                - search_terms: str - Search terms for ads
                - media_type: str - Media type filter
                - active_status: str - Active status filter
        
        Yields:
            Dict[str, Any]: Ad data dictionaries with Facebook-specific information
        """
        if not self.is_initialized:
            self.initialize()
        
        # Build search URL
        search_url = self._build_search_url(search_params or {})
        
        # Navigate to search page
        if not self.navigate_to_page(search_url):
            return
        
        # Wait for page to load
        self._wait_for_page_load()
        
        # Scroll to load all ads
        self.scroll_to_bottom()
        
        # Find all ad cards
        ad_cards = self._find_ad_cards()
        self.logger.info(f"Found {len(ad_cards)} ad cards")
        
        # Process each ad card
        for i, card in enumerate(ad_cards):
            try:
                ad_data = self._scrape_ad_card(card, i)
                if ad_data and ad_data.get('library_id'):
                    # Avoid duplicates
                    if ad_data['library_id'] not in self.processed_library_ids:
                        self.processed_library_ids.add(ad_data['library_id'])
                        self.total_scraped += 1
                        yield ad_data
                    else:
                        self.logger.debug(f"Skipping duplicate ad: {ad_data['library_id']}")
                        
            except Exception as e:
                self.logger.error(f"Error processing ad card {i}: {str(e)}")
                self.errors.append(f"Ad card {i} error: {str(e)}")
                continue
    
    def get_page_source(self) -> str:
        """
        Get the current page source for archiving.
        
        Returns:
            str: HTML source code of the current page
        """
        if self.driver:
            return self.driver.page_source
        return ""
    
    def _build_search_url(self, search_params: Dict[str, Any]) -> str:
        """
        Build search URL with parameters.
        
        Args:
            search_params: Search parameters dictionary
        
        Returns:
            str: Complete search URL
        """
        base_url = self.base_url
        params = []
        
        # Add country parameter
        country = search_params.get('country', 'US')
        params.append(f"country={country}")
        
        # Add search terms
        search_terms = search_params.get('search_terms', '')
        if search_terms:
            params.append(f"q={search_terms}")
        
        # Add media type
        media_type = search_params.get('media_type', '')
        if media_type:
            params.append(f"media_type={media_type}")
        
        # Add active status
        active_status = search_params.get('active_status', '')
        if active_status:
            params.append(f"active_status={active_status}")
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url
    
    def _wait_for_page_load(self) -> bool:
        """
        Wait for the Facebook Ad Library page to load completely.
        
        Returns:
            bool: True if page loaded successfully, False otherwise
        """
        try:
            # Wait for main content area
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            
            # Wait a bit more for dynamic content
            time.sleep(3)
            
            self.logger.info("Page loaded successfully")
            return True
            
        except TimeoutException:
            self.logger.error("Page load timeout")
            return False
    
    def _find_ad_cards(self) -> List[Any]:
        """
        Find all ad cards on the current page.
        
        Returns:
            List[WebElement]: List of ad card elements
        """
        # Try primary selector
        cards = self.safe_find_elements(By.CSS_SELECTOR, self.selectors.AD_CARD_CONTAINER)
        
        if not cards:
            # Try alternative selector using XPath
            cards = self.safe_find_elements(By.XPATH, self.selectors.AD_CARD_CONTAINER_ALT)
        
        if not cards:
            # Try finding by common patterns
            cards = self.safe_find_elements(By.CSS_SELECTOR, "[data-testid], [role='article'], .card")
        
        return cards
    
    def _scrape_ad_card(self, card_element, card_index: int) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single ad card.
        
        Args:
            card_element: WebElement of the ad card
            card_index: Index of the card for logging
        
        Returns:
            Dict[str, Any]: Ad data dictionary or None if extraction failed
        """
        try:
            ad_data = {
                'platform': self.platform_name,
                'scraped_at': datetime.now(),
                'library_id': '',
                'start_date': '',
                'platforms': [],
                'thumbnail_url': '',
                'learn_more_url': '',
                'multiple_versions_images': []
            }
            
            # Extract basic information
            ad_data['library_id'] = self._extract_library_id(card_element)
            ad_data['start_date'] = self._extract_start_date(card_element)
            ad_data['platforms'] = self._extract_platforms(card_element)
            ad_data['thumbnail_url'] = self._extract_thumbnail_url(card_element)
            ad_data['learn_more_url'] = self._extract_learn_more_url(card_element)
            
            # Extract detailed information (multiple versions)
            ad_data['multiple_versions_images'] = self._extract_multiple_versions(card_element)
            
            self.logger.debug(f"Scraped ad card {card_index}: {ad_data['library_id']}")
            return ad_data
            
        except Exception as e:
            self.logger.error(f"Error scraping ad card {card_index}: {str(e)}")
            return None
    
    def _extract_library_id(self, card_element) -> str:
        """Extract library ID from ad card."""
        # Try CSS selector first
        id_element = self.safe_find_element(By.CSS_SELECTOR, self.selectors.LIBRARY_ID, card_element)
        if id_element:
            # Check if it's a link with library ID in href
            href = self.get_element_attribute(id_element, 'href')
            if href and '/ads/library/' in href:
                # Extract ID from URL
                match = re.search(r'/ads/library/(\w+)', href)
                if match:
                    return match.group(1)
            
            # Check if it's text content
            text = self.get_element_text(id_element)
            if text:
                return text
        
        # Try XPath approach
        id_elements = self.safe_find_elements(By.XPATH, self.selectors.LIBRARY_ID_XPATH, card_element)
        for element in id_elements:
            text = self.get_element_text(element)
            if text:
                return text
        
        return ""
    
    def _extract_start_date(self, card_element) -> str:
        """Extract start date from ad card."""
        # Try XPath approach first
        date_elements = self.safe_find_elements(By.XPATH, self.selectors.START_DATE, card_element)
        for element in date_elements:
            text = self.get_element_text(element)
            if text and any(keyword in text.lower() for keyword in ['started', 'running', 'active']):
                return text
        
        # Try CSS selector
        date_element = self.safe_find_element(By.CSS_SELECTOR, self.selectors.START_DATE_ALT, card_element)
        if date_element:
            return self.get_element_text(date_element)
        
        return ""
    
    def _extract_platforms(self, card_element) -> List[str]:
        """Extract platforms from ad card."""
        platforms = []
        
        # Try XPath approach
        platform_elements = self.safe_find_elements(By.XPATH, self.selectors.PLATFORMS, card_element)
        for element in platform_elements:
            text = self.get_element_text(element)
            if text:
                platforms.append(text)
        
        # Try CSS selector
        if not platforms:
            platform_elements = self.safe_find_elements(By.CSS_SELECTOR, self.selectors.PLATFORMS_ALT, card_element)
            for element in platform_elements:
                text = self.get_element_text(element)
                if text:
                    platforms.append(text)
        
        return platforms
    
    def _extract_thumbnail_url(self, card_element) -> str:
        """Extract thumbnail image URL from ad card."""
        # Try CSS selector
        img_element = self.safe_find_element(By.CSS_SELECTOR, self.selectors.THUMBNAIL_IMAGE, card_element)
        if img_element:
            return self.get_element_attribute(img_element, 'src')
        
        # Try XPath approach
        img_elements = self.safe_find_elements(By.XPATH, self.selectors.THUMBNAIL_IMAGE_XPATH, card_element)
        for element in img_elements:
            src = self.get_element_attribute(element, 'src')
            if src:
                return src
        
        return ""
    
    def _extract_learn_more_url(self, card_element) -> str:
        """Extract learn more URL from ad card."""
        # Try CSS selector
        link_element = self.safe_find_element(By.CSS_SELECTOR, self.selectors.LEARN_MORE_LINK, card_element)
        if link_element:
            return self.get_element_attribute(link_element, 'href')
        
        # Try XPath approach
        link_elements = self.safe_find_elements(By.XPATH, self.selectors.LEARN_MORE_LINK_XPATH, card_element)
        for element in link_elements:
            href = self.get_element_attribute(element, 'href')
            if href:
                return href
        
        return ""
    
    def _extract_multiple_versions(self, card_element) -> List[str]:
        """Extract multiple version images from ad details."""
        try:
            # Find and click "See ad details" button
            details_button = self.safe_find_element(By.CSS_SELECTOR, self.selectors.SEE_AD_DETAILS_BUTTON, card_element)
            if not details_button:
                details_button = self.safe_find_element(By.XPATH, self.selectors.SEE_AD_DETAILS_BUTTON_XPATH, card_element)
            
            if not details_button:
                self.logger.debug("No 'See ad details' button found")
                return []
            
            # Click the button
            if not self.safe_click(details_button):
                self.logger.debug("Failed to click 'See ad details' button")
                return []
            
            # Wait for modal to appear
            time.sleep(2)
            
            # Look for multiple versions section
            versions_section = self.safe_find_element(By.CSS_SELECTOR, self.selectors.MULTIPLE_VERSIONS_SECTION)
            if not versions_section:
                versions_section = self.safe_find_element(By.XPATH, self.selectors.MULTIPLE_VERSIONS_SECTION_XPATH)
            
            image_urls = []
            
            if versions_section:
                # Extract images from versions section
                img_elements = self.safe_find_elements(By.CSS_SELECTOR, self.selectors.MULTIPLE_VERSIONS_IMAGES, versions_section)
                if not img_elements:
                    img_elements = self.safe_find_elements(By.XPATH, self.selectors.MULTIPLE_VERSIONS_IMAGES_XPATH, versions_section)
                
                for img in img_elements:
                    src = self.get_element_attribute(img, 'src')
                    if src:
                        image_urls.append(src)
            
            # Close modal
            self._close_modal()
            
            return image_urls
            
        except Exception as e:
            self.logger.error(f"Error extracting multiple versions: {str(e)}")
            self._close_modal()  # Ensure modal is closed even if error occurs
            return []
    
    def _close_modal(self) -> None:
        """Close any open modal/popup."""
        try:
            # Try to find and click close button
            close_button = self.safe_find_element(By.CSS_SELECTOR, self.selectors.CLOSE_BUTTON)
            if not close_button:
                close_button = self.safe_find_element(By.XPATH, self.selectors.CLOSE_BUTTON_XPATH)
            
            if close_button:
                self.safe_click(close_button)
                time.sleep(1)
            else:
                # Try pressing Escape key
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
                
        except Exception as e:
            self.logger.debug(f"Error closing modal: {str(e)}")
    
    def get_scraping_statistics(self) -> Dict[str, Any]:
        """
        Get Facebook-specific scraping statistics.
        
        Returns:
            Dict[str, Any]: Statistics including Facebook-specific metrics
        """
        stats = super().get_scraping_statistics()
        stats.update({
            'processed_library_ids': len(self.processed_library_ids),
            'unique_ads_found': len(self.processed_library_ids)
        })
        return stats