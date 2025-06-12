#!/usr/bin/env python3
"""
Daily Morning Email Automation Script with Built-in Scheduling
Sends automated morning emails using Gmail SMTP at 7:00 AM daily.
"""

import smtplib
import os
from email.message import EmailMessage
from datetime import datetime, time
import sys
import traceback
import schedule
import time as time_module
import pytz

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
    
    # Create email body with current date and time
    email_body = f"""Good Morning! 🌞

Hope you're having a wonderful start to your day!

📅 Today's Date: {current_date}
🕐 Current Time: {current_time}

This is your automated morning greeting from Campus Whisperer.

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
        print("Please check your Gmail address and app password in Replit Secrets.")
        print("Make sure you're using an App Password, not your regular Gmail password.")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

def send_scheduled_email():
    """
    Function to be called by the scheduler at 7:00 AM daily.
    """
    print(f"\n=== Scheduled Morning Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    # Load credentials from Replit Secrets
    print("Loading credentials from Replit Secrets...")
    gmail_address, app_password = load_credentials()
    
    if not gmail_address or not app_password:
        print("❌ Failed to load credentials. Please check your Replit Secrets configuration.")
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

def main():
    """
    Main function to set up scheduling and run the email automation service.
    """
    print("=== Daily Morning Email Automation Service ===")
    print(f"Service started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test credentials on startup
    print("Testing credentials...")
    gmail_address, app_password = load_credentials()
    
    if not gmail_address or not app_password:
        print("❌ Failed to load credentials. Please check your Replit Secrets configuration.")
        sys.exit(1)
    
    print(f"✅ Credentials verified for: {gmail_address}")
    
    # Schedule the email to be sent daily at 7:00 AM
    schedule.every().day.at("07:00").do(send_scheduled_email)
    
    print("📅 Email scheduled to send daily at 7:00 AM")
    print("🔄 Service is now running... Press Ctrl+C to stop")
    
    # Keep the script running and check for scheduled jobs
    while True:
        try:
            schedule.run_pending()
            time_module.sleep(60)  # Check every minute
            
            # Optional: Print status every hour
            now = datetime.now()
            if now.minute == 0:  # On the hour
                next_run = schedule.next_run()
                print(f"⏰ Status check at {now.strftime('%H:%M')} - Next email scheduled for: {next_run}")
                
        except KeyboardInterrupt:
            print("\n👋 Email automation service stopped by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error in main loop: {e}")
            traceback.print_exc()
            time_module.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    main()