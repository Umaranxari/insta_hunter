"""
Hunter_v7 Utility Functions
Additional helper functions and tools for enhanced functionality
"""

import os
import csv
import json
import time
import sys
import random
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class DataAnalyzer:
    """Advanced data analysis for HVT results"""
    
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.data = self.load_data()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """Load HVT data from CSV"""
        data = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        except FileNotFoundError:
            console.print(f"[red]File not found: {self.csv_file}[/red]")
        except Exception as e:
            console.print(f"[red]Error loading data: {e}[/red]")
        
        return data
    
    def generate_analytics_report(self):
        """Generate comprehensive analytics report"""
        if not self.data:
            console.print("[yellow]No data available for analysis[/yellow]")
            return
        
        console.print(Panel.fit("📊 Hunter_v7 Analytics Report", style="bold blue"))
        
        # Basic statistics
        total_hvts = len(self.data)
        
        # Follower count analysis
        follower_counts = [int(row.get('follower_count', 0)) for row in self.data if row.get('follower_count', '').isdigit()]
        avg_followers = sum(follower_counts) / len(follower_counts) if follower_counts else 0
        
        # Gender distribution
        gender_dist = {}
        for row in self.data:
            gender = row.get('estimated_gender', 'unknown')
            gender_dist[gender] = gender_dist.get(gender, 0) + 1
        
        # Language distribution
        lang_dist = {}
        for row in self.data:
            lang = row.get('bio_language', 'unknown')
            lang_dist[lang] = lang_dist.get(lang, 0) + 1
        
        # Source analysis
        source_dist = {}
        for row in self.data:
            source = row.get('source_hvt', 'unknown')
            source_dist[source] = source_dist.get(source, 0) + 1
        
        # Create summary table
        table = Table(title="Summary Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total HVTs", str(total_hvts))
        table.add_row("Average Followers", f"{avg_followers:,.0f}")
        table.add_row("Top Gender", max(gender_dist.items(), key=lambda x: x[1])[0] if gender_dist else "N/A")
        table.add_row("Top Language", max(lang_dist.items(), key=lambda x: x[1])[0] if lang_dist else "N/A")
        table.add_row("Most Productive Source", max(source_dist.items(), key=lambda x: x[1])[0] if source_dist else "N/A")
        
        console.print(table)
        
        # Gender distribution table
        if gender_dist:
            gender_table = Table(title="Gender Distribution")
            gender_table.add_column("Gender", style="cyan")
            gender_table.add_column("Count", style="green")
            gender_table.add_column("Percentage", style="yellow")
            
            for gender, count in sorted(gender_dist.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_hvts) * 100
                gender_table.add_row(gender.title(), str(count), f"{percentage:.1f}%")
            
            console.print(gender_table)
        
        # Top performers by follower count
        top_performers = sorted(self.data, key=lambda x: int(x.get('follower_count', 0)) if x.get('follower_count', '').isdigit() else 0, reverse=True)[:10]
        
        if top_performers:
            perf_table = Table(title="Top 10 HVTs by Follower Count")
            perf_table.add_column("Rank", style="cyan")
            perf_table.add_column("Username", style="green")
            perf_table.add_column("Followers", style="yellow")
            perf_table.add_column("Gender", style="magenta")
            
            for i, hvt in enumerate(top_performers, 1):
                perf_table.add_row(
                    str(i),
                    f"@{hvt.get('username', 'N/A')}",
                    f"{int(hvt.get('follower_count', 0)):,}" if hvt.get('follower_count', '').isdigit() else "N/A",
                    hvt.get('estimated_gender', 'unknown').title()
                )
            
            console.print(perf_table)
    
    def export_filtered_results(self, filter_criteria: Dict[str, Any], output_file: str):
        """Export filtered subset of results"""
        filtered_data = []
        
        for row in self.data:
            include = True
            
            # Apply filters
            if 'min_followers' in filter_criteria:
                followers = int(row.get('follower_count', 0)) if row.get('follower_count', '').isdigit() else 0
                if followers < filter_criteria['min_followers']:
                    include = False
            
            if 'max_followers' in filter_criteria:
                followers = int(row.get('follower_count', 0)) if row.get('follower_count', '').isdigit() else 0
                if followers > filter_criteria['max_followers']:
                    include = False
            
            if 'gender' in filter_criteria:
                if row.get('estimated_gender', '').lower() != filter_criteria['gender'].lower():
                    include = False
            
            if 'language' in filter_criteria:
                if row.get('bio_language', '').lower() != filter_criteria['language'].lower():
                    include = False
            
            if include:
                filtered_data.append(row)
        
        # Export filtered data
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if filtered_data:
                    writer = csv.DictWriter(f, fieldnames=filtered_data[0].keys())
                    writer.writeheader()
                    writer.writerows(filtered_data)
            
            console.print(f"[green]Exported {len(filtered_data)} filtered results to {output_file}[/green]")
        except Exception as e:
            console.print(f"[red]Export error: {e}[/red]")

class ProfileValidator:
    """Validate and verify profile data quality"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def validate_profile_data(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate profile data quality and completeness"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'quality_score': 100
        }
        
        # Check required fields
        required_fields = ['username', 'follower_count', 'post_count', 'bio']
        for field in required_fields:
            if not profile_data.get(field):
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['quality_score'] -= 20
        
        # Validate follower count
        follower_count = profile_data.get('follower_count', 0)
        if follower_count == 0:
            validation_result['warnings'].append("Zero follower count")
            validation_result['quality_score'] -= 10
        elif follower_count > 10000000:  # 10M
            validation_result['warnings'].append("Unusually high follower count (possible celebrity)")
            validation_result['quality_score'] -= 5
        
        # Validate engagement rate
        engagement_rate = profile_data.get('engagement_rate', 0)
        if engagement_rate > 20:
            validation_result['warnings'].append("Very high engagement rate (possible bot activity)")
            validation_result['quality_score'] -= 15
        elif engagement_rate < 0.1 and follower_count > 1000:
            validation_result['warnings'].append("Very low engagement rate (possible inactive account)")
            validation_result['quality_score'] -= 10
        
        # Validate bio content
        bio = profile_data.get('bio', '')
        if len(bio) < 10:
            validation_result['warnings'].append("Very short bio")
            validation_result['quality_score'] -= 5
        
        # Check for suspicious patterns
        suspicious_keywords = ['bot', 'fake', 'spam', 'test account']
        if any(keyword in bio.lower() for keyword in suspicious_keywords):
            validation_result['warnings'].append("Suspicious keywords in bio")
            validation_result['quality_score'] -= 10
        
        # Set validity based on errors
        if validation_result['errors']:
            validation_result['is_valid'] = False
        
        return validation_result

class SessionRecovery:
    """Handle session recovery and state management"""
    
    def __init__(self, session_file: str, logger):
        self.session_file = session_file
        self.logger = logger
    
    def backup_session(self):
        """Create backup of current session"""
        try:
            if os.path.exists(self.session_file):
                backup_file = f"{self.session_file}.backup_{int(time.time())}"
                import shutil
                shutil.copy2(self.session_file, backup_file)
                self.logger.info(f"Session backed up to {backup_file}")
        except Exception as e:
            self.logger.error(f"Failed to backup session: {e}")
    
    def recover_from_backup(self, backup_file: str) -> bool:
        """Recover session from backup file"""
        try:
            if os.path.exists(backup_file):
                import shutil
                shutil.copy2(backup_file, self.session_file)
                self.logger.success(f"Session recovered from {backup_file}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to recover session: {e}")
        
        return False
    
    def clean_old_backups(self, max_age_days: int = 7):
        """Clean up old backup files"""
        try:
            backup_pattern = f"{self.session_file}.backup_"
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            
            for file in os.listdir('.'):
                if file.startswith(backup_pattern):
                    file_path = os.path.join('.', file)
                    if os.path.getctime(file_path) < (current_time - max_age_seconds):
                        os.remove(file_path)
                        self.logger.info(f"Cleaned up old backup: {file}")
        except Exception as e:
            self.logger.warning(f"Backup cleanup warning: {e}")

class ProxyTester:
    """Test and validate proxy functionality"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def test_proxy(self, proxy_dict: Dict[str, str], timeout: int = 10) -> bool:
        """Test individual proxy connectivity"""
        try:
            test_url = "http://httpbin.org/ip"
            response = requests.get(test_url, proxies=proxy_dict, timeout=timeout)
            
            if response.status_code == 200:
                self.logger.info(f"Proxy test successful: {proxy_dict.get('http', 'Unknown proxy')}")
                return True
            else:
                self.logger.warning(f"Proxy test failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.warning(f"Proxy test error: {e}")
            return False
    
    def test_all_proxies(self, proxy_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Test all proxies and return working ones"""
        working_proxies = []
        
        console.print(f"[cyan]Testing {len(proxy_list)} proxies...[/cyan]")
        
        for i, proxy in enumerate(proxy_list, 1):
            console.print(f"Testing proxy {i}/{len(proxy_list)}...", end="")
            
            if self.test_proxy(proxy):
                working_proxies.append(proxy)
                console.print(" [green]✓[/green]")
            else:
                console.print(" [red]✗[/red]")
        
        console.print(f"[green]Found {len(working_proxies)} working proxies out of {len(proxy_list)}[/green]")
        return working_proxies

def generate_user_report(csv_file: str):
    """Generate user-friendly report from results"""
    try:
        analyzer = DataAnalyzer(csv_file)
        analyzer.generate_analytics_report()
    except Exception as e:
        console.print(f"[red]Report generation error: {e}[/red]")

def validate_system_requirements():
    """Validate system requirements and dependencies"""
    console.print(Panel.fit("🔍 System Requirements Check", style="bold blue"))
    
    requirements = {
        'Python': sys.version_info >= (3, 8),
        'ChromeDriver': check_chromedriver(),
        'Required Packages': check_required_packages()
    }
    
    table = Table(title="System Check Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    for component, status in requirements.items():
        if status:
            table.add_row(component, "✓ OK", "Available")
        else:
            table.add_row(component, "✗ FAIL", "Missing or incompatible")
    
    console.print(table)
    
    all_good = all(requirements.values())
    if all_good:
        console.print("[green]✓ All system requirements satisfied[/green]")
    else:
        console.print("[red]⚠ Some requirements not met. Please install missing components.[/red]")
    
    return all_good

def check_chromedriver() -> bool:
    """Check if ChromeDriver is available"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        driver.quit()
        return True
    except Exception:
        return False

def check_required_packages() -> bool:
    """Check if all required packages are installed"""
    required_packages = [
        'selenium', 'requests', 'pandas', 'nltk', 
        'textblob', 'colorama', 'rich'
    ]
    
    try:
        for package in required_packages:
            __import__(package)
        return True
    except ImportError:
        return False

def create_sample_data():
    """Create sample data for testing purposes"""
    sample_data = [
        {
            'username': 'sample_user1',
            'follower_count': 15000,
            'following_count': 1200,
            'post_count': 250,
            'bio': 'Travel enthusiast from California 🌴 ✈️',
            'profile_url': 'https://instagram.com/sample_user1',
            'has_active_story': True,
            'location': 'California, USA',
            'is_verified': False,
            'is_private': False,
            'engagement_rate': 3.5,
            'estimated_gender': 'female',
            'bio_language': 'en',
            'reason_for_selection': 'USA location confirmed: california; Active story confirmed; Normal engagement rate: 3.50%',
            'source_hvt': 'initial_seed',
            'discovery_timestamp': datetime.now().isoformat()
        },
        {
            'username': 'sample_user2', 
            'follower_count': 8500,
            'following_count': 800,
            'post_count': 180,
            'bio': 'NYC fitness coach 💪 DM for training tips',
            'profile_url': 'https://instagram.com/sample_user2',
            'has_active_story': True,
            'location': 'New York, NY',
            'is_verified': False,
            'is_private': False,
            'engagement_rate': 4.2,
            'estimated_gender': 'male',
            'bio_language': 'en',
            'reason_for_selection': 'USA location confirmed: nyc; Active story confirmed; Normal engagement rate: 4.20%',
            'source_hvt': 'sample_user1',
            'discovery_timestamp': datetime.now().isoformat()
        }
    ]
    
    # Write sample data to CSV
    with open('sample_hunter_results.csv', 'w', newline='', encoding='utf-8') as f:
        fieldnames = sample_data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)
    
    console.print("[green]Sample data created: sample_hunter_results.csv[/green]")

if __name__ == "__main__":
    
    # Command line utility functions
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'check':
            validate_system_requirements()
        elif command == 'report' and len(sys.argv) > 2:
            generate_user_report(sys.argv[2])
        elif command == 'sample':
            create_sample_data()
        else:
            console.print("Available commands:")
            console.print("  python utilities.py check      - Check system requirements")  
            console.print("  python utilities.py report <csv_file>  - Generate analytics report")
            console.print("  python utilities.py sample     - Create sample data")
    else:
        console.print("Hunter_v7 Utilities - Use with command line arguments")
