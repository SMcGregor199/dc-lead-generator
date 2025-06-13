#!/usr/bin/env python3
"""
Multi-Source Institution Matching and Cross-Referencing System
Detects and merges insights when multiple sources reference the same institution
Enhanced confidence scoring through source triangulation
"""

import json
import os
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import re

def normalize_institution_name(name):
    """
    Normalize institution names for better matching.
    
    Args:
        name (str): Institution name
    
    Returns:
        str: Normalized name for matching
    """
    if not name:
        return ""
    
    # Convert to lowercase and remove common suffixes/prefixes
    normalized = name.lower().strip()
    
    # Remove common institutional suffixes
    suffixes_to_remove = [
        ' university', ' college', ' institute', ' academy',
        ' school', ' system', ' campus', ' medical center'
    ]
    
    for suffix in suffixes_to_remove:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
            break
    
    # Remove common prefixes
    prefixes_to_remove = ['the ', 'university of ', 'college of ']
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
            break
    
    # Remove special characters and extra spaces
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def calculate_institution_similarity(name1, name2):
    """
    Calculate similarity score between two institution names.
    
    Args:
        name1 (str): First institution name
        name2 (str): Second institution name
    
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    if not name1 or not name2:
        return 0.0
    
    # Normalize names
    norm1 = normalize_institution_name(name1)
    norm2 = normalize_institution_name(name2)
    
    if norm1 == norm2:
        return 1.0
    
    # Use sequence matcher for similarity
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Boost similarity for common abbreviations
    abbreviations = {
        'mit': 'massachusetts institute technology',
        'ucla': 'university california los angeles',
        'usc': 'university southern california',
        'nyu': 'new york university',
        'fsu': 'florida state university',
        'osu': 'ohio state university'
    }
    
    if norm1 in abbreviations and abbreviations[norm1] in norm2:
        similarity = max(similarity, 0.9)
    elif norm2 in abbreviations and abbreviations[norm2] in norm1:
        similarity = max(similarity, 0.9)
    
    return similarity

def find_matching_institutions(articles_data, jobs_data, similarity_threshold=0.8):
    """
    Find institutions that appear in both articles and job postings.
    
    Args:
        articles_data (list): List of article data
        jobs_data (list): List of job posting data
        similarity_threshold (float): Minimum similarity score for matching
    
    Returns:
        list: List of matched institution data
    """
    matches = []
    
    # Extract institution names from articles
    article_institutions = {}
    for article in articles_data:
        if 'institution' in article and article['institution']:
            inst_name = article['institution']
            if inst_name not in article_institutions:
                article_institutions[inst_name] = []
            article_institutions[inst_name].append(article)
    
    # Extract institution names from jobs
    job_institutions = {}
    for job in jobs_data:
        if 'company' in job and job['company']:
            company_name = job['company']
            if company_name not in job_institutions:
                job_institutions[company_name] = []
            job_institutions[company_name].append(job)
    
    # Find matches between articles and jobs
    for article_inst, article_sources in article_institutions.items():
        for job_inst, job_sources in job_institutions.items():
            similarity = calculate_institution_similarity(article_inst, job_inst)
            
            if similarity >= similarity_threshold:
                # Check date proximity (within 30 days)
                article_dates = []
                job_dates = []
                
                for article in article_sources:
                    if 'date' in article:
                        try:
                            article_dates.append(datetime.fromisoformat(article['date']))
                        except:
                            continue
                
                for job in job_sources:
                    if 'date_scraped' in job:
                        try:
                            job_dates.append(datetime.strptime(job['date_scraped'], '%Y-%m-%d'))
                        except:
                            continue
                
                # Check if any dates are within 30 days of each other
                date_match = False
                if article_dates and job_dates:
                    for art_date in article_dates:
                        for job_date in job_dates:
                            if abs((art_date - job_date).days) <= 30:
                                date_match = True
                                break
                        if date_match:
                            break
                else:
                    # If no dates available, assume recent
                    date_match = True
                
                if date_match:
                    matches.append({
                        'institution': article_inst,
                        'matched_job_institution': job_inst,
                        'similarity_score': similarity,
                        'article_sources': article_sources,
                        'job_sources': job_sources,
                        'match_timestamp': datetime.now().isoformat()
                    })
    
    return matches

def calculate_cross_reference_confidence(match_data):
    """
    Calculate enhanced confidence score based on cross-referenced sources.
    
    Args:
        match_data (dict): Matched institution data
    
    Returns:
        float: Enhanced confidence score
    """
    base_confidence = 0.6  # Base for cross-referenced opportunities
    
    # Boost for multiple article sources
    article_count = len(match_data['article_sources'])
    if article_count >= 3:
        base_confidence += 0.2
    elif article_count >= 2:
        base_confidence += 0.1
    
    # Boost for multiple job sources
    job_count = len(match_data['job_sources'])
    if job_count >= 2:
        base_confidence += 0.1
    
    # Boost for high institution name similarity
    if match_data['similarity_score'] >= 0.95:
        base_confidence += 0.1
    elif match_data['similarity_score'] >= 0.9:
        base_confidence += 0.05
    
    # Boost for transformation-related job titles
    transformation_indicators = [
        'chief information officer', 'cio', 'digital transformation',
        'modernization', 'strategic', 'governance', 'cybersecurity'
    ]
    
    for job in match_data['job_sources']:
        job_title_lower = job.get('title', '').lower()
        if any(indicator in job_title_lower for indicator in transformation_indicators):
            base_confidence += 0.05
            break
    
    return min(0.95, base_confidence)

def merge_cross_referenced_insights(match_data):
    """
    Merge insights from multiple sources into a comprehensive opportunity summary.
    
    Args:
        match_data (dict): Matched institution data
    
    Returns:
        dict: Merged opportunity insights
    """
    institution = match_data['institution']
    article_sources = match_data['article_sources']
    job_sources = match_data['job_sources']
    
    # Combine all source content
    combined_content = []
    all_sources = []
    
    # Add article content
    for article in article_sources:
        if 'summary' in article:
            combined_content.append(f"News: {article['summary']}")
        all_sources.append({
            'title': article.get('title', 'News Article'),
            'url': article.get('url', ''),
            'type': 'article'
        })
    
    # Add job content
    for job in job_sources:
        job_title = job.get('title', 'IT Position')
        if 'summary' in job:
            combined_content.append(f"Job Opening: {job_title} - {job['summary']}")
        all_sources.append({
            'title': f"{job_title} at {job.get('company', institution)}",
            'url': job.get('url', ''),
            'type': 'job_posting'
        })
    
    # Generate enhanced opportunity summary
    opportunity_summary = f"""Cross-referenced opportunity at {institution} identified through multiple sources:

{' '.join(combined_content[:3])}

This institution shows multiple indicators of technology transformation activity including both news coverage and active IT leadership recruitment, suggesting genuine modernization initiatives in progress."""
    
    # Calculate enhanced confidence
    confidence_score = calculate_cross_reference_confidence(match_data)
    
    merged_insight = {
        'institution': institution,
        'opportunity_summary': opportunity_summary,
        'confidence_score': confidence_score,
        'source_types': ['article', 'job_posting'],
        'total_sources': len(all_sources),
        'sources': all_sources,
        'cross_reference_match': True,
        'similarity_score': match_data['similarity_score'],
        'date_identified': datetime.now().strftime('%m/%d/%Y')
    }
    
    return merged_insight

def process_cross_references(articles_data, jobs_data):
    """
    Process cross-references between articles and job postings.
    
    Args:
        articles_data (list): Article data
        jobs_data (list): Job data
    
    Returns:
        list: List of cross-referenced opportunities
    """
    print("Processing cross-references between articles and job postings...")
    
    # Find matching institutions
    matches = find_matching_institutions(articles_data, jobs_data)
    
    if not matches:
        print("No cross-referenced institutions found")
        return []
    
    # Merge insights for each match
    cross_referenced_opportunities = []
    
    for match in matches:
        merged_insight = merge_cross_referenced_insights(match)
        cross_referenced_opportunities.append(merged_insight)
        
        print(f"Cross-referenced: {match['institution']} (confidence: {merged_insight['confidence_score']:.2f})")
    
    print(f"Generated {len(cross_referenced_opportunities)} cross-referenced opportunities")
    return cross_referenced_opportunities

def load_article_data():
    """Load article data from news service or lead database"""
    try:
        # Try to load from existing leads database
        if os.path.exists('higher_ed_leads.json'):
            with open('higher_ed_leads.json', 'r') as f:
                leads_data = json.load(f)
                # Extract article-based sources
                article_data = []
                for lead in leads_data:
                    if not lead.get('is_fallback', False):
                        for source in lead.get('sources', []):
                            article_data.append({
                                'institution': lead.get('institution'),
                                'title': source.get('title'),
                                'url': source.get('url'),
                                'summary': lead.get('opportunity_summary', ''),
                                'date': lead.get('date_identified')
                            })
                return article_data
    except:
        pass
    return []

def load_job_data():
    """Load job data from job service database"""
    try:
        if os.path.exists('higher_ed_jobs.json'):
            with open('higher_ed_jobs.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return []

def main():
    """Main function for cross-reference processing"""
    print("Starting multi-source institution matching...")
    
    # Load data
    articles = load_article_data()
    jobs = load_job_data()
    
    print(f"Loaded {len(articles)} article sources and {len(jobs)} job postings")
    
    # Process cross-references
    cross_referenced = process_cross_references(articles, jobs)
    
    if cross_referenced:
        # Save results
        output_file = 'cross_referenced_opportunities.json'
        with open(output_file, 'w') as f:
            json.dump(cross_referenced, f, indent=2)
        
        print(f"Cross-referenced opportunities saved to {output_file}")
    else:
        print("No cross-referenced opportunities found")

if __name__ == "__main__":
    main()