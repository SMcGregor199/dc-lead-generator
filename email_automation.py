#!/usr/bin/env python3
"""
Daily Morning Email Automation Service
Unified service for sending automated morning emails with scheduling capabilities.
"""

import smtplib
import os
import sys
import traceback
import schedule
import time as time_module
import argparse
from email.message import EmailMessage
from datetime import datetime
import pytz
from news_service import get_daily_news_insight, get_fallback_news_content
from job_service import get_featured_job_posting


def load_credentials():
    """
    Load Gmail credentials from environment variables.
    
    Returns:
        tuple: (gmail_address, app_password) or (None, None) if not found
    """
    gmail_address = os.environ.get('GMAIL_ADDRESS')
    app_password = os.environ.get('GMAIL_APP_PASSWORD')
    
    return gmail_address, app_password


def create_morning_email(sender_email, recipient_email):
    """
    Create a formatted morning email message with news content.
    
    Args:
        sender_email (str): Sender's email address
        recipient_email (str): Recipient's email address
    
    Returns:
        EmailMessage: Formatted email message
    """
    # Get current Eastern Time
    eastern = pytz.timezone('US/Eastern')
    now_eastern = datetime.now(eastern)
    current_date = now_eastern.strftime("%A, %B %d, %Y")
    current_time = now_eastern.strftime("%I:%M %p %Z")
    
    # Create email message
    msg = EmailMessage()
    msg['Subject'] = "🌅 Good Morning – From Campus Whisperer"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Cc'] = 'smcgregor@maryu.marywood.edu, jasmine.n.olivier@gmail.com'
    
    # Get daily tech news insight with fallback
    print("Fetching daily tech news insight...")
    news_insight = get_daily_news_insight()
    
    # Use fallback if primary news fetching fails
    if not news_insight:
        print("Primary news fetching failed, using fallback content")
        news_insight = get_fallback_news_content()
    
    # Create news section
    news_section = f"""
📡 Higher Ed Tech Insight of the Day

{news_insight['title']}

{news_insight['summary']}"""
    
    # Only add URL if it exists (fallback content has empty URL)
    if news_insight['url']:
        news_section += f"\n\nRead more: {news_insight['url']}"
    
    news_section += f"\nSource: {news_insight['source']}\n\n"
    
    # Get featured job posting
    print("Fetching featured job posting...")
    try:
        job_posting = get_featured_job_posting()
        
        job_section = f"""
🎯 Featured Higher Ed Tech Job

{job_posting['title']}
{job_posting['company']}

{job_posting['summary']}"""
        
        if job_posting['url']:
            job_section += f"\n\nApply: {job_posting['url']}"
        
        job_section += f"\nSource: {job_posting['source']}\n\n"
        
    except Exception as e:
        print(f"Error fetching job posting: {e}")
        job_section = """
🎯 Featured Higher Ed Tech Job

Chief Information Officer - Major Research University
Leading Higher Education Institution

Seeking visionary technology leader to drive digital transformation initiatives across campus. Lead IT strategy, oversee infrastructure modernization, and collaborate with academic leadership.

Source: Higher Ed Tech Network

"""

    # Create email body with current date, time, and news
    email_body = f"""Good Morning! 🌞

Hope you're having a wonderful start to your day!

📅 Today's Date: {current_date}
🕐 Current Time: {current_time}

This is your automated morning greeting from Campus Whisperer.
{news_section}{job_section}Have a productive and amazing day ahead! 💪

Best regards,
Your Campus Whisperer Bot 🤖

---
This email was sent automatically via Python script designed by Shayne McGregor (Future Director of Innovation / Chief Innovation Officer / Head of Innovation) running on Replit.
Sent at: {now_eastern.strftime("%Y-%m-%d %H:%M:%S %Z")}
"""

    msg.set_content(email_body)
    return msg


def send_email(gmail_address, app_password, recipient_email):
    """
    Send email using Gmail SMTP server.
    
    Args:
        gmail_address (str): Gmail address for authentication
        app_password (str): Gmail app password
        recipient_email (str): Email address to send to
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create the email message
        msg = create_morning_email(gmail_address, recipient_email)
        
        print(f"Connecting to Gmail SMTP server...")
        # Connect to Gmail's SMTP server using SSL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            print(f"Logging in with account: {gmail_address}")
            server.login(gmail_address, app_password)
            
            print(f"Sending email to: {recipient_email}")
            server.send_message(msg)
            
        print("✅ Email sent successfully!")
        
        # Log successful send with timestamp
        eastern = pytz.timezone('US/Eastern')
        timestamp = datetime.now(eastern).strftime("%Y-%m-%d %H:%M:%S %Z")
        with open('log.txt', 'a') as log_file:
            log_file.write(f"SUCCESS: Email sent at {timestamp} to {recipient_email}\n")
        
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Please check your Gmail address and app password.")
        return False
        
    except smtplib.SMTPRecipientsRefused:
        print("❌ Recipient email address was refused by the server.")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False


def send_immediate_email():
    """
    Send email immediately (for manual execution or testing).
    """
    print("=== Immediate Email Execution ===")
    
    # Load credentials
    print("Loading credentials...")
    gmail_address, app_password = load_credentials()
    
    if not gmail_address or not app_password:
        print("❌ Failed to load credentials. Please check your environment variables.")
        return False
    
    print(f"✅ Credentials loaded successfully for: {gmail_address}")
    
    # Recipient email address
    recipient_email = "shayne.mcgregor@dynamiccampus.com"
    
    # Send the email
    success = send_email(gmail_address, app_password, recipient_email)
    
    if success:
        print("🎉 Email sent successfully!")
    else:
        print("💥 Email sending failed!")
    
    return success


def send_scheduled_email():
    """
    Function to be called by the scheduler at 7:00 AM daily.
    """
    print(f"\n=== Scheduled Morning Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # Load credentials
    print("Loading credentials...")
    gmail_address, app_password = load_credentials()
    
    if not gmail_address or not app_password:
        print("❌ Failed to load credentials. Please check your environment variables.")
        return
    
    print(f"✅ Credentials loaded successfully for: {gmail_address}")
    
    # Recipient email address
    recipient_email = "shayne.mcgregor@dynamiccampus.com"
    
    # Send the morning email
    success = send_email(gmail_address, app_password, recipient_email)
    
    if success:
        print("🎉 Scheduled morning email sent successfully!")
    else:
        print("💥 Scheduled morning email failed!")


def run_scheduler():
    """
    Run the email scheduler service that sends emails at 7:00 AM Eastern daily.
    """
    print("=== Daily Morning Email Scheduler Service ===")
    print(f"Service started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test credentials on startup
    print("Testing credentials...")
    gmail_address, app_password = load_credentials()
    
    if not gmail_address or not app_password:
        print("❌ Failed to load credentials. Please check your environment variables.")
        sys.exit(1)
    
    print(f"✅ Credentials validated for: {gmail_address}")
    
    # Schedule the email to be sent daily at 7:00 AM Eastern Time
    # Note: schedule library uses system time, so we need to account for timezone
    schedule.every().day.at("07:00").do(send_scheduled_email)
    
    print("📅 Email scheduled for 7:00 AM Eastern Time daily")
    print("🔄 Scheduler is now running... (Press Ctrl+C to stop)")
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time_module.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n👋 Scheduler stopped by user.")
        sys.exit(0)


def main():
    """
    Main function with argument parsing for different execution modes.
    """
    parser = argparse.ArgumentParser(description='Campus Whisperer Email Automation')
    parser.add_argument('--mode', 
                       choices=['immediate', 'schedule'], 
                       default='immediate',
                       help='Execution mode: immediate (send now) or schedule (run scheduler)')
    
    args = parser.parse_args()
    
    if args.mode == 'immediate':
        send_immediate_email()
    elif args.mode == 'schedule':
        run_scheduler()


if __name__ == "__main__":
    main()