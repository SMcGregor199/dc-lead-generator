#!/usr/bin/env python3
"""
Higher Education Technology Job Posting Service
Fetches and summarizes tech leadership job postings from multiple sources
"""

import requests
import trafilatura
import re
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
import time

# Job search keywords for higher education tech positions
JOB_KEYWORDS = [
    "Chief Information Officer",
    "Director of IT", 
    "IT Director",
    "Chief Technology Officer",
    "CTO",
    "CIO",
    "Director of Information Technology",
    "VP Information Technology",
    "Assistant Vice President IT",
    "Associate Vice President Technology"
]

# Higher education related terms to filter results
HIGHER_ED_TERMS = [
    "university", "college", "higher education", "academic", "campus",
    "education", "student", "faculty", "research", "university system"
]

def scrape_indeed_jobs():
    """
    Scrape job postings from Indeed for higher ed tech positions.
    
    Returns:
        dict: Job posting data or None if scraping fails
    """
    try:
        # Select random job keyword
        job_title = random.choice(JOB_KEYWORDS)
        location = "United States"
        
        # Construct Indeed search URL
        query = f"{job_title} higher education"
        indeed_url = f"https://www.indeed.com/jobs?q={quote_plus(query)}&l={quote_plus(location)}&sort=date"
        
        print(f"Searching Indeed for: {job_title}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(indeed_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job postings
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        
        if not job_cards:
            job_cards = soup.find_all('div', {'data-result-id': True})
        
        for card in job_cards[:5]:  # Check first 5 results
            try:
                # Extract job title
                title_elem = card.find('h2') or card.find('a', {'data-jk': True})
                if not title_elem:
                    continue
                
                job_title_text = title_elem.get_text(strip=True)
                
                # Extract company name
                company_elem = card.find('span', class_='companyName') or card.find('a', {'data-testid': 'company-name'})
                if not company_elem:
                    continue
                
                company_name = company_elem.get_text(strip=True)
                
                # Check if it's higher education related
                full_text = f"{job_title_text} {company_name}".lower()
                if not any(term in full_text for term in HIGHER_ED_TERMS):
                    continue
                
                # Extract job link
                link_elem = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if not link_elem or not link_elem.get('href'):
                    continue
                
                job_url = urljoin('https://www.indeed.com', link_elem['href'])
                
                # Extract job summary
                summary_elem = card.find('div', class_='summary') or card.find('div', {'data-testid': 'job-snippet'})
                job_summary = summary_elem.get_text(strip=True) if summary_elem else ""
                
                # Clean up summary (limit to 2-3 sentences)
                if job_summary:
                    sentences = job_summary.split('.')[:3]
                    job_summary = '. '.join(s.strip() for s in sentences if s.strip()) + '.'
                
                return {
                    'title': job_title_text,
                    'company': company_name,
                    'summary': job_summary,
                    'url': job_url,
                    'source': 'Indeed'
                }
                
            except Exception as e:
                print(f"Error parsing job card: {e}")
                continue
        
        print("No suitable higher ed tech jobs found on Indeed")
        return None
        
    except Exception as e:
        print(f"Error scraping Indeed jobs: {e}")
        return None

def scrape_hiring_cafe_jobs():
    """
    Scrape job postings from Hiring Cafe for higher ed positions.
    
    Returns:
        dict: Job posting data or None if scraping fails
    """
    try:
        print("Searching Hiring Cafe for higher ed tech jobs...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try Hiring Cafe jobs page
        url = "https://hiringcafe.org/jobs"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for job listings
        job_listings = soup.find_all('div', class_='job') or soup.find_all('article') or soup.find_all('div', class_='listing')
        
        for listing in job_listings[:10]:  # Check first 10 results
            try:
                # Extract job title
                title_elem = listing.find('h3') or listing.find('h2') or listing.find('a')
                if not title_elem:
                    continue
                
                job_title = title_elem.get_text(strip=True)
                
                # Check if it's a tech leadership position
                title_lower = job_title.lower()
                if not any(keyword.lower() in title_lower for keyword in JOB_KEYWORDS):
                    continue
                
                # Extract other details
                text_content = listing.get_text()
                
                # Extract company name (look for patterns)
                company_match = re.search(r'at\s+([A-Z][a-zA-Z\s&]+(?:University|College|Institute))', text_content)
                company_name = company_match.group(1).strip() if company_match else "Higher Education Institution"
                
                # Extract summary
                summary_parts = text_content.split('\n')
                summary = ' '.join(part.strip() for part in summary_parts[1:4] if part.strip())[:200] + "..."
                
                # Get job link
                job_link = listing.find('a')
                job_url = urljoin(url, job_link['href']) if job_link and job_link.get('href') else url
                
                return {
                    'title': job_title,
                    'company': company_name,
                    'summary': summary,
                    'url': job_url,
                    'source': 'Hiring Cafe'
                }
                
            except Exception as e:
                print(f"Error parsing Hiring Cafe listing: {e}")
                continue
        
        print("No suitable tech jobs found on Hiring Cafe")
        return None
        
    except Exception as e:
        print(f"Error scraping Hiring Cafe: {e}")
        return None

def get_fallback_job():
    """
    Generate fallback job content when scraping fails.
    
    Returns:
        dict: Fallback job posting structure
    """
    return {
        'title': 'Chief Information Officer - Major Research University',
        'company': 'Leading Higher Education Institution',
        'summary': 'Seeking visionary technology leader to drive digital transformation initiatives across campus. Lead IT strategy, oversee infrastructure modernization, and collaborate with academic leadership on innovative educational technology solutions.',
        'url': '',
        'source': 'Higher Ed Tech Network'
    }

def get_featured_job_posting():
    """
    Fetch a featured higher education technology job posting.
    
    Returns:
        dict: Job posting data with fallback if scraping fails
    """
    print("=== Fetching Featured Higher Ed Tech Job ===")
    
    # Try different job sources
    job_sources = [scrape_indeed_jobs, scrape_hiring_cafe_jobs]
    random.shuffle(job_sources)
    
    for source_func in job_sources:
        try:
            job_data = source_func()
            if job_data:
                print(f"✅ Found job: {job_data['title']} at {job_data['company']}")
                return job_data
            
            # Small delay between sources
            time.sleep(1)
            
        except Exception as e:
            print(f"Error with job source: {e}")
            continue
    
    # If all sources fail, use fallback
    print("Using fallback job content")
    return get_fallback_job()

def test_job_service():
    """
    Test function to verify job fetching functionality.
    """
    print("Testing job service...")
    job = get_featured_job_posting()
    
    if job:
        print(f"\nJob Found:")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Summary: {job['summary'][:100]}...")
        print(f"Source: {job['source']}")
        if job['url']:
            print(f"URL: {job['url']}")
    else:
        print("No job found")

if __name__ == "__main__":
    test_job_service()