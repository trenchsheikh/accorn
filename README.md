# Web Scraper

A Python web scraper that extracts all text information from websites. Supports both static HTML pages and JavaScript-rendered content. **Always produces RAG-optimized JSON output with intelligent business knowledge extraction!**

## Features

- **Always outputs JSON**: Default output is structured JSON optimized for RAG systems
- Extracts all text content from web pages
- **Deep scraping**: Follows all links from root page to scrape entire websites
- **Intelligent RAG processing**: Advanced business knowledge extraction and semantic chunking
- Removes scripts, styles, and other non-text elements
- Supports static HTML pages (using requests + BeautifulSoup)
- Optional support for JavaScript-rendered pages (using Selenium)
- Can include link information
- Configurable depth and page limits
- Rate limiting to be respectful to servers
- **Advanced entity extraction**: Companies, products, services, technologies, locations, contact info, prices, dates
- **Smart topic extraction**: TF-IDF-like scoring with position and length weighting
- **Semantic chunking**: Paragraph and sentence-aware chunking for better context preservation
- **Rich metadata**: Each chunk includes URL, depth, entities, topics, timestamps, and token counts

## How to Run

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/trenchsheikh/accorn.git
   cd accorn
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the scraper:**
   ```bash
   # Scrape a single page (outputs JSON by default)
   python web_scraper.py https://example.com
   
   # Deep scrape entire website (outputs JSON by default)
   python web_scraper.py https://example.com --deep -o knowledge_base.json
   
   # Output in JSONL format (one chunk per line)
   python web_scraper.py https://example.com --deep --rag-format jsonl
   
   # Get plain text output instead of JSON
   python web_scraper.py https://example.com --deep --text-output
   ```

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Optional: Selenium Setup (for JavaScript-rendered pages)

If you need to scrape JavaScript-heavy websites, install ChromeDriver:

- **macOS:** `brew install chromedriver`
- **Linux/Windows:** Download from [ChromeDriver downloads](https://chromedriver.chromium.org/)

Then use the `--selenium` flag when running the scraper.

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

### JSON Output (Default)

```bash
# JSON output is the default - no flags needed!
python web_scraper.py https://example.com --deep -o knowledge_base.json

# JSONL format (one chunk per line) for streaming processing
python web_scraper.py https://example.com --deep --rag-format jsonl -o knowledge_base.jsonl

# Custom chunk size and overlap
python web_scraper.py https://example.com --deep --chunk-size 2000 --chunk-overlap 400

# With Selenium for JavaScript sites
python web_scraper.py https://example.com --deep --selenium -o knowledge_base.json

# Plain text output (if you prefer text over JSON)
python web_scraper.py https://example.com --deep --text-output -o output.txt
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
- `--text-output`: Output in plain text format instead of JSON (default: JSON)
- `--rag-format`: JSON output format: `json` (structured) or `jsonl` (one chunk per line) (default: json)
- `--chunk-size`: Chunk size in characters for RAG output (default: 1000)
- `--chunk-overlap`: Overlap between chunks in characters for RAG output (default: 200)

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

### JSON Output Format (Default)
The scraper always outputs structured JSON/JSONL optimized for RAG systems:

**JSON Structure:**
```json
{
  "knowledge_base": {
    "root_url": "https://example.com",
    "total_pages": 10,
    "total_chunks": 45,
    "total_tokens": 12500,
    "scraped_at": "2024-01-01T12:00:00",
    "aggregated_entities": {
      "companies": ["Company A", "Company B"],
      "products": ["Product X", "Product Y"],
      "services": ["Service 1", "Service 2"],
      "technologies": ["Python", "React", "AWS"],
      "contact_info": ["email@example.com", "+1234567890"]
    },
    "aggregated_topics": ["business", "technology", "services"]
  },
  "chunks": [
    {
      "content": "Text content of the chunk...",
      "metadata": {
        "url": "https://example.com/page1",
        "source": "https://example.com",
        "depth": 1,
        "word_count": 250,
        "character_count": 1500,
        "scraped_at": "2024-01-01T12:00:00",
        "entities": {...},
        "topics": ["topic1", "topic2"]
      },
      "chunk_index": 0,
      "total_chunks": 3,
      "token_count": 375
    }
  ]
}
```

**Features:**
- **Semantic chunking**: Intelligent paragraph and sentence-aware chunking for better context preservation
- **Metadata-rich**: Each chunk includes URL, depth, entities, topics, timestamps, and token/character counts
- **Advanced entity extraction**: Automatically extracts:
  - Companies (with pattern matching for Inc, LLC, Corp, etc.)
  - Products and services (with version numbers and tiers)
  - Technologies (languages, frameworks, databases, cloud platforms, tools)
  - Locations (cities, states, countries)
  - Contact info (emails, phones, URLs)
  - Prices and dates
- **Smart topic extraction**: TF-IDF-like scoring with position weighting (first/last sentences) and length bonuses
- **Token counting**: Accurate token counts using tiktoken for embedding models
- **JSONL support**: One chunk per line format for streaming processing
- **Improved intelligence**: Better pattern recognition, context awareness, and entity disambiguation

## Notes

- **Deep scraping**: The scraper will only follow links within the same domain to avoid crawling external sites
- The scraper automatically skips non-content URLs (PDFs, images, etc.)
- Use `--delay` to add rate limiting between requests (be respectful to servers)
- The scraper respects robots.txt and rate limits - use responsibly
- Some websites may block automated scraping
- For JavaScript-heavy sites, use the `--selenium` flag
- The scraper automatically removes scripts, styles, and metadata
- Deep scraping can take a long time for large websites - use `--max-pages` to limit scope
- **JSON is default**: The scraper always produces JSON output optimized for RAG systems
- **Use `--text-output`**: If you prefer plain text output instead of JSON
- **RAG optimization**: Output is optimized for vector databases (Pinecone, Weaviate, Chroma, etc.) and LLM applications
- **Chunk sizing**: Default 1000 characters works well for most RAG systems, adjust based on your embedding model's context window
- **Entity extraction**: Uses advanced pattern matching, heuristics, and context analysis - for production use, consider integrating with NER models (spaCy, NLTK) for even better results
- **Quality improvements**: Enhanced entity extraction, smarter topic identification, and semantic chunking for better RAG performance

