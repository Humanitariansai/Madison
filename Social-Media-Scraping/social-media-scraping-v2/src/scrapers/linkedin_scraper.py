import os
import time
from datetime import datetime
from typing import List, Dict, Union, Optional
import hashlib
import re
import platform
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from shutil import which

class LinkedInScraper:
    def __init__(self, headless: bool = None):
        load_dotenv()
        self.username = os.getenv('LINKEDIN_USERNAME')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.browser = None
        # Auto-detect: headless in cloud (chromium path), visible locally unless overridden
        if headless is None:
            self.headless = os.getenv('LINKEDIN_HEADLESS', 'false').lower() == 'true' or \
                           os.path.exists('/usr/bin/chromium')
        else:
            self.headless = headless
        # Disable images in cloud by default to save memory/bandwidth
        self.disable_images = os.getenv('LINKEDIN_DISABLE_IMAGES', 'true').lower() == 'true'
        
    def initialize_browser(self):
        """Initialize and return a Chrome browser instance"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # Reduce memory and background activity
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--safebrowsing-disable-auto-update')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--mute-audio')
        chrome_options.add_argument('--lang=en-US')
        chrome_options.add_argument('--media-cache-size=0')
        chrome_options.add_argument('--disk-cache-size=0')
        if self.disable_images:
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        # Headless mode configurable
        if self.headless:
            chrome_options.add_argument('--headless=new')
            print("🔇 Running in HEADLESS mode (browser invisible)")
        else:
            print("👁️  Running in VISIBLE mode (you'll see the browser)")
        # Slightly smaller window to reduce memory
        chrome_options.add_argument('--window-size=1280,800')
        
        # Check if running on Streamlit Cloud (uses chromium)
        if os.path.exists('/usr/bin/chromium'):
            chrome_options.binary_location = '/usr/bin/chromium'
        
        try:
            # Try using Selenium 4's built-in driver manager (no external dependencies)
            self.browser = webdriver.Chrome(options=chrome_options)
        except Exception as e1:
            print(f"Selenium's built-in manager failed: {e1}")
            try:
                # Fallback to webdriver-manager with fix
                driver_path = self._get_correct_driver_path()
                service = Service(driver_path)
                self.browser = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e2:
                print(f"All automatic methods failed: {e2}")
                raise Exception(
                    "Could not initialize ChromeDriver. Please install it manually:\n"
                    "For Mac: brew install chromedriver\n"
                    "Then run: xattr -d com.apple.quarantine $(which chromedriver)"
                )
        
        # Add stealth scripts
        self.browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            self.browser.maximize_window()
        except:
            pass
        return self.browser
    
    def _get_correct_driver_path(self):
        """Get the correct ChromeDriver path, handling webdriver-manager issues"""
        import platform
        from pathlib import Path
        
        try:
            # First try webdriver-manager
            installed_path = ChromeDriverManager().install()
            
            # If it's the THIRD_PARTY_NOTICES file, find the actual driver
            if 'THIRD_PARTY_NOTICES' in installed_path or not os.access(installed_path, os.X_OK):
                driver_dir = Path(installed_path).parent
                
                # Look for the actual ChromeDriver executable
                possible_names = ['chromedriver', 'chromedriver.exe']
                for name in possible_names:
                    driver_file = driver_dir / name
                    if driver_file.exists() and driver_file.is_file():
                        driver_path = str(driver_file)
                        # Make it executable on Unix-like systems
                        if platform.system() != 'Windows':
                            os.chmod(driver_path, 0o755)
                        return driver_path
                
                # If not found in the same directory, search the parent directory
                parent_dir = driver_dir.parent
                for item in parent_dir.iterdir():
                    if item.is_file() and 'chromedriver' in item.name.lower() and 'THIRD_PARTY' not in item.name:
                        driver_path = str(item)
                        if platform.system() != 'Windows':
                            os.chmod(driver_path, 0o755)
                        return driver_path
            
            # If the original path looks good, use it
            if os.path.isfile(installed_path) and os.access(installed_path, os.X_OK):
                return installed_path
                
        except Exception as e:
            print(f"WebDriver manager failed: {e}")
        
        # Fallback: try to use system ChromeDriver
        from shutil import which
        system_driver = which('chromedriver')
        if system_driver:
            print("Using system ChromeDriver")
            return system_driver
        
        # Last resort: manual download instruction
        raise Exception(
            "Could not find ChromeDriver. Please install it manually:\n"
            "1. Download from: https://chromedriver.chromium.org/\n"
            "2. For Mac with Homebrew: brew install chromedriver\n"
            "3. For Mac manual: Download, extract, and run: xattr -d com.apple.quarantine chromedriver"
        )

    def login(self, verification_code: str = None) -> bool:
        """Login to LinkedIn with optional 2FA verification code"""
        try:
            # If already on verification page, just handle verification
            current_url = self.browser.current_url if self.browser else ""
            if "challenge" in current_url or "checkpoint" in current_url:
                print("Already on verification page, processing code...")
                if verification_code:
                    return self._handle_verification(verification_code)
                else:
                    print("⚠️ Still waiting for verification code")
                    return False
            
            print("Navigating to LinkedIn login page...")
            self.browser.get('https://www.linkedin.com/login')
            time.sleep(2)
            print(f"Current URL: {self.browser.current_url}")
            
            # Find and fill username
            print("Looking for username field...")
            username_elem = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            username_elem.clear()
            username_elem.send_keys(self.username)
            print("Username entered")
            
            # Find and fill password
            print("Looking for password field...")
            password_elem = self.browser.find_element(By.ID, 'password')
            password_elem.clear()
            password_elem.send_keys(self.password)
            password_elem.send_keys(Keys.RETURN)
            print("Login form submitted")
            
            # Wait for login to complete
            time.sleep(5)
            print(f"Post-login URL: {self.browser.current_url}")
            
            # Check for 2FA verification page
            if "challenge" in self.browser.current_url or "checkpoint" in self.browser.current_url:
                print("⚠️ LinkedIn verification required")
                print(f"📧 Check your email for a verification code from LinkedIn")
                print(f"🔗 Verification URL: {self.browser.current_url}")
                
                if verification_code:
                    return self._handle_verification(verification_code)
                else:
                    print("❌ Verification code required but not provided")
                    print("💡 Enter the code in the 'LinkedIn Verification Code' field and try again")
                    # Don't close browser - keep session alive for retry
                    return False
            
            # Check if login was successful without verification
            if "feed" in self.browser.current_url or "mynetwork" in self.browser.current_url:
                print("✅ Login successful!")
                return True
            else:
                print(f"❌ Login failed - unexpected URL: {self.browser.current_url}")
                return False
            
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            print(f"Current page title: {self.browser.title if self.browser else 'No browser'}")
            return False
    
    def _handle_verification(self, verification_code: str) -> bool:
        """Handle LinkedIn 2FA verification"""
        print(f"Entering verification code: {verification_code}")
        try:
            # Try to find the verification code input field
            code_field = None
            possible_ids = ['input__email_verification_pin', 'pin', 'verification-code', 'input__phone_verification_pin']
            
            for field_id in possible_ids:
                try:
                    code_field = self.browser.find_element(By.ID, field_id)
                    print(f"✅ Found verification field: {field_id}")
                    break
                except:
                    continue
            
            # If no ID worked, try by name or type
            if not code_field:
                try:
                    code_field = self.browser.find_element(By.NAME, 'pin')
                    print("✅ Found verification field by name")
                except:
                    try:
                        code_field = self.browser.find_element(By.CSS_SELECTOR, 'input[type="tel"]')
                        print("✅ Found verification field by CSS selector")
                    except:
                        pass
            
            if code_field:
                code_field.clear()
                code_field.send_keys(verification_code)
                code_field.send_keys(Keys.RETURN)
                print("📤 Verification code submitted")
                
                # Wait for verification to complete
                time.sleep(5)
                print(f"Post-verification URL: {self.browser.current_url}")
                
                if "feed" in self.browser.current_url or "mynetwork" in self.browser.current_url:
                    print("✅ Login successful after verification!")
                    return True
                elif "challenge" in self.browser.current_url or "checkpoint" in self.browser.current_url:
                    print("❌ Still on verification page - code may be incorrect")
                    return False
                else:
                    print("⚠️ Unexpected URL after verification")
                    return False
            else:
                print("❌ Could not find verification code input field")
                print(f"Page HTML snippet: {self.browser.page_source[:500]}")
                return False
                
        except Exception as ve:
            print(f"❌ Verification error: {str(ve)}")
            return False

    def search_content(self, keywords: Union[str, List[str]], search_type: str = 'hashtag', 
                      max_posts: int = 10, debug: bool = False, verification_code: str = None) -> List[Dict]:
        """
        Search LinkedIn content by keywords or hashtag
        verification_code: Optional 2FA code if LinkedIn requires verification
        """
        print(f"\nInitializing search for: {keywords}")
        
        if not self.browser:
            print("Initializing browser...")
            self.initialize_browser()
        
        # Always attempt login (it will handle already-logged-in state)
        print("Logging in to LinkedIn...")
        if not self.login(verification_code=verification_code):
            error_msg = "Failed to login to LinkedIn"
            if "challenge" in self.browser.current_url or "checkpoint" in self.browser.current_url:
                error_msg += " - Verification code required. Enter the code from your email and try again."
            raise Exception(error_msg)
        time.sleep(3)

        try:
            # Prepare search query
            if search_type == 'hashtag':
                if isinstance(keywords, list):
                    keywords = keywords[0]
                search_query = keywords.replace('#', '').strip()
                # For hashtags, go directly to the hashtag feed
                url = f"https://www.linkedin.com/feed/hashtag/?keywords={search_query}"
                print(f"Navigating to hashtag: #{search_query}")
                self.browser.get(url)
                time.sleep(4)
            else:
                if isinstance(keywords, str):
                    keywords = [keywords]
                search_query = ' '.join(keywords)
                
                print(f"Searching for keywords: {search_query}")
                
                # Method 1: Direct URL navigation to content search
                encoded_query = search_query.replace(' ', '%20')
                url = f"https://www.linkedin.com/search/results/content/?keywords={encoded_query}"
                self.browser.get(url)
                time.sleep(4)
                
                # If we're not on the content page, try the search box method
                if "/search/results/content" not in self.browser.current_url:
                    print("Retrying with search box method...")
                    # Navigate to feed first
                    self.browser.get('https://www.linkedin.com/feed/')
                    time.sleep(3)
                    
                    # Find and use the search box
                    try:
                        search_box = WebDriverWait(self.browser, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 
                                "input.search-global-typeahead__input"))
                        )
                        search_box.clear()
                        search_box.send_keys(search_query)
                        search_box.send_keys(Keys.RETURN)
                        time.sleep(4)
                        
                        # After search, explicitly click on "Posts" tab
                        self._click_posts_filter()
                        
                    except Exception as e:
                        print(f"Search box method failed: {e}")
            
            # Ensure we're viewing posts
            self._ensure_posts_view()
            
            # Wait for posts to load
            self._wait_for_posts_to_load()
            
            # Collect posts with improved deduplication
            posts = self._collect_posts_with_scroll(max_posts, debug)
            
            print(f"\nTotal unique posts collected: {len(posts)}")
            return posts
            
        except Exception as e:
            print(f"Error during search: {str(e)}")
            # Try alternative direct navigation method
            try:
                print("Trying alternative search method...")
                if search_type == 'hashtag':
                    # Direct hashtag URL
                    clean_keyword = keywords[0] if isinstance(keywords, list) else keywords
                    clean_keyword = clean_keyword.replace('#', '').strip()
                    url = f"https://www.linkedin.com/feed/hashtag/?keywords={clean_keyword}"
                else:
                    # Direct content search URL
                    search_terms = keywords if isinstance(keywords, list) else [keywords]
                    query = '%20'.join(search_terms)
                    url = f"https://www.linkedin.com/search/results/content/?keywords={query}&origin=SWITCH_SEARCH_VERTICAL"
                
                print(f"Direct navigation to: {url}")
                self.browser.get(url)
                time.sleep(5)
                
                # Wait and collect
                self._wait_for_posts_to_load()
                posts = self._collect_posts_with_scroll(max_posts, debug)
                
                print(f"\nTotal unique posts collected: {len(posts)}")
                return posts
                
            except Exception as e2:
                print(f"Alternative method also failed: {str(e2)}")
                return []
        finally:
            self.close()

    def _ensure_posts_view(self):
        """Ensure we're viewing posts, not other content types"""
        current_url = self.browser.current_url
        
        # Check if we're on a search results page but not on content/posts
        if "/search/results/" in current_url and "/content" not in current_url:
            print("Not on Posts view, attempting to switch...")
            
            # Try multiple methods to get to Posts
            if not self._click_posts_filter():
                # If clicking Posts filter didn't work, try modifying the URL
                if "/search/results/people" in current_url:
                    new_url = current_url.replace("/people", "/content")
                elif "/search/results/companies" in current_url:
                    new_url = current_url.replace("/companies", "/content")
                elif "/search/results/all" in current_url:
                    new_url = current_url.replace("/all", "/content")
                else:
                    # Generic replacement
                    new_url = re.sub(r'/search/results/\w+/', '/search/results/content/', current_url)
                
                print(f"Navigating directly to content URL: {new_url}")
                self.browser.get(new_url)
                time.sleep(3)
    
    def _click_posts_filter(self) -> bool:
        """Click on Posts filter/tab to show only posts"""
        try:
            # Try different selectors for the Posts button/filter
            posts_selectors = [
                "//button[contains(text(), 'Posts')]",
                "//button[contains(@aria-label, 'Posts')]",
                "//a[contains(text(), 'Posts')]",
                "//button[contains(text(), 'Content')]",
                "//button[@aria-label='View only Posts']",
                "//button[contains(@class, 'search-reusables__filter-pill-button') and contains(., 'Posts')]",
                "//button[contains(@id, 'POSTS')]",
                "//div[@role='tablist']//button[contains(., 'Posts')]"
            ]
            
            for selector in posts_selectors:
                try:
                    posts_button = self.browser.find_element(By.XPATH, selector)
                    if posts_button.is_displayed():
                        self.browser.execute_script("arguments[0].click();", posts_button)
                        print("Clicked on Posts filter")
                        time.sleep(3)
                        return True
                except:
                    continue
            
            # Alternative: Look for the tab navigation and click Posts
            try:
                # Find the search navigation tabs
                nav_items = self.browser.find_elements(By.CSS_SELECTOR, 
                    "div.search-navigation-panel__button-container button, div.search-nav-panel button")
                for item in nav_items:
                    if "Posts" in item.text or "Content" in item.text:
                        self.browser.execute_script("arguments[0].click();", item)
                        print("Clicked on Posts in navigation")
                        time.sleep(3)
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            print(f"Could not click Posts filter: {e}")
            return False

    def _wait_for_posts_to_load(self):
        """Wait for posts to load on the page"""
        try:
            # Wait for post containers to appear
            post_selectors = [
                "div.feed-shared-update-v2",
                "div.occludable-update", 
                "div[data-id]",
                "article.relative",
                "div[data-urn]"
            ]
            
            for selector in post_selectors:
                try:
                    WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"Posts loaded with selector: {selector}")
                    return True
                except:
                    continue
            
            print("Warning: Could not confirm posts loaded")
            return False
        except:
            return False

    def _collect_posts_with_scroll(self, max_posts: int, debug: bool = False) -> List[Dict]:
        """Collect posts with intelligent scrolling and deduplication"""
        posts = []
        seen_content_hashes = set()
        scroll_attempts = 0
        max_scroll_attempts = 30
        consecutive_no_new_posts = 0
        max_consecutive_no_new = 5
        
        # Check current page type
        current_url = self.browser.current_url
        is_hashtag_page = "/feed/hashtag" in current_url
        is_content_search = "/search/results/content" in current_url
        
        print(f"Page type - Hashtag: {is_hashtag_page}, Content Search: {is_content_search}")
        
        while len(posts) < max_posts and scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1
            
            # Get current page height
            old_height = self.browser.execute_script("return document.body.scrollHeight")
            
            # Parse current posts
            soup = BeautifulSoup(self.browser.page_source, 'html.parser')
            
            # Different selectors for different page types
            if is_hashtag_page:
                # Hashtag feed specific selectors
                post_selectors = [
                    "div.feed-shared-update-v2",
                    "div.occludable-update",
                    "article[data-id]",
                    "div[class*='feed-shared-update']"
                ]
            elif is_content_search:
                # Search results specific selectors
                post_selectors = [
                    "div.reusable-search__result-container",
                    "div.search-results__result-item",
                    "li.reusable-search__result-container",
                    "div.feed-shared-update-v2",
                    "div[data-chameleon-result-urn]",
                    "div[data-id]"
                ]
            else:
                # Generic selectors
                post_selectors = [
                    "div[data-id]",
                    "div.feed-shared-update-v2",
                    "div.occludable-update",
                    "article.relative",
                    "div[class*='feed-shared-update']",
                    "li.feed-item",
                    "div[data-urn]"
                ]
            
            post_elements = []
            for selector in post_selectors:
                elements = soup.select(selector)
                if elements:
                    post_elements.extend(elements)
                    if debug and elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
            
            # Remove duplicates while preserving order
            seen_ids = set()
            unique_elements = []
            for elem in post_elements:
                # Create unique identifier for element
                elem_id = (elem.get('data-id') or 
                          elem.get('data-urn') or 
                          elem.get('data-chameleon-result-urn') or
                          str(hash(str(elem)[:500])))
                          
                if elem_id not in seen_ids:
                    seen_ids.add(elem_id)
                    unique_elements.append(elem)
            
            if debug:
                print(f"Scroll {scroll_attempts}: Found {len(unique_elements)} unique post elements")
            
            new_posts_count = 0
            for element in unique_elements:
                if len(posts) >= max_posts:
                    break
                    
                post_data = self._extract_post_data_improved(element)
                if not post_data:
                    continue
                
                # Create content hash for deduplication
                content_hash = self._create_content_hash(post_data)
                if content_hash in seen_content_hashes:
                    if debug:
                        print(f"Skipping duplicate post from {post_data.get('author', 'Unknown')}")
                    continue
                
                seen_content_hashes.add(content_hash)
                posts.append(post_data)
                new_posts_count += 1
                print(f"Collected post {len(posts)}/{max_posts} from {post_data.get('author', 'Unknown')}")
            
            # Check if we got new posts
            if new_posts_count == 0:
                consecutive_no_new_posts += 1
                if consecutive_no_new_posts >= max_consecutive_no_new:
                    print("No new posts found after multiple scrolls, stopping...")
                    break
            else:
                consecutive_no_new_posts = 0
            
            if len(posts) >= max_posts:
                break
            
            # Expand "see more" buttons before scrolling
            self._expand_see_more_buttons()
            
            # Scroll down - try multiple scroll methods
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Check if page height changed
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == old_height:
                # Try alternative scroll methods
                try:
                    # Scroll to last element
                    all_posts = self.browser.find_elements(By.CSS_SELECTOR, 
                        "div[data-id], div.feed-shared-update-v2, div.occludable-update, div.reusable-search__result-container")
                    if all_posts:
                        self.browser.execute_script("arguments[0].scrollIntoView(true);", all_posts[-1])
                        time.sleep(2)
                    
                    # Try clicking "Show more results" if available
                    try:
                        show_more = self.browser.find_element(By.XPATH, 
                            "//button[contains(text(), 'Show more results')]")
                        self.browser.execute_script("arguments[0].click();", show_more)
                        time.sleep(2)
                    except:
                        pass
                        
                except:
                    pass
        
        return posts[:max_posts]

    def _create_content_hash(self, post_data: Dict) -> str:
        """Create a hash for deduplication based on post content"""
        unique_string = f"{post_data.get('author', '')}_{post_data.get('content', '')[:200] if post_data.get('content') else ''}_{post_data.get('posted_time', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _extract_post_data_improved(self, element) -> Optional[Dict]:
        """Improved post data extraction with better selectors"""
        try:
            # Initialize data
            data = {
                'author': None,
                'author_headline': None,
                'posted_time': None,
                'content': None,
                'likes': 0,
                'comments': 0,
                'reposts': 0,
                'link': None,
                'post_id': None
            }
            
            # Extract post ID
            data['post_id'] = (element.get('data-id') or 
                              element.get('data-urn') or 
                              element.get('id'))
            
            # Extract author information - IMPROVED
            author_selectors = [
                "span.feed-shared-actor__name span[aria-hidden='true']",
                "span.update-components-actor__name span[aria-hidden='true']",
                "div.update-components-actor__container span[aria-hidden='true']",
                "span.feed-shared-actor__name",
                "span.update-components-actor__name",
                "a.app-aware-link span[dir='ltr']",
                "span[class*='actor__name']",
                "div.update-components-actor a.app-aware-link",
                "h3.actor-name",
                "span.visually-hidden"  # Sometimes the name is in visually-hidden spans
            ]
            
            for selector in author_selectors:
                author_elem = element.select_one(selector)
                if author_elem:
                    author_text = author_elem.get_text(strip=True)
                    # Filter out non-author text
                    if author_text and not any(skip in author_text.lower() for skip in ['view', 'profile', 'image', 'logo']):
                        data['author'] = author_text
                        break
            
            # If still no author, try text extraction from actor container
            if not data['author']:
                actor_container = element.select_one("div.update-components-actor, div.feed-shared-actor")
                if actor_container:
                    # Get first substantial text that looks like a name
                    for text_elem in actor_container.find_all(text=True):
                        text = text_elem.strip()
                        if text and len(text) > 2 and len(text) < 100 and not text.startswith('•'):
                            data['author'] = text
                            break
            
            # Extract author headline - IMPROVED
            headline_selectors = [
                "span.feed-shared-actor__description",
                "span.update-components-actor__description", 
                "span[class*='actor__sub-description']",
                "div.feed-shared-actor__meta span[aria-hidden='true']",
                "div.update-components-actor__meta span"
            ]
            
            for selector in headline_selectors:
                headline_elem = element.select_one(selector)
                if headline_elem:
                    headline_text = headline_elem.get_text(strip=True)
                    # Clean up the headline
                    if headline_text and '•' in headline_text:
                        # Take the part before the bullet point (usually the job title)
                        headline_text = headline_text.split('•')[0].strip()
                    if headline_text and len(headline_text) < 200:
                        data['author_headline'] = headline_text
                        break
            
            # Extract time - IMPROVED
            time_elem = element.select_one("time")
            if time_elem:
                # Try to get the actual time text, not the full accessibility text
                time_text = time_elem.get_text(strip=True)
                if '•' in time_text:
                    # Extract just the time part (e.g., "2h" from "2h • Edited")
                    time_parts = time_text.split('•')
                    for part in time_parts:
                        if any(t in part.lower() for t in ['ago', 'h', 'd', 'w', 'm', 'y']):
                            data['posted_time'] = part.strip()
                            break
                else:
                    data['posted_time'] = time_text
            else:
                # Look for relative time in actor description
                time_pattern = r'\d+[smhdw]\s*(?:ago)?|\d+\s*(?:second|minute|hour|day|week|month|year)s?\s*ago'
                for elem in element.select("span[class*='sub-description'], div[class*='actor__meta']"):
                    text = elem.get_text(strip=True)
                    match = re.search(time_pattern, text, re.I)
                    if match:
                        data['posted_time'] = match.group(0)
                        break
            
            # Extract post content - IMPROVED
            content_selectors = [
                "div.feed-shared-text span[dir='ltr']",
                "div.update-components-text span.break-words",
                "div[class*='feed-shared-update-v2__description'] span[dir='ltr']",
                "div.feed-shared-text__text-view span",
                "span[class*='break-words']",
                "div.feed-shared-update-v2__commentary",
                "div.feed-shared-text"
            ]
            
            content_parts = []
            for selector in content_selectors:
                content_elems = element.select(selector)
                for elem in content_elems:
                    text = elem.get_text(strip=True)
                    # Filter out UI elements and very short text
                    if text and len(text) > 20 and not text.startswith('hashtag#'):
                        # Clean hashtags
                        text = re.sub(r'hashtag#(\w+)', r'#\1', text)
                        content_parts.append(text)
            
            if content_parts:
                # Deduplicate content parts
                unique_parts = []
                for part in content_parts:
                    # Check if this part is not a substring of existing parts
                    is_duplicate = False
                    for existing in unique_parts:
                        if part in existing or existing in part:
                            is_duplicate = True
                            if len(part) > len(existing):
                                # Replace with longer version
                                unique_parts.remove(existing)
                                unique_parts.append(part)
                            break
                    if not is_duplicate:
                        unique_parts.append(part)
                
                # Join and clean up
                if unique_parts:
                    content = ' '.join(unique_parts)
                    # Remove excessive whitespace
                    content = re.sub(r'\s+', ' ', content).strip()
                    data['content'] = content
            
            # Extract engagement metrics - IMPROVED
            engagement_selectors = {
                'likes': [
                    "button[aria-label*='reaction'] span",
                    "span[class*='social-counts-reactions__count']",
                    "button[class*='social-actions__reaction'] span",
                    "span.social-details-social-counts__reactions-count"
                ],
                'comments': [
                    "button[aria-label*='comment'] span",
                    "button[class*='comment'] span",
                    "span.social-details-social-counts__comments"
                ],
                'reposts': [
                    "button[aria-label*='repost'] span",
                    "button[class*='repost'] span",
                    "span.social-details-social-counts__reposts"
                ]
            }
            
            for metric, selectors in engagement_selectors.items():
                for selector in selectors:
                    try:
                        elems = element.select(selector)
                        for elem in elems:
                            text = elem.get_text(strip=True)
                            # Extract number from text
                            match = re.search(r'([\d,]+)', text)
                            if match:
                                data[metric] = int(match.group(1).replace(',', ''))
                                break
                        if data[metric] > 0:
                            break
                    except:
                        continue
            
            # Additional parsing for engagement if not found
            if data['likes'] == 0 or data['comments'] == 0:
                # Look for text patterns in the entire element
                full_text = element.get_text(' ', strip=True)
                
                if data['likes'] == 0:
                    likes_match = re.search(r'([\d,]+)\s*(?:reactions?|likes?)', full_text, re.I)
                    if likes_match:
                        try:
                            data['likes'] = int(likes_match.group(1).replace(',', ''))
                        except:
                            pass
                
                if data['comments'] == 0:
                    comments_match = re.search(r'([\d,]+)\s*comments?', full_text, re.I)
                    if comments_match:
                        try:
                            data['comments'] = int(comments_match.group(1).replace(',', ''))
                        except:
                            pass
                
                if data['reposts'] == 0:
                    reposts_match = re.search(r'([\d,]+)\s*reposts?', full_text, re.I)
                    if reposts_match:
                        try:
                            data['reposts'] = int(reposts_match.group(1).replace(',', ''))
                        except:
                            pass
            
            # Extract post link
            link_elem = element.select_one("a[href*='/feed/update/'], a[href*='/posts/']")
            if link_elem:
                data['link'] = link_elem.get('href')
                if data['link'] and not data['link'].startswith('http'):
                    data['link'] = f"https://www.linkedin.com{data['link']}"
            
            # Debug output
            if not data['author'] and data['content']:
                # Try one more time to get author from the full element text
                full_text = element.get_text(' ', strip=True)
                # Look for pattern like "Name • Title"
                author_match = re.search(r'^([A-Za-z\s]+)(?:•|\|)', full_text)
                if author_match:
                    data['author'] = author_match.group(1).strip()
            
            # Only return if we have meaningful content
            if data['author'] or data['content']:
                return data
            
            return None
            
        except Exception as e:
            print(f"Error extracting post: {str(e)}")
            return None

    def _expand_see_more_buttons(self):
        """Expand 'see more' buttons to get full content"""
        try:
            see_more_selectors = [
                "button[aria-label*='see more']",
                "button.feed-shared-inline-show-more-text__see-more-less-toggle",
                "button[class*='see-more']",
                "button[aria-expanded='false']"
            ]
            
            for selector in see_more_selectors:
                buttons = self.browser.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons[:5]:  # Limit to avoid too many expansions
                    try:
                        if button.is_displayed():
                            self.browser.execute_script("arguments[0].click();", button)
                            time.sleep(0.3)
                    except:
                        continue
        except:
            pass

    def close(self):
        """Close the browser"""
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
            finally:
                self.browser = None

def main():
    """Example usage with Streamlit integration"""
    scraper = LinkedInScraper()
    
    try:
        # Example search
        keyword = "artificial intelligence"  # This would come from Streamlit input
        num_posts = 5  # This would come from Streamlit number input
        
        print(f"\nSearching for '{keyword}' posts...")
        results = scraper.search_content(keyword, search_type='keywords', max_posts=num_posts, debug=True)
        
        print(f"\n{'='*60}")
        print(f"Found {len(results)} unique posts")
        print(f"{'='*60}\n")
        
        for i, post in enumerate(results, 1):
            print(f"Post {i}:")
            print(f"Author: {post.get('author', 'Unknown')}")
            print(f"Headline: {post.get('author_headline', 'N/A')}")
            print(f"Time: {post.get('posted_time', 'N/A')}")
            print(f"Content: {post.get('content', 'No content')[:200]}...")
            print(f"Engagement: {post.get('likes', 0)} likes, {post.get('comments', 0)} comments, {post.get('reposts', 0)} reposts")
            if post.get('link'):
                print(f"Link: {post.get('link')}")
            print("-" * 60)
            
    finally:
        scraper.close()

if __name__ == "__main__":
    main()