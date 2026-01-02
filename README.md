Hunter_v7 - Advanced Social Media Target Acquisition & Analysis Tool
🎯 Overview
Hunter_v7 is a sophisticated Python-based tool designed to automate the identification, filtering, and analysis of high-value social media profiles. Built with advanced AI capabilities, robust architecture, and comprehensive filtering mechanisms.

✨ Key Features
Core Functionality
Interactive Configuration: Dynamic session setup with user-defined parameters
USA Geographic Filtering: Multi-point verification for US-based profiles
Active Story Detection: Validates account activity through story presence
Recursive Follower Expansion: Deep analysis of follower networks
Advanced AI Filtering: NLP-based bio analysis and sentiment detection
Engagement Rate Analysis: Bot detection through engagement patterns
Gender Estimation: Profile categorization with female preference option
Technical Features
Proxy Rotation: Automatic proxy management and rotation
Human Behavior Simulation: Randomized delays and browsing patterns
Session Persistence: Resume interrupted sessions
Email Notifications: Real-time alerts and session summaries
Comprehensive Logging: Detailed activity tracking
CSV Export: Structured data output with justification column
Error Recovery: Robust error handling and retry mechanisms
🚀 Installation
Clone or download the Hunter_v7 files
Install dependencies:
pip install -r requirements.txt
Install ChromeDriver (for Selenium):
Download from: https://chromedriver.chromium.org/
Add to PATH or place in project directory
⚙️ Configuration
1. Update Credentials
Edit config.ini and update the following:

[CREDENTIALS]
username = your_instagram_username
password = your_instagram_password
email_username = your_email@gmail.com
email_password = your_email_app_password
2. Configure Proxies (Optional)
Add your proxies to proxy_list.txt:

ip:port
ip:port:username:password
3. Customize Filtering
Adjust filtering parameters in config.ini as needed.

🎮 Usage
Quick Start
python main_orchestrator.py
Interactive Configuration
The tool will prompt you for:

Follower count limits (min/max)
Minimum post count
Keyword inclusion/exclusion
Recursion depth
Maximum profiles to scan
Session Management
Sessions are automatically saved
Resume interrupted sessions when prompted
All progress is preserved
📊 Output
CSV Results
The tool exports results to hunter_v7_results.csv with columns:

username: Profile username
follower_count: Number of followers
post_count: Number of posts
bio: Profile biography
profile_url: Direct profile link
has_active_story: Story activity status
location: Geographic location
engagement_rate: Calculated engagement percentage
estimated_gender: AI-estimated gender
bio_language: Detected bio language
reason_for_selection: Detailed justification
source_hvt: Discovery source
discovery_timestamp: When profile was found
Logs
Detailed logs are saved to hunter_v7_activity.log including:

Profile analysis results
Error messages and warnings
Performance metrics
Session statistics
🔧 Advanced Features
Filtering Criteria
The tool applies multiple filtering layers:

Basic Filters: Follower/post count limits
Geographic Filters: USA location verification
Activity Filters: Active story requirement
Quality Filters: Engagement rate analysis
Content Filters: Bio keyword analysis
Commercial Filters: Promotional content detection
Verification Filters: Excludes verified accounts (as configured)
AI-Powered Analysis
Sentiment Analysis: Bio text sentiment scoring
Topic Extraction: Content categorization
Gender Estimation: Profile gender prediction
Language Detection: Bio language identification
Bot Detection: Engagement pattern analysis
Human Behavior Simulation
Randomized scroll patterns
Variable delay intervals
Mouse movement simulation
Natural browsing rhythm
📧 Notifications
Email Alerts
Real-time HVT discovery notifications
Session completion summaries
Error alerts and warnings
Configuration
Update email settings in config.ini:

[NOTIFICATIONS]
send_email_reports = true
email_recipient = your_email@example.com
notify_on_hvt_found = true
🔄 Session Management
Auto-Save
Session state automatically saved
Profile scanning progress preserved
Graceful shutdown on interruption (Ctrl+C)
Resume Functionality
Continue from last known state
Avoid re-scanning seen profiles
Maintain discovery lineage
🛡️ Security & Ethics
Rate Limiting
Human-like delays between requests
Adaptive rate limiting based on responses
Proxy rotation for anonymity
Responsible Usage
Respect platform terms of service
Implement appropriate delays
Use for legitimate research purposes only
🐛 Troubleshooting
Common Issues
Login Failures

Verify credentials in config.ini
Check for two-factor authentication
Ensure account is not restricted
WebDriver Issues

Update ChromeDriver to latest version
Check Chrome browser compatibility
Verify ChromeDriver is in PATH
Proxy Problems

Test proxy connectivity
Update proxy list with working proxies
Set use_proxies = false to disable
No HVTs Found

Adjust filtering criteria
Expand follower/post count ranges
Check location keywords
Logs Analysis
Check hunter_v7_activity.log for detailed error information and performance metrics.

📈 Performance Optimization
Speed Improvements
Use high-quality proxies
Optimize delay intervals
Increase concurrent threads (advanced users)
Resource Management
Monitor memory usage for large sessions
Clear browser cache periodically
Use SSD storage for better I/O performance
🔮 Future Enhancements
Planned Features
Machine learning model training
Advanced demographic analysis
API integration for data enrichment
Web dashboard interface
Batch processing capabilities
Community Contributions
Bug reports and fixes welcome
Feature suggestions encouraged
Code reviews and improvements
📝 License & Disclaimer
This tool is provided for educational and research purposes only. Users are responsible for complying with all applicable laws and terms of service. The developers assume no liability for misuse or violations.

🆘 Support
For issues, questions, or contributions:

Check the troubleshooting section
Review log files for error details
Ensure proper configuration setup
Test with minimal settings first
Hunter_v7 - Advanced Social Media Intelligence Tool
