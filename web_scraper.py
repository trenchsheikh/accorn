#!/usr/bin/env python3
"""
Web Scraper - Extracts all text information from a website
Supports both static HTML pages and JavaScript-rendered content
"""

import argparse
import sys
import time
from urllib.parse import urljoin, urlparse
from typing import Set, Optional, List, Dict
from collections import deque
import re

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class WebScraper:
    """Web scraper that extracts all text content from a website"""
    
    def __init__(self, use_selenium: bool = False, headless: bool = True):
        """
        Initialize the web scraper
        
        Args:
            use_selenium: Whether to use Selenium for JavaScript-rendered pages
            headless: Run browser in headless mode (only for Selenium)
        """
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.headless = headless
        self.visited_urls: Set[str] = set()
        self.driver: Optional[webdriver.Chrome] = None
        self.base_domain: Optional[str] = None
        
        if self.use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Warning: Could not initialize Selenium: {e}")
            print("Falling back to requests/BeautifulSoup")
            self.use_selenium = False
    
    def _get_page_content(self, url: str) -> Optional[str]:
        """Fetch page content using requests or Selenium"""
        if self.use_selenium and self.driver:
            try:
                self.driver.get(url)
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                return self.driver.page_source
            except Exception as e:
                print(f"Error fetching {url} with Selenium: {e}")
                return None
        else:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return None
    
    def _extract_text_from_html(self, html: str) -> str:
        """Extract all text content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "link", "noscript"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract all links from HTML that are within the same domain"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Parse the URL
            parsed = urlparse(absolute_url)
            
            # Only include HTTP/HTTPS links
            if parsed.scheme not in ('http', 'https'):
                continue
            
            # Remove fragments (anchor links)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                clean_url += f"?{parsed.query}"
            
            # Check if URL is within the same domain
            if self.base_domain and parsed.netloc != self.base_domain:
                continue
            
            # Filter out common non-content URLs
            skip_patterns = [
                'mailto:', 'tel:', 'javascript:', '#',
                '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg',
                '.zip', '.tar', '.gz', '.mp4', '.mp3', '.avi'
            ]
            if any(skip in clean_url.lower() for skip in skip_patterns):
                continue
            
            links.append(clean_url)
        
        return list(set(links))  # Remove duplicates
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing trailing slashes and fragments"""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL should be scraped"""
        parsed = urlparse(url)
        
        # Must be HTTP or HTTPS
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # Must be within the same domain
        if self.base_domain and parsed.netloc != self.base_domain:
            return False
        
        # Skip already visited
        normalized = self._normalize_url(url)
        if normalized in self.visited_urls:
            return False
        
        return True
    
    def scrape(self, url: str, include_links: bool = False) -> dict:
        """
        Scrape text content from a single page
        
        Args:
            url: URL to scrape
            include_links: Whether to include link text and URLs
        
        Returns:
            Dictionary with scraped content
        """
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        normalized_url = self._normalize_url(url)
        
        if normalized_url in self.visited_urls:
            return {
                'url': url,
                'text': '',
                'error': 'Already visited'
            }
        
        print(f"Scraping: {url}")
        
        html = self._get_page_content(url)
        if not html:
            return {
                'url': url,
                'text': '',
                'error': 'Failed to fetch page content'
            }
        
        # Mark as visited
        self.visited_urls.add(normalized_url)
        
        # Extract main text content
        text_content = self._extract_text_from_html(html)
        
        result = {
            'url': url,
            'text': text_content,
            'word_count': len(text_content.split()),
            'character_count': len(text_content)
        }
        
        if include_links:
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            for link in soup.find_all('a', href=True):
                link_text = link.get_text(strip=True)
                link_url = urljoin(url, link['href'])
                if link_text or link_url:
                    links.append({
                        'text': link_text,
                        'url': link_url
                    })
            result['links'] = links
        
        return result
    
    def deep_scrape(
        self,
        root_url: str,
        max_depth: int = 5,
        max_pages: int = 100,
        delay: float = 1.0,
        include_links: bool = False
    ) -> List[Dict]:
        """
        Deep scrape a website starting from root URL, following all links
        
        Args:
            root_url: Starting URL
            max_depth: Maximum depth to crawl (default: 5)
            max_pages: Maximum number of pages to scrape (default: 100)
            delay: Delay between requests in seconds (default: 1.0)
            include_links: Whether to include link information
        
        Returns:
            List of dictionaries with scraped content from all pages
        """
        if not root_url.startswith(('http://', 'https://')):
            root_url = 'https://' + root_url
        
        # Set base domain
        parsed = urlparse(root_url)
        self.base_domain = parsed.netloc
        
        # Initialize queue with (url, depth) tuples
        queue = deque([(root_url, 0)])
        results = []
        
        print(f"Starting deep scrape of {root_url}")
        print(f"Max depth: {max_depth}, Max pages: {max_pages}")
        print("-" * 80)
        
        while queue and len(results) < max_pages:
            current_url, depth = queue.popleft()
            
            # Skip if too deep
            if depth > max_depth:
                continue
            
            # Skip if already visited
            normalized = self._normalize_url(current_url)
            if normalized in self.visited_urls:
                continue
            
            # Fetch page content once
            html = self._get_page_content(current_url)
            if not html:
                print(f"  ✗ Failed to fetch: {current_url}")
                continue
            
            # Scrape the page (mark as visited)
            normalized = self._normalize_url(current_url)
            self.visited_urls.add(normalized)
            
            # Extract text content
            text_content = self._extract_text_from_html(html)
            
            result = {
                'url': current_url,
                'text': text_content,
                'word_count': len(text_content.split()),
                'character_count': len(text_content),
                'depth': depth
            }
            
            if include_links:
                soup = BeautifulSoup(html, 'html.parser')
                links = []
                for link in soup.find_all('a', href=True):
                    link_text = link.get_text(strip=True)
                    link_url = urljoin(current_url, link['href'])
                    if link_text or link_url:
                        links.append({
                            'text': link_text,
                            'url': link_url
                        })
                result['links'] = links
            
            results.append(result)
            
            print(f"  ✓ Scraped (depth {depth}): {len(result['text'])} chars, {result['word_count']} words")
            
            # If not at max depth, extract links and add to queue
            if depth < max_depth:
                links = self._extract_links(html, current_url)
                for link in links:
                    if self._is_valid_url(link):
                        queue.append((link, depth + 1))
            
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
        
        print("-" * 80)
        print(f"Deep scrape complete: {len(results)} pages scraped")
        
        return results
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()


def main():
    parser = argparse.ArgumentParser(
        description='Web scraper that extracts all text information from a website'
    )
    parser.add_argument('url', help='URL of the website to scrape')
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: print to stdout)',
        default=None
    )
    parser.add_argument(
        '--selenium', '-s',
        action='store_true',
        help='Use Selenium for JavaScript-rendered pages (requires ChromeDriver)'
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run browser in visible mode (only for Selenium)'
    )
    parser.add_argument(
        '--include-links',
        action='store_true',
        help='Include links information in output'
    )
    parser.add_argument(
        '--deep', '-d',
        action='store_true',
        help='Deep scrape: follow all links from root page to end'
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        default=5,
        help='Maximum crawl depth for deep scrape (default: 5)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=100,
        help='Maximum number of pages to scrape (default: 100)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    scraper = WebScraper(
        use_selenium=args.selenium,
        headless=not args.no_headless
    )
    
    try:
        if args.deep:
            # Deep scrape mode
            results = scraper.deep_scrape(
                args.url,
                max_depth=args.max_depth,
                max_pages=args.max_pages,
                delay=args.delay,
                include_links=args.include_links
            )
            
            # Generate output
            output_text = f"DEEP SCRAPE RESULTS\n"
            output_text += f"{'='*80}\n"
            output_text += f"Root URL: {args.url}\n"
            output_text += f"Total Pages Scraped: {len(results)}\n"
            output_text += f"Total Words: {sum(r['word_count'] for r in results)}\n"
            output_text += f"Total Characters: {sum(r['character_count'] for r in results)}\n"
            output_text += f"{'='*80}\n\n"
            
            # Add content from each page
            for i, result in enumerate(results, 1):
                output_text += f"\n{'='*80}\n"
                output_text += f"PAGE {i} (Depth {result['depth']})\n"
                output_text += f"{'='*80}\n"
                output_text += f"URL: {result['url']}\n"
                output_text += f"Word Count: {result['word_count']}\n"
                output_text += f"Character Count: {result['character_count']}\n"
                output_text += f"\nTEXT CONTENT:\n"
                output_text += f"{'-'*80}\n"
                output_text += result['text']
                output_text += "\n"
                
                if args.include_links and 'links' in result:
                    output_text += f"\nLINKS:\n"
                    output_text += f"{'-'*80}\n"
                    for link in result['links']:
                        output_text += f"Text: {link['text']}\nURL: {link['url']}\n\n"
        else:
            # Single page scrape mode
            result = scraper.scrape(args.url, include_links=args.include_links)
            
            output_text = f"URL: {result['url']}\n"
            output_text += f"Word Count: {result['word_count']}\n"
            output_text += f"Character Count: {result['character_count']}\n"
            output_text += "\n" + "="*80 + "\n"
            output_text += "TEXT CONTENT:\n"
            output_text += "="*80 + "\n\n"
            output_text += result['text']
            
            if args.include_links and 'links' in result:
                output_text += "\n\n" + "="*80 + "\n"
                output_text += "LINKS:\n"
                output_text += "="*80 + "\n\n"
                for link in result['links']:
                    output_text += f"Text: {link['text']}\nURL: {link['url']}\n\n"
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"\nContent saved to: {args.output}")
        else:
            print(output_text)
            
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
        if args.deep:
            print(f"Scraped {len(scraper.visited_urls)} pages before interruption")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        scraper.close()


if __name__ == '__main__':
    main()

