#!/usr/bin/env python3
"""
Standalone LinkedIn Scraper
============================
A self-contained script to scrape LinkedIn posts and save results as CSV.

Requirements:
    pip install selenium webdriver-manager beautifulsoup4 lxml python-dotenv pandas

Setup:
    1. Create a .env file in the same directory with:
       LINKEDIN_USERNAME="your_email@example.com"
       LINKEDIN_PASSWORD="your_password"
    
    2. Edit the SEARCH_CONFIG section below to customize your search
    
    3. Run: python linkedin_scraper_standalone.py

Output:
    - CSV file saved as: linkedin_results_YYYYMMDD_HHMMSS.csv
"""

import os
import time
import re
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pandas as pd

# ============================================================================
# SEARCH CONFIGURATION - EDIT THESE VALUES
# ============================================================================

SEARCH_CONFIG = {
    # Search query: keywords or hashtag (without #)
    "keywords": "artificial intelligence",
    
    # Search type: "keywords" or "hashtag"
    "search_type": "keywords",
    
    # Maximum number of posts to scrape
    "max_posts": 20,
    
    # Debug mode: set to True to see detailed logging
    "debug": False,
    
    # Output CSV filename (leave None for auto-generated timestamp filename)
    "output_csv": None  # e.g., "linkedin_results.csv" or None
}

# ============================================================================
# LINKEDIN SCRAPER CLASS
# ============================================================================

class LinkedInScraper:
    def __init__(self):
        load_dotenv()
        self.username = os.getenv('LINKEDIN_USERNAME')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        
        if not self.username or not self.password:
            raise Exception("LinkedIn credentials not found. Please create a .env file with LINKEDIN_USERNAME and LINKEDIN_PASSWORD")
        
        self.browser = None
        
    def initialize_browser(self):
        """Initialize Chrome browser"""
        print("🌐 Initializing browser...")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            self.browser = webdriver.Chrome(options=chrome_options)
        except Exception as e1:
            try:
                driver_path = ChromeDriverManager().install()
                service = Service(driver_path)
                self.browser = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e2:
                raise Exception(f"Could not initialize ChromeDriver: {e2}")
        
        self.browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Browser initialized")
        return self.browser
    
    def login(self, verification_code: str = None) -> bool:
        """Login to LinkedIn"""
        try:
            print("🔐 Logging in to LinkedIn...")
            self.browser.get('https://www.linkedin.com/login')
            time.sleep(2)
            
            username_elem = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            username_elem.clear()
            username_elem.send_keys(self.username)
            
            password_elem = self.browser.find_element(By.ID, 'password')
            password_elem.clear()
            password_elem.send_keys(self.password)
            password_elem.send_keys(Keys.RETURN)
            
            time.sleep(5)
            
            if "challenge" in self.browser.current_url or "checkpoint" in self.browser.current_url:
                print("⚠️  LinkedIn verification required")
                print("📧 Check your email for a verification code from LinkedIn")
                
                if verification_code:
                    return self._handle_verification(verification_code)
                else:
                    print("❌ Please run the script again with verification_code parameter")
                    return False
            
            if "feed" in self.browser.current_url or "mynetwork" in self.browser.current_url:
                print("✅ Login successful")
                return True
            else:
                print(f"❌ Login failed - unexpected URL: {self.browser.current_url}")
                return False
            
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def _handle_verification(self, verification_code: str) -> bool:
        """Handle LinkedIn 2FA verification"""
        print(f"🔑 Entering verification code...")
        try:
            code_field = None
            possible_ids = ['input__email_verification_pin', 'pin', 'verification-code', 'input__phone_verification_pin']
            
            for field_id in possible_ids:
                try:
                    code_field = self.browser.find_element(By.ID, field_id)
                    break
                except:
                    continue
            
            if not code_field:
                try:
                    code_field = self.browser.find_element(By.NAME, 'pin')
                except:
                    try:
                        code_field = self.browser.find_element(By.CSS_SELECTOR, 'input[type="tel"]')
                    except:
                        pass
            
            if code_field:
                code_field.clear()
                code_field.send_keys(verification_code)
                code_field.send_keys(Keys.RETURN)
                
                time.sleep(5)
                
                if "feed" in self.browser.current_url or "mynetwork" in self.browser.current_url:
                    print("✅ Verification successful")
                    return True
                else:
                    print("❌ Verification failed")
                    return False
            else:
                print("❌ Could not find verification code input field")
                return False
                
        except Exception as ve:
            print(f"❌ Verification error: {str(ve)}")
            return False

    def search_content(self, keywords: str, search_type: str = 'keywords', 
                      max_posts: int = 10, debug: bool = False) -> List[Dict]:
        """Search LinkedIn content"""
        print(f"\n🔍 Searching for: {keywords}")
        
        if not self.browser:
            self.initialize_browser()
        
        if not self.login():
            raise Exception("Failed to login to LinkedIn")
        time.sleep(3)

        try:
            if search_type == 'hashtag':
                search_query = keywords.replace('#', '').strip()
                url = f"https://www.linkedin.com/feed/hashtag/?keywords={search_query}"
                print(f"📍 Navigating to hashtag: #{search_query}")
                self.browser.get(url)
                time.sleep(4)
            else:
                search_query = keywords
                encoded_query = search_query.replace(' ', '%20')
                url = f"https://www.linkedin.com/search/results/content/?keywords={encoded_query}"
                print(f"📍 Navigating to content search")
                self.browser.get(url)
                time.sleep(4)
            
            self._wait_for_posts_to_load()
            posts = self._collect_posts_with_scroll(max_posts, debug)
            
            print(f"✅ Collected {len(posts)} posts")
            return posts
            
        except Exception as e:
            print(f"❌ Error during search: {str(e)}")
            return []
        finally:
            self.close()

    def _wait_for_posts_to_load(self):
        """Wait for posts to load"""
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
                return True
            except:
                continue
        return False

    def _collect_posts_with_scroll(self, max_posts: int, debug: bool = False) -> List[Dict]:
        """Collect posts with scrolling"""
        posts = []
        seen_content_hashes = set()
        scroll_attempts = 0
        max_scroll_attempts = 30
        consecutive_no_new_posts = 0
        max_consecutive_no_new = 5
        
        print(f"📜 Scrolling and collecting posts...")
        
        while len(posts) < max_posts and scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1
            
            old_height = self.browser.execute_script("return document.body.scrollHeight")
            soup = BeautifulSoup(self.browser.page_source, 'html.parser')
            
            post_selectors = [
                "div.feed-shared-update-v2",
                "div.occludable-update",
                "div.reusable-search__result-container",
                "div[data-id]"
            ]
            
            post_elements = []
            for selector in post_selectors:
                elements = soup.select(selector)
                if elements:
                    post_elements.extend(elements)
            
            seen_ids = set()
            unique_elements = []
            for elem in post_elements:
                elem_id = (elem.get('data-id') or 
                          elem.get('data-urn') or 
                          str(hash(str(elem)[:500])))
                          
                if elem_id not in seen_ids:
                    seen_ids.add(elem_id)
                    unique_elements.append(elem)
            
            if debug:
                print(f"  Scroll {scroll_attempts}: Found {len(unique_elements)} unique elements")
            
            new_posts_count = 0
            for element in unique_elements:
                if len(posts) >= max_posts:
                    break
                    
                post_data = self._extract_post_data(element)
                if not post_data:
                    continue
                
                content_hash = self._create_content_hash(post_data)
                if content_hash in seen_content_hashes:
                    continue
                
                seen_content_hashes.add(content_hash)
                posts.append(post_data)
                new_posts_count += 1
                print(f"  📝 Collected post {len(posts)}/{max_posts} from {post_data.get('author', 'Unknown')}")
            
            if new_posts_count == 0:
                consecutive_no_new_posts += 1
                if consecutive_no_new_posts >= max_consecutive_no_new:
                    break
            else:
                consecutive_no_new_posts = 0
            
            if len(posts) >= max_posts:
                break
            
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == old_height:
                try:
                    all_posts = self.browser.find_elements(By.CSS_SELECTOR, 
                        "div[data-id], div.feed-shared-update-v2")
                    if all_posts:
                        self.browser.execute_script("arguments[0].scrollIntoView(true);", all_posts[-1])
                        time.sleep(2)
                except:
                    pass
        
        return posts[:max_posts]

    def _create_content_hash(self, post_data: Dict) -> str:
        """Create hash for deduplication"""
        unique_string = f"{post_data.get('author', '')}_{post_data.get('content', '')[:200]}_{post_data.get('posted_time', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def _extract_post_data(self, element) -> Optional[Dict]:
        """Extract post data from HTML element"""
        try:
            data = {
                'author': None,
                'author_headline': None,
                'posted_time': None,
                'content': None,
                'likes': 0,
                'comments': 0,
                'reposts': 0,
                'link': None
            }
            
            # Author
            author_selectors = [
                "span.feed-shared-actor__name",
                "span.update-components-actor__name",
                "div.update-components-actor span[aria-hidden='true']"
            ]
            
            for selector in author_selectors:
                author_elem = element.select_one(selector)
                if author_elem:
                    author_text = author_elem.get_text(strip=True)
                    if author_text and not any(skip in author_text.lower() for skip in ['view', 'profile', 'image']):
                        data['author'] = author_text
                        break
            
            # Headline
            headline_elem = element.select_one("span.feed-shared-actor__description, span.update-components-actor__description")
            if headline_elem:
                headline_text = headline_elem.get_text(strip=True)
                if '•' in headline_text:
                    headline_text = headline_text.split('•')[0].strip()
                data['author_headline'] = headline_text
            
            # Time
            time_elem = element.select_one("time")
            if time_elem:
                time_text = time_elem.get_text(strip=True)
                if '•' in time_text:
                    time_parts = time_text.split('•')
                    for part in time_parts:
                        if any(t in part.lower() for t in ['ago', 'h', 'd', 'w', 'm', 'y']):
                            data['posted_time'] = part.strip()
                            break
                else:
                    data['posted_time'] = time_text
            
            # Content
            content_selectors = [
                "div.feed-shared-text span[dir='ltr']",
                "div.update-components-text span.break-words"
            ]
            
            content_parts = []
            for selector in content_selectors:
                content_elems = element.select(selector)
                for elem in content_elems:
                    text = elem.get_text(strip=True)
                    if text and len(text) > 20:
                        text = re.sub(r'hashtag#(\w+)', r'#\1', text)
                        content_parts.append(text)
            
            if content_parts:
                content = ' '.join(list(dict.fromkeys(content_parts)))
                data['content'] = re.sub(r'\s+', ' ', content).strip()
            
            # Engagement metrics
            full_text = element.get_text(' ', strip=True)
            
            likes_match = re.search(r'([\d,]+)\s*(?:reactions?|likes?)', full_text, re.I)
            if likes_match:
                try:
                    data['likes'] = int(likes_match.group(1).replace(',', ''))
                except:
                    pass
            
            comments_match = re.search(r'([\d,]+)\s*comments?', full_text, re.I)
            if comments_match:
                try:
                    data['comments'] = int(comments_match.group(1).replace(',', ''))
                except:
                    pass
            
            reposts_match = re.search(r'([\d,]+)\s*reposts?', full_text, re.I)
            if reposts_match:
                try:
                    data['reposts'] = int(reposts_match.group(1).replace(',', ''))
                except:
                    pass
            
            # Link
            link_elem = element.select_one("a[href*='/feed/update/'], a[href*='/posts/']")
            if link_elem:
                data['link'] = link_elem.get('href')
                if data['link'] and not data['link'].startswith('http'):
                    data['link'] = f"https://www.linkedin.com{data['link']}"
            
            if data['author'] or data['content']:
                return data
            
            return None
            
        except Exception as e:
            return None

    def close(self):
        """Close browser"""
        if self.browser:
            try:
                self.browser.quit()
            except:
                pass
            finally:
                self.browser = None

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def save_to_csv(posts: List[Dict], filename: str = None) -> str:
    """Save posts to CSV file"""
    if not posts:
        print("⚠️  No posts to save")
        return None
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_results_{timestamp}.csv"
    
    df = pd.DataFrame(posts)
    
    # Reorder columns for better readability
    columns = ['author', 'author_headline', 'content', 'posted_time', 
               'likes', 'comments', 'reposts', 'link']
    df = df[[col for col in columns if col in df.columns]]
    
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"💾 Saved {len(posts)} posts to: {filename}")
    return filename

def main():
    """Main execution"""
    print("=" * 70)
    print("LinkedIn Scraper - Standalone Version")
    print("=" * 70)
    print()
    
    # Display configuration
    print("📋 Configuration:")
    print(f"   Keywords: {SEARCH_CONFIG['keywords']}")
    print(f"   Search Type: {SEARCH_CONFIG['search_type']}")
    print(f"   Max Posts: {SEARCH_CONFIG['max_posts']}")
    print(f"   Debug Mode: {SEARCH_CONFIG['debug']}")
    print()
    
    try:
        scraper = LinkedInScraper()
        
        results = scraper.search_content(
            keywords=SEARCH_CONFIG['keywords'],
            search_type=SEARCH_CONFIG['search_type'],
            max_posts=SEARCH_CONFIG['max_posts'],
            debug=SEARCH_CONFIG['debug']
        )
        
        if results:
            csv_file = save_to_csv(results, SEARCH_CONFIG['output_csv'])
            print()
            print("=" * 70)
            print("✅ Scraping completed successfully!")
            print(f"📊 Total posts collected: {len(results)}")
            if csv_file:
                print(f"📁 CSV file: {csv_file}")
            print("=" * 70)
        else:
            print()
            print("=" * 70)
            print("⚠️  No posts found")
            print("=" * 70)
            
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ Error: {str(e)}")
        print("=" * 70)
    finally:
        try:
            scraper.close()
        except:
            pass

if __name__ == "__main__":
    main()
