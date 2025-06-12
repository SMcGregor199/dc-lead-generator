# Daily Morning Email Automation

This Python script sends automated morning emails using Gmail SMTP and Replit's scheduling feature.

## Features

- 📧 Sends daily morning emails at 7:00 AM
- 🔐 Secure credential management using Replit Secrets
- 📅 Includes current date and time in email body
- 🛡️ Robust error handling and logging
- 🌐 Uses Gmail SMTP with SSL (port 465)

## Setup Instructions

### Step 1: Configure Replit Secrets

1. Open your Replit project
2. Click on the "Secrets" tab in the left sidebar (🔒 icon)
3. Add the following secrets:

   **Secret Name:** `GMAIL_ADDRESS`
   **Secret Value:** Your Gmail address (e.g., your.email@gmail.com)

   **Secret Name:** `GMAIL_APP_PASSWORD`
   **Secret Value:** Your Gmail App Password (see instructions below)

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

### Step 3: Test the Script

1. Run the script manually first to test:
   ```bash
   python main.py
   ```

2. If successful, you should see output like:
   ```
   ✅ Credentials loaded successfully for: your.email@gmail.com
   ✅ Morning email sent successfully!
   🎉 Morning email automation completed successfully!
   ```

### Step 4: Schedule Daily Execution (7:00 AM)

To schedule the script to run automatically every morning at 7:00 AM:

1. **Option A: Using Replit Cron Jobs**
   - Go to your Replit project
   - Click on the "Shell" tab
   - Install cron if not available: `sudo apt-get update && sudo apt-get install cron`
   - Edit crontab: `crontab -e`
   - Add this line for 7:00 AM daily execution:
     ```
     0 7 * * * cd /home/runner/your-project-name && python main.py
     ```
   - Save and exit (Ctrl+X, then Y, then Enter)

2. **Option B: Using Replit Always On (Recommended)**
   - Enable "Always On" for your Replit project
   - The script will run continuously and can be modified to include scheduling logic
   - Add a scheduling loop to main.py (see below)

3. **Option C: External Scheduling Services**
   - Use services like GitHub Actions, Heroku Scheduler, or Vercel Cron
   - Set up a webhook to trigger your Replit project

### Step 5: Add Internal Scheduling (Recommended Approach)

For better reliability, modify main.py to include scheduling logic:
   