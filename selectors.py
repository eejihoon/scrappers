"""
Robust selector definitions for ad platform scraping.

This module contains CSS selectors and XPath expressions that are designed to be
resilient to HTML structure changes. The strategy prioritizes:
1. Functional attributes (data-testid, data-pagelet, role, aria-label)
2. Relative positioning using stable anchor elements
3. Text-based selectors for unchanging content

Note: Class names are avoided as they frequently change in dynamic web applications.
"""

from typing import Dict, Any

class FacebookSelectors:
    """
    Selector definitions for Facebook Ad Library.
    
    These selectors use robust strategies to minimize breakage when Facebook
    updates their HTML structure.
    """
    
    # Main ad card container - using data attributes preferred by Facebook
    AD_CARD_CONTAINER = "[data-testid='ad-library-card']"
    
    # Alternative selectors for ad cards using relative positioning
    AD_CARD_CONTAINER_ALT = "//div[contains(@role, 'article') or contains(@class, 'card')]"
    
    # Library ID - typically found in data attributes or as part of URLs
    LIBRARY_ID = "[data-testid='library-id'], [data-ad-id], a[href*='/ads/library/']"
    LIBRARY_ID_XPATH = "//span[contains(text(), 'Library ID:')]/following-sibling::span | //a[contains(@href, '/ads/library/')]/@href"
    
    # Start date - looking for date patterns near "Started running" text
    START_DATE = "//span[contains(text(), 'Started running')]/following-sibling::span | //span[contains(text(), 'Started running')]/parent::*/following-sibling::*//span"
    START_DATE_ALT = "[data-testid='start-date'], [data-testid='ad-start-date']"
    
    # Platforms - typically shown as badges or chips
    PLATFORMS = "//span[contains(text(), 'Platforms:')]/following-sibling::* | //div[contains(@aria-label, 'Platform')]//span"
    PLATFORMS_ALT = "[data-testid='platforms'], [data-testid='ad-platforms'] span"
    
    # Thumbnail image - main image in the ad card
    THUMBNAIL_IMAGE = "img[src*='scontent'], img[src*='fbcdn'], [data-testid='ad-image'] img"
    THUMBNAIL_IMAGE_XPATH = "//img[contains(@src, 'scontent') or contains(@src, 'fbcdn')]/@src"
    
    # Learn more link - external link from the ad
    LEARN_MORE_LINK = "a[href*='l.facebook.com'], a[aria-label*='Learn more'], a[data-testid='learn-more-link']"
    LEARN_MORE_LINK_XPATH = "//a[contains(@href, 'l.facebook.com') or contains(@aria-label, 'Learn more')]/@href"
    
    # See ad details button - button to view additional versions
    SEE_AD_DETAILS_BUTTON = "button[aria-label*='See ad details'], button[data-testid='see-ad-details'], button:contains('See ad details')"
    SEE_AD_DETAILS_BUTTON_XPATH = "//button[contains(@aria-label, 'See ad details') or contains(text(), 'See ad details')]"
    
    # Multiple versions section - appears in the detail popup
    MULTIPLE_VERSIONS_SECTION = "[data-testid='multiple-versions'], [aria-label*='multiple versions']"
    MULTIPLE_VERSIONS_SECTION_XPATH = "//div[contains(text(), 'multiple versions') or contains(@aria-label, 'multiple versions')]"
    
    # Images within multiple versions section
    MULTIPLE_VERSIONS_IMAGES = "img[src*='scontent'], img[src*='fbcdn']"
    MULTIPLE_VERSIONS_IMAGES_XPATH = "//div[contains(text(), 'multiple versions')]//img[contains(@src, 'scontent') or contains(@src, 'fbcdn')]/@src"
    
    # Close button for popup/modal
    CLOSE_BUTTON = "button[aria-label*='Close'], button[data-testid='close-button'], [role='button'][aria-label*='Close']"
    CLOSE_BUTTON_XPATH = "//button[contains(@aria-label, 'Close') or contains(@aria-label, 'close')]"
    
    # Sponsored indicator - used as anchor for relative positioning
    SPONSORED_ANCHOR = "//span[contains(text(), 'Sponsored')]"
    
    # Load more button or infinite scroll trigger
    LOAD_MORE_BUTTON = "button[aria-label*='Load more'], button[data-testid='load-more']"
    LOAD_MORE_TRIGGER = "[data-testid='load-more-trigger'], [data-testid='infinite-scroll-trigger']"


class GoogleSelectors:
    """
    Selector definitions for Google Ad Transparency Center.
    Placeholder for future implementation.
    """
    
    # Placeholder selectors for Google Ad Transparency
    AD_CARD_CONTAINER = "[data-testid='ad-card']"
    AD_TITLE = "[data-testid='ad-title']"
    AD_CONTENT = "[data-testid='ad-content']"
    

class TikTokSelectors:
    """
    Selector definitions for TikTok Creative Center.
    Placeholder for future implementation.
    """
    
    # Placeholder selectors for TikTok Creative Center
    AD_CARD_CONTAINER = "[data-testid='creative-card']"
    AD_VIDEO = "[data-testid='ad-video']"
    AD_METADATA = "[data-testid='ad-metadata']"


class CommonSelectors:
    """
    Common selectors that might be used across multiple platforms.
    """
    
    # Generic loading indicators
    LOADING_SPINNER = "[data-testid='loading'], [aria-label*='Loading'], .loading-spinner"
    LOADING_SPINNER_XPATH = "//div[contains(@aria-label, 'Loading') or contains(@class, 'loading')]"
    
    # Generic error messages
    ERROR_MESSAGE = "[data-testid='error'], [role='alert'], .error-message"
    ERROR_MESSAGE_XPATH = "//div[contains(@role, 'alert') or contains(@class, 'error')]"
    
    # Generic pagination
    NEXT_PAGE_BUTTON = "button[aria-label*='Next'], button[data-testid='next-page']"
    PREV_PAGE_BUTTON = "button[aria-label*='Previous'], button[data-testid='prev-page']"


# Selector mapping for easy platform switching
PLATFORM_SELECTORS = {
    'facebook': FacebookSelectors,
    'google': GoogleSelectors,
    'tiktok': TikTokSelectors,
}


def get_selectors(platform: str) -> Any:
    """
    Get selector class for the specified platform.
    
    Args:
        platform: Platform name ('facebook', 'google', 'tiktok')
        
    Returns:
        Selector class for the platform
        
    Raises:
        ValueError: If platform is not supported
    """
    if platform.lower() not in PLATFORM_SELECTORS:
        raise ValueError(f"Unsupported platform: {platform}")
    
    return PLATFORM_SELECTORS[platform.lower()]