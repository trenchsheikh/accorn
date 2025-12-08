#!/usr/bin/env python3
"""
Web Scraper - Extracts all text information from a website
Supports both static HTML pages and JavaScript-rendered content
"""

import argparse
import sys
import time
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Set, Optional, List, Dict, Tuple
from collections import deque
import re

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

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


class RAGKnowledgeExtractor:
    """Extracts and structures business knowledge optimized for RAG systems"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the RAG knowledge extractor
        
        Args:
            chunk_size: Target chunk size in characters (default: 1000)
            chunk_overlap: Overlap between chunks in characters (default: 200)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = None
        if TIKTOKEN_AVAILABLE:
            try:
                self.encoding = tiktoken.get_encoding("cl100k_base")
            except:
                pass
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken if available"""
        if self.encoding:
            return len(self.encoding.encode(text))
        # Fallback: approximate 1 token = 4 characters
        return len(text) // 4
    
    def _extract_business_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract business-relevant entities from text with improved intelligence"""
        entities = {
            'companies': [],
            'products': [],
            'services': [],
            'technologies': [],
            'locations': [],
            'contact_info': [],
            'prices': [],
            'dates': []
        }
        
        # Extract email addresses (improved pattern)
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        entities['contact_info'].extend(emails)
        
        # Extract phone numbers (improved patterns)
        phone_patterns = [
            r'\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\+?\d{10,15}',
            r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}'
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            entities['contact_info'].extend(phones)
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s<>"\'\)]+', text)
        entities['contact_info'].extend(urls)
        
        # Extract prices/currency amounts
        prices = re.findall(r'\$[\d,]+\.?\d*|€[\d,]+\.?\d*|£[\d,]+\.?\d*|[\d,]+\.?\d*\s*(USD|EUR|GBP|dollars?|euros?|pounds?)', text, re.IGNORECASE)
        entities['prices'].extend([p[0] if isinstance(p, tuple) else p for p in prices])
        
        # Extract dates
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}'
        ]
        for pattern in date_patterns:
            dates = re.findall(pattern, text, re.IGNORECASE)
            entities['dates'].extend(dates)
        
        # Improved company name extraction
        # Look for patterns like "Company Name Inc.", "Company Name LLC", etc.
        company_suffixes = ['Inc', 'LLC', 'Ltd', 'Corp', 'Corporation', 'Company', 'Co', 'LLP', 'LP', 'PC']
        company_patterns = []
        
        # Pattern 1: Capitalized words followed by company suffix
        for suffix in company_suffixes:
            pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+' + re.escape(suffix) + r'\b'
            matches = re.findall(pattern, text)
            company_patterns.extend(matches)
        
        # Pattern 2: Standalone capitalized phrases (2-4 words, all caps or title case)
        standalone = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b', text)
        # Filter out common words that aren't company names
        common_words = {'The', 'This', 'That', 'These', 'Those', 'There', 'Here', 'Where', 'When', 'What', 'How', 'Why',
                       'About', 'Above', 'Below', 'After', 'Before', 'During', 'While', 'Since', 'Until', 'Because',
                       'However', 'Therefore', 'Moreover', 'Furthermore', 'Additionally', 'Also', 'Other', 'Another',
                       'First', 'Second', 'Third', 'Last', 'Next', 'Previous', 'Current', 'Recent', 'New', 'Old'}
        company_patterns.extend([c for c in standalone if c not in common_words and len(c.split()) >= 2])
        
        # Pattern 3: Look for "we", "our company", "our product" patterns
        context_patterns = re.findall(r'\b(?:we|our|us)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', text, re.IGNORECASE)
        company_patterns.extend(context_patterns)
        
        entities['companies'] = list(set([c.strip() for c in company_patterns if 3 < len(c) < 50]))[:25]
        
        # Improved technology extraction
        tech_keywords = {
            'languages': ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'Swift', 'Kotlin', 'TypeScript',
                         'Ruby', 'PHP', 'Scala', 'R', 'MATLAB', 'Perl', 'Shell', 'Bash'],
            'frameworks': ['React', 'Vue', 'Angular', 'Django', 'Flask', 'FastAPI', 'Express', 'Spring', 'Laravel',
                          'Rails', 'ASP.NET', 'Next.js', 'Nuxt', 'Svelte', 'Ember'],
            'databases': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch', 'Cassandra', 'DynamoDB',
                         'SQLite', 'Oracle', 'SQL Server', 'MariaDB', 'Neo4j'],
            'cloud': ['AWS', 'Azure', 'GCP', 'Google Cloud', 'Amazon Web Services', 'Heroku', 'DigitalOcean',
                     'Cloudflare', 'Vercel', 'Netlify'],
            'tools': ['Docker', 'Kubernetes', 'Git', 'Jenkins', 'CI/CD', 'GitHub', 'GitLab', 'Jira', 'Confluence'],
            'concepts': ['API', 'REST', 'GraphQL', 'Microservices', 'DevOps', 'Agile', 'Scrum', 'Machine Learning',
                        'AI', 'Artificial Intelligence', 'Blockchain', 'Cryptocurrency', 'IoT', 'Big Data']
        }
        
        found_tech = []
        text_lower = text.lower()
        for category, keywords in tech_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_tech.append(keyword)
        
        entities['technologies'] = list(set(found_tech))[:30]
        
        # Extract products/services (look for patterns like "our product", "our service", product names)
        product_patterns = [
            r'(?:our|the|a|an)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:product|service|solution|platform|tool|software|application)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:v\d+|version\s+\d+|v\.\d+)',  # Version numbers
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:Pro|Plus|Premium|Enterprise|Standard|Basic)'
        ]
        for pattern in product_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['products'].extend([m.strip() for m in matches if len(m.strip()) > 3])
        
        # Extract services (look for service-related keywords)
        service_keywords = ['service', 'consulting', 'support', 'maintenance', 'training', 'implementation',
                          'integration', 'development', 'design', 'strategy', 'analytics', 'marketing']
        service_patterns = re.findall(
            r'(?:our|we\s+offer|provides?|offers?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:' + '|'.join(service_keywords) + ')',
            text, re.IGNORECASE
        )
        entities['services'].extend([s.strip() for s in service_patterns if len(s.strip()) > 3])
        
        # Extract locations (cities, countries, addresses)
        # Common city/country patterns
        location_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(?:CA|NY|TX|FL|IL|PA|OH|GA|NC|MI|NJ|VA|WA|AZ|MA|TN|IN|MO|MD|WI|CO|MN|SC|AL|LA|KY|OR|OK|CT|IA|AR|UT|NV|MS|KS|NM|NE|WV|ID|HI|NH|ME|MT|RI|DE|SD|ND|AK|DC|VT|WY)\b',  # US states
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*(?:USA|United States|UK|United Kingdom|Canada|Australia|Germany|France|Italy|Spain|Japan|China|India)\b'
        ]
        for pattern in location_patterns:
            locations = re.findall(pattern, text)
            entities['locations'].extend([l.strip() for l in locations if len(l.strip()) > 2])
        
        # Remove duplicates and filter
        for key in entities:
            entities[key] = list(set([e for e in entities[key] if e and len(str(e).strip()) > 0]))[:20]
        
        return entities
    
    def _extract_key_topics(self, text: str, max_topics: int = 15) -> List[str]:
        """Extract key topics from text using improved TF-IDF-like analysis"""
        # Extended stop words list
        stop_words = {
            'that', 'this', 'with', 'from', 'have', 'will', 'your', 'they', 'their', 'there', 'these', 'those',
            'about', 'which', 'would', 'could', 'should', 'shall', 'must', 'might', 'may', 'can', 'cannot',
            'what', 'when', 'where', 'why', 'how', 'who', 'whom', 'whose', 'while', 'during', 'after', 'before',
            'since', 'until', 'because', 'although', 'though', 'however', 'therefore', 'moreover', 'furthermore',
            'additionally', 'also', 'other', 'another', 'first', 'second', 'third', 'last', 'next', 'previous',
            'current', 'recent', 'new', 'old', 'many', 'much', 'more', 'most', 'some', 'any', 'all', 'each',
            'every', 'both', 'either', 'neither', 'such', 'same', 'different', 'same', 'very', 'quite', 'rather',
            'just', 'only', 'even', 'still', 'yet', 'already', 'again', 'once', 'twice', 'here', 'there', 'where',
            'when', 'then', 'now', 'today', 'yesterday', 'tomorrow', 'soon', 'later', 'early', 'late', 'always',
            'never', 'often', 'sometimes', 'usually', 'rarely', 'seldom', 'already', 'just', 'now', 'then'
        }
        
        # Extract words (4+ characters, alphanumeric)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Filter stop words
        filtered_words = [w for w in words if w not in stop_words]
        
        # Calculate word frequency
        word_freq = {}
        total_words = len(filtered_words)
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Calculate importance score (TF with length bonus and position bonus)
        # Longer words and words appearing in first/last sentences are more important
        sentences = re.split(r'[.!?]+\s+', text)
        first_sentence_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', sentences[0].lower() if sentences else ''))
        last_sentence_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', sentences[-1].lower() if sentences else ''))
        
        word_scores = {}
        for word, freq in word_freq.items():
            # Base TF score
            tf_score = freq / total_words if total_words > 0 else 0
            
            # Length bonus (longer words often more specific/important)
            length_bonus = len(word) / 10.0
            
            # Position bonus (words in first/last sentences are often key topics)
            position_bonus = 0
            if word in first_sentence_words:
                position_bonus += 0.3
            if word in last_sentence_words:
                position_bonus += 0.2
            
            # Combined score
            word_scores[word] = tf_score * (1 + length_bonus + position_bonus)
        
        # Get top topics by score
        topics = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)[:max_topics]
        return [topic[0] for topic in topics if topic[1] > 0.001]  # Filter very low scores
    
    def _chunk_text(self, text: str, metadata: Dict) -> List[Dict]:
        """Chunk text into optimal sizes for RAG with improved semantic awareness"""
        chunks = []
        
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        if len(text) <= self.chunk_size:
            # Text fits in one chunk
            chunks.append({
                'content': text,
                'metadata': metadata.copy(),
                'chunk_index': 0,
                'total_chunks': 1,
                'token_count': self._count_tokens(text),
                'char_count': len(text)
            })
        else:
            # Try semantic chunking: split by paragraphs first
            paragraphs = text.split('\n\n')
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            # If paragraphs are too large, split by sentences
            if not paragraphs or max(len(p) for p in paragraphs) > self.chunk_size * 1.5:
                # Split by sentences
                sentences = re.split(r'([.!?]+\s+)', text)
                # Recombine sentences with their punctuation
                sentences = [''.join(sentences[i:i+2]) for i in range(0, len(sentences)-1, 2)]
                if sentences[-1]:
                    sentences.append(sentences[-1])
                paragraphs = [s.strip() for s in sentences if s.strip()]
            
            # Build chunks from paragraphs
            current_chunk = []
            current_length = 0
            chunk_index = 0
            
            for para in paragraphs:
                para_length = len(para)
                
                # If single paragraph is larger than chunk size, split it
                if para_length > self.chunk_size:
                    # Save current chunk if exists
                    if current_chunk:
                        chunk_text = ' '.join(current_chunk)
                        chunks.append({
                            'content': chunk_text,
                            'metadata': metadata.copy(),
                            'chunk_index': chunk_index,
                            'token_count': self._count_tokens(chunk_text),
                            'char_count': len(chunk_text)
                        })
                        chunk_index += 1
                        current_chunk = []
                        current_length = 0
                    
                    # Split large paragraph by sentences
                    para_sentences = re.split(r'([.!?]+\s+)', para)
                    para_sentences = [''.join(para_sentences[i:i+2]) for i in range(0, len(para_sentences)-1, 2)]
                    if para_sentences[-1]:
                        para_sentences.append(para_sentences[-1])
                    
                    for sent in para_sentences:
                        sent = sent.strip()
                        if not sent:
                            continue
                        sent_length = len(sent)
                        
                        if current_length + sent_length > self.chunk_size and current_chunk:
                            # Save current chunk
                            chunk_text = ' '.join(current_chunk)
                            chunks.append({
                                'content': chunk_text,
                                'metadata': metadata.copy(),
                                'chunk_index': chunk_index,
                                'token_count': self._count_tokens(chunk_text),
                                'char_count': len(chunk_text)
                            })
                            chunk_index += 1
                            
                            # Start new chunk with overlap (last sentence from previous chunk)
                            if current_chunk:
                                overlap_text = current_chunk[-1] if len(current_chunk) > 0 else ''
                                current_chunk = [overlap_text] if overlap_text else []
                                current_length = len(overlap_text)
                        
                        current_chunk.append(sent)
                        current_length += sent_length + 1  # +1 for space
                
                # If adding this paragraph would exceed chunk size
                elif current_length + para_length > self.chunk_size and current_chunk:
                    # Save current chunk
                    chunk_text = ' '.join(current_chunk)
                    chunks.append({
                        'content': chunk_text,
                        'metadata': metadata.copy(),
                        'chunk_index': chunk_index,
                        'token_count': self._count_tokens(chunk_text),
                        'char_count': len(chunk_text)
                    })
                    chunk_index += 1
                    
                    # Start new chunk with overlap
                    if self.chunk_overlap > 0 and current_chunk:
                        # Take last N characters for overlap
                        overlap_text = ' '.join(current_chunk[-2:]) if len(current_chunk) >= 2 else current_chunk[-1]
                        if len(overlap_text) > self.chunk_overlap:
                            overlap_text = overlap_text[-self.chunk_overlap:]
                        current_chunk = [overlap_text] if overlap_text else []
                        current_length = len(overlap_text)
                    else:
                        current_chunk = []
                        current_length = 0
                
                # Add paragraph to current chunk
                current_chunk.append(para)
                current_length += para_length + 2  # +2 for paragraph spacing
            
            # Add final chunk
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'metadata': metadata.copy(),
                    'chunk_index': chunk_index,
                    'token_count': self._count_tokens(chunk_text),
                    'char_count': len(chunk_text)
                })
            
            # Update total_chunks for all chunks
            for chunk in chunks:
                chunk['total_chunks'] = len(chunks)
        
        return chunks
    
    def process_for_rag(self, scrape_results: List[Dict], root_url: str) -> Dict:
        """
        Process scraped results into RAG-optimized format
        
        Args:
            scrape_results: List of scraped page results
            root_url: Root URL of the website
        
        Returns:
            Dictionary with RAG-optimized knowledge base
        """
        all_chunks = []
        all_entities = {
            'companies': set(),
            'products': set(),
            'services': set(),
            'technologies': set(),
            'locations': set(),
            'contact_info': set(),
            'prices': set(),
            'dates': set()
        }
        all_topics = set()
        
        for result in scrape_results:
            if result.get('error') or not result.get('text'):
                continue
            
            url = result['url']
            text = result['text']
            depth = result.get('depth', 0)
            
            # Extract entities and topics
            entities = self._extract_business_entities(text)
            topics = self._extract_key_topics(text)
            
            # Aggregate entities
            for key in all_entities:
                all_entities[key].update(entities.get(key, []))
            all_topics.update(topics)
            
            # Create metadata for this page
            metadata = {
                'url': url,
                'source': root_url,
                'depth': depth,
                'word_count': result.get('word_count', 0),
                'character_count': result.get('character_count', 0),
                'scraped_at': datetime.now().isoformat(),
                'entities': entities,
                'topics': topics
            }
            
            # Chunk the text
            chunks = self._chunk_text(text, metadata)
            all_chunks.extend(chunks)
        
        # Convert sets to lists for JSON serialization
        aggregated_entities = {k: list(v)[:20] for k, v in all_entities.items()}
        
        return {
            'knowledge_base': {
                'root_url': root_url,
                'total_pages': len(scrape_results),
                'total_chunks': len(all_chunks),
                'total_tokens': sum(c['token_count'] for c in all_chunks),
                'scraped_at': datetime.now().isoformat(),
                'aggregated_entities': aggregated_entities,
                'aggregated_topics': list(all_topics)[:30]
            },
            'chunks': all_chunks
        }
    
    def save_rag_format(self, rag_data: Dict, output_path: str, format: str = 'json'):
        """
        Save RAG-optimized data to file
        
        Args:
            rag_data: RAG-optimized data dictionary
            output_path: Output file path
            format: Output format ('json' or 'jsonl')
        """
        if format == 'jsonl':
            # JSONL format: one JSON object per line (each chunk)
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write knowledge base summary first
                f.write(json.dumps({'type': 'knowledge_base', 'data': rag_data['knowledge_base']}, ensure_ascii=False) + '\n')
                # Write each chunk
                for chunk in rag_data['chunks']:
                    f.write(json.dumps({'type': 'chunk', 'data': chunk}, ensure_ascii=False) + '\n')
        else:
            # Standard JSON format
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(rag_data, f, indent=2, ensure_ascii=False)


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
    parser.add_argument(
        '--text-output',
        action='store_true',
        help='Output in plain text format instead of JSON (default: JSON)'
    )
    parser.add_argument(
        '--rag-format',
        choices=['json', 'jsonl'],
        default='json',
        help='JSON output format: json (structured) or jsonl (one chunk per line) (default: json)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help='Chunk size in characters for RAG output (default: 1000)'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=200,
        help='Overlap between chunks in characters for RAG output (default: 200)'
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
            
            # Always process for RAG (JSON output by default)
            print("\nProcessing content for RAG optimization...")
            extractor = RAGKnowledgeExtractor(
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap
            )
            rag_data = extractor.process_for_rag(results, args.url)
            
            if args.text_output:
                # Generate standard text output if requested
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
                
                output_path = args.output or 'scrape_output.txt'
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                print(f"\nText content saved to: {output_path}")
            else:
                # Default: JSON output
                output_path = args.output or 'knowledge_base.json'
                extractor.save_rag_format(rag_data, output_path, format=args.rag_format)
                
                print(f"\n{'='*80}")
                print("RAG Knowledge Base Generated")
                print(f"{'='*80}")
                print(f"Total Pages: {rag_data['knowledge_base']['total_pages']}")
                print(f"Total Chunks: {rag_data['knowledge_base']['total_chunks']}")
                print(f"Total Tokens: {rag_data['knowledge_base']['total_tokens']}")
                print(f"\nAggregated Entities:")
                for entity_type, entities in rag_data['knowledge_base']['aggregated_entities'].items():
                    if entities:
                        print(f"  {entity_type}: {', '.join(str(e) for e in entities[:5])}{'...' if len(entities) > 5 else ''}")
                print(f"\nTop Topics: {', '.join(rag_data['knowledge_base']['aggregated_topics'][:10])}")
                print(f"\nSaved to: {output_path}")
        else:
            # Single page scrape mode
            result = scraper.scrape(args.url, include_links=args.include_links)
            
            # Always process for RAG (JSON output by default)
            print("\nProcessing content for RAG optimization...")
            extractor = RAGKnowledgeExtractor(
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap
            )
            rag_data = extractor.process_for_rag([result], args.url)
            
            if args.text_output:
                # Generate standard text output if requested
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
                
                output_path = args.output or 'scrape_output.txt'
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                print(f"\nText content saved to: {output_path}")
            else:
                # Default: JSON output
                output_path = args.output or 'knowledge_base.json'
                extractor.save_rag_format(rag_data, output_path, format=args.rag_format)
                
                print(f"\n{'='*80}")
                print("RAG Knowledge Base Generated")
                print(f"{'='*80}")
                print(f"Total Pages: {rag_data['knowledge_base']['total_pages']}")
                print(f"Total Chunks: {rag_data['knowledge_base']['total_chunks']}")
                print(f"Total Tokens: {rag_data['knowledge_base']['total_tokens']}")
                print(f"\nAggregated Entities:")
                for entity_type, entities in rag_data['knowledge_base']['aggregated_entities'].items():
                    if entities:
                        print(f"  {entity_type}: {', '.join(str(e) for e in entities[:5])}{'...' if len(entities) > 5 else ''}")
                print(f"\nTop Topics: {', '.join(rag_data['knowledge_base']['aggregated_topics'][:10])}")
                print(f"\nSaved to: {output_path}")
            
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

