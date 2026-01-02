"""
Hunter_v7 Scraping Engine
Advanced web scraping with proxy rotation, rate limiting, and bot detection avoidance
"""
import os
import time
import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

from hunter_v7 import UserProfile, Logger, ConfigManager
from hunter_core import ProfileFilter, SessionManager, BioAnalyzer, LocationValidator

class ScrapingEngine:
    """Advanced scraping engine with human-like behavior simulation"""
    
    def __init__(self, config: ConfigManager, logger: Logger, proxy_manager, session_manager: SessionManager):
        self.config = config
        self.logger = logger
        self.proxy_manager = proxy_manager
        self.session_manager = session_manager
        self.driver = None
        self.current_proxy = None
        self.request_count = 0
        self.last_request_time = 0
        
        # Initialize analysis components
        self.location_validator = LocationValidator(logger)
        self.bio_analyzer = BioAnalyzer(logger)
        self.profile_filter = ProfileFilter(config, logger, self.location_validator, self.bio_analyzer)
        
        # Scraping parameters
        self.min_delay = config.getfloat('SCRAPING', 'min_delay')
        self.max_delay = config.getfloat('SCRAPING', 'max_delay')
        self.max_retries = int(config.get('SCRAPING', 'max_retries'))
        self.timeout = int(config.get('SCRAPING', 'request_timeout'))
        
        # Human behavior patterns
        self.scroll_patterns = [
            'slow_scroll', 'fast_scroll', 'random_scroll', 'pause_scroll'
        ]

    def check_login_status(self, timeout: int = 10) -> bool:
        """
        Checks if a valid login session already exists by loading the home page.
        """
        self.logger.info("Checking for an existing login session...")
        try:
            self.driver.get("https://www.instagram.com/")

            # If we are immediately redirected to the login page, we are not logged in.
            if "accounts/login" in self.driver.current_url:
                self.logger.info("No active session found. A new login is required.")
                return False

            # As a more reliable check, look for a key element that only appears when logged in,
            # like the "Home" icon's link or the "Messages" icon.
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='/']"))
            )
            self.logger.success("✅ Active login session found. Skipping login.")
            return True

        except Exception:
            self.logger.info("Session appears to be invalid or expired. A new login is required.")
            return False

    def initialize_driver(self) -> bool:
        """Initialize Selenium WebDriver with proxy and stealth settings"""
        try:
            options = Options()
            
            # Stealth settings
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # Load the persistent browser profile to reuse login sessions
            user_data_path = self.config.get('SCRAPING', 'user_data_dir', fallback='browser_profile')
            options.add_argument(f'--user-data-dir={os.path.join(os.getcwd(), user_data_path)}')
            
            # Random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # Proxy configuration
            if self.proxy_manager and self.config.getboolean('SCRAPING', 'use_proxies'):
                self.current_proxy = self.proxy_manager.get_next_proxy()
                if self.current_proxy:
                    proxy_url = self.current_proxy['http'].replace('http://', '')
                    options.add_argument(f'--proxy-server=http://{proxy_url}')
                    self.logger.info(f"Using proxy: {proxy_url}")
            
            # Let Selenium Manager handle the driver automatically
            self.driver = webdriver.Chrome(options=options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.success("WebDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    def human_delay(self, min_extra: float = 0, max_extra: float = 2):
        """Implement human-like delays"""
        base_delay = random.uniform(self.min_delay, self.max_delay)
        extra_delay = random.uniform(min_extra, max_extra)
        total_delay = base_delay + extra_delay
        
        self.logger.info(f"Human delay: {total_delay:.2f}s")
        time.sleep(total_delay)
    
    def simulate_human_behavior(self):
        """Simulate human-like browsing behavior"""
        try:
            # Random scrolling
            scroll_type = random.choice(self.scroll_patterns)
            
            if scroll_type == 'slow_scroll':
                for _ in range(random.randint(2, 5)):
                    self.driver.execute_script("window.scrollBy(0, 200);")
                    time.sleep(random.uniform(0.5, 1.5))
            
            elif scroll_type == 'fast_scroll':
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(random.uniform(0.2, 0.8))
            
            elif scroll_type == 'random_scroll':
                scroll_amount = random.randint(-300, 800)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(0.3, 1.2))
            
            # Random mouse movements (if needed)
            if random.random() < 0.3:  # 30% chance
                try:
                    action = ActionChains(self.driver)
                    action.move_by_offset(random.randint(-50, 50), random.randint(-50, 50))
                    action.perform()
                except:
                    pass  # Ignore mouse movement errors
                    
        except Exception as e:
            self.logger.warning(f"Human behavior simulation error: {e}")
    
    def login_to_instagram(self, username: str, password: str) -> bool:
        """Login to Instagram with retry logic"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Login attempt {attempt + 1}/{max_attempts}")
                
                # Navigate to Instagram
                self.driver.get("https://www.instagram.com/accounts/login/")
                self.human_delay(2, 5)
                
                # Handle cookies popup if present
                try:
                    cookies_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Only allow essential cookies') or contains(text(), 'Accept')]"))
                    )
                    cookies_button.click()
                    self.human_delay(1, 2)
                except TimeoutException:
                    pass  # No cookies popup
                
                # Find and fill username
                username_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                
                # Type username character by character
                for char in username:
                    username_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                self.human_delay(0.5, 1.5)
                
                # Find and fill password
                password_field = self.driver.find_element(By.NAME, "password")
                
                # Type password character by character
                for char in password:
                    password_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                self.human_delay(1, 2)
                
                # Click login button
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                
                # Wait for login to complete
                self.human_delay(3, 6)
                
                # Check for successful login
                if "instagram.com" in self.driver.current_url and "login" not in self.driver.current_url:
                    self.logger.success("Successfully logged in to Instagram")
                    
                    # Handle "Save Your Login Info" popup
                    try:
                        not_now_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                        )
                        not_now_button.click()
                        self.human_delay(1, 2)
                    except TimeoutException:
                        pass
                    
                    # Handle notifications popup
                    try:
                        not_now_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                        )
                        not_now_button.click()
                        self.human_delay(1, 2)
                    except TimeoutException:
                        pass
                    
                    return True
                else:
                    self.logger.warning("Login may have failed, checking for errors...")
                    
                    # Check for error messages
                    try:
                        error_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'error') or contains(text(), 'incorrect')]")
                        error_text = error_element.text
                        self.logger.error(f"Login error: {error_text}")
                        
                        if "incorrect" in error_text.lower():
                            self.logger.error("Invalid credentials provided")
                            return False
                    except NoSuchElementException:
                        pass
            
            except Exception as e:
                self.logger.error(f"Login attempt {attempt + 1} failed: {e}")
                
                if attempt < max_attempts - 1:
                    self.logger.info("Retrying login...")
                    self.human_delay(5, 10)  # Longer delay before retry
                    
                    # Rotate proxy if available
                    if self.proxy_manager and self.current_proxy:
                        self.proxy_manager.mark_proxy_failed(self.current_proxy)
                        self.logger.info("Rotating proxy for retry...")
                        self.cleanup_driver()
                        if not self.initialize_driver():
                            continue
        
        self.logger.error("All login attempts failed")
        return False
    
    def get_profiles_from_hashtags(self, hashtags: list[str], limit_per_hashtag: int = 5) -> list[str]:
        """
        Scrapes Instagram hashtag pages to find usernames from top posts.
        Returns a list of unique usernames to use as seed profiles.
        """
        self.logger.info(f"Searching for seed profiles from hashtags: {', '.join(hashtags)}")
        seed_profiles = set()
    
        for tag in hashtags:
            try:
                # 1. Navigate to the hashtag page
                url = f"https://www.instagram.com/explore/tags/{tag.strip()}/"
                self.driver.get(url)
                self.human_delay(2, 4)
                
                self.logger.info(f"Scraping top posts for #{tag}...")
                # 2. Scrape the links to the first few posts from the "Top posts" section
                # This XPath targets links to posts within the main article grid.
                post_links = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//article//a[@href]"))
                )
                
                # Limit to the top posts to get high-quality seeds
                links_to_visit = [link.get_attribute('href') for link in post_links[:limit_per_hashtag]]

                # 3. Visit each post and get the author's username
                for i, post_url in enumerate(links_to_visit):
                    self.logger.info(f"Analyzing post {i+1}/{len(links_to_visit)} from #{tag}")
                    self.driver.get(post_url)
                    self.human_delay(1.5, 3.5)
                    
                    try:
                        # This XPath targets the author's username link in the post header.
                        author_element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//header//div/div/a"))
                        )
                        username = author_element.text
                        if username and username not in seed_profiles:
                            self.logger.info(f"Found potential seed profile: @{username}")
                            seed_profiles.add(username)
                            
                    except TimeoutException:
                        self.logger.warning(f"Could not find author on post: {post_url}")
            
            except Exception as e:
                self.logger.error(f"Failed to scrape hashtag #{tag}: {e}")
        
        self.logger.success(f"Collected {len(seed_profiles)} unique seed profiles.")
        return list(seed_profiles)
        
    
    def get_profile_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Extract comprehensive profile data"""
        try:
            profile_url = f"https://www.instagram.com/{username}/"
            self.logger.info(f"Scraping profile: @{username}")
            
            self.driver.get(profile_url)
            self.human_delay(2, 4)
            
            # Check if profile exists
            if "Page Not Found" in self.driver.page_source or "Sorry, this page isn't available" in self.driver.page_source:
                self.logger.warning(f"Profile @{username} not found")
                return None
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Extract profile data
            profile_data = {
                'username': username,
                'profile_url': profile_url,
                'follower_count': 0,
                'following_count': 0,
                'post_count': 0,
                'bio': '',
                'location': '',
                'is_verified': False,
                'is_private': False,
                'profile_pic_url': '',
                'has_active_story': False,
                'last_post_date': None,
                'engagement_rate': 0.0
            }
            
            # Extract follower, following, and post counts
            try:
                stats_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/followers/') or contains(@href, '/following/')]/span | //div[contains(text(), 'posts')]/span")
                
                for element in stats_elements:
                    text = element.text.replace(',', '').replace('K', '000').replace('M', '000000')
                    parent_text = element.find_element(By.XPATH, "..").text.lower()
                    
                    if 'follower' in parent_text:
                        profile_data['follower_count'] = self.parse_count(text)
                    elif 'following' in parent_text:
                        profile_data['following_count'] = self.parse_count(text)
                    elif 'post' in parent_text:
                        profile_data['post_count'] = self.parse_count(text)
            
            except Exception as e:
                self.logger.warning(f"Could not extract stats for @{username}: {e}")
            
            # Extract bio
            try:
                bio_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'bio') or @data-testid='user-bio']")
                profile_data['bio'] = bio_element.text
            except NoSuchElementException:
                try:
                    # Alternative bio selector
                    bio_element = self.driver.find_element(By.XPATH, "//span[contains(@class, '_ap3a')]")
                    profile_data['bio'] = bio_element.text
                except NoSuchElementException:
                    pass
            
            # Check for verification badge
            try:
                verified_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'verified') or @title='Verified']")
                profile_data['is_verified'] = True
            except NoSuchElementException:
                pass
            
            # Check if profile is private
            try:
                private_element = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'This Account is Private')]")
                profile_data['is_private'] = True
            except NoSuchElementException:
                pass
            
            # Check for active story
            try:
                story_element = self.driver.find_element(By.XPATH, "//canvas[@role='button'] | //img[contains(@style, 'background-image') and contains(@alt, 'story')]")
                profile_data['has_active_story'] = True
                self.logger.info(f"Active story detected for @{username}")
            except NoSuchElementException:
                self.logger.info(f"No active story for @{username}")
            
            # Extract profile picture URL
            try:
                profile_pic = self.driver.find_element(By.XPATH, "//img[contains(@alt, 'profile picture')]")
                profile_data['profile_pic_url'] = profile_pic.get_attribute('src')
            except NoSuchElementException:
                pass
            
            # Calculate engagement rate (simplified)
            if not profile_data['is_private'] and profile_data['post_count'] > 0:
                try:
                    # Get engagement from recent posts (simplified calculation)
                    posts = self.driver.find_elements(By.XPATH, "//article//a[@href]")[:9]  # Recent 9 posts
                    total_engagement = 0
                    post_count = 0
                    
                    for post in posts[:3]:  # Check first 3 posts to avoid being too aggressive
                        try:
                            post.click()
                            self.human_delay(1, 2)
                            
                            # Extract likes (this is a simplified approach)
                            likes_element = self.driver.find_element(By.XPATH, "//button[contains(@class, 'like')]/following-sibling::div | //span[contains(text(), 'likes')]")
                            likes_text = likes_element.text
                            likes = self.parse_count(likes_text.split()[0])
                            
                            total_engagement += likes
                            post_count += 1
                            
                            # Close post
                            close_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Close']")
                            close_button.click()
                            self.human_delay(0.5, 1)
                            
                        except Exception as e:
                            self.logger.warning(f"Could not get engagement for post: {e}")
                            break
                    
                    if post_count > 0 and profile_data['follower_count'] > 0:
                        avg_engagement = total_engagement / post_count
                        profile_data['engagement_rate'] = (avg_engagement / profile_data['follower_count']) * 100
                
                except Exception as e:
                    self.logger.warning(f"Could not calculate engagement rate: {e}")
            
            self.session_manager.increment_scanned()
            return profile_data
            
        except Exception as e:
            self.logger.error(f"Error scraping profile @{username}: {e}")
            self.session_manager.increment_errors()
            return None
    
    def parse_count(self, count_str: str) -> int:
        """Parse follower/following/post count strings"""
        try:
            count_str = count_str.replace(',', '').replace(' ', '')
            
            if 'K' in count_str:
                return int(float(count_str.replace('K', '')) * 1000)
            elif 'M' in count_str:
                return int(float(count_str.replace('M', '')) * 1000000)
            else:
                return int(count_str)
        except (ValueError, TypeError):
            return 0
    
    def get_followers(self, username: str, limit: int = 100) -> List[str]:
        """Extract followers list from a profile"""
        try:
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            self.human_delay(2, 4)
            
            # Click followers link
            followers_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers/')]"))
            )
            followers_link.click()
            self.human_delay(2, 4)
            
            # Scroll and collect followers
            followers = set()
            scroll_attempts = 0
            max_scroll_attempts = limit // 12  # Approximately 12 followers per scroll
            
            while len(followers) < limit and scroll_attempts < max_scroll_attempts:
                try:
                    # Find follower elements
                    follower_elements = self.driver.find_elements(By.XPATH, "//div[@role='dialog']//a[contains(@href, '/')]")
                    
                    for element in follower_elements:
                        href = element.get_attribute('href')
                        if href and 'instagram.com/' in href:
                            username_from_href = href.split('/')[-2] if href.endswith('/') else href.split('/')[-1]
                            if username_from_href and len(username_from_href) > 0:
                                followers.add(username_from_href)
                    
                    # Scroll down
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", 
                                                self.driver.find_element(By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]"))
                    
                    self.human_delay(1, 3)
                    scroll_attempts += 1
                    
                    if len(followers) % 20 == 0:
                        self.logger.info(f"Collected {len(followers)} followers so far...")
                
                except Exception as e:
                    self.logger.warning(f"Error during follower collection: {e}")
                    break
            
            # Close followers dialog
            try:
                close_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Close']")
                close_button.click()
                self.human_delay(1, 2)
            except:
                pass
            
            followers_list = list(followers)[:limit]
            self.logger.success(f"Collected {len(followers_list)} followers from @{username}")
            return followers_list
            
        except Exception as e:
            self.logger.error(f"Error getting followers for @{username}: {e}")
            return []
    
    def cleanup_driver(self):
        """Clean up WebDriver resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.logger.info("WebDriver cleaned up")
        except Exception as e:
            self.logger.warning(f"Error during driver cleanup: {e}")
