"""
RSS Feed Parser Client for Investment Scout

Parses RSS feeds from various financial news sources.
No API key required, respects rate limits and robots.txt.
"""

import logging
from datetime import datetime
from typing import List, Optional
import xml.etree.ElementTree as ET
import requests
from email.utils import parsedate_to_datetime

from src.clients.base_api_client import BaseAPIClient
from src.models.investment_scout_models import NewsArticle


logger = logging.getLogger(__name__)


class RSSFeedClient(BaseAPIClient):
    """
    RSS feed parser for financial news.
    
    No API key required, self-imposed rate limiting.
    """
    
    # Common financial RSS feeds
    DEFAULT_FEEDS = [
        'https://feeds.finance.yahoo.com/rss/2.0/headline',
        'https://www.cnbc.com/id/100003114/device/rss/rss.html',  # Top news
        'https://www.reuters.com/finance',
        'https://www.marketwatch.com/rss/topstories',
    ]
    
    def __init__(self):
        super().__init__(
            name="RSSFeed",
            requests_per_minute=30,  # Conservative rate limiting
            failure_threshold=5,
            circuit_timeout=60
        )
    
    def parse_feed(self, feed_url: str) -> List[NewsArticle]:
        """
        Parse an RSS feed and extract news articles.
        
        Args:
            feed_url: URL of the RSS feed
            
        Returns:
            List of NewsArticle objects
        """
        def _fetch():
            headers = {
                'User-Agent': 'InvestmentScout/1.0 (Educational Project)'
            }
            
            response = requests.get(feed_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            articles = []
            
            # Handle both RSS 2.0 and Atom formats
            if root.tag == 'rss':
                articles = self._parse_rss(root, feed_url)
            elif root.tag.endswith('feed'):
                articles = self._parse_atom(root, feed_url)
            else:
                logger.warning(f"Unknown feed format for {feed_url}")
            
            logger.info(f"Parsed {len(articles)} articles from {feed_url}")
            return articles
        
        try:
            return self.call_with_retry(_fetch)
        except Exception as e:
            logger.error(f"Failed to parse RSS feed {feed_url}: {e}")
            return []
    
    def _parse_rss(self, root: ET.Element, feed_url: str) -> List[NewsArticle]:
        """Parse RSS 2.0 format"""
        articles = []
        
        for item in root.findall('.//item'):
            try:
                title = item.findtext('title', '')
                description = item.findtext('description', '')
                link = item.findtext('link', '')
                pub_date_str = item.findtext('pubDate', '')
                
                # Parse publication date
                try:
                    published_at = parsedate_to_datetime(pub_date_str)
                except Exception:
                    published_at = datetime.now()
                
                # Extract source from feed URL
                source = self._extract_source(feed_url)
                
                article = NewsArticle(
                    title=title,
                    summary=description,
                    source=source,
                    published_at=published_at,
                    url=link,
                    sentiment=None
                )
                articles.append(article)
            except Exception as e:
                logger.warning(f"Error parsing RSS item: {e}")
                continue
        
        return articles
    
    def _parse_atom(self, root: ET.Element, feed_url: str) -> List[NewsArticle]:
        """Parse Atom format"""
        articles = []
        
        # Atom uses namespaces
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        for entry in root.findall('atom:entry', ns):
            try:
                title = entry.findtext('atom:title', '', ns)
                summary = entry.findtext('atom:summary', '', ns)
                
                # Get link
                link_elem = entry.find('atom:link', ns)
                link = link_elem.get('href', '') if link_elem is not None else ''
                
                # Parse publication date
                updated_str = entry.findtext('atom:updated', '', ns)
                try:
                    published_at = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                except Exception:
                    published_at = datetime.now()
                
                source = self._extract_source(feed_url)
                
                article = NewsArticle(
                    title=title,
                    summary=summary,
                    source=source,
                    published_at=published_at,
                    url=link,
                    sentiment=None
                )
                articles.append(article)
            except Exception as e:
                logger.warning(f"Error parsing Atom entry: {e}")
                continue
        
        return articles
    
    def _extract_source(self, feed_url: str) -> str:
        """Extract source name from feed URL"""
        if 'yahoo' in feed_url:
            return 'Yahoo Finance'
        elif 'cnbc' in feed_url:
            return 'CNBC'
        elif 'reuters' in feed_url:
            return 'Reuters'
        elif 'marketwatch' in feed_url:
            return 'MarketWatch'
        elif 'bloomberg' in feed_url:
            return 'Bloomberg'
        else:
            return 'RSS Feed'
    
    def parse_multiple_feeds(self, feed_urls: Optional[List[str]] = None) -> List[NewsArticle]:
        """
        Parse multiple RSS feeds and aggregate results.
        
        Args:
            feed_urls: List of feed URLs (uses defaults if None)
            
        Returns:
            Aggregated list of NewsArticle objects
        """
        if feed_urls is None:
            feed_urls = self.DEFAULT_FEEDS
        
        all_articles = []
        for feed_url in feed_urls:
            articles = self.parse_feed(feed_url)
            all_articles.extend(articles)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article.url and article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        logger.info(
            f"Parsed {len(unique_articles)} unique articles from "
            f"{len(feed_urls)} feeds"
        )
        return unique_articles
