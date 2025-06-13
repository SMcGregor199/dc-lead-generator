#!/usr/bin/env python3
"""
News Fetcher Module for Higher Education News
Fetches and summarizes news articles from Higher Ed RSS feeds
Enhanced with reliability, security, and optimization improvements
"""

import feedparser
import requests
import trafilatura
import os
import json
import random
import time
from datetime import datetime
from openai import OpenAI
from urllib.parse import urlparse
from source_logger import log_broken_feed, get_active_sources, mark_source_verified, mark_source_broken
from newspaper import Article
import newspaper

# Load RSS feeds from centralized configuration
def load_news_feeds():
    """Load active news feeds from sources configuration"""
    return get_active_sources('news_sources')

# Technology keywords for filtering non-tech-focused feeds
TECH_KEYWORDS = [
    'cybersecurity', 'data', 'AI', 'artificial intelligence', 'technology', 'IT', 
    'digital', 'infrastructure', 'CIO', 'ERP', 'LMS', 'SIS', 'software', 
    'innovation', 'modernization', 'IT strategy', 'cloud', 'analytics', 
    'machine learning', 'automation', 'platform', 'system', 'database',
    'security', 'network', 'tech', 'technological', 'computing', 'virtual',
    'online learning', 'e-learning', 'edtech', 'learning management'
]


# Configuration constants
MAX_CONTENT_LENGTH = 4000  # Maximum content length for OpenAI
REQUEST_TIMEOUT = 10  # Timeout for HTTP requests in seconds
MAX_RETRIES = 2  # Maximum retry attempts for failed requests

def log_success(message):
    """
    Log successful operations to log.txt with timestamp.
    
    Args:
        message (str): Message to log
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        log_entry = f"{timestamp} – {message}\n"
        
        with open('log.txt', 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
        print(f"Logged: {message}")
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}")

def get_openai_client():
    """
    Initialize OpenAI client with API key from environment.
    
    Returns:
        OpenAI: Configured OpenAI client or None if API key not found
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        return None
    
    return OpenAI(api_key=api_key)

def validate_url(url):
    """
    Validate URL format and check if it's accessible.
    
    Args:
        url (str): URL to validate
    
    Returns:
        bool: True if URL is valid and accessible, False otherwise
    """
    try:
        # Parse URL structure
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            print(f"Invalid URL format: {url}")
            return False
        
        # Check if URL is accessible with HEAD request
        response = requests.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if response.status_code >= 400:
            print(f"URL returned status {response.status_code}: {url}")
            return False
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"URL validation failed for {url}: {e}")
        return False


def is_tech_related(title, description="", content=""):
    """
    Check if an article is technology-related based on keywords.
    
    Args:
        title (str): Article title
        description (str): Article description/summary
        content (str): Article content
    
    Returns:
        bool: True if article contains tech keywords, False otherwise
    """
    # Combine all text and convert to lowercase
    full_text = f"{title} {description} {content}".lower()
    
    # Check if any tech keywords are present
    for keyword in TECH_KEYWORDS:
        if keyword.lower() in full_text:
            return True
    
    return False

def fetch_rss_articles_with_retry(feed_url, max_articles=3):
    """
    Fetch articles from RSS feed with retry logic and validation.
    
    Args:
        feed_url (str): RSS feed URL
        max_articles (int): Maximum number of articles to fetch
    
    Returns:
        list: List of article dictionaries, randomly shuffled
    """
    # Validate feed URL first
    if not validate_url(feed_url):
        print(f"Skipping invalid or inaccessible feed: {feed_url}")
        return []
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            print(f"Fetching RSS feed (attempt {attempt + 1}): {feed_url}")
            
            # Parse feed with timeout
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and feed.bozo_exception:
                print(f"RSS parsing warning for {feed_url}: {feed.bozo_exception}")
            
            if not hasattr(feed, 'entries') or len(feed.entries) == 0:
                print(f"No entries found in RSS feed: {feed_url}")
                return []
            
            articles = []
            for entry in feed.entries[:max_articles]:
                # Validate required fields
                title = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                
                if not title or not link:
                    print(f"Skipping article with missing title or link")
                    continue
                
                article = {
                    'title': title,
                    'link': link,
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', '')
                }
                articles.append(article)
            
            # Randomize article order as requested
            if articles:
                random.shuffle(articles)
                print(f"Successfully fetched and shuffled {len(articles)} articles")
            
            return articles
            
        except requests.exceptions.Timeout:
            print(f"Timeout fetching RSS feed (attempt {attempt + 1}): {feed_url}")
        except requests.exceptions.RequestException as e:
            print(f"Request error fetching RSS feed (attempt {attempt + 1}): {feed_url} - {e}")
        except Exception as e:
            print(f"Unexpected error fetching RSS feed (attempt {attempt + 1}): {feed_url} - {e}")
        
        if attempt < MAX_RETRIES:
            time.sleep(2)  # Wait before retry
    
    print(f"Failed to fetch RSS feed after {MAX_RETRIES + 1} attempts: {feed_url}")
    return []

def extract_article_content_safe(article_url):
    """
    Extract full text content from article URL with safety checks.
    
    Args:
        article_url (str): URL of the article
    
    Returns:
        str: Extracted article text or None if extraction fails
    """
    # Validate URL first
    if not validate_url(article_url):
        return None
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            print(f"Extracting content (attempt {attempt + 1}): {article_url}")
            
            # Download the webpage
            downloaded = trafilatura.fetch_url(article_url)
            if not downloaded:
                print(f"Failed to download article content: {article_url}")
                continue
            
            # Extract main text content
            text = trafilatura.extract(downloaded)
            if not text:
                print(f"No content extracted from article: {article_url}")
                continue
            
            # Sanitize and truncate content
            text = text.strip()
            if len(text) > MAX_CONTENT_LENGTH:
                text = text[:MAX_CONTENT_LENGTH] + "..."
                print(f"Content truncated to {MAX_CONTENT_LENGTH} characters")
            
            print(f"Successfully extracted {len(text)} characters of content")
            return text
            
        except requests.exceptions.Timeout:
            print(f"Timeout extracting content (attempt {attempt + 1}): {article_url}")
        except requests.exceptions.RequestException as e:
            print(f"Request error extracting content (attempt {attempt + 1}): {article_url} - {e}")
        except Exception as e:
            print(f"Unexpected error extracting content (attempt {attempt + 1}): {article_url} - {e}")
        
        if attempt < MAX_RETRIES:
            time.sleep(2)  # Wait before retry
    
    print(f"Failed to extract content after {MAX_RETRIES + 1} attempts: {article_url}")
    return None

def sanitize_content_for_ai(content):
    """
    Sanitize content before sending to OpenAI.
    
    Args:
        content (str): Raw article content
    
    Returns:
        str: Sanitized content safe for AI processing
    """
    if not content:
        return ""
    
    # Remove excessive whitespace and normalize
    content = ' '.join(content.split())
    
    # Ensure content is within safe limits
    if len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH] + "..."
    
    # Remove potentially problematic characters
    content = content.encode('utf-8', errors='ignore').decode('utf-8')
    
    return content

def summarize_with_openai_safe(content, max_sentences=4):
    """
    Summarize article content using OpenAI with safety checks.
    
    Args:
        content (str): Article content to summarize
        max_sentences (int): Maximum sentences in summary
    
    Returns:
        str: Summarized content or None if summarization fails
    """
    try:
        client = get_openai_client()
        if not client:
            return None
        
        # Sanitize content
        sanitized_content = sanitize_content_for_ai(content)
        if not sanitized_content:
            print("No valid content to summarize after sanitization")
            return None
        
        print("Generating summary with OpenAI...")
        
        prompt = f"""Please summarize the following higher education news article in {max_sentences} concise, informative sentences. Focus on the key facts, implications for higher education, and any actionable insights. Write in a professional, engaging tone suitable for an education professional's morning briefing.

Article content:
{sanitized_content}"""
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert education journalist who writes concise, insightful summaries of higher education news for busy education professionals."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content
        if summary:
            summary = summary.strip()
            print(f"Generated summary: {len(summary)} characters")
            return summary
        else:
            print("Empty response from OpenAI")
            return None
        
    except Exception as e:
        print(f"Error generating summary with OpenAI: {e}")
        return None

def get_daily_news_insight():
    """
    Fetch and summarize the top higher education news article of the day.
    Enhanced with reliability and safety improvements.
    
    Returns:
        dict: Dictionary containing title, summary, url, and source
              Returns None if no article could be processed
    """
    print("=== Fetching Daily Higher Ed Tech News Insight ===")
    
    # Separate tech-focused and general feeds
    tech_feeds = [feed for feed in RSS_FEEDS if feed.get('tech_focused', False)]
    general_feeds = [feed for feed in RSS_FEEDS if not feed.get('tech_focused', False)]
    
    # First, search for tech articles in general feeds
    print("Searching for tech articles from general feeds...")
    shuffled_general = general_feeds.copy()
    random.shuffle(shuffled_general)
    
    for feed_info in shuffled_general:
        try:
            print(f"Checking {feed_info['name']} for tech articles...")
            
            articles = fetch_rss_articles_with_retry(feed_info['url'], max_articles=5)
            if not articles:
                continue
            
            # Filter for tech-related articles
            tech_articles = []
            for article in articles:
                description = article.get('description', '')
                if is_tech_related(article['title'], description):
                    tech_articles.append(article)
            
            if tech_articles:
                print(f"Found {len(tech_articles)} tech articles in {feed_info['name']}")
                
                # Process the first tech article found
                for article in tech_articles:
                    print(f"Processing tech article: {article['title'][:50]}...")
                    
                    content = extract_article_content_safe(article['link'])
                    if not content:
                        continue
                    
                    summary = summarize_with_openai_safe(content)
                    if not summary:
                        continue
                    
                    log_success(f"Tech: {article['title'][:50]}...")
                    print(f"✅ Successfully processed tech article from {feed_info['name']}")
                    
                    return {
                        'title': article['title'],
                        'summary': summary,
                        'url': article['link'],
                        'source': feed_info['name']
                    }
                    
        except Exception as e:
            print(f"Error processing feed {feed_info['name']}: {e}")
            continue
    
    # If no tech articles found in general feeds, use tech-focused feeds
    print("No tech articles found in general feeds, trying tech-focused feeds...")
    shuffled_tech = tech_feeds.copy()
    random.shuffle(shuffled_tech)
    
    for feed_info in shuffled_tech:
        print(f"\nTrying {feed_info['name']}...")
        
        # Fetch articles from this feed
        articles = fetch_rss_articles_with_retry(feed_info['url'], max_articles=3)
        
        if not articles:
            print(f"No articles found from {feed_info['name']}")
            continue
        
        # Try to process articles (already randomized in fetch function)
        for article in articles:
            print(f"\nProcessing article: {article['title'][:60]}...")
            
            # Extract full content with safety checks
            content = extract_article_content_safe(article['link'])
            
            if not content:
                print("Could not extract content, trying next article...")
                continue
            
            # Generate summary with safety checks
            summary = summarize_with_openai_safe(content)
            
            if not summary:
                print("Could not generate summary, trying next article...")
                continue
            
            # Success! Log and return the processed article
            result = {
                'title': article['title'],
                'summary': summary,
                'url': article['link'],
                'source': feed_info['name'],
                'published': article.get('published', '')
            }
            
            # Log successful article processing
            log_message = f"Sent: {article['title'][:50]}{'...' if len(article['title']) > 50 else ''}"
            log_success(log_message)
            
            print(f"✅ Successfully processed article from {feed_info['name']}")
            return result
    
    print("❌ Could not process any articles from available feeds")
    return None

def get_fallback_news_content():
    """
    Generate fallback content when news fetching fails.
    
    Returns:
        dict: Fallback news content structure
    """
    return {
        'title': 'Daily Campus Insight Temporarily Unavailable',
        'summary': 'We encountered technical difficulties fetching today\'s higher education news. This could be due to RSS feed maintenance or connectivity issues. Your daily campus insights will resume with the next scheduled email.',
        'url': '',
        'source': 'System Message',
        'published': datetime.now().strftime('%Y-%m-%d')
    }

def test_news_fetcher():
    """
    Test function to verify news fetching functionality with improvements.
    """
    print("=== Testing Enhanced News Fetcher ===")
    
    # Test OpenAI connection
    client = get_openai_client()
    if not client:
        print("❌ OpenAI API key not configured")
        return False
    
    print("✅ OpenAI client initialized")
    
    # Test URL validation
    test_url = "https://www.insidehighered.com"
    if validate_url(test_url):
        print("✅ URL validation working")
    else:
        print("❌ URL validation failed")
        return False
    
    # Test news fetching
    news_insight = get_daily_news_insight()
    
    if news_insight and news_insight['source'] != 'System Message':
        print("\n=== News Insight Retrieved ===")
        print(f"Title: {news_insight['title']}")
        print(f"Source: {news_insight['source']}")
        print(f"Summary: {news_insight['summary']}")
        print(f"URL: {news_insight['url']}")
        print("✅ News fetcher test completed successfully")
        return True
    else:
        print("❌ Failed to retrieve authentic news insight")
        return False

if __name__ == "__main__":
    test_news_fetcher()