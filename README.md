# Web Scraper

A Python web scraper that extracts all text information from websites. Supports both static HTML pages and JavaScript-rendered content.

## Features

- Extracts all text content from web pages
- **Deep scraping**: Follows all links from root page to scrape entire websites
- Removes scripts, styles, and other non-text elements
- Supports static HTML pages (using requests + BeautifulSoup)
- Optional support for JavaScript-rendered pages (using Selenium)
- Can include link information
- Configurable depth and page limits
- Rate limiting to be respectful to servers
- Outputs to file or stdout
- Clean, readable text output

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. For Selenium support (optional, for JavaScript-rendered pages):
   - Install ChromeDriver:
     - macOS: `brew install chromedriver`
     - Linux: Download from [ChromeDriver downloads](https://chromedriver.chromium.org/)
     - Windows: Download from [ChromeDriver downloads](https://chromedriver.chromium.org/)

## Usage

### Basic Usage (Static HTML)

```bash
python web_scraper.py https://example.com
```

### Save to File

```bash
python web_scraper.py https://example.com -o output.txt
```

### Use Selenium for JavaScript-Rendered Pages

```bash
python web_scraper.py https://example.com --selenium
```

### Include Links Information

```bash
python web_scraper.py https://example.com --include-links
```

### Run Browser in Visible Mode (Selenium)

```bash
python web_scraper.py https://example.com --selenium --no-headless
```

### Deep Scrape (Follow All Links)

```bash
# Deep scrape with default settings (max depth 5, max 100 pages)
python web_scraper.py https://example.com --deep

# Deep scrape with custom depth and page limits
python web_scraper.py https://example.com --deep --max-depth 3 --max-pages 50

# Deep scrape with faster rate (0.5 second delay)
python web_scraper.py https://example.com --deep --delay 0.5

# Deep scrape and save to file
python web_scraper.py https://example.com --deep -o full_site_content.txt
```

## Command Line Options

- `url`: The website URL to scrape (required)
- `-o, --output`: Output file path (default: print to stdout)
- `-s, --selenium`: Use Selenium for JavaScript-rendered pages
- `--no-headless`: Run browser in visible mode (Selenium only)
- `--include-links`: Include links information in output
- `-d, --deep`: Deep scrape mode - follow all links from root page to end
- `--max-depth`: Maximum crawl depth for deep scrape (default: 5)
- `--max-pages`: Maximum number of pages to scrape (default: 100)
- `--delay`: Delay between requests in seconds (default: 1.0)

## Examples

```bash
# Scrape a single page
python web_scraper.py https://example.com

# Scrape and save to file
python web_scraper.py https://example.com -o scraped_content.txt

# Deep scrape entire website (follows all links)
python web_scraper.py https://example.com --deep -o full_site.txt

# Deep scrape with custom limits
python web_scraper.py https://example.com --deep --max-depth 3 --max-pages 200

# Scrape a JavaScript-heavy site
python web_scraper.py https://example.com --selenium -o output.txt

# Deep scrape JavaScript-heavy site
python web_scraper.py https://example.com --deep --selenium -o full_site.txt

# Scrape with links included
python web_scraper.py https://example.com --include-links -o full_content.txt
```

## Output Format

### Single Page Mode
The scraper outputs:
- URL
- Word count
- Character count
- Full text content
- Links (if `--include-links` is used)

### Deep Scrape Mode
The scraper outputs:
- Summary statistics (total pages, words, characters)
- For each page:
  - Page number and depth
  - URL
  - Word count
  - Character count
  - Full text content
  - Links (if `--include-links` is used)

## Notes

- **Deep scraping**: The scraper will only follow links within the same domain to avoid crawling external sites
- The scraper automatically skips non-content URLs (PDFs, images, etc.)
- Use `--delay` to add rate limiting between requests (be respectful to servers)
- The scraper respects robots.txt and rate limits - use responsibly
- Some websites may block automated scraping
- For JavaScript-heavy sites, use the `--selenium` flag
- The scraper automatically removes scripts, styles, and metadata
- Deep scraping can take a long time for large websites - use `--max-pages` to limit scope

