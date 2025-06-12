#!/usr/bin/env python3
"""
Daily Morning Email Automation Script
Sends automated morning emails using Gmail SMTP with Replit scheduling.
"""

import smtplib
import os
from email.message import EmailMessage
from datetime import datetime
import sys
import traceback
import pytz
from news_fetcher import get_daily_news_insight


def load_credentials():
    """
    Load Gmail credentials from Replit Secrets.
    
    Returns:
        tuple: (gmail_address, app_password) or (None, None) if not found
    """
    gmail_address = os.getenv('GMAIL_ADDRESS')
    app_password = os.getenv('GMAIL_APP_PASSWORD')

    if not gmail_address:
        print("ERROR: GMAIL_ADDRESS not found in Replit Secrets")
        return None, None

    if not app_password:
        print("ERROR: GMAIL_APP_PASSWORD not found in Replit Secrets")
        return None, None

    return gmail_address, app_password


def create_morning_email(sender_email, recipient_email):
    """
    Create a formatted morning email message.
    
    Args:
        sender_email (str): Sender's email address
        recipient_email (str): Recipient's email address
    
    Returns:
        EmailMessage: Formatted email message
    """
    # Get current date and time in Eastern Time
    eastern = pytz.timezone('US/Eastern')
    now_utc = datetime.now(pytz.utc)
    now_eastern = now_utc.astimezone(eastern)
    current_date = now_eastern.strftime("%A, %B %d, %Y")
    current_time = now_eastern.strftime("%I:%M %p %Z")

    # Create email message
    msg = EmailMessage()
    msg['Subject'] = "🌅 Good Morning – From Campus Whisperer"
    msg['From'] = sender_email
    msg['To'] = recipient_email

    # Get daily news insight
    print("Fetching daily news insight...")
    news_insight = get_daily_news_insight()
    
    # Create news section
    if news_insight:
        news_section = f"""
📡 Campus Insight of the Day

{news_insight['title']}

{news_insight['summary']}

Read more: {news_insight['url']}
Source: {news_insight['source']}

"""
    else:
        news_section = """
📡 Campus Insight of the Day

Unable to fetch today's higher education news. Please check back later for your daily campus insight.

"""

    # Create email body with current date, time, and news
    email_body = f"""Good Morning! 🌞

Hope you're having a wonderful start to your day!

📅 Today's Date: {current_date}
🕐 Current Time: {current_time}

This is your automated morning greeting from Campus Whisperer.
{news_section}
Have a productive and amazing day ahead! 💪

Best regards,
Your Campus Whisperer Bot 🤖

---
This email was sent automatically via Python script running on Replit.
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
        print(f"Attempting to send morning email to {recipient_email}...")

        # Create email message
        msg = create_morning_email(gmail_address, recipient_email)

        # Connect to Gmail SMTP server
        print("Connecting to Gmail SMTP server...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            print("Logging in to Gmail...")
            server.login(gmail_address, app_password)

            print("Sending email...")
            server.send_message(msg)

        print("✅ Morning email sent successfully!")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error: {e}")
        print(
            "Please check your Gmail address and app password in Replit Secrets."
        )
        print(
            "Make sure you're using an App Password, not your regular Gmail password."
        )
        return False

    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
        return False

    except Exception as e:
        print(f"❌ Unexpected error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False


def main():
    """
    Main function to execute the morning email automation.
    """
    print("=== Daily Morning Email Automation ===")
    print(f"Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load credentials from Replit Secrets
    print("Loading credentials from Replit Secrets...")
    gmail_address, app_password = load_credentials()

    if not gmail_address or not app_password:
        print(
            "❌ Failed to load credentials. Please check your Replit Secrets configuration."
        )
        sys.exit(1)

    print(f"✅ Credentials loaded successfully for: {gmail_address}")

    # Recipient email address
    recipient_email = "shayne.mcgregor@dynamiccampus.com"

    # Send the morning email
    success = send_email(gmail_address, app_password, recipient_email)

    if success:
        print("🎉 Morning email automation completed successfully!")
    else:
        print("💥 Morning email automation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
