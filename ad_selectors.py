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
    
    These selectors are based on actual Facebook Ad Library structure
    as observed in the Korean and English versions.
    """
    
    # Main ad card container - look for divs containing Library ID text
    AD_CARD_CONTAINER = "div"  # We'll filter by content
    AD_CARD_CONTAINER_XPATH = "//div[contains(., '라이브러리 ID:') or contains(., 'Library ID:')]"
    
    # Library ID - appears as "라이브러리 ID: " or "Library ID: " followed by the ID
    LIBRARY_ID_XPATH = "//span[contains(text(), '라이브러리 ID:') or contains(text(), 'Library ID:')]"
    
    # Start date - appears as "Started running on" or date information
    START_DATE_XPATH = "//span[contains(text(), 'Started running') or contains(text(), '게재 시작일') or contains(text(), '시작일')]"
    
    # Platforms - Facebook and Instagram icons/text
    PLATFORMS_XPATH = "//span[contains(text(), 'Platforms') or contains(text(), '플랫폼')]//following-sibling::*"
    
    # Thumbnail image - main ad image
    THUMBNAIL_IMAGE = "img[src*='scontent'], img[src*='fbcdn']"
    
    # Learn more button - "Learn More" or "자세히 알아보기"
    LEARN_MORE_BUTTON_XPATH = "//span[contains(text(), 'Learn More') or contains(text(), '자세히 알아보기')]/parent::*"
    
    # See ad details button - "See ad details" or "광고 상세 정보 보기"
    SEE_AD_DETAILS_BUTTON_XPATH = "//span[contains(text(), 'See ad details') or contains(text(), '광고 상세 정보 보기')]/parent::*"
    
    # Multiple versions indicator - "This ad has multiple versions" or "여러 버전이 있는 광고입니다"
    MULTIPLE_VERSIONS_INDICATOR_XPATH = "//span[contains(text(), 'multiple versions') or contains(text(), '여러 버전')]"
    
    # Close button for modal - X button or close text
    CLOSE_BUTTON_XPATH = "//div[@aria-label='Close' or @aria-label='닫기']"
    
    # Website link - bottom of ad card showing the domain
    WEBSITE_LINK_XPATH = "//span[contains(text(), '.COM') or contains(text(), '.com')]/parent::*"
    
    # Ad status - "Active" or "활성"
    AD_STATUS_XPATH = "//span[contains(text(), 'Active') or contains(text(), '활성')]"


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