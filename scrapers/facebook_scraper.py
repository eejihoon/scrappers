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
        
        # Add default parameters
        params.append("active_status=active")
        params.append("ad_type=all")
        params.append("is_targeted_country=false")
        params.append("media_type=all")
        
        # Check if page_id is provided (for specific page search)
        page_id = search_params.get('page_id', '')
        if page_id:
            params.append(f"search_type=page")
            params.append(f"view_all_page_id={page_id}")
        else:
            # Default to keyword search
            params.append("search_type=keyword_unordered")
            search_terms = search_params.get('search_terms', '')
            if search_terms:
                params.append(f"q={search_terms}")
        
        # Add media type override if specified
        media_type = search_params.get('media_type', '')
        if media_type and media_type != 'all':
            # Replace the default media_type=all
            params = [p for p in params if not p.startswith('media_type=')]
            params.append(f"media_type={media_type}")
        
        # Add active status override if specified
        active_status = search_params.get('active_status', '')
        if active_status and active_status != 'active':
            # Replace the default active_status=active
            params = [p for p in params if not p.startswith('active_status=')]
            params.append(f"active_status={active_status}")
        
        return f"{base_url}?{'&'.join(params)}"
    
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
        # Find divs containing Library ID text - these are the ad cards
        cards = self.safe_find_elements(By.XPATH, self.selectors.AD_CARD_CONTAINER_XPATH)
        
        # Filter to get the parent containers that represent complete ad cards
        ad_cards = []
        for card in cards:
            # Look for parent element that contains all ad information
            # Usually 2-4 levels up from the Library ID element
            current = card
            for _ in range(5):  # Go up max 5 levels
                if current.tag_name == 'body':
                    break
                parent = current.find_element(By.XPATH, "..")
                # Check if this parent contains other ad elements
                if self._is_complete_ad_card(parent):
                    if parent not in ad_cards:
                        ad_cards.append(parent)
                    break
                current = parent
        
        self.logger.info(f"Found {len(ad_cards)} ad cards containing Library ID")
        return ad_cards
    
    def _is_complete_ad_card(self, element) -> bool:
        """Check if element contains a complete ad card."""
        try:
            # Check if element contains key ad components
            text_content = element.text
            has_library_id = '라이브러리 ID:' in text_content or 'Library ID:' in text_content
            has_date = '2025' in text_content or '2024' in text_content
            has_platforms = 'Facebook' in text_content or 'Instagram' in text_content or '플랫폼' in text_content
            
            return has_library_id and (has_date or has_platforms)
        except:
            return False
    
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
            # Get all text content from the card element
            card_text = card_element.text
            
            # Skip if no text content
            if not card_text:
                self.logger.debug(f"Ad card {card_index}: No text content, skipping")
                return None
            
            ad_data = {
                'platform': self.platform_name,
                'scraped_at': datetime.now(),
                'library_id': '',
                'start_date': '',
                'platforms': ['Facebook'],  # Default platform
                'thumbnail_url': '',
                'learn_more_url': '',
                'multiple_versions_images': []
            }
            
            # Extract basic information with simpler approach
            ad_data['library_id'] = self._extract_library_id_simple(card_text)
            
            # Skip if no library ID found
            if not ad_data['library_id']:
                self.logger.debug(f"Ad card {card_index}: No Library ID found, skipping")
                return None
            
            ad_data['start_date'] = self._extract_start_date_simple(card_text)
            ad_data['platforms'] = self._extract_platforms_simple(card_text)
            ad_data['thumbnail_url'] = self._extract_thumbnail_url(card_element)
            ad_data['learn_more_url'] = self._extract_learn_more_url(card_element)
            
            # Skip multiple versions for now to improve reliability
            # ad_data['multiple_versions_images'] = self._extract_multiple_versions(card_element)
            
            self.logger.debug(f"Scraped ad card {card_index}: {ad_data['library_id']}")
            return ad_data
            
        except Exception as e:
            self.logger.error(f"Error scraping ad card {card_index}: {str(e)}")
            return None
    
    def _extract_library_id_simple(self, text: str) -> str:
        """Extract library ID from text using simple regex."""
        import re
        
        # Look for "라이브러리 ID: " or "Library ID: " followed by numbers
        patterns = [
            r'라이브러리 ID:\s*(\d+)',
            r'Library ID:\s*(\d+)',
            r'라이브러리ID:\s*(\d+)',
            r'LibraryID:\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_start_date_simple(self, text: str) -> str:
        """Extract start date from text."""
        import re
        
        # Look for detailed date patterns first (more specific to less specific)
        patterns = [
            # Korean detailed date formats
            r'(\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.에\s+게재\s+시작함)',  # 2025. 6. 26.에 게재 시작함
            r'(\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.에\s+게재\s+시작)',   # 2025. 6. 26.에 게재 시작
            r'(\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.)',                 # 2025. 6. 26.
            r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)',                # 2025년 6월 26일
            r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일에\s+게재\s+시작)',  # 2025년 6월 26일에 게재 시작
            
            # English detailed date formats
            r'Started running on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',  # Started running on Jul 1, 2025
            r'Started running on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',   # Started running on 1 Jul 2025
            
            # Generic date patterns
            r'게재\s+시작일:\s*([^\n]+)',
            r'시작일:\s*([^\n]+)',
            r'게재\s+시작:\s*([^\n]+)',
            
            # Fallback to month only
            r'(\d{4}년\s*\d{1,2}월)',  # 2025년 7월
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                result = match.group(1).strip()
                # Clean up the result
                result = re.sub(r'\s+', ' ', result)  # Normalize whitespace
                return result
        
        return ""
    
    def _extract_platforms_simple(self, text: str) -> List[str]:
        """Extract platforms from text."""
        platforms = []
        
        if 'Facebook' in text or 'facebook' in text:
            platforms.append('Facebook')
        if 'Instagram' in text or 'instagram' in text:
            platforms.append('Instagram')
        if '플랫폼' in text:
            platforms.append('Facebook')  # Default assumption
            
        return platforms if platforms else ['Facebook']
    
    def _extract_library_id(self, card_element) -> str:
        """Extract library ID from ad card."""
        try:
            # Look for text containing "라이브러리 ID:" or "Library ID:"
            id_elements = self.safe_find_elements(By.XPATH, self.selectors.LIBRARY_ID_XPATH, card_element)
            for element in id_elements:
                text = self.get_element_text(element)
                if text:
                    # Extract the ID part after the colon
                    if ':' in text:
                        library_id = text.split(':', 1)[1].strip()
                        if library_id:
                            return library_id
                    return text
            
            self.logger.debug("Library ID not found in card")
            return ""
            
        except Exception as e:
            self.logger.error(f"Error extracting library ID: {str(e)}")
            return ""
    
    def _extract_start_date(self, card_element) -> str:
        """Extract start date from ad card."""
        try:
            # Look for date-related text
            date_elements = self.safe_find_elements(By.XPATH, self.selectors.START_DATE_XPATH, card_element)
            for element in date_elements:
                text = self.get_element_text(element)
                if text:
                    return text
            
            # Also look for date patterns in the card
            all_spans = self.safe_find_elements(By.TAG_NAME, "span", card_element)
            for span in all_spans:
                text = self.get_element_text(span)
                if text and any(keyword in text for keyword in ['Started running', '게재 시작', '시작일', '2025', '2024']):
                    return text
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error extracting start date: {str(e)}")
            return ""
    
    def _extract_platforms(self, card_element) -> List[str]:
        """Extract platforms from ad card."""
        try:
            platforms = []
            
            # Look for platform information
            platform_elements = self.safe_find_elements(By.XPATH, self.selectors.PLATFORMS_XPATH, card_element)
            for element in platform_elements:
                text = self.get_element_text(element)
                if text:
                    platforms.append(text)
            
            # Also look for platform icons/text patterns
            all_spans = self.safe_find_elements(By.TAG_NAME, "span", card_element)
            for span in all_spans:
                text = self.get_element_text(span)
                if text and any(platform in text for platform in ['Facebook', 'Instagram', '플랫폼']):
                    if text not in platforms:
                        platforms.append(text)
            
            # Default to common platforms if none found
            if not platforms:
                platforms = ['Facebook', 'Instagram']
            
            return platforms
            
        except Exception as e:
            self.logger.error(f"Error extracting platforms: {str(e)}")
            return ['Facebook']
    
    def _extract_thumbnail_url(self, card_element) -> str:
        """Extract thumbnail image URL from ad card."""
        try:
            # Look for images in the card
            img_elements = self.safe_find_elements(By.CSS_SELECTOR, self.selectors.THUMBNAIL_IMAGE, card_element)
            for img in img_elements:
                src = self.get_element_attribute(img, 'src')
                if src and ('scontent' in src or 'fbcdn' in src):
                    return src
            
            # Try any image element
            all_imgs = self.safe_find_elements(By.TAG_NAME, "img", card_element)
            for img in all_imgs:
                src = self.get_element_attribute(img, 'src')
                if src and not src.startswith('data:'):
                    return src
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error extracting thumbnail URL: {str(e)}")
            return ""
    
    def _extract_learn_more_url(self, card_element) -> str:
        """Extract learn more URL from ad card."""
        try:
            # Look for "Learn More" or "자세히 알아보기" button
            learn_more_elements = self.safe_find_elements(By.XPATH, self.selectors.LEARN_MORE_BUTTON_XPATH, card_element)
            for element in learn_more_elements:
                href = self.get_element_attribute(element, 'href')
                if href:
                    return href
            
            # Look for any link in the bottom area of the card
            all_links = self.safe_find_elements(By.TAG_NAME, "a", card_element)
            for link in all_links:
                text = self.get_element_text(link)
                href = self.get_element_attribute(link, 'href')
                if href and ('Learn More' in text or '자세히 알아보기' in text or 'Shop Now' in text):
                    return href
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error extracting learn more URL: {str(e)}")
            return ""
    
    def _extract_multiple_versions(self, card_element) -> List[str]:
        """Extract multiple version images from ad details."""
        try:
            # Check if this ad has multiple versions
            multiple_versions_indicator = self.safe_find_element(By.XPATH, self.selectors.MULTIPLE_VERSIONS_INDICATOR_XPATH, card_element)
            if not multiple_versions_indicator:
                self.logger.debug("No multiple versions indicator found")
                return []
            
            # Find and click "See ad details" button
            details_button = self.safe_find_element(By.XPATH, self.selectors.SEE_AD_DETAILS_BUTTON_XPATH, card_element)
            
            if not details_button:
                self.logger.debug("No 'See ad details' button found")
                return []
            
            # Click the button
            if not self.safe_click(details_button):
                self.logger.debug("Failed to click 'See ad details' button")
                return []
            
            # Wait for modal to appear
            time.sleep(3)
            
            # Look for images in the modal
            image_urls = []
            modal_images = self.safe_find_elements(By.CSS_SELECTOR, "img[src*='scontent'], img[src*='fbcdn']")
            
            for img in modal_images:
                src = self.get_element_attribute(img, 'src')
                if src and ('scontent' in src or 'fbcdn' in src):
                    image_urls.append(src)
            
            # Close modal
            self._close_modal()
            
            return list(set(image_urls))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error extracting multiple versions: {str(e)}")
            self._close_modal()  # Ensure modal is closed even if error occurs
            return []
    
    def _close_modal(self) -> None:
        """Close any open modal/popup."""
        try:
            # Try to find and click close button
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