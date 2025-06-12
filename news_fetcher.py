#!/usr/bin/env python3
"""
News Fetcher Module for Higher Education News
Fetches and summarizes news articles from Higher Ed RSS feeds
"""

import feedparser
import requests
import trafilatura
import os
import json
from openai import OpenAI

# Higher Ed news RSS feeds
RSS_FEEDS = [
    {
        'name': 'Inside Higher Ed',
        'url': 'https://www.insidehighered.com/rss.xml',
        'description': 'Leading source for higher education news'
    },
    {
        'name': 'EdTech Magazine Higher Ed',
        'url': 'https://edtechmagazine.com/higher/rss.xml',
        'description': 'Technology in higher education'
    },
    {
        'name': 'Chronicle of Higher Education',
        'url': 'https://www.chronicle.com/section/news/10/rss',
        'description': 'Academic news and commentary'
    }
]

def get_openai_client():
    """
    Initialize OpenAI client with API key from environment.
    
    Returns:
        OpenAI: Configured OpenAI client or None if API key not found
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        return None
    
    return OpenAI(api_key=api_key)

def fetch_rss_articles(feed_url, max_articles=5):
    """
    Fetch articles from RSS feed.
    
    Args:
        feed_url (str): RSS feed URL
        max_articles (int): Maximum number of articles to fetch
    
    Returns:
        list: List of article dictionaries with title, link, published date
    """
    try:
        print(f"Fetching RSS feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        if feed.bozo:
            print(f"Warning: RSS feed may have parsing issues: {feed_url}")
        
        articles = []
        for entry in feed.entries[:max_articles]:
            article = {
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': entry.get('summary', '')
            }
            articles.append(article)
        
        print(f"Successfully fetched {len(articles)} articles")
        return articles
        
    except Exception as e:
        print(f"Error fetching RSS feed {feed_url}: {e}")
        return []

def extract_article_content(article_url):
    """
    Extract full text content from article URL.
    
    Args:
        article_url (str): URL of the article
    
    Returns:
        str: Extracted article text or None if extraction fails
    """
    try:
        print(f"Extracting content from: {article_url}")
        
        # Download the webpage
        downloaded = trafilatura.fetch_url(article_url)
        if not downloaded:
            print("Failed to download article content")
            return None
        
        # Extract main text content
        text = trafilatura.extract(downloaded)
        if text:
            print(f"Successfully extracted {len(text)} characters of content")
            return text
        else:
            print("No content extracted from article")
            return None
            
    except Exception as e:
        print(f"Error extracting article content: {e}")
        return None

def summarize_with_openai(content, max_sentences=4):
    """
    Summarize article content using OpenAI GPT.
    
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
        
        print("Generating summary with OpenAI...")
        
        prompt = f"""Please summarize the following higher education news article in {max_sentences} concise, informative sentences. Focus on the key facts, implications for higher education, and any actionable insights. Write in a professional, engaging tone suitable for an education professional's morning briefing.

Article content:
{content[:4000]}"""  # Limit content to avoid token limits
        
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
    
    Returns:
        dict: Dictionary containing title, summary, url, and source
              Returns None if no article could be processed
    """
    print("=== Fetching Daily Higher Ed News Insight ===")
    
    # Try each RSS feed until we successfully get and process an article
    for feed_info in RSS_FEEDS:
        print(f"\nTrying {feed_info['name']}...")
        
        # Fetch articles from this feed
        articles = fetch_rss_articles(feed_info['url'], max_articles=3)
        
        if not articles:
            print(f"No articles found from {feed_info['name']}")
            continue
        
        # Try to process the first few articles until one works
        for article in articles:
            print(f"\nProcessing article: {article['title'][:60]}...")
            
            # Extract full content
            content = extract_article_content(article['link'])
            
            if not content:
                print("Could not extract content, trying next article...")
                continue
            
            # Generate summary
            summary = summarize_with_openai(content)
            
            if not summary:
                print("Could not generate summary, trying next article...")
                continue
            
            # Success! Return the processed article
            result = {
                'title': article['title'],
                'summary': summary,
                'url': article['link'],
                'source': feed_info['name'],
                'published': article.get('published', '')
            }
            
            print(f"✅ Successfully processed article from {feed_info['name']}")
            return result
    
    print("❌ Could not process any articles from available feeds")
    return None

def test_news_fetcher():
    """
    Test function to verify news fetching functionality.
    """
    print("=== Testing News Fetcher ===")
    
    # Test OpenAI connection
    client = get_openai_client()
    if not client:
        print("❌ OpenAI API key not configured")
        return False
    
    print("✅ OpenAI client initialized")
    
    # Test news fetching
    news_insight = get_daily_news_insight()
    
    if news_insight:
        print("\n=== News Insight Retrieved ===")
        print(f"Title: {news_insight['title']}")
        print(f"Source: {news_insight['source']}")
        print(f"Summary: {news_insight['summary']}")
        print(f"URL: {news_insight['url']}")
        return True
    else:
        print("❌ Failed to retrieve news insight")
        return False

if __name__ == "__main__":
    test_news_fetcher()