#!/usr/bin/env python3
"""
Higher Education Lead Generation System
AI-powered system to identify genuine tech opportunities for Dynamic Campus
"""

import requests
import random
import time
import os
import json
import hashlib
from datetime import datetime, timedelta
import pytz
import feedparser
import trafilatura
from openai import OpenAI
import smtplib
from email.message import EmailMessage
from dataclasses import dataclass
from typing import List, Dict, Optional
import schedule
import argparse

# File to store persistent lead database
LEADS_DATABASE_FILE = 'higher_ed_leads.json'
CLIENTS_DATABASE_FILE = 'dynamic_campus_clients.json'

@dataclass
class LeadOpportunity:
    """Data class for lead opportunities"""
    institution: str
    opportunity_summary: str
    engagement_tier: str  # Small | Medium | Recurring | Full Outsourcing
    suggested_action: str
    sources: List[Dict[str, str]]  # [{"title": "", "url": ""}]
    date_identified: str
    confidence_score: float
    lead_type: str  # ERP | IT Leadership | Cybersecurity | AI/Data | LMS/CRM | Analytics
    notes: str
    lead_id: str

# RSS Feeds for lead generation
HIGHER_ED_FEEDS = [
    {
        'name': 'Inside Higher Ed',
        'url': 'https://www.insidehighered.com/rss.xml',
        'focus': 'general_higher_ed'
    },
    {
        'name': 'EdTech Magazine Higher Ed',
        'url': 'https://edtechmagazine.com/higher/rss.xml',
        'focus': 'tech_specific'
    },
    {
        'name': 'Higher Ed Dive',
        'url': 'https://www.highereddive.com/feeds/',
        'focus': 'general_higher_ed'
    },
    {
        'name': 'The Chronicle of Higher Education',
        'url': 'https://www.chronicle.com/section/news/rss',
        'focus': 'general_higher_ed'
    },
    {
        'name': 'EDUCAUSE Review',
        'url': 'https://er.educause.edu/articles/rss',
        'focus': 'tech_specific'
    }
]

# Tech keywords that indicate potential leads
LEAD_KEYWORDS = {
    'erp': ['ERP', 'enterprise resource planning', 'student information system', 'SIS', 'financial system'],
    'it_leadership': ['CIO', 'CTO', 'CDO', 'chief information officer', 'chief technology officer', 'IT director', 'technology leadership'],
    'cybersecurity': ['cybersecurity', 'data breach', 'security incident', 'ransomware', 'cyber attack', 'FERPA violation'],
    'ai_data': ['artificial intelligence', 'AI governance', 'data analytics', 'machine learning', 'predictive analytics'],
    'lms_crm': ['learning management system', 'LMS', 'customer relationship management', 'CRM', 'student success platform'],
    'analytics': ['institutional research', 'business intelligence', 'dashboard', 'analytics platform', 'data visualization']
}

ENGAGEMENT_TIERS = {
    'Small': 'Single project or consultation (under $50K)',
    'Medium': 'Multi-phase implementation (50K-200K)',
    'Recurring': 'Ongoing advisory or managed services',
    'Full Outsourcing': 'Comprehensive IT transformation (200K+)'
}

def get_openai_client():
    """Initialize OpenAI client"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Warning: OPENAI_API_KEY not found")
        return None
    return OpenAI(api_key=api_key)

def load_leads_database():
    """Load existing leads from database"""
    try:
        if os.path.exists(LEADS_DATABASE_FILE):
            with open(LEADS_DATABASE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading leads database: {e}")
        return []

def save_leads_database(leads_list):
    """Save leads to database"""
    try:
        with open(LEADS_DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(leads_list, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(leads_list)} leads to database")
    except Exception as e:
        print(f"Error saving leads database: {e}")

def load_clients_database():
    """Load current Dynamic Campus clients"""
    try:
        if os.path.exists(CLIENTS_DATABASE_FILE):
            with open(CLIENTS_DATABASE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading clients database: {e}")
        return []

def generate_lead_id(institution, lead_type):
    """Generate unique lead ID"""
    combined = f"{institution.lower().strip()}{lead_type.lower()}{datetime.now().strftime('%Y%m%d')}"
    return hashlib.md5(combined.encode()).hexdigest()[:12]

def is_duplicate_lead(institution, lead_type, existing_leads, days_threshold=180):
    """Check if lead already exists within threshold"""
    cutoff_date = datetime.now() - timedelta(days=days_threshold)
    
    for lead in existing_leads:
        if (lead['institution'].lower() == institution.lower() and 
            lead['lead_type'] == lead_type):
            lead_date = datetime.strptime(lead['date_identified'], '%m/%d/%Y')
            if lead_date > cutoff_date:
                return True
    return False

def is_current_client(institution, clients_list):
    """Check if institution is current Dynamic Campus client"""
    for client in clients_list:
        if client['name'].lower() in institution.lower() or institution.lower() in client['name'].lower():
            return True
    return False

def extract_institutions_from_text(text):
    """Extract higher education institution names from text using AI"""
    client = get_openai_client()
    if not client:
        return []
    
    try:
        prompt = f"""Extract all higher education institution names from this text. Return only institution names, one per line, no additional text.

Text: {text[:2000]}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at identifying higher education institutions. Extract only official institution names."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        institutions = []
        content = response.choices[0].message.content
        if content:
            for line in content.strip().split('\n'):
                if line.strip() and ('university' in line.lower() or 'college' in line.lower()):
                    institutions.append(line.strip())
        
        return institutions[:3]  # Limit to 3 institutions per article
        
    except Exception as e:
        print(f"Error extracting institutions: {e}")
        return []

def analyze_lead_potential(articles_data):
    """Analyze articles to identify potential leads using AI"""
    client = get_openai_client()
    if not client:
        return []
    
    try:
        # Combine article data for analysis
        combined_text = ""
        sources = []
        
        for article in articles_data:
            combined_text += f"Title: {article['title']}\nSummary: {article['summary']}\nSource: {article['source']}\n\n"
            sources.append({"title": article['title'], "url": article['url']})
        
        if len(sources) < 3:
            print("Insufficient sources for triangulated lead analysis")
            return []
        
        prompt = f"""Analyze these higher education articles to identify genuine business opportunities for a digital transformation consultancy. 

Focus on these opportunity types:
- ERP modernization or system transitions
- IT leadership changes (new CIOs, CTOs, digital officers)
- Cybersecurity incidents or policy changes
- AI/data governance initiatives
- LMS/CRM implementations or upgrades
- Analytics or institutional research transformations

For each potential lead, provide:
1. Institution name
2. Opportunity type
3. Brief description (2-3 sentences)
4. Engagement tier (Small/Medium/Recurring/Full Outsourcing)
5. Confidence score (0.1-1.0)

Only identify leads with strong evidence and clear business relevance.

Articles:
{combined_text[:4000]}

Respond in JSON format:
{{
    "leads": [
        {{
            "institution": "Institution Name",
            "lead_type": "ERP|IT Leadership|Cybersecurity|AI/Data|LMS/CRM|Analytics",
            "opportunity_summary": "Brief description",
            "engagement_tier": "Small|Medium|Recurring|Full Outsourcing",
            "confidence_score": 0.8
        }}
    ]
}}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert business development analyst specializing in higher education technology opportunities."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        if not content:
            return []
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            print("Error parsing AI response as JSON")
            return []
        
        # Process and enhance leads
        processed_leads = []
        for lead_data in result.get('leads', []):
            if lead_data['confidence_score'] >= 0.6:  # Minimum confidence threshold
                
                # Generate suggested action using AI
                action_prompt = f"""For this higher education technology opportunity, suggest a specific strategic action for Dynamic Campus (a digital transformation consultancy):

Institution: {lead_data['institution']}
Opportunity: {lead_data['opportunity_summary']}
Type: {lead_data['lead_type']}
Tier: {lead_data['engagement_tier']}

Provide a 1-2 sentence strategic recommendation."""

                action_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": action_prompt}],
                    max_tokens=100,
                    temperature=0.4
                )
                
                suggested_action = action_response.choices[0].message.content.strip()
                
                lead = LeadOpportunity(
                    institution=lead_data['institution'],
                    opportunity_summary=lead_data['opportunity_summary'],
                    engagement_tier=lead_data['engagement_tier'],
                    suggested_action=suggested_action,
                    sources=sources,
                    date_identified=datetime.now().strftime('%m/%d/%Y'),
                    confidence_score=lead_data['confidence_score'],
                    lead_type=lead_data['lead_type'],
                    notes=f"Triangulated from {len(sources)} sources. Confidence: {lead_data['confidence_score']:.2f}",
                    lead_id=generate_lead_id(lead_data['institution'], lead_data['lead_type'])
                )
                
                processed_leads.append(lead)
        
        return processed_leads
        
    except Exception as e:
        print(f"Error analyzing lead potential: {e}")
        return []

def fetch_articles_for_lead_analysis():
    """Fetch articles from multiple sources for lead analysis"""
    print("=== Fetching Articles for Lead Analysis ===")
    
    all_articles = []
    
    for feed in HIGHER_ED_FEEDS:
        try:
            print(f"Fetching from {feed['name']}...")
            
            # Fetch RSS feed
            response = requests.get(feed['url'], timeout=10)
            response.raise_for_status()
            
            parsed_feed = feedparser.parse(response.content)
            
            if not parsed_feed.entries:
                print(f"No entries found in {feed['name']}")
                continue
            
            # Get recent articles (last 7 days)
            recent_articles = []
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for entry in parsed_feed.entries[:10]:  # Check last 10 articles
                try:
                    # Parse publication date
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    else:
                        continue  # Skip if no date
                    
                    if pub_date > cutoff_date:
                        recent_articles.append(entry)
                
                except Exception as e:
                    print(f"Error processing entry date: {e}")
                    continue
            
            # Process recent articles
            for entry in recent_articles[:3]:  # Limit per feed
                try:
                    title = entry.title
                    url = entry.link
                    
                    # Extract full content
                    downloaded = trafilatura.fetch_url(url)
                    if downloaded:
                        content = trafilatura.extract(downloaded)
                        if content and len(content) > 500:  # Minimum content length
                            
                            # Check for tech relevance
                            content_lower = f"{title} {content}".lower()
                            tech_relevant = any(
                                any(keyword.lower() in content_lower for keyword in keywords)
                                for keywords in LEAD_KEYWORDS.values()
                            )
                            
                            if tech_relevant or feed['focus'] == 'tech_specific':
                                article_data = {
                                    'title': title,
                                    'url': url,
                                    'summary': content[:1000],  # First 1000 chars
                                    'source': feed['name'],
                                    'focus': feed['focus']
                                }
                                all_articles.append(article_data)
                                print(f"Added tech-relevant article: {title[:60]}...")
                
                except Exception as e:
                    print(f"Error processing article: {e}")
                    continue
        
        except Exception as e:
            print(f"Error fetching from {feed['name']}: {e}")
            continue
    
    print(f"Collected {len(all_articles)} tech-relevant articles for analysis")
    return all_articles

def identify_new_leads():
    """Main function to identify new leads"""
    print("=== Higher Ed Lead Generation Analysis ===")
    
    # Load existing data
    existing_leads = load_leads_database()
    current_clients = load_clients_database()
    
    # Fetch and analyze articles
    articles = fetch_articles_for_lead_analysis()
    
    if len(articles) < 3:
        print("Insufficient articles for triangulated analysis")
        return None
    
    # Analyze for lead potential
    potential_leads = analyze_lead_potential(articles)
    
    if not potential_leads:
        print("No qualified leads identified")
        return None
    
    # Filter and validate leads
    qualified_leads = []
    
    for lead in potential_leads:
        # Check if already a client
        if is_current_client(lead.institution, current_clients):
            print(f"Skipping {lead.institution} - current client")
            continue
        
        # Check for recent duplicates
        if is_duplicate_lead(lead.institution, lead.lead_type, existing_leads):
            print(f"Skipping {lead.institution} - recent duplicate")
            continue
        
        qualified_leads.append(lead)
    
    if not qualified_leads:
        print("No new qualified leads after filtering")
        return None
    
    # Select highest confidence lead
    best_lead = max(qualified_leads, key=lambda x: x.confidence_score)
    
    # Add to database
    lead_dict = {
        'institution': best_lead.institution,
        'opportunity_summary': best_lead.opportunity_summary,
        'engagement_tier': best_lead.engagement_tier,
        'suggested_action': best_lead.suggested_action,
        'sources': best_lead.sources,
        'date_identified': best_lead.date_identified,
        'confidence_score': best_lead.confidence_score,
        'lead_type': best_lead.lead_type,
        'notes': best_lead.notes,
        'lead_id': best_lead.lead_id
    }
    
    existing_leads.append(lead_dict)
    save_leads_database(existing_leads)
    
    print(f"Identified new lead: {best_lead.institution} - {best_lead.lead_type}")
    return best_lead

def create_lead_email(lead):
    """Create formatted lead email"""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    
    sources_text = ""
    for i, source in enumerate(lead.sources[:3], 1):
        sources_text += f"- [{source['title'][:60]}...]({source['url']})\n"
    
    subject = f"🧠 New Lead Identified: {lead.institution} | {lead.lead_type} | {lead.engagement_tier}"
    
    body = f"""**🎓 Institution:** {lead.institution}

**🔍 Opportunity Summary:**
{lead.opportunity_summary}

**🏷️ Engagement Tier:** {lead.engagement_tier}
*{ENGAGEMENT_TIERS.get(lead.engagement_tier, 'Custom engagement')}*

**💡 Suggested Action:**
{lead.suggested_action}

**🔗 Sources:**
{sources_text}

**📅 Date Identified:** {lead.date_identified}
**📌 Notes:**
{lead.notes}

---
Generated by Higher Ed Lead Generation System
Processed at: {current_date}
Lead ID: {lead.lead_id}
"""
    
    return subject, body

def send_lead_email(lead):
    """Send lead email to team"""
    try:
        # Load credentials
        gmail_address = os.environ.get('GMAIL_ADDRESS')
        app_password = os.environ.get('GMAIL_APP_PASSWORD')
        
        if not gmail_address or not app_password:
            print("Gmail credentials not found")
            return False
        
        # Create email
        subject, body = create_lead_email(lead)
        
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = gmail_address
        msg['To'] = 'shayne.mcgregor@dynamiccampus.com'
        msg['Cc'] = 'smcgregor@maryu.marywood.edu, jasmine.n.olivier@gmail.com'
        msg.set_content(body)
        
        # Send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_address, app_password)
            server.send_message(msg)
        
        print(f"✅ Lead email sent: {lead.institution}")
        return True
        
    except Exception as e:
        print(f"Error sending lead email: {e}")
        return False

def test_lead_generation():
    """Test the lead generation system"""
    print("Testing Higher Ed Lead Generation System...")
    
    lead = identify_new_leads()
    
    if lead:
        print(f"\nGenerated Lead:")
        print(f"Institution: {lead.institution}")
        print(f"Type: {lead.lead_type}")
        print(f"Tier: {lead.engagement_tier}")
        print(f"Confidence: {lead.confidence_score:.2f}")
        print(f"Summary: {lead.opportunity_summary}")
        
        # Show email preview
        subject, body = create_lead_email(lead)
        print(f"\nEmail Preview:")
        print(f"Subject: {subject}")
        print(f"Body: {body[:300]}...")
        
        return lead
    else:
        print("No leads identified in current cycle")
        return None

def run_daily_lead_generation():
    """Run daily lead generation at 7 AM"""
    print("=== Daily Lead Generation Execution ===")
    
    # Load credentials
    gmail_address = os.environ.get('GMAIL_ADDRESS')
    app_password = os.environ.get('GMAIL_APP_PASSWORD')
    
    if not gmail_address or not app_password:
        print("❌ Gmail credentials not found")
        return
    
    print(f"✅ Credentials loaded for: {gmail_address}")
    
    # Generate lead
    lead = identify_new_leads()
    
    if lead:
        # Send lead email
        success = send_lead_email(lead)
        if success:
            print("🎉 Daily lead email sent successfully!")
        else:
            print("❌ Failed to send lead email")
    else:
        print("No qualified leads found today")

def run_scheduler():
    """Run the lead generation scheduler"""
    print("=== Higher Ed Lead Generation Scheduler ===")
    
    # Test credentials first
    gmail_address = os.environ.get('GMAIL_ADDRESS')
    if not gmail_address:
        print("❌ Gmail credentials not configured")
        return
    
    print(f"Service started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Testing credentials...")
    print(f"✅ Credentials validated for: {gmail_address}")
    print("📅 Lead generation scheduled for 7:00 AM Eastern Time daily")
    print("🔄 Scheduler is now running... (Press Ctrl+C to stop)")
    
    # Schedule daily execution
    schedule.every().day.at("07:00").do(run_daily_lead_generation)
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def main():
    """Main function with mode selection"""
    parser = argparse.ArgumentParser(description='Higher Ed Lead Generation System')
    parser.add_argument('--mode', choices=['immediate', 'schedule', 'test'], 
                       default='immediate', help='Execution mode')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        test_lead_generation()
    elif args.mode == 'immediate':
        run_daily_lead_generation()
    elif args.mode == 'schedule':
        run_scheduler()

if __name__ == "__main__":
    main()