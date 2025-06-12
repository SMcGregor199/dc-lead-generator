#!/usr/bin/env python3
"""
Higher Education Technology Job Posting Service
Fetches live higher ed tech jobs via SerpAPI with persistent storage
"""

import requests
import random
import time
import os
import json
import hashlib
from openai import OpenAI

# File to store persistent job database
JOBS_DATABASE_FILE = 'higher_ed_jobs.json'

# Default curated job postings (seed data)
DEFAULT_JOB_POSTINGS = [
    {
        'title': 'Chief Information Officer',
        'company': 'University of California, San Diego',
        'summary': 'Lead strategic technology initiatives for 38,000+ students and 9,000 faculty/staff. Oversee enterprise systems, cybersecurity, digital transformation, and academic technology infrastructure.',
        'url': 'https://employment.ucsd.edu/staff-positions',
        'source': 'UC San Diego Careers',
        'job_id': 'ucsd_cio_001'
    },
    {
        'title': 'Associate Vice President for Information Technology',
        'company': 'Northwestern University',
        'summary': 'Direct comprehensive IT strategy and operations for premier research institution. Manage enterprise infrastructure, academic technology services, and digital innovation initiatives.',
        'url': 'https://careers.northwestern.edu/jobs',
        'source': 'Northwestern Careers',
        'job_id': 'northwestern_avp_001'
    },
    {
        'title': 'Director of Information Technology Services',
        'company': 'Massachusetts Institute of Technology',
        'summary': 'Oversee mission-critical IT services including network infrastructure, cloud platforms, and emerging technologies. Collaborate with academic departments to enhance research computing capabilities.',
        'url': 'https://careers.mit.edu/job-search',
        'source': 'MIT Careers',
        'job_id': 'mit_director_001'
    },
    {
        'title': 'VP of Information Technology & CIO',
        'company': 'Duke University',
        'summary': 'Lead digital transformation across campus serving 16,000+ students and 40,000+ faculty/staff. Manage enterprise technology portfolio, cybersecurity strategy, and educational technology innovation.',
        'url': 'https://duke.wd1.myworkdayjobs.com/Staff_Career_Pages',
        'source': 'Duke University Careers',
        'job_id': 'duke_vp_001'
    }
]

def load_jobs_database():
    """
    Load job postings from persistent JSON storage.
    
    Returns:
        list: List of job posting dictionaries
    """
    try:
        if os.path.exists(JOBS_DATABASE_FILE):
            with open(JOBS_DATABASE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Initialize with default seed data
            save_jobs_database(DEFAULT_JOB_POSTINGS)
            return DEFAULT_JOB_POSTINGS.copy()
    except Exception as e:
        print(f"Error loading jobs database: {e}")
        return DEFAULT_JOB_POSTINGS.copy()

def save_jobs_database(jobs_list):
    """
    Save job postings to persistent JSON storage.
    
    Args:
        jobs_list (list): List of job posting dictionaries
    """
    try:
        with open(JOBS_DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(jobs_list, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(jobs_list)} jobs to database")
    except Exception as e:
        print(f"Error saving jobs database: {e}")

def generate_job_id(title, company):
    """
    Generate unique job ID based on title and company.
    
    Args:
        title (str): Job title
        company (str): Company/institution name
    
    Returns:
        str: Unique job identifier
    """
    combined = f"{title.lower().strip()}{company.lower().strip()}"
    return hashlib.md5(combined.encode()).hexdigest()[:12]

def is_duplicate_job(new_job, existing_jobs):
    """
    Check if a job already exists in the database.
    
    Args:
        new_job (dict): New job posting
        existing_jobs (list): List of existing job postings
    
    Returns:
        bool: True if duplicate exists, False otherwise
    """
    new_id = generate_job_id(new_job['title'], new_job['company'])
    
    for job in existing_jobs:
        existing_id = job.get('job_id', generate_job_id(job['title'], job['company']))
        if new_id == existing_id:
            return True
    
    return False

def get_openai_summary(job_description, max_sentences=3):
    """
    Summarize job description using OpenAI GPT-4o.
    
    Args:
        job_description (str): Full job description text
        max_sentences (int): Maximum sentences in summary
    
    Returns:
        str: Summarized job description
    """
    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return job_description[:200] + "..." if len(job_description) > 200 else job_description
        
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Summarize this higher education technology job posting in {max_sentences} concise, professional sentences. Focus on key responsibilities, qualifications, and institutional context.

Job description:
{job_description[:2000]}"""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at summarizing higher education technology job postings for busy professionals."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content
        return summary.strip() if summary else job_description[:200] + "..."
        
    except Exception as e:
        print(f"OpenAI summarization failed: {e}")
        return job_description[:200] + "..." if len(job_description) > 200 else job_description

def fetch_jobs_via_serpapi():
    """
    Fetch higher education technology jobs using SerpAPI.
    
    Returns:
        list: List of new job postings
    """
    try:
        api_key = os.environ.get('SERPAPI_KEY')
        if not api_key:
            print("SERPAPI_KEY not found in environment")
            return []
        
        # SerpAPI endpoint for Google Jobs
        url = "https://serpapi.com/search.json"
        
        # Search queries for higher ed tech jobs
        queries = [
            'information technology university',
            'IT director college',
            'academic technology manager university',
            'CIO chief information officer university',
            'technology coordinator college'
        ]
        
        # Randomly select a query for this search
        query = random.choice(queries)
        
        params = {
            'engine': 'google_jobs',
            'q': query,
            'location': 'United States',
            'api_key': api_key,
            'num': 10
        }
        
        print("Fetching jobs from SerpAPI...")
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'jobs_results' not in data:
            print("No jobs_results in SerpAPI response")
            return []
        
        new_jobs = []
        existing_jobs = load_jobs_database()
        
        for job_data in data['jobs_results']:
            try:
                # Extract job details
                title = job_data.get('title', '').strip()
                company = job_data.get('company_name', '').strip()
                description = job_data.get('description', '').strip()
                job_url = job_data.get('share_link', '') or job_data.get('related_links', [{}])[0].get('link', '')
                
                # Validate required fields
                if not title or not company:
                    continue
                
                # Check if it's a higher education institution
                company_lower = company.lower()
                if not any(term in company_lower for term in ['university', 'college', 'institute', 'school']):
                    continue
                
                # Check if it's a technology-related position
                title_desc = f"{title} {description}".lower()
                tech_keywords = ['technology', 'information', 'IT', 'tech', 'digital', 'computer', 'software', 'network', 'system', 'data']
                if not any(keyword in title_desc for keyword in tech_keywords):
                    continue
                
                # Create job posting object
                new_job = {
                    'title': title,
                    'company': company,
                    'summary': get_openai_summary(description),
                    'url': job_url,
                    'source': 'SerpAPI Google Jobs',
                    'job_id': generate_job_id(title, company)
                }
                
                # Check for duplicates
                if not is_duplicate_job(new_job, existing_jobs):
                    new_jobs.append(new_job)
                    print(f"Found new job: {title} at {company}")
                
            except Exception as e:
                print(f"Error processing job result: {e}")
                continue
        
        # Add new jobs to database
        if new_jobs:
            updated_jobs = existing_jobs + new_jobs
            save_jobs_database(updated_jobs)
            print(f"Added {len(new_jobs)} new jobs to database")
        else:
            print("No new jobs found via SerpAPI")
        
        return new_jobs
        
    except Exception as e:
        print(f"Error fetching jobs via SerpAPI: {e}")
        return []

def get_featured_job_posting():
    """
    Get a featured higher education technology job posting.
    First tries SerpAPI, then falls back to curated database.
    
    Returns:
        dict: Job posting data
    """
    print("=== Fetching Featured Higher Ed Tech Job ===")
    
    # Try to fetch new jobs via SerpAPI
    new_jobs = fetch_jobs_via_serpapi()
    
    # Load current job database
    all_jobs = load_jobs_database()
    
    # If we found new jobs, randomly select from them
    if new_jobs:
        selected_job = random.choice(new_jobs)
        print(f"Selected new job: {selected_job['title']} at {selected_job['company']}")
        return selected_job
    
    # Otherwise, select from existing database
    if all_jobs:
        selected_job = random.choice(all_jobs)
        print(f"Selected from database: {selected_job['title']} at {selected_job['company']}")
        return selected_job
    
    # Fallback to default if database is empty
    fallback_job = random.choice(DEFAULT_JOB_POSTINGS)
    print(f"Using fallback: {fallback_job['title']} at {fallback_job['company']}")
    return fallback_job

def get_database_stats():
    """
    Get statistics about the jobs database.
    
    Returns:
        dict: Database statistics
    """
    jobs = load_jobs_database()
    sources = {}
    
    for job in jobs:
        source = job.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    
    return {
        'total_jobs': len(jobs),
        'sources': sources,
        'database_file': JOBS_DATABASE_FILE
    }

def test_job_service():
    """
    Test the job fetching functionality and show database stats.
    """
    print("Testing higher education job service...")
    
    # Show database stats
    stats = get_database_stats()
    print(f"\nDatabase Stats:")
    print(f"Total jobs: {stats['total_jobs']}")
    print("Sources:")
    for source, count in stats['sources'].items():
        print(f"  {source}: {count}")
    
    # Test job fetching
    job = get_featured_job_posting()
    
    print(f"\nSelected Job:")
    print(f"Title: {job['title']}")
    print(f"Institution: {job['company']}")
    print(f"Summary: {job['summary']}")
    print(f"Source: {job['source']}")
    print(f"URL: {job['url']}")

if __name__ == "__main__":
    test_job_service()