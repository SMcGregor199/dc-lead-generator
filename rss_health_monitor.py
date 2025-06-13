#!/usr/bin/env python3
"""
RSS Feed Health Monitoring System
Automated health checker for higher education news feeds
Enhanced with email alerts and comprehensive logging
"""

import requests
import feedparser
import json
import os
import sys
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# RSS Feeds to monitor
HIGHER_ED_FEEDS = [
    {
        'name': 'Inside Higher Ed',
        'url': 'https://www.insidehighered.com/rss.xml',
        'category': 'news'
    },
    {
        'name': 'EdTech Magazine Higher Ed',
        'url': 'https://edtechmagazine.com/higher/rss.xml',
        'category': 'technology'
    },
    {
        'name': 'Higher Ed Dive',
        'url': 'https://www.highereddive.com/feeds/',
        'category': 'news'
    },
    {
        'name': 'The Chronicle of Higher Education',
        'url': 'https://www.chronicle.com/section/news/rss',
        'category': 'news'
    },
    {
        'name': 'EDUCAUSE Review',
        'url': 'https://er.educause.edu/articles/rss',
        'category': 'technology'
    }
]

RSS_HEALTH_LOG = 'rss_health_log.txt'
FEED_STATUS_FILE = 'feed_status.json'

def log_health_check(message):
    """Log health check results with timestamp"""
    try:
        with open(RSS_HEALTH_LOG, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Failed to write to log: {e}")

def load_previous_status():
    """Load previous feed status for comparison"""
    try:
        if os.path.exists(FEED_STATUS_FILE):
            with open(FEED_STATUS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_current_status(status_data):
    """Save current feed status"""
    try:
        with open(FEED_STATUS_FILE, 'w') as f:
            json.dump(status_data, f, indent=2)
    except Exception as e:
        print(f"Failed to save status: {e}")

def test_rss_feed(feed_info, timeout=15):
    """
    Test a single RSS feed for health and content.
    
    Args:
        feed_info (dict): Feed information with name and url
        timeout (int): Request timeout in seconds
    
    Returns:
        dict: Detailed test results
    """
    result = {
        'name': feed_info['name'],
        'url': feed_info['url'],
        'category': feed_info['category'],
        'timestamp': datetime.now().isoformat(),
        'status': 'unknown',
        'response_code': None,
        'entry_count': 0,
        'latest_entry_date': None,
        'error_message': None,
        'response_time': None
    }
    
    try:
        start_time = datetime.now()
        
        # Test HTTP response
        response = requests.get(feed_info['url'], timeout=timeout, headers={
            'User-Agent': 'Higher Ed Lead Generation Health Monitor/1.0'
        })
        
        response_time = (datetime.now() - start_time).total_seconds()
        result['response_time'] = round(response_time, 2)
        result['response_code'] = response.status_code
        
        if response.status_code == 200:
            # Parse RSS content
            feed = feedparser.parse(response.content)
            
            if hasattr(feed, 'entries') and len(feed.entries) > 0:
                result['entry_count'] = len(feed.entries)
                
                # Check latest entry date
                if feed.entries[0].get('published_parsed'):
                    latest_date = datetime(*feed.entries[0].published_parsed[:6])
                    result['latest_entry_date'] = latest_date.isoformat()
                    
                    # Check if content is fresh (within last 7 days)
                    days_old = (datetime.now() - latest_date).days
                    if days_old <= 7:
                        result['status'] = 'healthy'
                    elif days_old <= 30:
                        result['status'] = 'stale'
                    else:
                        result['status'] = 'very_stale'
                else:
                    result['status'] = 'no_dates'
            else:
                result['status'] = 'empty'
                result['error_message'] = 'No entries found in feed'
        else:
            result['status'] = 'http_error'
            result['error_message'] = f'HTTP {response.status_code}'
            
    except requests.exceptions.Timeout:
        result['status'] = 'timeout'
        result['error_message'] = f'Request timeout after {timeout}s'
    except requests.exceptions.ConnectionError:
        result['status'] = 'connection_error'
        result['error_message'] = 'Connection failed'
    except Exception as e:
        result['status'] = 'error'
        result['error_message'] = str(e)
    
    return result

def check_all_feeds():
    """
    Check health of all RSS feeds and generate comprehensive report.
    
    Returns:
        dict: Complete health check results
    """
    print("Starting RSS feed health check...")
    log_health_check("=== RSS Feed Health Check Started ===")
    
    current_status = {}
    results = []
    
    for feed in HIGHER_ED_FEEDS:
        print(f"Testing {feed['name']}...")
        result = test_rss_feed(feed)
        results.append(result)
        current_status[feed['name']] = result
        
        # Log individual results
        if result['status'] == 'healthy':
            log_health_check(f"✅ {feed['name']}: Healthy ({result['entry_count']} entries)")
        else:
            log_health_check(f"❌ {feed['name']}: {result['status']} - {result['error_message']}")
    
    # Generate summary
    healthy_count = sum(1 for r in results if r['status'] == 'healthy')
    total_count = len(results)
    
    summary = {
        'check_timestamp': datetime.now().isoformat(),
        'total_feeds': total_count,
        'healthy_feeds': healthy_count,
        'unhealthy_feeds': total_count - healthy_count,
        'results': results
    }
    
    log_health_check(f"Health check complete: {healthy_count}/{total_count} feeds healthy")
    
    # Save current status
    save_current_status(current_status)
    
    return summary

def detect_persistent_failures():
    """
    Detect feeds that have been failing for multiple consecutive checks.
    
    Returns:
        list: Feeds with persistent failures
    """
    try:
        previous_status = load_previous_status()
        if not previous_status:
            return []
        
        current_results = check_all_feeds()
        persistent_failures = []
        
        for result in current_results['results']:
            feed_name = result['name']
            current_status = result['status']
            previous_result = previous_status.get(feed_name, {})
            previous_status_value = previous_result.get('status', 'unknown')
            
            # Check if feed has been unhealthy in both checks
            if (current_status in ['http_error', 'timeout', 'connection_error', 'empty'] and 
                previous_status_value in ['http_error', 'timeout', 'connection_error', 'empty']):
                
                persistent_failures.append({
                    'name': feed_name,
                    'url': result['url'],
                    'current_status': current_status,
                    'previous_status': previous_status_value,
                    'error_message': result['error_message']
                })
        
        return persistent_failures
        
    except Exception as e:
        log_health_check(f"Error detecting persistent failures: {e}")
        return []

def send_admin_alert(persistent_failures):
    """
    Send email alert to admin about persistent feed failures.
    
    Args:
        persistent_failures (list): List of persistently failing feeds
    """
    try:
        if not persistent_failures:
            return
        
        gmail_address = os.environ.get('GMAIL_ADDRESS')
        app_password = os.environ.get('GMAIL_APP_PASSWORD')
        
        if not gmail_address or not app_password:
            log_health_check("Cannot send admin alert: Gmail credentials not configured")
            return
        
        # Create alert email
        subject = f"RSS Feed Health Alert: {len(persistent_failures)} Persistent Failures"
        
        html_body = f"""<html>
<body style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>
<h2 style='color: #e74c3c;'>RSS Feed Health Alert</h2>

<p>The following RSS feeds have been failing for 2+ consecutive health checks:</p>

<table style='border-collapse: collapse; width: 100%;'>
<tr style='background-color: #f8f9fa;'>
    <th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Feed Name</th>
    <th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Status</th>
    <th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Error</th>
</tr>"""
        
        for failure in persistent_failures:
            html_body += f"""
<tr>
    <td style='border: 1px solid #ddd; padding: 8px;'>{failure['name']}</td>
    <td style='border: 1px solid #ddd; padding: 8px;'>{failure['current_status']}</td>
    <td style='border: 1px solid #ddd; padding: 8px;'>{failure['error_message']}</td>
</tr>"""
        
        html_body += f"""
</table>

<p><strong>Recommended Actions:</strong></p>
<ul>
    <li>Check feed URLs for changes or redirects</li>
    <li>Contact feed providers if issues persist</li>
    <li>Consider alternative sources for affected feeds</li>
</ul>

<hr style='margin: 20px 0; border: 1px solid #eee;'>
<p style='font-size: 12px; color: #666;'>
Generated by RSS Health Monitoring System<br>
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</p>
</body>
</html>"""
        
        # Send email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = gmail_address
        msg['To'] = 'shayne.mcgregor@dynamiccampus.com'
        msg['Cc'] = 'smcgregor@maryu.marywood.edu, jasmine.n.olivier@gmail.com'
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_address, app_password)
            server.send_message(msg)
        
        log_health_check(f"Admin alert sent for {len(persistent_failures)} persistent failures")
        
    except Exception as e:
        log_health_check(f"Failed to send admin alert: {e}")

def run_health_monitoring():
    """
    Run complete RSS health monitoring with persistence detection and alerts.
    
    Returns:
        dict: Complete monitoring results
    """
    try:
        print("Running RSS feed health monitoring...")
        
        # Check for persistent failures
        persistent_failures = detect_persistent_failures()
        
        # Run current health check
        current_results = check_all_feeds()
        
        # Send alerts if needed
        if persistent_failures:
            print(f"Detected {len(persistent_failures)} persistent failures - sending admin alert")
            send_admin_alert(persistent_failures)
        
        # Generate final report
        monitoring_report = {
            'monitoring_timestamp': datetime.now().isoformat(),
            'persistent_failures': persistent_failures,
            'current_results': current_results
        }
        
        return monitoring_report
        
    except Exception as e:
        log_health_check(f"RSS health monitoring failed: {e}")
        return None

def main():
    """Main function for RSS health monitoring"""
    if len(sys.argv) > 1 and sys.argv[1] == '--check-only':
        # Just run health check without persistence detection
        results = check_all_feeds()
        print(f"Health check complete: {results['healthy_feeds']}/{results['total_feeds']} feeds healthy")
    else:
        # Run full monitoring with alerts
        results = run_health_monitoring()
        if results:
            healthy = results['current_results']['healthy_feeds']
            total = results['current_results']['total_feeds']
            persistent = len(results['persistent_failures'])
            print(f"Monitoring complete: {healthy}/{total} feeds healthy, {persistent} persistent failures")

if __name__ == "__main__":
    main()