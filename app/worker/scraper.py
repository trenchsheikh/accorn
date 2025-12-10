import asyncio
import json
import logging
import re
import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.models import Agent, Chunk, ScrapeJob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperWorker:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.db: Session = SessionLocal()
        
        # Convert string job_id to UUID for SQLAlchemy
        import uuid
        try:
            real_id = uuid.UUID(job_id)
        except ValueError:
            print(f"Invalid job_id: {job_id}")
            return

        self.job = self.db.query(ScrapeJob).filter(ScrapeJob.id == real_id).first()
        if not self.job:
            raise ValueError(f"Job {job_id} not found")
        
        self.agent = self.job.agent
        self.visited_urls: Set[str] = set()
        self.base_domain = urlparse(self.job.root_url).netloc
        
        # Config
        self.config = self.job.config or {}
        self.max_depth = self.config.get("max_depth", 3)
        self.max_pages = self.config.get("max_pages", 50)
        self.delay = self.config.get("delay_seconds", 1.0)
        
    async def run(self):
        """Execute the scraping job"""
        try:
            self.job.status = "running"
            self.job.started_at = datetime.utcnow()
            self.db.commit()
            
            await self._deep_scrape(self.job.root_url)
            
            self.job.status = "completed"
            self.job.completed_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Scrape job failed: {e}")
            self.job.status = "failed"
            self.job.error_message = str(e)
            self.db.commit()
        finally:
            self.db.close()

    async def _deep_scrape(self, root_url: str):
        """Deep scrape using Playwright or Requests"""
        queue = deque([(root_url, 0)])
        pages_scraped = 0
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            
            while queue and pages_scraped < self.max_pages:
                url, depth = queue.popleft()
                
                if depth > self.max_depth:
                    continue
                
                if url in self.visited_urls:
                    continue
                
                logger.info(f"Scraping {url} (Depth {depth})")
                
                try:
                    page_content = await self._fetch_page(context, url)
                    if not page_content:
                        continue
                        
                    self.visited_urls.add(url)
                    pages_scraped += 1
                    self.job.pages_scraped = pages_scraped
                    self.db.commit()
                    
                    # Process content
                    text = self._extract_text(page_content)
                    chunks = self._chunk_text(text, url)
                    self._save_chunks(chunks)
                    
                    # Find links
                    if depth < self.max_depth:
                        links = self._extract_links(page_content, url)
                        for link in links:
                            if link not in self.visited_urls:
                                queue.append((link, depth + 1))
                                
                    if self.delay > 0:
                        await asyncio.sleep(self.delay)
                        
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    
            await browser.close()

    async def _fetch_page(self, context, url: str) -> Optional[str]:
        """Fetch page content using Playwright"""
        try:
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            content = await page.content()
            await page.close()
            return content
        except Exception as e:
            logger.error(f"Playwright error for {url}: {e}")
            return None

    def _extract_text(self, html: str) -> str:
        """Extract clean text from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup(["script", "style", "meta", "link", "noscript"]):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', text).strip()

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract internal links"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            
            if parsed.netloc == self.base_domain and parsed.scheme in ('http', 'https'):
                links.append(full_url)
        return list(set(links))

    def _chunk_text(self, text: str, url: str) -> List[Dict]:
        """Simple chunking strategy (can be improved with the one from plan.md)"""
        # Using a simplified version for MVP, can upgrade to the smart chunker later
        chunk_size = 1000
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk_content = text[i:i + chunk_size]
            chunks.append({
                "content": chunk_content,
                "url": url,
                "token_count": len(chunk_content) // 4  # Approx
            })
        return chunks

    def _save_chunks(self, chunks_data: List[Dict]):
        """Save chunks to DB"""
        for data in chunks_data:
            chunk = Chunk(
                agent_id=self.agent.id,
                chunk_id=f"{self.job.id}-{uuid.uuid4()}", # Temporary ID generation
                page_url=data['url'],
                content=data['content'],
                token_count=data['token_count'],
                metadata_={"source": "scraper"}
            )
            self.db.add(chunk)
        self.db.commit()

import uuid
