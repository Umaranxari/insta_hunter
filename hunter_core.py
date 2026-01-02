"""
Hunter_v7 Core Components
Advanced filtering, analysis, and scraping functionality
"""

import os
import re
import time
import random
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import asdict
import nltk
from textblob import TextBlob
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from hunter_v7 import UserProfile, Logger, ConfigManager, ProxyManager, EmailNotifier

class LocationValidator:
    """Advanced USA location validation with multiple verification methods"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.usa_keywords = [
            # States (full names and abbreviations)
            'alabama', 'al', 'alaska', 'ak', 'arizona', 'az', 'arkansas', 'ar',
            'california', 'ca', 'colorado', 'co', 'connecticut', 'ct', 'delaware', 'de',
            'florida', 'fl', 'georgia', 'ga', 'hawaii', 'hi', 'idaho', 'id',
            'illinois', 'il', 'indiana', 'in', 'iowa', 'ia', 'kansas', 'ks',
            'kentucky', 'ky', 'louisiana', 'la', 'maine', 'me', 'maryland', 'md',
            'massachusetts', 'ma', 'michigan', 'mi', 'minnesota', 'mn', 'mississippi', 'ms',
            'missouri', 'mo', 'montana', 'mt', 'nebraska', 'ne', 'nevada', 'nv',
            'new hampshire', 'nh', 'new jersey', 'nj', 'new mexico', 'nm', 'new york', 'ny',
            'north carolina', 'nc', 'north dakota', 'nd', 'ohio', 'oh', 'oklahoma', 'ok',
            'oregon', 'or', 'pennsylvania', 'pa', 'rhode island', 'ri', 'south carolina', 'sc',
            'south dakota', 'sd', 'tennessee', 'tn', 'texas', 'tx', 'utah', 'ut',
            'vermont', 'vt', 'virginia', 'va', 'washington', 'wa', 'west virginia', 'wv',
            'wisconsin', 'wi', 'wyoming', 'wy',
            # Major cities
            'new york city', 'nyc', 'los angeles', 'chicago', 'houston', 'phoenix',
            'philadelphia', 'san antonio', 'san diego', 'dallas', 'san jose', 'austin',
            'jacksonville', 'fort worth', 'columbus', 'charlotte', 'san francisco',
            'indianapolis', 'seattle', 'denver', 'washington dc', 'boston', 'nashville',
            'miami', 'atlanta', 'vegas', 'las vegas', 'detroit', 'portland', 'memphis',
            # General USA identifiers
            'usa', 'united states', 'america', 'us', 'american',
            # Territories
            'puerto rico', 'pr', 'guam', 'virgin islands', 'american samoa'
        ]
        
        self.non_usa_indicators = [
            'uk', 'london', 'england', 'britain', 'canada', 'toronto', 'vancouver',
            'australia', 'sydney', 'melbourne', 'germany', 'berlin', 'france', 'paris',
            'italy', 'spain', 'mexico', 'brazil', 'india', 'mumbai', 'delhi',
            'japan', 'tokyo', 'china', 'beijing', 'russia', 'moscow'
        ]
    
    def is_usa_location(self, bio: str, location_field: str = "") -> Tuple[bool, str]:
        """
        Comprehensive USA location validation
        Returns (is_usa, reason)
        """
        combined_text = f"{bio} {location_field}".lower()
        
        # Check for explicit non-USA indicators first
        for indicator in self.non_usa_indicators:
            if indicator in combined_text:
                return False, f"Non-USA location detected: {indicator}"
        
        # Check for USA indicators
        usa_matches = []
        for keyword in self.usa_keywords:
            if keyword in combined_text:
                usa_matches.append(keyword)
        
        if usa_matches:
            return True, f"USA location confirmed: {', '.join(usa_matches[:3])}"
        
        # Handle ambiguous cases (Springfield, etc.)
        ambiguous_cities = ['springfield', 'madison', 'franklin', 'georgetown', 'clinton']
        for city in ambiguous_cities:
            if city in combined_text:
                # Look for additional context
                if any(state in combined_text for state in self.usa_keywords):
                    return True, f"Ambiguous city ({city}) with USA context"
                else:
                    return False, f"Ambiguous city ({city}) without USA context"
        
        return False, "No clear USA location indicators found"

class BioAnalyzer:
    """Advanced bio analysis with NLP capabilities"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.setup_nltk()
    
    def setup_nltk(self):
        """Download required NLTK data"""
        try:
            nltk.download('vader_lexicon', quiet=True)
            nltk.download('punkt', quiet=True)
        except Exception as e:
            self.logger.warning(f"NLTK setup warning: {e}")
    
    def analyze_bio(self, bio: str) -> Dict[str, Any]:
        """Comprehensive bio analysis"""
        if not bio:
            return {
                'language': 'unknown',
                'sentiment': 'neutral',
                'has_commercial_intent': False,
                'estimated_gender': 'unknown',
                'age_indicators': [],
                'topics': []
            }
        
        blob = TextBlob(bio)
        
        return {
            'language': self.detect_language(bio),
            'sentiment': self.analyze_sentiment(bio),
            'has_commercial_intent': self.detect_commercial_intent(bio),
            'estimated_gender': self.estimate_gender(bio),
            'age_indicators': self.detect_age_indicators(bio),
            'topics': self.extract_topics(bio)
        }
    
    def detect_language(self, text: str) -> str:
        """Detect primary language of text"""
        try:
            blob = TextBlob(text)
            return blob.detect_language()
        except:
            # Fallback: simple heuristic
            english_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with']
            english_count = sum(1 for word in english_words if word in text.lower())
            return 'en' if english_count > 2 else 'unknown'
    
    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of bio text"""
        try:
            from nltk.sentiment import SentimentIntensityAnalyzer
            sia = SentimentIntensityAnalyzer()
            scores = sia.polarity_scores(text)
            
            if scores['compound'] >= 0.05:
                return 'positive'
            elif scores['compound'] <= -0.05:
                return 'negative'
            else:
                return 'neutral'
        except:
            return 'neutral'
    
    def detect_commercial_intent(self, bio: str) -> bool:
        """Detect commercial/promotional intent in bio"""
        commercial_keywords = [
            'link in bio', 'linktree', 'dm for collab', 'business inquiries',
            'sponsored', 'promo code', 'discount', 'shop now', 'buy now',
            'affiliate', 'partnership', 'brand ambassador', 'influencer',
            'onlyfans', 'premium', 'exclusive content', 'subscribe'
        ]
        
        bio_lower = bio.lower()
        return any(keyword in bio_lower for keyword in commercial_keywords)
    
    def estimate_gender(self, bio: str) -> str:
        """Estimate gender based on bio content"""
        # Simple heuristic approach
        female_indicators = ['she/her', 'girl', 'woman', 'mom', 'mother', 'wife', 'daughter',
                           'sister', 'queen', 'goddess', 'beauty', 'makeup', 'fashion']
        male_indicators = ['he/him', 'guy', 'man', 'dad', 'father', 'husband', 'son',
                         'brother', 'king', 'fitness', 'gym', 'sports']
        
        bio_lower = bio.lower()
        
        female_score = sum(1 for indicator in female_indicators if indicator in bio_lower)
        male_score = sum(1 for indicator in male_indicators if indicator in bio_lower)
        
        if female_score > male_score:
            return 'female'
        elif male_score > female_score:
            return 'male'
        else:
            return 'unknown'
    
    def detect_age_indicators(self, bio: str) -> List[str]:
        """Detect age-related indicators in bio"""
        age_patterns = [
            r'\b(\d{2})\b',  # Age numbers
            r'born in (\d{4})',  # Birth year
            r'class of (\d{4})',  # Graduation year
        ]
        
        indicators = []
        for pattern in age_patterns:
            matches = re.findall(pattern, bio, re.IGNORECASE)
            indicators.extend(matches)
        
        return indicators
    
    def extract_topics(self, bio: str) -> List[str]:
        """Extract main topics from bio"""
        topic_keywords = {
            'fitness': ['gym', 'workout', 'fitness', 'health', 'yoga', 'trainer'],
            'fashion': ['fashion', 'style', 'outfit', 'designer', 'model'],
            'food': ['food', 'cooking', 'chef', 'restaurant', 'recipe'],
            'travel': ['travel', 'adventure', 'explore', 'wanderlust', 'vacation'],
            'tech': ['tech', 'developer', 'coding', 'startup', 'innovation'],
            'art': ['art', 'artist', 'creative', 'design', 'photography'],
            'music': ['music', 'musician', 'singer', 'band', 'concert'],
            'business': ['entrepreneur', 'business', 'ceo', 'founder', 'startup']
        }
        
        bio_lower = bio.lower()
        detected_topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in bio_lower for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics

class ProfileFilter:
    """Advanced profile filtering with multiple criteria"""
    
    def __init__(self, config: ConfigManager, logger: Logger, location_validator: LocationValidator, bio_analyzer: BioAnalyzer):
        self.config = config
        self.logger = logger
        self.location_validator = location_validator
        self.bio_analyzer = bio_analyzer
        
        # Load filtering parameters
        self.min_engagement_rate = config.getfloat('FILTERING', 'min_engagement_rate')
        self.max_engagement_rate = config.getfloat('FILTERING', 'max_engagement_rate')
        self.prefer_female = config.getboolean('FILTERING', 'prefer_female_profiles')
        self.require_profile_pic = config.getboolean('FILTERING', 'require_profile_pic')
        
        self.exclude_keywords = [kw.strip().lower() for kw in config.get('FILTERING', 'exclude_keywords').split(',')]
    
    def should_target_profile(self, profile_data: Dict[str, Any], user_filters: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Comprehensive profile filtering
        Returns (should_target, reason)
        """
        reasons = []
        
        # Basic follower/post count check
        if not (user_filters['min_followers'] <= profile_data['follower_count'] <= user_filters['max_followers']):
            return False, f"Follower count ({profile_data['follower_count']}) outside range {user_filters['min_followers']}-{user_filters['max_followers']}"
        
        if profile_data['post_count'] < user_filters['min_posts']:
            return False, f"Post count ({profile_data['post_count']}) below minimum {user_filters['min_posts']}"
        
        # Exclude verified accounts (as per user preference)
        if profile_data.get('is_verified', False):
            return False, "Verified account (excluded by preference)"
        
        # Exclude private profiles
        if profile_data.get('is_private', False):
            return False, "Private profile"
        
        # USA location check
        is_usa, location_reason = self.location_validator.is_usa_location(
            profile_data.get('bio', ''), 
            profile_data.get('location', '')
        )
        if not is_usa:
            return False, f"Location check failed: {location_reason}"
        reasons.append(f"USA location: {location_reason}")
        
        # Active story check
        if not profile_data.get('has_active_story', False):
            return False, "No active story found"
        reasons.append("Active story confirmed")
        
        # Profile picture check
        if self.require_profile_pic and not profile_data.get('profile_pic_url'):
            return False, "No profile picture"
        
        # Bio analysis
        bio_analysis = self.bio_analyzer.analyze_bio(profile_data.get('bio', ''))
        
        # Language check (mention if not English but don't exclude)
        if bio_analysis['language'] != 'en' and bio_analysis['language'] != 'unknown':
            reasons.append(f"Bio language: {bio_analysis['language']}")
        
        # Commercial intent check
        if bio_analysis['has_commercial_intent']:
            return False, "Commercial intent detected in bio"
        
        # Exclude keywords check
        bio_lower = profile_data.get('bio', '').lower()
        for keyword in self.exclude_keywords:
            if keyword in bio_lower:
                return False, f"Excluded keyword found: {keyword}"
        
        # Engagement rate check (bot detection)
        engagement_rate = profile_data.get('engagement_rate', 0)
        if engagement_rate > 0:  # Only check if we have engagement data
            if not (self.min_engagement_rate <= engagement_rate <= self.max_engagement_rate):
                return False, f"Engagement rate ({engagement_rate:.2f}%) outside normal range (possible bot)"
            reasons.append(f"Normal engagement rate: {engagement_rate:.2f}%")
        
        # Gender preference
        if self.prefer_female and bio_analysis['estimated_gender'] == 'female':
            reasons.append("Female profile (preferred)")
        elif bio_analysis['estimated_gender'] != 'unknown':
            reasons.append(f"Gender: {bio_analysis['estimated_gender']}")
        
        # Success
        reason_string = "; ".join(reasons)
        return True, f"All criteria met: {reason_string}"

class SessionManager:
    """Manages session state and persistence"""
    
    def __init__(self, config: ConfigManager, logger: Logger):
        self.config = config
        self.logger = logger
        self.session_file = config.get('OUTPUT', 'session_state_file')
        self.session_data = self.load_session()
        
    def load_session(self) -> Dict[str, Any]:
        """Load existing session or create new one"""
        # Inside the load_session method - AFTER THE FIX ✅
        if os.path.exists(self.session_file):
              try:
                with open(self.session_file, 'r') as f:
                   data = json.load(f)
                   # Convert the 'seen_profiles' list back to a set
                   data['seen_profiles'] = set(data.get('seen_profiles', []))
                   return data
              except Exception as e:
                 self.logger.warning(f"Could not load session file: {e}")
        
        return {
            'seen_profiles': set(),
            'discovered_hvts': [],
            'current_depth': 0,
            'processing_queue': [],
            'session_start': datetime.now().isoformat(),
            'total_profiles_scanned': 0,
            'errors_encountered': 0
        }
    
    def save_session(self):
        """Save current session state"""
        try:
            # Convert sets to lists for JSON serialization
            session_copy = self.session_data.copy()
            session_copy['seen_profiles'] = list(session_copy['seen_profiles'])
            
            with open(self.session_file, 'w') as f:
                json.dump(session_copy, f, indent=2)
            
            self.logger.info(f"Session state saved to {self.session_file}")
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
    
    def add_seen_profile(self, username: str):
        """Add profile to seen list"""
        self.session_data['seen_profiles'].add(username)
    
    def is_profile_seen(self, username: str) -> bool:
        """Check if profile has been seen"""
        return username in self.session_data['seen_profiles']
    
    def add_hvt(self, hvt: UserProfile):
        """Add HVT to session"""
        self.session_data['discovered_hvts'].append(asdict(hvt))
    
    def increment_scanned(self):
        """Increment profiles scanned counter"""
        self.session_data['total_profiles_scanned'] += 1
    
    def increment_errors(self):
        """Increment error counter"""
        self.session_data['errors_encountered'] += 1
