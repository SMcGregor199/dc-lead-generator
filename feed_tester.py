#!/usr/bin/env python3
"""
RSS Feed Testing and Validation Script
Tests all RSS feeds for accessibility and content validity
"""

import requests
import feedparser
import sys
from news_service import RSS_FEEDS

def test_rss_feed(feed_info, timeout=10):
    """
    Test a single RSS feed for accessibility and content.
    
    Args:
        feed_info (dict): Feed information with name and url
        timeout (int): Request timeout in seconds
    
    Returns:
        dict: Test results
    """
    result = {
        'name': feed_info['name'],
        'url': feed_info['url'],
        'status_code': None,
        'accessible': False,
        'valid_entries': 0,
        'error': None
    }
    
    try:
        # Test HTTP accessibility
        print(f"Testing {feed_info['name']}...")
        response = requests.get(feed_info['url'], timeout=timeout)
        result['status_code'] = response.status_code
        
        if response.status_code == 200:
            result['accessible'] = True
            
            # Test feed parsing
            feed = feedparser.parse(feed_info['url'])
            
            if hasattr(feed, 'entries') and len(feed.entries) > 0:
                # Count valid entries (with title and link)
                valid_count = 0
                for entry in feed.entries:
                    if entry.get('title') and entry.get('link'):
                        valid_count += 1
                
                result['valid_entries'] = valid_count
                print(f"  ✅ Status: {response.status_code}, Valid entries: {valid_count}")
            else:
                print(f"  ⚠️  Status: {response.status_code}, No entries found")
        else:
            print(f"  ❌ Status: {response.status_code}")
            
    except requests.exceptions.Timeout:
        result['error'] = 'Timeout'
        print(f"  ❌ Timeout error")
    except requests.exceptions.ConnectionError:
        result['error'] = 'Connection Error'
        print(f"  ❌ Connection error")
    except requests.exceptions.RequestException as e:
        result['error'] = f'Request Error: {str(e)}'
        print(f"  ❌ Request error: {e}")
    except Exception as e:
        result['error'] = f'Unexpected Error: {str(e)}'
        print(f"  ❌ Unexpected error: {e}")
    
    return result

def test_all_feeds():
    """
    Test all RSS feeds and provide summary report.
    """
    print("=== RSS Feed Testing Report ===\n")
    
    results = []
    working_feeds = 0
    failed_feeds = 0
    
    for feed_info in RSS_FEEDS:
        result = test_rss_feed(feed_info)
        results.append(result)
        
        if result['accessible'] and result['valid_entries'] > 0:
            working_feeds += 1
        else:
            failed_feeds += 1
    
    # Print detailed summary
    print(f"\n=== Summary Report ===")
    print(f"Total feeds tested: {len(RSS_FEEDS)}")
    print(f"Working feeds: {working_feeds}")
    print(f"Failed feeds: {failed_feeds}")
    
    if failed_feeds > 0:
        print(f"\n=== Failed Feeds Details ===")
        for result in results:
            if not result['accessible'] or result['valid_entries'] == 0:
                print(f"❌ {result['name']}")
                print(f"   URL: {result['url']}")
                print(f"   Status: {result['status_code']}")
                print(f"   Error: {result['error'] or 'No valid entries found'}")
                print()
    
    print(f"\n=== Working Feeds ===")
    for result in results:
        if result['accessible'] and result['valid_entries'] > 0:
            print(f"✅ {result['name']} - {result['valid_entries']} entries")
    
    return results

if __name__ == "__main__":
    test_all_feeds()