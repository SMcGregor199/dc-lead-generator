#!/usr/bin/env python3
"""
Test Source Intake Upgrades
Test the automated job refresh, RSS health monitoring, and cross-referencing system
"""

import os
import sys
sys.path.append('.')
from job_service import refresh_jobs_database, scrape_fresh_higher_ed_jobs
from rss_health_monitor import run_health_monitoring
from source_cross_reference import process_cross_references, load_article_data, load_job_data
from lead_generation_service import *

def test_job_refresh():
    """Test automated job database refresh"""
    print("=== Testing Automated Job Refresh ===")
    
    try:
        # Test fresh job scraping
        print("Testing job scraping...")
        fresh_jobs = scrape_fresh_higher_ed_jobs()
        
        if fresh_jobs:
            print(f"Successfully scraped {len(fresh_jobs)} fresh jobs")
            for job in fresh_jobs[:3]:
                print(f"  - {job['title']} at {job['company']} (confidence: {job['confidence_score']:.2f})")
        else:
            print("No fresh jobs found (this may be expected if SerpAPI key not configured)")
        
        # Test database refresh
        print("Testing database refresh...")
        success = refresh_jobs_database()
        
        if success:
            print("Job database refresh completed successfully")
        else:
            print("Job database refresh failed")
            
        return success
        
    except Exception as e:
        print(f"Job refresh test failed: {e}")
        return False

def test_rss_health_monitoring():
    """Test RSS feed health monitoring system"""
    print("\n=== Testing RSS Health Monitoring ===")
    
    try:
        monitoring_results = run_health_monitoring()
        
        if monitoring_results:
            current_results = monitoring_results['current_results']
            persistent_failures = monitoring_results['persistent_failures']
            
            print(f"Health monitoring completed:")
            print(f"  - {current_results['healthy_feeds']}/{current_results['total_feeds']} feeds healthy")
            print(f"  - {len(persistent_failures)} persistent failures detected")
            
            if persistent_failures:
                print("Persistent failures:")
                for failure in persistent_failures:
                    print(f"  - {failure['name']}: {failure['current_status']}")
            
            return True
        else:
            print("RSS health monitoring failed")
            return False
            
    except Exception as e:
        print(f"RSS health monitoring test failed: {e}")
        return False

def test_cross_referencing():
    """Test multi-source institution matching"""
    print("\n=== Testing Cross-Referencing System ===")
    
    try:
        # Load data
        articles = load_article_data()
        jobs = load_job_data()
        
        print(f"Loaded {len(articles)} article sources and {len(jobs)} job postings")
        
        if articles and jobs:
            # Process cross-references
            cross_referenced = process_cross_references(articles, jobs)
            
            print(f"Generated {len(cross_referenced)} cross-referenced opportunities")
            
            for opportunity in cross_referenced[:2]:
                print(f"  - {opportunity['institution']} (confidence: {opportunity['confidence_score']:.2f})")
                print(f"    Sources: {opportunity['total_sources']} ({', '.join(opportunity['source_types'])})")
            
            return len(cross_referenced) > 0
        else:
            print("Insufficient data for cross-referencing test")
            return False
            
    except Exception as e:
        print(f"Cross-referencing test failed: {e}")
        return False

def test_source_confidence_scoring():
    """Test the new source confidence scoring system"""
    print("\n=== Testing Source Confidence Scoring ===")
    
    try:
        from job_service import calculate_job_confidence_score, SOURCE_CONFIDENCE_WEIGHTS
        
        print("Source confidence weights:")
        for source_type, weight in SOURCE_CONFIDENCE_WEIGHTS.items():
            print(f"  - {source_type}: {weight}")
        
        # Test job confidence calculation
        test_cases = [
            ("Chief Information Officer", "Lead strategic digital transformation initiatives for 30,000+ students. Oversee enterprise systems, cybersecurity, cloud migration, and data governance.", "Harvard University"),
            ("IT Support Specialist", "Provide basic technical support for desktop computers.", "Local College"),
            ("VP of Technology", "Short job description.", "MIT")
        ]
        
        print("\nJob confidence scoring tests:")
        for title, description, institution in test_cases:
            confidence = calculate_job_confidence_score(title, description, institution)
            print(f"  - '{title}': {confidence:.2f}")
        
        return True
        
    except Exception as e:
        print(f"Source confidence scoring test failed: {e}")
        return False

def create_test_lead_with_upgrades():
    """Create a test lead using the upgraded systems"""
    print("\n=== Testing Enhanced Lead Generation ===")
    
    try:
        # Create a test lead that showcases the upgraded features
        test_sources = [
            {
                "title": "University Announces $50M Digital Transformation Initiative",
                "url": "https://example.edu/press-release",
                "summary": "Major research university launching comprehensive ERP modernization with cloud migration and cybersecurity enhancements.",
                "confidence_weight": 0.8  # edu_press_release weight
            },
            {
                "title": "CIO Position Open: Lead Digital Innovation",
                "url": "https://jobs.example.edu/cio",
                "summary": "Seeking Chief Information Officer to oversee strategic technology initiatives and enterprise systems modernization.",
                "confidence_weight": 0.6  # job_posting_detailed weight
            }
        ]
        
        # Calculate enhanced confidence based on multiple source types
        total_confidence_weight = sum(source['confidence_weight'] for source in test_sources)
        average_confidence = total_confidence_weight / len(test_sources)
        
        # Create enhanced lead
        enhanced_lead = LeadOpportunity(
            institution="University of Innovation",
            opportunity_summary="Cross-referenced opportunity combining press release announcing $50M digital transformation with concurrent CIO recruitment. Multiple indicators suggest active ERP modernization, cloud migration, and cybersecurity enhancement projects in progress.",
            engagement_tier="Medium",
            potential_contacts=[
                {"name": "Dr. Sarah Johnson", "title": "Interim CIO", "email": "", "source": "Press release"},
                {"name": "", "title": "Chief Information Officer (Open Position)", "email": "", "source": "Job posting"}
            ],
            sources=test_sources,
            date_identified=datetime.now().strftime("%m/%d/%Y"),
            confidence_score=average_confidence,
            lead_type="ERP",
            notes=f"Enhanced lead generated using upgraded source intake system. Confidence based on multi-source validation ({len(test_sources)} sources, avg weight: {average_confidence:.2f})",
            lead_id=generate_lead_id("University of Innovation", "ERP"),
            is_fallback=False
        )
        
        print(f"Created enhanced lead:")
        print(f"  - Institution: {enhanced_lead.institution}")
        print(f"  - Confidence: {enhanced_lead.confidence_score:.2f}")
        print(f"  - Sources: {len(enhanced_lead.sources)}")
        print(f"  - Contacts: {len(enhanced_lead.potential_contacts)}")
        
        # Send test email
        success = send_lead_email(enhanced_lead)
        
        if success:
            print("Enhanced lead email sent successfully")
        else:
            print("Failed to send enhanced lead email")
            
        return success
        
    except Exception as e:
        print(f"Enhanced lead generation test failed: {e}")
        return False

def main():
    """Run comprehensive testing of all source intake upgrades"""
    print("Testing Source Intake & Cross-Referencing Upgrades")
    print("=" * 60)
    
    results = {
        'job_refresh': test_job_refresh(),
        'rss_monitoring': test_rss_health_monitoring(),
        'cross_referencing': test_cross_referencing(),
        'confidence_scoring': test_source_confidence_scoring(),
        'enhanced_lead': create_test_lead_with_upgrades()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "PASS" if passed_test else "FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All source intake upgrades are working correctly!")
    else:
        print("Some upgrades need attention.")

if __name__ == "__main__":
    main()