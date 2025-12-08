# Web Scraper

A Python web scraper that extracts all text information from websites. Supports both static HTML pages and JavaScript-rendered content. **Now with RAG-optimized business knowledge extraction!**

## Features

- Extracts all text content from web pages
- **Deep scraping**: Follows all links from root page to scrape entire websites
- **RAG-optimized output**: Extracts business knowledge and structures it for Retrieval-Augmented Generation systems
- Removes scripts, styles, and other non-text elements
- Supports static HTML pages (using requests + BeautifulSoup)
- Optional support for JavaScript-rendered pages (using Selenium)
- Can include link information
- Configurable depth and page limits
- Rate limiting to be respectful to servers
- Outputs to file or stdout
- Clean, readable text output
- **Business entity extraction**: Companies, products, services, technologies, contact info
- **Intelligent chunking**: Optimal text chunking for RAG systems with metadata

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
   # Scrape a single page
   python web_scraper.py https://example.com
   
   # Deep scrape entire website
   python web_scraper.py https://example.com --deep -o output.txt
   
   # Generate RAG-optimized business knowledge
   python web_scraper.py https://example.com --deep --rag -o rag_knowledge.json
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

### RAG-Optimized Business Knowledge Extraction

```bash
# Generate RAG-optimized knowledge base (JSON format)
python web_scraper.py https://example.com --deep --rag -o rag_knowledge.json

# Generate RAG knowledge in JSONL format (one chunk per line)
python web_scraper.py https://example.com --deep --rag --rag-format jsonl -o rag_knowledge.jsonl

# Custom chunk size and overlap for RAG
python web_scraper.py https://example.com --deep --rag --chunk-size 2000 --chunk-overlap 400

# RAG with Selenium for JavaScript sites
python web_scraper.py https://example.com --deep --rag --selenium -o rag_knowledge.json
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
- `--rag`: Output in RAG-optimized format (business knowledge extraction)
- `--rag-format`: RAG output format: `json` (structured) or `jsonl` (one chunk per line) (default: json)
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

### RAG-Optimized Format
When using `--rag`, the output is structured JSON/JSONL optimized for RAG systems:

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
- **Intelligent chunking**: Text split into optimal sizes with sentence boundary awareness
- **Metadata-rich**: Each chunk includes URL, depth, entities, topics, and timestamps
- **Entity extraction**: Automatically extracts companies, products, services, technologies, and contact info
- **Topic extraction**: Identifies key topics from content
- **Token counting**: Accurate token counts for embedding models
- **JSONL support**: One chunk per line format for streaming processing

## Notes

- **Deep scraping**: The scraper will only follow links within the same domain to avoid crawling external sites
- The scraper automatically skips non-content URLs (PDFs, images, etc.)
- Use `--delay` to add rate limiting between requests (be respectful to servers)
- The scraper respects robots.txt and rate limits - use responsibly
- Some websites may block automated scraping
- For JavaScript-heavy sites, use the `--selenium` flag
- The scraper automatically removes scripts, styles, and metadata
- Deep scraping can take a long time for large websites - use `--max-pages` to limit scope
- **RAG output**: Optimized for use with vector databases (Pinecone, Weaviate, Chroma, etc.) and LLM applications
- **Chunk sizing**: Default 1000 characters works well for most RAG systems, adjust based on your embedding model's context window
- **Entity extraction**: Uses pattern matching and heuristics - for production use, consider integrating with NER models (spaCy, NLTK)

