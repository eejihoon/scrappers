#!/usr/bin/env python3
"""
Multi-platform Ad Library Scraper - Main Application

This is the main entry point for the ad scraper application. It orchestrates
the entire scraping workflow including initialization, data collection,
storage, and cleanup.

Usage:
    python main.py [options]
    
Examples:
    python main.py                              # Basic Facebook scraping
    python main.py --platform facebook --country US --max-ads 100
    python main.py --search-terms "fitness" --headless
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import signal
import os

from config import config
from scrapers import FacebookScraper
from storage import CsvStorage
from ad_selectors import get_selectors


class AdScraperApp:
    """
    Main application class for the ad scraper.
    
    This class manages the entire scraping workflow from initialization
    to cleanup, providing a clean interface for running scraping jobs.
    """
    
    def __init__(self, args: argparse.Namespace):
        """
        Initialize the application with command line arguments.
        
        Args:
            args: Parsed command line arguments
        """
        self.args = args
        self.scraper = None
        self.storage = None
        self.logger = None
        self.interrupted = False
        
        # Setup logging
        self._setup_logging()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Ad Scraper Application initialized")
    
    def run(self) -> int:
        """
        Run the main scraping workflow.
        
        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        try:
            self.logger.info("Starting ad scraping workflow")
            
            # Initialize components
            if not self._initialize_components():
                return 1
            
            # Run scraping
            if not self._run_scraping():
                return 1
            
            # Generate summary
            self._generate_summary()
            
            self.logger.info("Scraping workflow completed successfully")
            return 0
            
        except KeyboardInterrupt:
            self.logger.info("Scraping interrupted by user")
            return 1
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return 1
        finally:
            self._cleanup()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = logging.DEBUG if self.args.debug else logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('scraper.log')
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.interrupted = True
    
    def _initialize_components(self) -> bool:
        """
        Initialize scraper and storage components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Initialize storage
            self.logger.info("Initializing storage system")
            output_path = self.args.output_dir or config.get_csv_path("")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            self.storage = CsvStorage(
                output_path=os.path.dirname(output_path),
                csv_filename=self.args.output_file,
                archive_html=not self.args.no_archive
            )
            self.storage.initialize()
            
            # Initialize scraper
            self.logger.info(f"Initializing {self.args.platform} scraper")
            if self.args.platform.lower() == 'facebook':
                self.scraper = FacebookScraper()
            else:
                self.logger.error(f"Unsupported platform: {self.args.platform}")
                return False
            
            # Override config with command line arguments
            if self.args.headless is not None:
                config.HEADLESS = self.args.headless
            
            if self.args.timeout:
                config.SELENIUM_TIMEOUT = self.args.timeout
            
            self.scraper.initialize()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {str(e)}")
            return False
    
    def _run_scraping(self) -> bool:
        """
        Execute the main scraping process.
        
        Returns:
            bool: True if scraping completed successfully, False otherwise
        """
        try:
            # Build search parameters
            search_params = self._build_search_params()
            
            self.logger.info(f"Starting scraping with parameters: {search_params}")
            
            # Start scraping
            ads_scraped = 0
            ads_saved = 0
            
            for ad_data in self.scraper.scrape_ads(search_params):
                if self.interrupted:
                    self.logger.info("Scraping interrupted, stopping...")
                    break
                
                ads_scraped += 1
                
                # Save ad data
                if self.storage.save_ad_data(ad_data):
                    ads_saved += 1
                    self.logger.info(f"Saved ad {ads_saved}/{ads_scraped}: {ad_data.get('library_id', 'N/A')}")
                else:
                    self.logger.warning(f"Failed to save ad: {ad_data.get('library_id', 'N/A')}")
                
                # Check if we've reached the maximum SAVED ads (not scraped)
                if self.args.max_ads and ads_saved >= self.args.max_ads:
                    self.logger.info(f"Reached maximum ads limit ({self.args.max_ads})")
                    break
                
                # Progress update
                if ads_scraped % 10 == 0:
                    self.logger.info(f"Progress: {ads_scraped} ads scraped, {ads_saved} saved")
            
            # Save HTML archive
            if not self.args.no_archive:
                self.logger.info("Saving HTML archive")
                html_content = self.scraper.get_page_source()
                archive_filename = f"facebook_ads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                self.storage.save_page_archive(html_content, archive_filename)
            
            self.logger.info(f"Scraping completed: {ads_scraped} ads scraped, {ads_saved} saved")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            return False
    
    def _build_search_params(self) -> Dict[str, Any]:
        """
        Build search parameters from command line arguments.
        
        Returns:
            Dict[str, Any]: Search parameters dictionary
        """
        params = {}
        
        if self.args.country:
            params['country'] = self.args.country
        
        if self.args.page_id:
            params['page_id'] = self.args.page_id
        elif self.args.search_terms:
            params['search_terms'] = self.args.search_terms
        
        if self.args.media_type:
            params['media_type'] = self.args.media_type
        
        if self.args.active_status:
            params['active_status'] = self.args.active_status
        
        return params
    
    def _generate_summary(self) -> None:
        """Generate and display scraping summary."""
        try:
            scraper_stats = self.scraper.get_scraping_statistics()
            storage_stats = self.storage.get_scraping_statistics()
            
            self.logger.info("=== SCRAPING SUMMARY ===")
            self.logger.info(f"Platform: {scraper_stats.get('platform', 'N/A')}")
            self.logger.info(f"Total ads scraped: {scraper_stats.get('total_scraped', 0)}")
            self.logger.info(f"Total ads saved: {storage_stats.get('total_ads', 0)}")
            self.logger.info(f"Errors encountered: {scraper_stats.get('errors', 0)}")
            
            if scraper_stats.get('error_details'):
                self.logger.info("Error details:")
                for error in scraper_stats['error_details']:
                    self.logger.info(f"  - {error}")
            
            self.logger.info("=== END SUMMARY ===")
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.scraper:
                self.scraper.close()
            
            if self.storage:
                self.storage.close()
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Multi-platform Ad Library Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Basic Facebook scraping
  %(prog)s --platform facebook --country US  # Facebook scraping for US
  %(prog)s --search-terms "fitness" --max-ads 100  # Search with limit
  %(prog)s --page-id 119546338123785 --country KR   # Get all ads from specific page
  %(prog)s --headless --output-file custom.csv     # Headless mode with custom output
        """
    )
    
    # Platform selection
    parser.add_argument(
        '--platform',
        choices=['facebook', 'google', 'tiktok'],
        default='facebook',
        help='Platform to scrape (default: facebook)'
    )
    
    # Search parameters
    parser.add_argument(
        '--country',
        default='US',
        help='Country code for ads (default: US)'
    )
    
    parser.add_argument(
        '--search-terms',
        help='Search terms to filter ads'
    )
    
    parser.add_argument(
        '--page-id',
        help='Facebook Page ID to get all ads from specific page'
    )
    
    parser.add_argument(
        '--media-type',
        choices=['all', 'image', 'video', 'text'],
        help='Media type filter'
    )
    
    parser.add_argument(
        '--active-status',
        choices=['all', 'active', 'inactive'],
        help='Active status filter'
    )
    
    # Scraping options
    parser.add_argument(
        '--max-ads',
        type=int,
        help='Maximum number of ads to scrape'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    parser.add_argument(
        '--no-headless',
        dest='headless',
        action='store_false',
        help='Run browser with GUI (default)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        help='Selenium timeout in seconds'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        help='Output directory path'
    )
    
    parser.add_argument(
        '--output-file',
        default='ad_data.csv',
        help='Output CSV filename (default: ad_data.csv)'
    )
    
    parser.add_argument(
        '--no-archive',
        action='store_true',
        help='Skip HTML archiving'
    )
    
    # Logging options
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.set_defaults(headless=None)
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    app = AdScraperApp(args)
    exit_code = app.run()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()