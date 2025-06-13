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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import html
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
    engagement_tier: str  # Small | Medium | Recurring | Full Outsourcing | Exploratory
    suggested_action: str
    sources: List[Dict[str, str]]  # [{"title": "", "url": ""}]
    date_identified: str
    confidence_score: float
    lead_type: str  # ERP | IT Leadership | Cybersecurity | AI/Data | LMS/CRM | Analytics | Signal
    notes: str
    lead_id: str
    is_fallback: bool = False  # True for Signal Insights

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
    'Full Outsourcing': 'Comprehensive IT transformation (200K+)',
    'Exploratory': 'Trend to monitor; not immediately actionable'
}

# Configuration for institution confidence threshold
INSTITUTION_CONFIDENCE_THRESHOLD = 0.6

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
        prompt = f"""Extract all higher education institution names from this text. Return only official institution names that are specifically mentioned, one per line. Do not include generic references like "universities" or "colleges".

Examples of what to extract:
- "Harvard University" 
- "MIT"
- "University of California, Berkeley"
- "Tulane University"

Do not extract:
- "universities"
- "higher education institutions" 
- "colleges"

Text: {text[:2000]}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at identifying specific higher education institutions. Only extract explicitly named institutions, not generic references."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        institutions = []
        content = response.choices[0].message.content
        if content:
            for line in content.strip().split('\n'):
                line = line.strip()
                # Clean up formatting (remove bullets, dashes, numbers)
                line = line.lstrip('- •*1234567890. ')
                
                if (line and 
                    ('university' in line.lower() or 'college' in line.lower() or 'institute' in line.lower()) and
                    not any(generic in line.lower() for generic in ['universities', 'colleges', 'institutions', 'higher education', 'all ', 'many ', 'some ', 'various'])):
                    institutions.append(line)
        
        return institutions[:5]  # Return up to 5 specific institutions
        
    except Exception as e:
        print(f"Error extracting institutions: {e}")
        return []

def generate_signal_insight(articles_data):
    """Generate a Signal Insight fallback when no specific institutions are identified"""
    client = get_openai_client()
    if not client:
        return None
    
    try:
        # Combine article data for trend analysis
        combined_text = ""
        sources = []
        
        for article in articles_data:
            combined_text += f"Title: {article['title']}\nSummary: {article['summary']}\nSource: {article['source']}\n\n"
            sources.append({"title": article['title'], "url": article['url']})
        
        prompt = f"""Analyze these higher education articles to identify emerging trends or sector-wide issues that could affect multiple institutions, even if no specific universities are named.

Focus on trends like:
- Sector-wide technology adoption patterns
- Regulatory or policy changes affecting higher ed IT
- Emerging cybersecurity threats or best practices
- AI/data governance developments across higher education
- ERP or system modernization trends
- Funding or budget pressures affecting IT investments

Articles:
{combined_text[:3000]}

If you identify a meaningful trend or signal, respond in JSON format:
{{
    "signal_found": true,
    "trend_summary": "2-4 sentence description of the emerging trend or issue",
    "potential_impact": "How this might affect higher education institutions",
    "confidence_score": 0.5
}}

If no clear trend emerges, respond:
{{
    "signal_found": false,
    "reason": "Brief explanation"
}}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a higher education technology trend analyst. Identify sector-wide patterns and emerging issues."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=400,
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        if not content:
            return None
            
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            print("Error parsing Signal Insight response")
            return None
        
        if result.get('signal_found') and result.get('confidence_score', 0) >= 0.4:
            # Create fallback suggested action
            suggested_action = ("Brief internal review: Does this signal align with existing Dynamic Campus services? "
                              "Could it affect existing clients or near-future opportunities?")
            
            # Generate trend summary combining both fields
            trend_summary = f"{result['trend_summary']} {result.get('potential_impact', '')}"
            
            fallback_lead = LeadOpportunity(
                institution="❓ No specific institution identified",
                opportunity_summary=trend_summary,
                engagement_tier="Exploratory",
                suggested_action=suggested_action,
                sources=sources[:5],
                date_identified=datetime.now().strftime('%m/%d/%Y'),
                confidence_score=result['confidence_score'],
                lead_type="Signal",
                notes=f"This is a fallback signal with no identified institution. Confidence: {result['confidence_score']:.2f}",
                lead_id=generate_lead_id("signal_insight", "fallback"),
                is_fallback=True
            )
            
            print(f"Generated Signal Insight fallback with confidence: {result['confidence_score']:.2f}")
            return fallback_lead
        
        return None
        
    except Exception as e:
        print(f"Error generating Signal Insight: {e}")
        return None

def analyze_lead_potential(articles_data):
    """Analyze articles to identify potential leads using AI"""
    client = get_openai_client()
    if not client:
        return []
    
    try:
        # First, extract all institutions mentioned across articles
        all_institutions = set()
        institution_articles = {}
        
        for article in articles_data:
            article_text = f"{article['title']} {article['summary']}"
            institutions = extract_institutions_from_text(article_text)
            
            for institution in institutions:
                all_institutions.add(institution)
                if institution not in institution_articles:
                    institution_articles[institution] = []
                institution_articles[institution].append(article)
        
        if not all_institutions:
            print("No specific institutions found in articles")
            return []
        
        print(f"Found specific institutions: {list(all_institutions)}")
        
        # Now analyze each institution for lead potential
        processed_leads = []
        
        for institution in all_institutions:
            related_articles = institution_articles[institution]
            
            # Combine article data for this institution
            combined_text = ""
            sources = []
            
            for article in related_articles:
                combined_text += f"Title: {article['title']}\nSummary: {article['summary']}\nSource: {article['source']}\n\n"
                sources.append({"title": article['title'], "url": article['url']})
            
            # Add additional context from other articles mentioning similar topics
            for article in articles_data:
                if article not in related_articles:
                    article_text = f"{article['title']} {article['summary']}".lower()
                    institution_keywords = institution.lower().split()
                    
                    # Check if article discusses similar topics that could be relevant
                    tech_keywords = ['technology', 'digital', 'ai', 'cybersecurity', 'erp', 'system', 'data']
                    if any(keyword in article_text for keyword in tech_keywords):
                        sources.append({"title": article['title'], "url": article['url']})
                        combined_text += f"Title: {article['title']}\nSummary: {article['summary'][:500]}\nSource: {article['source']}\n\n"
            
            if len(sources) < 2:  # Need at least 2 sources for credibility
                print(f"Insufficient sources for {institution}")
                continue
            
            prompt = f"""Analyze these articles to identify specific business opportunities for a digital transformation consultancy at {institution}.

CRITICAL: Only identify opportunities if there is explicit evidence in the articles about {institution}. Do not make generic assumptions.

Focus on these opportunity types ONLY if explicitly mentioned or strongly implied for {institution}:
- ERP modernization or system transitions
- IT leadership changes (new CIOs, CTOs, digital officers)
- Cybersecurity incidents or policy changes
- AI/data governance initiatives
- LMS/CRM implementations or upgrades
- Analytics or institutional research transformations

Articles mentioning {institution}:
{combined_text[:3000]}

If you find a genuine opportunity for {institution}, respond in JSON format:
{{
    "lead_found": true,
    "institution": "{institution}",
    "lead_type": "ERP|IT Leadership|Cybersecurity|AI/Data|LMS/CRM|Analytics",
    "opportunity_summary": "Specific description of what {institution} needs/is doing",
    "engagement_tier": "Small|Medium|Recurring|Full Outsourcing",
    "confidence_score": 0.7
}}

If no specific opportunity is evident for {institution}, respond:
{{
    "lead_found": false,
    "reason": "Brief explanation"
}}"""

            analysis_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"You are analyzing business opportunities specifically for {institution}. Only identify opportunities with explicit evidence."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=500,
                temperature=0.2
            )
            
            analysis_content = analysis_response.choices[0].message.content
            if not analysis_content:
                continue
                
            try:
                analysis_result = json.loads(analysis_content)
            except json.JSONDecodeError:
                print(f"Error parsing analysis for {institution}")
                continue
            
            if analysis_result.get('lead_found') and analysis_result.get('confidence_score', 0) >= INSTITUTION_CONFIDENCE_THRESHOLD:
                # Generate suggested action
                action_prompt = f"""For this specific opportunity at {institution}, suggest a concrete strategic action for Dynamic Campus:

Institution: {institution}
Opportunity: {analysis_result['opportunity_summary']}
Type: {analysis_result['lead_type']}

Provide a 1-2 sentence strategic recommendation."""

                action_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": action_prompt}],
                    max_tokens=100,
                    temperature=0.4
                )
                
                action_content = action_response.choices[0].message.content
                if action_content:
                    suggested_action = action_content.strip()
                else:
                    suggested_action = f"Contact {institution} leadership to discuss digital transformation opportunities."
                
                lead = LeadOpportunity(
                    institution=institution,
                    opportunity_summary=analysis_result['opportunity_summary'],
                    engagement_tier=analysis_result['engagement_tier'],
                    suggested_action=suggested_action,
                    sources=sources[:5],  # Limit to 5 sources
                    date_identified=datetime.now().strftime('%m/%d/%Y'),
                    confidence_score=analysis_result['confidence_score'],
                    lead_type=analysis_result['lead_type'],
                    notes=f"Institution-specific analysis from {len(sources)} sources. Confidence: {analysis_result['confidence_score']:.2f}",
                    lead_id=generate_lead_id(institution, analysis_result['lead_type']),
                    is_fallback=False
                )
                
                processed_leads.append(lead)
                print(f"Generated lead for {institution}: {analysis_result['lead_type']}")
            else:
                print(f"No qualified opportunity found for {institution}")
        
        # If no institution-specific leads found, generate a Signal Insight fallback
        if not processed_leads:
            fallback_lead = generate_signal_insight(articles_data)
            if fallback_lead:
                processed_leads.append(fallback_lead)
        
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
        'lead_id': best_lead.lead_id,
        'is_fallback': best_lead.is_fallback
    }
    
    existing_leads.append(lead_dict)
    save_leads_database(existing_leads)
    
    print(f"Identified new lead: {best_lead.institution} - {best_lead.lead_type}")
    return best_lead

def format_email_body(lead):
    """Format lead data into clean HTML email body"""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    
    # Escape AI-generated content to prevent HTML injection
    institution = html.escape(lead.institution)
    opportunity_summary = html.escape(lead.opportunity_summary).replace('\n', '<br>')
    suggested_action = html.escape(lead.suggested_action).replace('\n', '<br>')
    notes = html.escape(lead.notes).replace('\n', '<br>')
    
    # Format sources as HTML links
    sources_html = ""
    for source in lead.sources[:3]:
        title = html.escape(source['title'][:60] + "..." if len(source['title']) > 60 else source['title'])
        url = html.escape(source['url'])
        sources_html += f"&bull; <a href='{url}'>{title}</a><br>"
    
    if lead.is_fallback:
        # Signal Insight fallback format
        body = f"""<html>
<body style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>
<h2 style='color: #2c3e50;'>📡 Signal Insight: Sector Trend Analysis</h2>

<p><strong>🎓 Institution:</strong> {institution}</p>

<p><strong>📡 Signal Insight:</strong><br>
{opportunity_summary}</p>

<p><strong>🏷️ Engagement Potential:</strong> {lead.engagement_tier} – {html.escape(ENGAGEMENT_TIERS.get(lead.engagement_tier, 'Trend monitoring'))}</p>

<p><strong>💡 Suggested Action:</strong><br>
{suggested_action}</p>

<p><strong>🔗 Sources:</strong><br>
{sources_html}</p>

<p><strong>📅 Date Identified:</strong> {lead.date_identified}</p>

<p><strong>📌 Notes:</strong><br>
{notes}<br>
Lead Type: {lead.lead_type.lower()}</p>

<hr style='margin: 20px 0; border: 1px solid #eee;'>
<p style='font-size: 12px; color: #666;'>
Generated by Higher Ed Lead Generation System<br>
Processed at: {current_date}<br>
Lead ID: {lead.lead_id}
</p>
</body>
</html>"""
    else:
        # Standard institution-specific lead format
        engagement_desc = html.escape(ENGAGEMENT_TIERS.get(lead.engagement_tier, 'Custom engagement'))
        
        body = f"""<html>
<body style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>
<h2 style='color: #2c3e50;'>🧠 New Lead Identified</h2>

<p><strong>🎓 Institution:</strong> {institution}</p>

<p><strong>🔍 Opportunity Summary:</strong><br>
{opportunity_summary}</p>

<p><strong>🏷️ Engagement Tier:</strong> {lead.engagement_tier}<br>
<em>{engagement_desc}</em></p>

<p><strong>💡 Suggested Action:</strong><br>
{suggested_action}</p>

<p><strong>🔗 Sources:</strong><br>
{sources_html}</p>

<p><strong>📅 Date Identified:</strong> {lead.date_identified}</p>

<p><strong>📌 Notes:</strong><br>
{notes}</p>

<hr style='margin: 20px 0; border: 1px solid #eee;'>
<p style='font-size: 12px; color: #666;'>
Generated by Higher Ed Lead Generation System custom built by Shayne McGregor<br>
Processed at: {current_date}<br>
Lead ID: {lead.lead_id}
</p>
</body>
</html>"""
    
    return body

def create_lead_email(lead):
    """Create formatted lead email with HTML body"""
    if lead.is_fallback:
        subject = f"📡 Signal Insight: {lead.lead_type} | Sector Trend Analysis"
    else:
        subject = f"🧠 New Lead Identified: {lead.institution} | {lead.lead_type} | {lead.engagement_tier}"
    
    html_body = format_email_body(lead)
    
    return subject, html_body

def send_lead_email(lead):
    """Send lead email to team with HTML formatting"""
    try:
        # Load credentials
        gmail_address = os.environ.get('GMAIL_ADDRESS')
        app_password = os.environ.get('GMAIL_APP_PASSWORD')
        
        if not gmail_address or not app_password:
            print("Gmail credentials not found")
            return False
        
        # Create email with HTML formatting
        subject, html_body = create_lead_email(lead)
        
        # Create multipart message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = gmail_address
        msg['To'] = 'shayne.mcgregor@dynamiccampus.com'
        msg['Cc'] = 'smcgregor@maryu.marywood.edu, jasmine.n.olivier@gmail.com'
        
        # Attach HTML content
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
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