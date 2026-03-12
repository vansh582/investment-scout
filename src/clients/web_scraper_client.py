"""
Web Scraper Client for Investment Scout

Scrapes publicly available financial data with rate limiting and robots.txt compliance.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
import time

from src.clients.base_api_client import BaseAPIClient


logger = logging.getLogger(__name__)


class WebScraperClient(BaseAPIClient):
    """
    Web scraper for public financial data.
    
    Respects robots.txt and implements aggressive rate limiting.
    """
    
    def __init__(self):
        super().__init__(
            name="WebScraper",
            requests_per_minute=10,  # Very conservative rate limiting
            failure_threshold=5,
            circuit_timeout=60
        )
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.user_agent = 'InvestmentScout/1.0 (Educational Project; +https://github.com/investment-scout)'
    
    def can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False otherwise
        """
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Check cache
        if base_url not in self.robots_cache:
            robots_url = urljoin(base_url, '/robots.txt')
            rp = RobotFileParser()
            rp.set_url(robots_url)
            
            try:
                rp.read()
                self.robots_cache[base_url] = rp
            except Exception as e:
                logger.warning(f"Could not read robots.txt for {base_url}: {e}")
                # If we can't read robots.txt, be conservative and allow
                return True
        
        rp = self.robots_cache[base_url]
        return rp.can_fetch(self.user_agent, url)
    
    def scrape_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Scrape a web page with robots.txt compliance.
        
        Args:
            url: URL to scrape
            
        Returns:
            BeautifulSoup object or None if failed
        """
        # Check robots.txt
        if not self.can_fetch(url):
            logger.warning(f"Robots.txt disallows scraping {url}")
            return None
        
        def _fetch():
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None
    
    def scrape_text_content(self, url: str) -> Optional[str]:
        """
        Scrape text content from a page.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted text or None
        """
        soup = self.scrape_page(url)
        if soup is None:
            return None
        
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        return text
    
    def scrape_with_delay(self, urls: List[str], delay_seconds: float = 2.0) -> List[Dict]:
        """
        Scrape multiple URLs with delay between requests.
        
        Args:
            urls: List of URLs to scrape
            delay_seconds: Delay between requests
            
        Returns:
            List of results with url and content
        """
        results = []
        
        for url in urls:
            content = self.scrape_text_content(url)
            if content:
                results.append({
                    'url': url,
                    'content': content,
                    'scraped_at': datetime.now()
                })
            
            # Delay between requests
            if url != urls[-1]:  # Don't delay after last URL
                time.sleep(delay_seconds)
        
        logger.info(f"Successfully scraped {len(results)}/{len(urls)} URLs")
        return results
    
    def extract_tables(self, url: str) -> List[List[List[str]]]:
        """
        Extract all tables from a page.
        
        Args:
            url: URL to scrape
            
        Returns:
            List of tables, where each table is a list of rows
        """
        soup = self.scrape_page(url)
        if soup is None:
            return []
        
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = []
                for cell in tr.find_all(['td', 'th']):
                    cells.append(cell.get_text(strip=True))
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        
        logger.info(f"Extracted {len(tables)} tables from {url}")
        return tables
