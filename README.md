# Higher Education Lead Generation System

An AI-powered lead generation system that identifies genuine technology opportunities for Dynamic Campus by analyzing higher education news sources and institutional developments.

## Key Features

- 🧠 AI-powered lead identification from higher education news
- 🎯 Institution-specific opportunity analysis with named entity recognition
- 📊 Configurable engagement tier classification system
- 👥 Automated contact enrichment and potential contact identification
- 📧 HTML-formatted daily email reports at 7:00 AM Eastern Time
- 🔗 Real-time RSS feed analysis from verified Higher Ed sources
- 🛡️ Client filtering to avoid duplicate outreach to current customers
- 📈 Confidence scoring based on Dynamic Campus service alignment

## Project Structure

### Core Files
- `lead_generation_service.py` - Main lead generation system with AI analysis
- `news_service.py` - RSS feed parsing and content extraction
- `job_service.py` - Higher education job posting integration
- `higher_ed_leads.json` - Persistent lead database
- `dynamic_campus_clients.json` - Current client database for filtering
- `log.txt` - Timestamped operation logs

### Configuration Files
- `pyproject.toml` - Python dependencies and project metadata
- `README.md` - System documentation and setup instructions

## Engagement Tier Classification System

The system uses configurable rules to classify opportunities into engagement tiers:

### ENGAGEMENT_TIER_RULES
- **Small**: LMS updates, website rebuilds, pilot projects, single system upgrades
- **Medium**: ERP implementation, AI governance, cloud migration, cybersecurity assessments
- **Recurring**: Security audits, managed services, ongoing institutional support
- **Full Outsourcing**: Complete IT management, infrastructure overhauls, digital transformation

*Note: Dynamic Campus should review and customize these tier definitions before production use.*

## Confidence Scoring System

Confidence scores (0.3-0.95) are calculated based on Dynamic Campus service keyword alignment:

### DC_SERVICE_KEYWORDS
- Core services: ERP, AI governance, cybersecurity, data governance, LMS, CRM
- Extended services: Cloud migration, digital transformation, IT infrastructure
- Specialized areas: Institutional research, analytics, business intelligence

*Note: This keyword list represents Dynamic Campus services and should be finalized before production deployment.*

## Contact Enrichment

The system attempts to identify potential contacts through:
1. **Source Content Analysis**: Extracts names and titles from article content
2. **Common Higher Ed Roles**: Provides likely IT leadership positions when specific contacts aren't found
3. **Fallback Guidance**: Directs to university leadership directories when no contacts are available

## Setup Instructions

### Step 1: Configure Environment Variables

Set up the required environment variables in Replit Secrets:

**Required Secrets:**
- `GMAIL_ADDRESS` - Your Gmail address
- `GMAIL_APP_PASSWORD` - Gmail App Password (not regular password)
- `OPENAI_API_KEY` - OpenAI API key for news summarization

### Step 2: Generate Gmail App Password

⚠️ **Important**: You must use a Gmail App Password, not your regular Gmail password.

1. Go to your Google Account settings: https://myaccount.google.com/
2. Click on "Security" in the left sidebar
3. Enable 2-Factor Authentication if not already enabled
4. Under "2-Step Verification", click on "App passwords"
5. Select "Mail" and "Other" device
6. Enter "Replit Email Bot" as the device name
7. Copy the 16-character app password (format: xxxx xxxx xxxx xxxx)
8. Use this app password in your Replit Secret

### Step 3: Usage

**Immediate Email (Testing):**
```bash
python email_automation.py --mode immediate
```

**Scheduled Service (Production):**
```bash
python email_automation.py --mode schedule
```

### Step 4: RSS Feed Testing

Validate all RSS feeds:
```bash
python feed_tester.py
```

## Verified RSS Feeds

The system uses these validated higher education news sources:
- Inside Higher Ed
- EdTech Magazine Higher Ed  
- Higher Ed Dive
- Faculty Focus
- The PIE News
- Ruffalo Noel Levitz Blog
- The Guardian Higher Education

## Usage Examples

**Test RSS Feeds:**
```bash
python feed_tester.py
```

**Send Test Email:**
```bash
python email_automation.py --mode immediate
```

**Run Scheduler Service:**
```bash
python email_automation.py --mode schedule
```

## Troubleshooting

### Common Issues:

1. **Authentication Error**: Verify your Gmail App Password is correct
2. **Email Not Received**: Check spam folder, verify recipient address
3. **Service Stopped**: Restart the workflow or enable Replit Always On
4. **Time Zone Issues**: The script uses server time (UTC) - adjust schedule if needed

### Checking Logs:

Monitor the workflow console for:
- ✅ Successful email sends
- ❌ Error messages
- ⏰ Status updates

## Security Notes

- Gmail credentials are stored securely in Replit Secrets
- App passwords are used instead of regular passwords for enhanced security
- No sensitive information is logged or displayed
   