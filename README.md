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

For better reliability, use the `scheduled_main.py` file which includes built-in scheduling:

```bash
python scheduled_main.py
```

This version will:
- Run continuously in the background
- Automatically send emails at 7:00 AM daily
- Provide status updates and error handling
- Restart automatically if there are issues

### Step 6: Enable Always On (Important)

For 24/7 operation on Replit:

1. Go to your Replit project settings
2. Enable "Always On" feature (requires Replit subscription)
3. Your email service will run continuously even when you close the browser

### Step 7: Deploy to Production

Once tested, you can deploy this to run continuously:

1. **Current Status**: The scheduled service is now running
2. **Next Email**: Will be sent tomorrow at 7:00 AM
3. **Monitoring**: Check the console logs for status updates

## Files Explained

- `main.py` - Single-run version for testing
- `scheduled_main.py` - Continuous service with built-in 7:00 AM scheduling
- `README.md` - This setup guide

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
   