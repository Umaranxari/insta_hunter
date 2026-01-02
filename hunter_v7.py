#!/usr/bin/env python3
"""
Hunter_v7 - Advanced Social Media Target Acquisition & Analysis Tool
A complete overhaul with sophisticated filtering, AI capabilities, and robust architecture.
"""

import os
import sys
import json
import csv
import time
import random
import logging
import smtplib
import configparser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import re
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Third-party imports (to be installed)
try:
    import pandas as pd
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    from colorama import init, Fore, Back, Style
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.table import Table
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)

# Initialize colorama and rich
init(autoreset=True)
console = Console()

@dataclass
class UserProfile:
    """Data class for storing user profile information"""
    username: str
    follower_count: int
    following_count: int
    post_count: int
    bio: str
    profile_url: str
    has_active_story: bool
    location: str
    is_verified: bool
    is_private: bool
    profile_pic_url: str
    last_post_date: Optional[str]
    engagement_rate: float
    estimated_gender: str
    bio_language: str
    account_age_estimate: str
    reason_for_selection: str
    source_hvt: str
    discovery_timestamp: str

class ConfigManager:
    """Manages configuration settings and validation"""
    
    def __init__(self, config_path: str = "config.ini"):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.load_or_create_config()
    
    def load_or_create_config(self):
        """Load existing config or create template"""
        if not os.path.exists(self.config_path):
            self.create_template_config()
        
        self.config.read(self.config_path)
        self.validate_config()
    
    def create_template_config(self):
        """Create template configuration file"""
        template_config = {
            'CREDENTIALS': {
                'username': 'your_instagram_username',
                'password': 'your_instagram_password',
                'email_username': 'your_email@gmail.com',
                'email_password': 'your_email_app_password'
            },
            'SCRAPING': {
                'min_delay': '2',
                'max_delay': '8',
                'request_timeout': '10',
                'max_retries': '3',
                'use_proxies': 'true',
                'max_recursion_depth': '3',
                'profiles_per_session': '1000'
            },
            'FILTERING': {
                'usa_location_keywords': 'USA,United States,US,America,NYC,Los Angeles,Chicago,Houston,Phoenix,Philadelphia,San Antonio,San Diego,Dallas,San Jose,Austin,Jacksonville,Fort Worth,Columbus,Charlotte,San Francisco,Indianapolis,Seattle,Denver,Washington,Boston,Nashville',
                'exclude_keywords': 'OnlyFans,escort,sugar daddy,cam girl,premium,link in bio',
                'require_profile_pic': 'true',
                'min_engagement_rate': '0.5',
                'max_engagement_rate': '15.0',
                'prefer_female_profiles': 'true'
            },
            'OUTPUT': {
                'csv_filename': 'hunter_v7_results.csv',
                'log_filename': 'hunter_v7_activity.log',
                'save_session_state': 'true',
                'session_state_file': 'hunter_v7_session.json'
            },
            'PROXIES': {
                'proxy_list': 'proxy_list.txt',
                'rotate_after_requests': '50',
                'test_proxies_on_startup': 'true'
            },
            'NOTIFICATIONS': {
                'send_email_reports': 'true',
                'email_recipient': 'justflawlessperfect@gmail.com',
                'notify_on_hvt_found': 'true',
                'hvt_notification_threshold': '10'
            }
        }
        
        config = configparser.ConfigParser()
        for section, options in template_config.items():
            config.add_section(section)
            for key, value in options.items():
                config.set(section, key, value)
        
        with open(self.config_path, 'w') as f:
            config.write(f)
        
        console.print(f"[yellow]Created template config file: {self.config_path}[/yellow]")
        console.print("[yellow]Please update the credentials and settings before running the script.[/yellow]")
    
    def validate_config(self):
        """Validate configuration entries"""
        required_sections = ['CREDENTIALS', 'SCRAPING', 'FILTERING', 'OUTPUT', 'PROXIES', 'NOTIFICATIONS']
        
        for section in required_sections:
            if not self.config.has_section(section):
                raise ValueError(f"Missing required config section: {section}")
        
        # Validate critical settings
        if self.config.get('CREDENTIALS', 'username') == 'your_instagram_username':
            console.print("[red]Warning: Please update Instagram credentials in config.ini[/red]")
    
    def get(self, section: str, key: str, fallback: str = None) -> str:
        """Get configuration value"""
        return self.config.get(section, key, fallback=fallback)
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value"""
        return self.config.getboolean(section, key, fallback=fallback)
    
    def getfloat(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get float configuration value"""
        return self.config.getfloat(section, key, fallback=fallback)

class Logger:
    """Advanced logging system with multiple levels and formatting"""
    
    def __init__(self, log_file: str = "hunter_v7_activity.log"):
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
        console.print(f"[blue]INFO:[/blue] {message}")
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
        console.print(f"[yellow]WARNING:[/yellow] {message}")
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
        console.print(f"[red]ERROR:[/red] {message}")
    
    def success(self, message: str):
        """Log success message"""
        self.logger.info(f"SUCCESS: {message}")
        console.print(f"[green]SUCCESS:[/green] {message}")
    
    def hvt_found(self, username: str, reason: str):
        """Log HVT discovery"""
        message = f"HVT FOUND: @{username} - {reason}"
        self.logger.info(message)
        console.print(f"[bright_green]🎯 HVT FOUND:[/bright_green] @{username}")
        console.print(f"[cyan]Reason:[/cyan] {reason}")

class ProxyManager:
    """Manages proxy rotation and validation"""
    
    def __init__(self, proxy_file: str, logger: Logger):
        self.proxy_file = proxy_file
        self.logger = logger
        self.proxies = []
        self.current_proxy_index = 0
        self.failed_proxies = set()
        self.load_proxies()
    
    def load_proxies(self):
        """Load proxies from file"""
        if os.path.exists(self.proxy_file):
            with open(self.proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            self.logger.info(f"Loaded {len(self.proxies)} proxies from {self.proxy_file}")
        else:
            self.logger.warning(f"Proxy file {self.proxy_file} not found. Creating template...")
            self.create_template_proxy_file()
    
    def create_template_proxy_file(self):
        """Create template proxy file"""
        template_proxies = [
            "# Add your proxies here, one per line",
            "# Format: ip:port or ip:port:username:password",
            "# Example: 192.168.1.1:8080",
            "# Example: 192.168.1.1:8080:username:password",
        ]
        
        with open(self.proxy_file, 'w') as f:
            f.write('\n'.join(template_proxies))
        
        self.logger.warning("Template proxy file created. Please add your proxies.")
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """Get next available proxy"""
        if not self.proxies:
            return None
        
        attempts = 0
        while attempts < len(self.proxies):
            proxy = self.proxies[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
            
            if proxy not in self.failed_proxies:
                return self.format_proxy(proxy)
            
            attempts += 1
        
        return None
    
    def format_proxy(self, proxy: str) -> Dict[str, str]:
        """Format proxy string into requests format"""
        parts = proxy.split(':')
        if len(parts) >= 2:
            ip, port = parts[0], parts[1]
            if len(parts) >= 4:
                username, password = parts[2], parts[3]
                proxy_url = f"http://{username}:{password}@{ip}:{port}"
            else:
                proxy_url = f"http://{ip}:{port}"
            
            return {
                'http': proxy_url,
                'https': proxy_url
            }
        return {}
    
    def mark_proxy_failed(self, proxy: Dict[str, str]):
        """Mark proxy as failed"""
        if proxy:
            proxy_str = proxy.get('http', '')
            self.failed_proxies.add(proxy_str)
            self.logger.warning(f"Marked proxy as failed: {proxy_str}")

class EmailNotifier:
    """Handles email notifications"""
    
    def __init__(self, config: ConfigManager, logger: Logger):
        self.config = config
        self.logger = logger
        self.email_username = config.get('CREDENTIALS', 'email_username')
        self.email_password = config.get('CREDENTIALS', 'email_password')
        self.recipient = config.get('NOTIFICATIONS', 'email_recipient')
        self.enabled = config.getboolean('NOTIFICATIONS', 'send_email_reports')
    
    def send_hvt_notification(self, hvt: UserProfile):
        """Send notification when HVT is found"""
        if not self.enabled or self.email_username == 'your_email@gmail.com':
            return
        
        subject = f"🎯 Hunter_v7: New HVT Found - @{hvt.username}"
        body = f"""
        New High-Value Target Discovered!
        
        Username: @{hvt.username}
        Followers: {hvt.follower_count:,}
        Posts: {hvt.post_count:,}
        Location: {hvt.location}
        Bio: {hvt.bio[:100]}...
        
        Reason for Selection: {hvt.reason_for_selection}
        
        Profile URL: {hvt.profile_url}
        Discovery Time: {hvt.discovery_timestamp}
        """
        
        self.send_email(subject, body)
    
    def send_session_summary(self, total_hvts: int, session_duration: str, errors: int):
        """Send session summary email"""
        if not self.enabled or self.email_username == 'your_email@gmail.com':
            return
        
        subject = f"📊 Hunter_v7 Session Complete - {total_hvts} HVTs Found"
        body = f"""
        Hunter_v7 Session Summary
        
        Total HVTs Found: {total_hvts}
        Session Duration: {session_duration}
        Errors Encountered: {errors}
        
        Check the CSV file for detailed results.
        """
        
        self.send_email(subject, body)
    
    def send_email(self, subject: str, body: str):
        """Send email notification"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_username
            msg['To'] = self.recipient
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_username, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_username, self.recipient, text)
            server.quit()
            
            self.logger.success(f"Email notification sent: {subject}")
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")

if __name__ == "__main__":
    console.print(Panel.fit("🎯 Hunter_v7 - Advanced Social Media Target Acquisition Tool", style="bold blue"))
    console.print("Initializing system components...")
    
    # Initialize core components
    config = ConfigManager()
    logger = Logger(config.get('OUTPUT', 'log_filename'))
    
    logger.info("Hunter_v7 initialization complete")
    logger.info("Ready to begin target acquisition...")
