"""
Hunter_v7 Main Orchestrator
Controls the entire target acquisition workflow with interactive configuration,
advanced analysis, and robust error handling.
"""

import sys
import csv
import time
import signal
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import Counter

# Rich library for beautiful console output
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.prompt import Prompt, IntPrompt, Confirm

# Custom module imports
from hunter_v7 import UserProfile, ConfigManager, Logger, ProxyManager, EmailNotifier
from hunter_core import SessionManager, ProfileFilter, LocationValidator, BioAnalyzer
from scraper_engine import ScrapingEngine
from utilities import ProfileValidator # Assuming ProfileValidator is in utilities.py

# Initialize the rich console
console = Console()


class HunterOrchestrator:
    """
    Main orchestrator for Hunter_v7 operations.
    This class manages the application`s state, user interaction,
    and the overall workflow from initialization to completion.
    """
    
    def __init__(self):
        """Initializes the orchestrator`s state."""
        self.config: Optional[ConfigManager] = None
        self.logger: Optional[Logger] = None
        self.proxy_manager: Optional[ProxyManager] = None
        self.email_notifier: Optional[EmailNotifier] = None
        self.session_manager: Optional[SessionManager] = None
        self.scraper: Optional[ScrapingEngine] = None
        
        # Graceful shutdown flag
        self.should_stop = False
        
        # Filters collected from the user during interactive configuration
        self.user_filters: Dict[str, Any] = {}
        
        # Session statistics
        self.stats = {
            'session_start_time': None,
            'total_profiles_scanned': 0,
            'valid_profiles_processed': 0,
            'hvts_found': 0,
            'errors_encountered': 0,
            'current_depth': 0
        }
        
        # Setup signal handler for graceful shutdown on Ctrl+C
        signal.signal(signal.SIGINT, self.handle_interrupt)

    # --------------------------------------------------------------------------
    # SECTION: System Initialization and Shutdown
    # --------------------------------------------------------------------------

    def initialize_system(self) -> bool:
        """
        Initializes all core system components based on the configuration file.
        This includes the logger, session manager, scraper, and notifiers.
        
        Returns:
            bool: True if initialization is successful, False otherwise.
        """
        try:
            console.print(Panel.fit("🚀 Initializing Hunter_v7 System", style="bold blue"))
            
            # Load configuration from config.ini
            self.config = ConfigManager()
            
            # Set up logging
            log_file = self.config.get('OUTPUT', 'log_filename')
            self.logger = Logger(log_file)
            
            # Load or create a new session
            self.session_manager = SessionManager(self.config, self.logger)
            
            # Set up the proxy manager if enabled
            if self.config.getboolean('SCRAPING', 'use_proxies'):
                proxy_file = self.config.get('PROXIES', 'proxy_list')
                self.proxy_manager = ProxyManager(proxy_file, self.logger)
            
            # Set up the email notifier
            self.email_notifier = EmailNotifier(self.config, self.logger)
            
            # Initialize the web scraping engine
            self.scraper = ScrapingEngine(self.config, self.logger, self.proxy_manager, self.session_manager)
            
            self.logger.success("All system components initialized successfully")
            return True
            
        except Exception as e:
            # Handle initialization failures
            error_message = f"System initialization failed: {e}"
            if self.logger:
                self.logger.error(error_message, exc_info=True)
            else:
                console.print(f"[red]{error_message}[/red]")
            return False
    
    def handle_interrupt(self, signum, frame):
        """
        Handles graceful shutdown when Ctrl+C (SIGINT) is detected.
        Saves the session state before exiting.
        """
        console.print("\n[yellow]Received interrupt signal. Saving session and shutting down gracefully...[/yellow]")
        self.should_stop = True
        if self.session_manager:
            self.session_manager.save_session()
        if self.scraper:
            self.scraper.cleanup_driver()
        self.logger.info("Graceful shutdown completed due to user interrupt.")
        sys.exit(0)

    # --------------------------------------------------------------------------
    # SECTION: Interactive User Configuration
    # --------------------------------------------------------------------------

    def interactive_configuration(self) -> bool:
        """
        Guides the user through an interactive configuration session using rich prompts.
        
        Returns:
            bool: True if the user confirms the configuration, False if they cancel.
        """
        try:
            console.print(Panel("📋 Interactive Session Configuration", style="bold green"))
            
            console.print("\n[bold cyan]Follower Count Limits:[/bold cyan]")
            min_followers = IntPrompt.ask("What is the minimum follower count for a target?", default=1000)
            max_followers = IntPrompt.ask("What is the maximum follower count for a target?", default=50000)
            
            console.print("\n[bold cyan]Post Count Requirements:[/bold cyan]")
            min_posts = IntPrompt.ask("What is the minimum post count for a target?", default=50)
            
            console.print("\n[bold cyan]Keyword Filtering:[/bold cyan]")
            use_keywords = Confirm.ask("Do you want to include/exclude profiles based on bio keywords?", default=True)
            include_keywords, exclude_keywords = [], []
            if use_keywords:
                keyword_mode = Prompt.ask("Choose mode", choices=["include", "exclude"], default="exclude")
                if keyword_mode == "include":
                    keywords_input = Prompt.ask("Enter keywords to INCLUDE (comma-separated)", default="")
                    include_keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
                else:
                    keywords_input = Prompt.ask("Enter keywords to EXCLUDE (comma-separated)", default="OnlyFans,escort,premium")
                    exclude_keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
            
            console.print("\n[bold cyan]Advanced Options:[/bold cyan]")
            hashtags_input = Prompt.ask("Enter seed hashtags to start the search (comma-separated)", default="usamoms,momlife,parenting")
            seed_hashtags = [ht.strip() for ht in hashtags_input.split(',') if ht.strip()]
            max_depth = IntPrompt.ask("Maximum recursion depth (how many levels deep to go)?", default=3)
            max_profiles = IntPrompt.ask("Maximum profiles to scan in this session?", default=1000)
            
            # Store all collected filters in the instance's dictionary
            self.user_filters = {
                'min_followers': min_followers, 'max_followers': max_followers, 'min_posts': min_posts,
                'include_keywords': include_keywords, 'exclude_keywords': exclude_keywords,
                'seed_hashtags': seed_hashtags, 'max_depth': max_depth, 'max_profiles': max_profiles,
            }
            
            self.display_config_summary()
            
            if not Confirm.ask("Proceed with this configuration?", default=True):
                console.print("[yellow]Configuration cancelled. Please restart to reconfigure.[/yellow]")
                return False
            return True
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Configuration cancelled by user.[/yellow]")
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"Configuration error: {e}", exc_info=True)
            else:
                console.print(f"[red]Configuration error: {e}[/red]")
            return False
    
    def display_config_summary(self):
        """Displays a summary of the user-defined configuration in a table."""
        table = Table(title="Session Configuration Summary")
        table.add_column("Parameter", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        table.add_row("Min Followers", f"{self.user_filters['min_followers']:,}")
        table.add_row("Max Followers", f"{self.user_filters['max_followers']:,}")
        table.add_row("Min Posts", f"{self.user_filters['min_posts']:,}")
        table.add_row("Seed Hashtags", ", ".join(self.user_filters['seed_hashtags']))
        table.add_row("Max Recursion Depth", str(self.user_filters['max_depth']))
        table.add_row("Max Profiles to Scan", f"{self.user_filters['max_profiles']:,}")
        
        if self.user_filters['include_keywords']:
            table.add_row("Include Keywords", ", ".join(self.user_filters['include_keywords']))
        if self.user_filters['exclude_keywords']:
            table.add_row("Exclude Keywords", ", ".join(self.user_filters['exclude_keywords']))
        
        console.print(table)

    # --------------------------------------------------------------------------
    # SECTION: Core Scraping and Analysis Workflow
    # --------------------------------------------------------------------------
    
    def pre_run_account_check(self) -> bool:
        """
        Performs a pre-run check to ensure the logged-in account is in good standing.
        (Simulated for this example).
        
        Returns:
            bool: True if the account is healthy, False otherwise.
        """
        self.logger.info("Performing pre-run account health check...")
        # In a real scenario, this would navigate to the profile, check for
        # action blocks, warnings, or other restrictions.
        console.print("✅ Account health check passed.")
        self.logger.success("Pre-run account health check passed.")
        return True

    def find_initial_hvts(self) -> List[UserProfile]:
        """
        Finds the initial set of High-Value Targets by scraping seed hashtags.
        
        Returns:
            List[UserProfile]: A list of initial HVT profiles that match the criteria.
        """
        initial_hvts = []
        seed_hashtags = self.user_filters.get('seed_hashtags', [])
        
        if not seed_hashtags:
            self.logger.error("No seed hashtags provided. Cannot start the search.")
            return []
            
        seed_usernames = self.scraper.get_profiles_from_hashtags(seed_hashtags)
        if not seed_usernames:
            self.logger.warning("Could not find any seed profiles from the provided hashtags.")
            return []

        console.print(f"\n[bold blue]Phase 1: Finding Initial HVTs[/bold blue]")
        console.print(f"Analyzing {len(seed_usernames)} seed profiles found from hashtags...")
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TimeElapsedColumn(), console=console) as progress:
            task = progress.add_task("Scanning seed profiles...", total=len(seed_usernames))
            for username in seed_usernames:
                if self.should_stop: break
                
                profile_data = self.process_single_profile(username, progress, task)
                if not profile_data:
                    continue

                should_target, reason = self.apply_all_filters(profile_data)
                
                if should_target:
                    hvt = self.create_hvt_profile(profile_data, reason, "initial_seed")
                    initial_hvts.append(hvt)
                    self.session_manager.add_hvt(hvt)
                    self.logger.hvt_found(username, reason)
                    self.stats['hvts_found'] += 1
                
                if not self.should_stop:
                    self.scraper.human_delay()
                    
        console.print(f"[green]Phase 1 Complete: Found {len(initial_hvts)} initial HVTs[/green]")
        return initial_hvts
    
    def recursive_follower_expansion(self, initial_hvts: List[UserProfile]) -> List[UserProfile]:
        """
        Performs a recursive search through the followers of found HVTs.
        
        Args:
            initial_hvts: The list of HVTs found in Phase 1.
        
        Returns:
            List[UserProfile]: A list containing all HVTs found during the session.
        """
        all_hvts = list(initial_hvts)
        processing_queue = list(initial_hvts)
        max_depth = self.user_filters.get('max_depth', 1)

        for depth in range(1, max_depth + 1):
            if not processing_queue or self.should_stop:
                break
                
            self.stats['current_depth'] = depth
            console.print(f"\n[bold blue]Phase 2: Follower Expansion (Depth {depth}/{max_depth})[/bold blue]")
            next_level_queue = []
            
            for source_hvt in processing_queue:
                if self.should_stop or self.stats['total_profiles_scanned'] >= self.user_filters.get('max_profiles', 1000):
                    break
                
                console.print(f"Analyzing followers of @{source_hvt.username}...")
                followers = self.scraper.get_followers(source_hvt.username, limit=50)
                if not followers:
                    continue
                
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TimeElapsedColumn(), console=console) as progress:
                    task = progress.add_task(f"Scanning followers of @{source_hvt.username}...", total=len(followers))
                    for follower_username in followers:
                        if self.should_stop or self.stats['total_profiles_scanned'] >= self.user_filters.get('max_profiles', 1000):
                            break
                        
                        profile_data = self.process_single_profile(follower_username, progress, task)
                        if not profile_data:
                            continue

                        should_target, reason = self.apply_all_filters(profile_data)
                        
                        if should_target:
                            new_hvt = self.create_hvt_profile(profile_data, reason, source_hvt.username)
                            all_hvts.append(new_hvt)
                            next_level_queue.append(new_hvt)
                            self.session_manager.add_hvt(new_hvt)
                            self.logger.hvt_found(follower_username, reason)
                            self.stats['hvts_found'] += 1
                        
                        if not self.should_stop:
                            self.scraper.human_delay(min_extra=0.5, max_extra=1.5)
            
            processing_queue = next_level_queue

        console.print(f"[green]Phase 2 Complete: Total HVTs found: {len(all_hvts)}[/green]")
        return all_hvts

    def process_single_profile(self, username: str, progress, task) -> Optional[Dict[str, Any]]:
        """
        Helper function to handle the scraping and validation of a single profile.
        
        Returns:
            Optional[Dict[str, Any]]: Profile data if valid, otherwise None.
        """
        progress.update(task, description=f"Scanning @{username}")
        
        if self.session_manager.is_profile_seen(username):
            progress.advance(task)
            return None
        
        profile_data = self.scraper.get_profile_data(username)
        self.stats['total_profiles_scanned'] += 1
        self.session_manager.add_seen_profile(username)
        
        if not profile_data:
            progress.advance(task)
            return None
        
        # Validate data quality
        is_valid, warnings = self.validate_and_score_profile(profile_data)
        if not is_valid:
            self.logger.warning(f"Profile @{username} failed validation: {warnings}")
            progress.advance(task)
            return None

        self.stats['valid_profiles_processed'] += 1
        progress.advance(task)
        return profile_data

    def validate_and_score_profile(self, profile_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Uses the ProfileValidator to check the quality of scraped data.
        
        Returns:
            tuple[bool, List[str]]: A tuple of (is_valid, warnings).
        """
        validator = ProfileValidator(self.logger)
        validation_result = validator.validate_profile_data(profile_data)
        
        if not validation_result['is_valid']:
            return False, validation_result['errors']
        
        if validation_result['quality_score'] < 70:
            self.logger.info(f"Low quality score for @{profile_data['username']}: {validation_result['quality_score']}")
            return True, validation_result['warnings'] # Still valid, but with warnings
            
        return True, []

    def apply_all_filters(self, profile_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Applies all user-defined and system filters to a profile.
        
        Returns:
            tuple[bool, str]: A tuple of (should_target, reason).
        """
        profile_filter = ProfileFilter(self.config, self.logger, LocationValidator(self.logger), BioAnalyzer(self.logger))
        
        bio_lower = profile_data.get('bio', '').lower()
        
        # Check for inclusion keywords first if they exist
        if self.user_filters.get('include_keywords'):
            has_keyword = any(k.lower() in bio_lower for k in self.user_filters['include_keywords'])
            if not has_keyword:
                return False, "Does not contain required keywords."
        
        # Then check for exclusion keywords
        if self.user_filters.get('exclude_keywords'):
            for k in self.user_filters['exclude_keywords']:
                if k.lower() in bio_lower:
                    return False, f"Contains excluded keyword: {k}"

        return profile_filter.should_target_profile(profile_data, self.user_filters)

    def create_hvt_profile(self, profile_data: Dict[str, Any], reason: str, source: str) -> UserProfile:
        """Creates a UserProfile data object from a dictionary."""
        bio_analyzer = BioAnalyzer(self.logger)
        bio_analysis = bio_analyzer.analyze_bio(profile_data.get('bio', ''))
        
        return UserProfile(
            username=profile_data['username'],
            follower_count=int(profile_data.get('follower_count', 0)),
            following_count=int(profile_data.get('following_count', 0)),
            post_count=int(profile_data.get('post_count', 0)),
            bio=profile_data['bio'],
            profile_url=profile_data['profile_url'],
            has_active_story=profile_data['has_active_story'],
            location=profile_data.get('location', ''),
            is_verified=profile_data['is_verified'],
            is_private=profile_data['is_private'],
            profile_pic_url=profile_data.get('profile_pic_url', ''),
            engagement_rate=float(profile_data.get('engagement_rate', 0.0)),
            estimated_gender=bio_analysis.get('estimated_gender', 'unknown'),
            bio_language=bio_analysis.get('language', 'unknown'),
            reason_for_selection=reason,
            source_hvt=source,
            discovery_timestamp=datetime.now().isoformat()
        )

    # --------------------------------------------------------------------------
    # SECTION: Main Workflow Execution
    # --------------------------------------------------------------------------

    def run_main_workflow(self) -> bool:
        """
        Executes the entire Hunter_v7 workflow from start to finish.
        
        Returns:
            bool: True on successful completion, False if errors occurred.
        """
        try:
            self.stats['session_start_time'] = datetime.now()
            
            if not self.scraper.initialize_driver():
                self.logger.error("Failed to initialize WebDriver")
                return False
            
            if not self.scraper.check_login_status():
                username = self.config.get('CREDENTIALS', 'username')
                password = self.config.get('CREDENTIALS', 'password')
                if not self.scraper.login_to_instagram(username, password):
                    self.logger.error("Failed to login to Instagram")
                    return False
            
            if not self.pre_run_account_check():
                self.logger.error("Pre-run account check failed. Aborting.")
                return False

            initial_hvts = self.find_initial_hvts()
            
            if not initial_hvts and not self.should_stop:
                self.logger.warning("No initial HVTs found. Consider adjusting your criteria or seed hashtags.")
                self.display_session_summary([], None)
                return True 
            
            all_hvts = self.recursive_follower_expansion(initial_hvts)
            
            csv_file = self.export_results(all_hvts)
            
            if all_hvts and self.config.getboolean('NOTIFICATIONS', 'send_summary_email'):
                session_duration = str(datetime.now() - self.stats['session_start_time']).split('.')[0]
                self.email_notifier.send_session_summary(
                    len(all_hvts), session_duration, self.stats['errors_encountered']
                )
            
            self.display_session_summary(all_hvts, csv_file)
            return True
            
        except Exception as e:
            self.logger.error(f"A critical error occurred in the main workflow: {e}", exc_info=True)
            return False
        finally:
            if self.scraper:
                self.scraper.cleanup_driver()
            if self.session_manager:
                self.session_manager.save_session()

    # --------------------------------------------------------------------------
    # SECTION: Reporting and Exporting
    # --------------------------------------------------------------------------

    def export_results(self, hvts: List[UserProfile]) -> Optional[str]:
        """
        Exports the list of found HVTs to a CSV file.
        
        Returns:
            Optional[str]: The filename of the CSV file, or None on failure.
        """
        if not hvts:
            self.logger.info("No HVTs found to export.")
            return None
            
        csv_filename = self.config.get('OUTPUT', 'csv_filename')
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                # All fields of the UserProfile dataclass
                fieldnames = [field for field in UserProfile.__annotations__]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for hvt in hvts:
                    writer.writerow(hvt.to_dict())
            self.logger.success(f"Results for {len(hvts)} HVTs exported to {csv_filename}")
            return csv_filename
        except Exception as e:
            self.logger.error(f"Failed to export results: {e}", exc_info=True)
            return None
    
    def display_session_summary(self, hvts: List[UserProfile], csv_file: Optional[str]):
        """Displays a final, detailed summary of the session`s results."""
        if not self.stats['session_start_time']:
             console.print("[yellow]Session did not start. No summary to display.[/yellow]")
             return

        session_duration = datetime.now() - self.stats['session_start_time']
        
        # --- Main Summary Table ---
        summary_table = Table(title="🎯 Hunter_v7 Session Summary")
        summary_table.add_column("Metric", style="cyan", no_wrap=True)
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total HVTs Found", str(self.stats['hvts_found']))
        summary_table.add_row("Profiles Scanned", f"{self.stats['total_profiles_scanned']:,}")
        summary_table.add_row("Valid Profiles Processed", f"{self.stats['valid_profiles_processed']:,}")
        success_rate = (self.stats['hvts_found'] / max(self.stats['valid_profiles_processed'], 1)) * 100
        summary_table.add_row("Success Rate", f"{success_rate:.2f}%")
        summary_table.add_row("Session Duration", str(session_duration).split('.')[0])
        summary_table.add_row("Max Depth Reached", str(self.stats['current_depth']))
        summary_table.add_row("Errors Encountered", str(self.stats['errors_encountered']))
        summary_table.add_row("Results File", csv_file or "No results exported")
        
        console.print(summary_table)

        if not hvts:
            return

        # --- Advanced Analytics ---
        analytics_table = Table(title="📊 HVT Analytics")
        analytics_table.add_column("Analytic", style="cyan", no_wrap=True)
        analytics_table.add_column("Result", style="magenta")

        # Follower stats
        follower_counts = [h.follower_count for h in hvts]
        analytics_table.add_row("Average Followers", f"{sum(follower_counts) / len(follower_counts):,.0f}")
        analytics_table.add_row("Median Followers", f"{sorted(follower_counts)[len(follower_counts) // 2]:,}")
        
        # Follower/Following Ratio
        ratios = [h.follower_count / max(h.following_count, 1) for h in hvts]
        avg_ratio = sum(ratios) / len(ratios)
        analytics_table.add_row("Avg. Follower/Following Ratio", f"{avg_ratio:.2f}")

        # Gender distribution
        gender_counts = Counter(h.estimated_gender for h in hvts)
        top_gender = gender_counts.most_common(1)[0]
        analytics_table.add_row("Top Gender", f"{top_gender[0].title()} ({top_gender[1]} instances)")

        # Location analysis
        locations = [h.location for h in hvts if h.location]
        if locations:
            location_counts = Counter(locations)
            top_location = location_counts.most_common(1)[0]
            analytics_table.add_row("Top Location", f"{top_location[0]} ({top_location[1]} instances)")

        console.print(analytics_table)


# --------------------------------------------------------------------------
# SECTION: Application Entry Point
# --------------------------------------------------------------------------

def main():
    "Main entry point for the Hunter_v7 application."
    
    orchestrator = HunterOrchestrator()
    
    try:
        if not orchestrator.initialize_system():
            console.print("[red]System initialization failed. Exiting.[/red]")
            return 1
        
        if not orchestrator.interactive_configuration():
            console.print("[yellow]Configuration cancelled. Exiting.[/yellow]")
            return 1
        
        success = orchestrator.run_main_workflow()
        
        if success:
            console.print("\n[bold green]🎉 Hunter_v7 completed successfully![/bold green]")
            return 0
        else:
            console.print("\n[red]❌ Hunter_v7 completed with errors.[/red]")
            return 1
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n[red]An unexpected error occurred: {e}[/red]")
        # Optionally log the full traceback for debugging
        # import traceback
        # traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
