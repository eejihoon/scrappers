# Claude AI Assistant Context

## Project Overview
This is a multi-platform ad library scraper designed to collect advertising data from major platforms like Facebook, Google, and TikTok. The initial implementation focuses on Facebook Ad Library with a robust, extensible architecture.

## Architecture
- **Modular Design**: Separate modules for scrapers, storage, and configuration
- **Extensible**: Easy to add new platforms and storage methods
- **Robust**: Resilient selectors and comprehensive error handling

## Key Components

### 1. Configuration (`config.py`)
- Centralized configuration management
- Platform URLs and Selenium settings
- Automatic directory creation
- Configurable timeouts and scraping limits

### 2. Selector Strategy (`selectors.py`)
- Robust selector definitions using functional attributes
- XPath-based relative positioning from stable anchors
- Fallback strategies for UI changes
- Platform-specific selector classes

### 3. Storage System (`storage/`)
- Abstract base class for pluggable storage backends
- CSV storage implementation with JSON serialization
- HTML archiving for compliance
- Batch operations and duplicate detection

### 4. Scraper System (`scrapers/`)
- Abstract base scraper with common Selenium functionality
- Facebook scraper with complete ad data extraction
- Anti-detection measures and error handling
- Generator-based streaming for memory efficiency

### 5. Main Application (`main.py`)
- Command-line interface with comprehensive options
- Orchestrates entire workflow
- Graceful shutdown handling
- Progress tracking and summary reporting

## Usage

### Basic Usage
```bash
python main.py
```

### Advanced Usage
```bash
# Search specific terms with limits
python main.py --search-terms "fitness" --max-ads 100

# Headless mode with custom output
python main.py --headless --output-file custom.csv

# Different platform and country
python main.py --platform facebook --country US
```

### Command Line Options
- `--platform`: Choose platform (facebook, google, tiktok)
- `--country`: Country code for ads (default: US)
- `--search-terms`: Search terms to filter ads
- `--max-ads`: Maximum number of ads to scrape
- `--headless`: Run browser in headless mode
- `--output-file`: Custom CSV filename
- `--no-archive`: Skip HTML archiving
- `--debug`: Enable debug logging

## Dependencies
Install dependencies with:
```bash
pip install -r requirements.txt
```

Required:
- selenium>=4.15.0
- pandas>=2.0.0
- numpy>=1.24.0

## Development Notes

### Adding New Platforms
1. Create new selector class in `selectors.py`
2. Implement platform scraper inheriting from `BaseScraper`
3. Add platform choice to main.py argument parser
4. Update configuration with platform URL

### Adding New Storage Methods
1. Implement new storage class inheriting from `BaseStorage`
2. Add storage selection logic to main.py
3. Update configuration as needed

### Troubleshooting
- Check Chrome/Chromium installation for Selenium
- Verify internet connection and platform accessibility
- Check logs in `scraper.log` for detailed error information
- Use `--debug` flag for verbose logging

## Data Schema
Each scraped ad contains:
- `library_id`: Unique identifier
- `start_date`: When ad started running
- `platforms`: List of platforms (Facebook, Instagram, etc.)
- `thumbnail_url`: Main ad image URL
- `learn_more_url`: Landing page URL
- `multiple_versions_images`: Additional ad version images
- `scraped_at`: Timestamp of data collection
- `platform`: Source platform name

## Best Practices
- Run with reasonable rate limits to avoid being blocked
- Use headless mode for production/automated runs
- Monitor logs for selector issues indicating UI changes
- Keep HTML archives for compliance and debugging
- Test selectors regularly as platforms update UI

## Maintenance
- Update selectors in `selectors.py` when platforms change UI
- Monitor error rates and adjust timeouts as needed
- Keep dependencies updated for security and compatibility
- Add new platforms as business requirements evolve