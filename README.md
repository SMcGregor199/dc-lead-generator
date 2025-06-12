# Campus Whisperer - Email Automation System

A Python-powered email automation tool that sends intelligent, personalized daily morning emails with AI-generated higher education news summaries.

## Key Features

- 📧 Automated daily emails at 7:00 AM Eastern Time
- 🤖 AI-powered news summarization using OpenAI GPT-4o
- 📰 Real-time RSS feed parsing from verified Higher Ed sources
- 🔐 Secure credential management via environment variables
- 🛡️ Enterprise-grade error handling and retry logic
- 📊 Comprehensive logging and monitoring
- 🌐 Gmail SMTP with SSL encryption (port 465)

## Project Structure

### Core Files
- `email_automation.py` - Unified email service (immediate and scheduled modes)
- `news_service.py` - RSS feed parsing and OpenAI summarization
- `feed_tester.py` - RSS feed validation utility
- `log.txt` - Timestamped success logs

### Configuration
- `pyproject.toml` - Python dependencies
- `IMPROVEMENTS_SUMMARY.md` - Enhancement documentation

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
   