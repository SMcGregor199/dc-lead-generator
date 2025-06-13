#!/usr/bin/env python3
"""
Source Logging Utilities
Centralized logging for broken feeds and source validation
"""

import os
from datetime import datetime
import json

BROKEN_SOURCES_LOG = 'broken_sources.log'
SOURCES_CONFIG_FILE = 'sources_config.json'

def log_broken_feed(url, error_message=None, source_name=None):
    """
    Log broken or dead feeds to broken_sources.log
    
    Args:
        url (str): The feed URL that failed
        error_message (str): Optional error details
        source_name (str): Optional source name for context
    """
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        log_entry = f"[{timestamp}] BROKEN FEED: {url}"
        if source_name:
            log_entry += f" ({source_name})"
        if error_message:
            log_entry += f" - Error: {error_message}"
        log_entry += "\n"
        
        with open(BROKEN_SOURCES_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
        print(f"Logged broken feed: {source_name or url}")
        
    except Exception as e:
        print(f"Failed to log broken feed: {e}")

def load_sources_config():
    """
    Load sources configuration from JSON file
    
    Returns:
        dict: Sources configuration data
    """
    try:
        if os.path.exists(SOURCES_CONFIG_FILE):
            with open(SOURCES_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading sources config: {e}")
    
    return {"news_sources": [], "job_sources": []}

def update_source_status(source_name, source_type, status, error_message=None):
    """
    Update source status in configuration file
    
    Args:
        source_name (str): Name of the source
        source_type (str): 'news_sources' or 'job_sources'
        status (bool): Whether source is working
        error_message (str): Optional error details
    """
    try:
        config = load_sources_config()
        
        if source_type in config:
            for source in config[source_type]:
                if source['name'] == source_name:
                    source['active'] = status
                    source['last_verified'] = datetime.now().strftime('%Y-%m-%d')
                    if error_message:
                        source['note'] = error_message
                    break
        
        with open(SOURCES_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
            
    except Exception as e:
        print(f"Error updating source status: {e}")

def get_active_sources(source_type):
    """
    Get list of active sources by type
    
    Args:
        source_type (str): 'news_sources' or 'job_sources'
    
    Returns:
        list: Active sources of the specified type
    """
    config = load_sources_config()
    
    if source_type in config:
        return [source for source in config[source_type] if source.get('active', True)]
    
    return []

def mark_source_verified(source_name, source_type):
    """
    Mark a source as verified and working
    
    Args:
        source_name (str): Name of the source
        source_type (str): 'news_sources' or 'job_sources'
    """
    update_source_status(source_name, source_type, True)

def mark_source_broken(source_name, source_type, error_message):
    """
    Mark a source as broken and log the issue
    
    Args:
        source_name (str): Name of the source
        source_type (str): 'news_sources' or 'job_sources'
        error_message (str): Error details
    """
    config = load_sources_config()
    
    # Find the source URL for logging
    source_url = None
    if source_type in config:
        for source in config[source_type]:
            if source['name'] == source_name:
                source_url = source['url']
                break
    
    # Log the broken feed
    if source_url:
        log_broken_feed(source_url, error_message, source_name)
    
    # Update status in config
    update_source_status(source_name, source_type, False, error_message)