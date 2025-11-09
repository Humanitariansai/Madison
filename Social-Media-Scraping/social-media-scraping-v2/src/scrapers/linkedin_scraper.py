import os
import time
from datetime import datetime
from typing import List, Dict, Union
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

class LinkedInScraper:
    def __init__(self):
        load_dotenv()
        self.username = os.getenv('LINKEDIN_USERNAME')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.browser = None
        
    def initialize_browser(self):
        """Initialize and return a Chrome browser instance"""
        chrome_options = Options()
        # Add options for better performance/reliability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        # Uncomment below line to run in headless mode
        # chrome_options.add_argument('--headless')
        
        # Initialize Chrome with automatic driver management
        driver_install_path = ChromeDriverManager().install()

        # webdriver-manager sometimes returns a path to a NOTICE file (e.g. THIRD_PARTY_NOTICES.chromedriver)
        # or a directory. Detect that case and try to locate the actual chromedriver binary.
        driver_path = driver_install_path
        try:
            # If install returned a directory, look for an executable named like 'chromedriver'
            if os.path.isdir(driver_install_path):
                for fname in os.listdir(driver_install_path):
                    if fname.startswith('chromedriver'):
                        candidate = os.path.join(driver_install_path, fname)
                        if os.path.isfile(candidate):
                            driver_path = candidate
                            break

            # If install returned a file but it's not executable or is a NOTICE file, search parent dir
            if (not os.access(driver_path, os.X_OK)) or driver_path.endswith('THIRD_PARTY_NOTICES.chromedriver'):
                parent = os.path.dirname(driver_install_path)
                for root, dirs, files in os.walk(parent):
                    for fname in files:
                        if fname.startswith('chromedriver'):
                            candidate = os.path.join(root, fname)
                            if os.path.isfile(candidate):
                                driver_path = candidate
                                break
                    if driver_path != driver_install_path:
                        break

            # Ensure driver binary is executable
            try:
                os.chmod(driver_path, 0o755)
            except Exception:
                # If chmod fails, continue and let Service raise a clearer error later
                pass
        except Exception:
            # If anything unexpected happens while locating the binary, keep the original path
            driver_path = driver_install_path

        # Fallback: if the resolved path still looks wrong, try system chromedriver
        if not os.path.isfile(driver_path) or not os.access(driver_path, os.X_OK):
            # try to use 'chromedriver' from PATH
            from shutil import which

            system_path = which('chromedriver')
            if system_path:
                driver_path = system_path

        service = Service(driver_path)
        self.browser = webdriver.Chrome(service=service, options=chrome_options)
        return self.browser

    def login(self) -> bool:
        """Login to LinkedIn"""
        try:
            self.browser.get('https://www.linkedin.com/uas/login')
            
            # Find and fill username
            username_elem = self.browser.find_element(By.ID, 'username')
            username_elem.send_keys(self.username)
            
            # Find and fill password
            password_elem = self.browser.find_element(By.ID, 'password')
            password_elem.send_keys(self.password)
            password_elem.send_keys(Keys.RETURN)
            
            return True
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def search_content(self, keywords: Union[str, List[str]], search_type: str = 'hashtag', max_posts: int = 10) -> List[Dict]:
        """
        Search LinkedIn content by keywords or hashtag
        
        Args:
            keywords: String for hashtag, or list of keywords for keyword search
            search_type: 'hashtag' or 'keywords'
            max_posts: Maximum number of posts to retrieve (default: 10)
            
        Returns:
            List of dictionaries containing scraped data
        """
        print(f"\nInitializing search for: {keywords}")
        if not self.browser:
            print("Initializing browser...")
            self.initialize_browser()
            print("Logging in to LinkedIn...")
            if not self.login():
                raise Exception("Failed to login to LinkedIn")
            print("Login successful!")
            # Add a delay after login to ensure we're properly authenticated
            time.sleep(3)

        try:
            # First ensure we're on the search page
            self.browser.get('https://www.linkedin.com/search/results/content/')
            time.sleep(2)

            # Look for the search box
            search_box = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.search-global-typeahead__input"))
            )
            
            # Clear any existing search
            search_box.clear()
            
            # Convert keywords to search string
            if search_type == 'hashtag':
                if isinstance(keywords, list):
                    keywords = keywords[0]  # Take first keyword for hashtag search
                search_query = f"#{keywords}"
            else:
                if isinstance(keywords, str):
                    keywords = [keywords]
                search_query = ' '.join(keywords)
            
            print(f"Searching for: {search_query}")
            
            # Enter search terms and submit
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for search results to load
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results-container, .scaffold-finite-scroll__content"))
            )
            
            # Additional wait to ensure content loads
            time.sleep(3)
            
            # Initialize posts list and tracking variables
            posts = []
            scroll_count = 0
            max_scrolls = 30
            last_height = self.browser.execute_script("return document.documentElement.scrollHeight")
            
            # Main scrolling and scraping loop
            while len(posts) < max_posts and scroll_count < max_scrolls:
                # Get current page content
                soup = BeautifulSoup(self.browser.page_source, 'lxml')
                
                # Find main container
                main_content = soup.find('div', {'class': 'search-results-container'})
                if not main_content:
                    main_content = soup.find('div', {'class': 'scaffold-finite-scroll__content'})
                
                if main_content:
                    # Find all post containers
                    post_elements = main_content.find_all('div', {
                        'class': ['feed-shared-update-v2', 'update-components-actor']
                    })
                    
                    # Process new posts
                    current_length = len(posts)
                    for post_element in post_elements:
                        # Extract data from post
                        post_data = self._extract_post_data(post_element)
                        if post_data and post_data not in posts:  # Check for duplicates
                            posts.append(post_data)
                            print(f"Found post {len(posts)}/{max_posts}")
                            if len(posts) >= max_posts:
                                break
                
                # Break if we found enough posts
                if len(posts) >= max_posts:
                    break
                
                # Scroll down
                self.browser.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(2)  # Wait for content to load
                
                # Get new height
                new_height = self.browser.execute_script("return document.documentElement.scrollHeight")
                
                # If heights are the same and we haven't found new posts, we might be at the end
                if new_height == last_height and len(posts) == current_length:
                    scroll_count += 1
                else:
                    scroll_count = 0  # Reset counter if we made progress
                    
                last_height = new_height
                
                # Expand any "show more" buttons
                self._expand_content()
            
            # Cleanup and return results
            self.logout()
            self.close()
            return posts[:max_posts]  # Ensure we don't return more than requested
            
            # If we have enough posts, expand content and extract
            if enough_posts:
                # Only expand visible posts
                self._expand_content()
                
                # Get posts from the page
                soup = BeautifulSoup(self.browser.page_source, 'lxml')
                posts = []
                
                # Find main container
                main_content = soup.find('div', {'class': 'search-results-container'})
                if not main_content:
                    main_content = soup.find('div', {'class': 'scaffold-finite-scroll__content'})
                
                if main_content:
                    # Find all post containers
                    post_elements = main_content.find_all('div', {
                        'class': ['feed-shared-update-v2', 'update-components-actor']
                    })
                    
                    # Extract data from each post
                    for post_element in post_elements[:max_posts]:
                        post_data = self._extract_post_data(post_element)
                        if post_data:
                            posts.append(post_data)
                
                # Logout and close browser
                self.close()
                return posts
                
            # If we don't have enough posts after scrolling, try to get what we can
            self._expand_content()
            
            # Get posts from the page
            soup = BeautifulSoup(self.browser.page_source, 'lxml')
            posts = []
            
            # Find main container
            main_content = soup.find('div', {'class': 'search-results-container'})
            if not main_content:
                main_content = soup.find('div', {'class': 'scaffold-finite-scroll__content'})
            
            if main_content:
                # Find all post containers
                post_elements = main_content.find_all('div', {
                    'class': ['feed-shared-update-v2', 'update-components-actor']
                })
                
                # Extract data from each post
                for post_element in post_elements[:max_posts]:
                    post_data = self._extract_post_data(post_element)
                    if post_data:
                        posts.append(post_data)
            
            # Logout and close browser
            self.close()
            return posts
            
        except Exception as e:
            print(f"Error during search: {str(e)}")
            # If direct search fails, try using the URL method as fallback
            try:
                if search_type == 'hashtag':
                    if isinstance(keywords, list):
                        keywords = keywords[0]
                    link = f'https://www.linkedin.com/feed/hashtag/{keywords}/'
                else:
                    if isinstance(keywords, str):
                        keywords = [keywords]
                    link = 'https://www.linkedin.com/search/results/content/?keywords=' + '%20'.join(keywords)
                
                print(f"Trying direct URL: {link}")
                self.browser.get(link)
                time.sleep(3)
                
                self._scroll_page()
                self._expand_content()
                
                # Get posts from the page
                soup = BeautifulSoup(self.browser.page_source, 'lxml')
                posts = []
                
                # Find main container
                main_content = soup.find('div', {'class': 'search-results-container'})
                if not main_content:
                    main_content = soup.find('div', {'class': 'scaffold-finite-scroll__content'})
                
                if main_content:
                    # Find all post containers
                    post_elements = main_content.find_all('div', {
                        'class': ['feed-shared-update-v2', 'update-components-actor']
                    })
                    
                    # Extract data from each post
                    for post_element in post_elements[:max_posts]:
                        post_data = self._extract_post_data(post_element)
                        if post_data:
                            posts.append(post_data)
                
                return posts
                
            except Exception as e2:
                print(f"Both search methods failed: {str(e2)}")
                return []

    def _scroll_page(self, scroll_count: int = 10, pause_time: int = 3, max_posts: int = 10):
        """
        Scroll the page to load more content
        Returns True if enough posts are found, False otherwise
        """
        last_height = self.browser.execute_script("return document.body.scrollHeight")
        
        for _ in range(scroll_count):
            # Check if we have enough posts before scrolling more
            page_source = self.browser.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Count available posts
            post_items = []
            containers = soup.find_all('div', {'class': ['search-results-container', 'scaffold-finite-scroll__content']})
            for container in containers:
                items = container.find_all(['div', 'article'], {
                    'class': [
                        'feed-shared-update-v2',
                        'update-components-actor',
                        'search-content-card',
                        'feed-shared-update-v2__content',
                        'relative',
                        'occludable-update',
                        'ember-view'
                    ]
                })
                post_items.extend(items)
            
            # If we have enough posts, stop scrolling
            if len(post_items) >= max_posts:
                return True
                
            # Otherwise continue scrolling
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause_time)
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        return False

    def _expand_content(self):
        """Click on 'see more' buttons to expand content"""
        self.browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
        time.sleep(1)
        try:
            # Get visible posts first
            posts = self.browser.find_elements(By.CSS_SELECTOR, 
                "[class*='feed-shared-update-v2'], [class*='search-content-card'], [class*='occludable-update']")
            
            # Only process visible posts
            visible_posts = []
            for post in posts:
                try:
                    if post.is_displayed():
                        visible_posts.append(post)
                except:
                    continue
            
            # Try both old and new class names for "see more" buttons within visible posts
            button_classes = [
                'feed-shared-inline-show-more-text__see-more-less-toggle',
                'inline-show-more-text__button',
                'see-more-less-button'
            ]
            
            for post in visible_posts:
                try:
                    for class_name in button_classes:
                        try:
                            buttons = post.find_elements(By.CLASS_NAME, class_name)
                            for button in buttons:
                                try:
                                    if button.is_displayed():
                                        self.browser.execute_script("arguments[0].click();", button)
                                        time.sleep(0.2)  # Shorter pause between clicks
                                except:
                                    continue
                        except:
                            continue
                except:
                    continue
                    
        except Exception as e:
            print(f"Error expanding content: {str(e)}")

    def _extract_post_data(self, post_element) -> Dict:
        """Extract the minimal required data from a BeautifulSoup post element.

        Returns a dict with keys:
            - author: str or None
            - posted_seconds_ago: int or None (seconds between now and post time)
            - description: str or None
            - likes: int (0 if not found)
            - comments: int (0 if not found)
        """
        try:
            now = datetime.utcnow()

            author = None
            posted_seconds = None
            description = None
            likes = 0
            comments = 0
            author_headline = None

            # --- Author ---
            author_section = post_element.find(['div', 'span'], {
                'class': [
                    'update-components-actor__meta',
                    'feed-shared-actor__meta',
                    'update-components-actor__title',
                    'feed-shared-actor__title'
                ]
            })

            if author_section:
                author_name = author_section.find(['span', 'a'], {
                    'class': [
                        'update-components-actor__name',
                        'feed-shared-actor__name',
                        'update-components-actor__title',
                        'feed-shared-actor__title',
                        'app-aware-link'
                    ]
                })
                if author_name:
                    author = author_name.get_text(strip=True)

                # Try to get author headline/description
                author_desc = author_section.find(['span', 'div'], {
                    'class': [
                        'update-components-actor__description',
                        'feed-shared-actor__description',
                        'update-components-actor__sub-description',
                        'feed-shared-actor__sub-description'
                    ]
                })
                if author_desc:
                    author_headline = author_desc.get_text(strip=True)

            # Try fallback selectors for author
            if not author:
                maybe = post_element.find(['a', 'span'], {'class': ['app-aware-link', 'ember-view']})
                if maybe:
                    author = maybe.get_text(strip=True)

            # --- Time ---
            # Prefer <time datetime="..."> if available
            time_el = post_element.find('time')
            time_text = None
            if time_el:
                datetime_attr = time_el.get('datetime')
                if datetime_attr:
                    try:
                        # parse ISO-like datetime
                        post_dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        posted_seconds = int((now - post_dt).total_seconds())
                    except Exception:
                        # fallback to text
                        time_text = time_el.get_text(strip=True)
                else:
                    time_text = time_el.get_text(strip=True)

            if posted_seconds is None and not time_text:
                # search for time-like text in small tags/spans
                for candidate in post_element.find_all(['span', 'div'], limit=10):
                    t = candidate.get_text(strip=True)
                    if t and any(suffix in t.lower() for suffix in ['h', 'm', 'd', 'w', 'mo', 'y', 'min', 'hr', 'secs', 'sec', 'hour', 'day', 'week', 'month', 'year']):
                        time_text = t
                        break

            if time_text:
                posted_seconds = self._parse_relative_time_to_seconds(time_text)

            # --- Description / post text ---
            content_texts = []
            # Common selectors for LinkedIn post body
            content_selectors = [
                ('div', ['update-components-text', 'feed-shared-update-v2__description']),
                ('span', ['break-words']),
                ('div', ['feed-shared-text', 'feed-shared-update-v2__commentary']),
                ('p', ['attributed-text-segment__text'])
            ]
            for tag, classes in content_selectors:
                for el in post_element.find_all(tag, {'class': classes}):
                    text = el.get_text(separator=' ', strip=True)
                    if text:
                        content_texts.append(text)

            # Fallback: try any element with long text
            if not content_texts:
                for el in post_element.find_all(['p', 'span', 'div']):
                    txt = el.get_text(strip=True)
                    if txt and len(txt) > 40:
                        content_texts.append(txt)
                        break

            if content_texts:
                description = ' '.join(content_texts).strip()

            # --- Likes & comments ---
            full_text = ' '.join([t.get_text(' ', strip=True) for t in post_element.find_all(['span', 'button', 'a', 'li', 'div'])])

            # Try to find patterns like '1,234 likes' or '1,234 reactions' and '123 comments'
            import re

            def _num_from_match(m):
                if not m:
                    return 0
                s = m.group(1)
                s = s.replace(',', '').strip()
                try:
                    return int(s)
                except Exception:
                    try:
                        return int(float(s))
                    except Exception:
                        return 0

            like_match = re.search(r"([0-9,]+)\s*(?:likes?|reactions?)", full_text, flags=re.I)
            if not like_match:
                # sometimes likes are shown as just numbers near reaction icons
                like_match = re.search(r"([0-9,]+)\s*(?:reactions?)", full_text, flags=re.I)
            likes = _num_from_match(like_match)

            comment_match = re.search(r"([0-9,]+)\s*(?:comments?)", full_text, flags=re.I)
            if not comment_match:
                # sometimes comments appear as 'View all 12 comments' or similar
                comment_match = re.search(r"view all\s*([0-9,]+)\s*comments", full_text, flags=re.I)
            comments = _num_from_match(comment_match)

            engagement_str = None
            try:
                engagement_parts = []
                if likes:
                    engagement_parts.append(f"{likes} likes")
                if comments:
                    engagement_parts.append(f"{comments} comments")
                if engagement_parts:
                    engagement_str = ' | '.join(engagement_parts)
            except Exception:
                engagement_str = None

            return {
                'author': author,
                'author_headline': author_headline,
                'posted_seconds_ago': int(posted_seconds) if posted_seconds is not None else None,
                'description': description,
                'content': description,  # backward-compatible alias
                'likes': likes,
                'comments': comments,
                'engagement': engagement_str,
                'link': None
            }

        except Exception as e:
            print(f"Error extracting post data: {str(e)}")
            return None

    def _parse_relative_time_to_seconds(self, time_str: str) -> Union[int, None]:
        """Parse LinkedIn relative time strings like '2d', '3h', '1 mo', '4 weeks' into seconds.

        Returns integer seconds or None if it can't parse.
        """
        try:
            s = time_str.strip().lower()
            # remove bullets or separators
            s = s.replace('\u2022', ' ').replace('·', ' ').strip()

            import re
            # patterns: '5h', '5 h', '5 hrs', '5 hours', '2d', '2 days', '1 mo', '1 month'
            m = re.search(r"(\d+)\s*(s|sec|secs|second|seconds|m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days|w|week|weeks|mo|month|months|y|yr|year|years)", s)
            if not m:
                # maybe text like '2 weeks ago' or '3 months'
                m = re.search(r"(\d+)\s*(week|weeks|month|months|year|years)", s)
            if not m:
                return None

            num = int(m.group(1))
            unit = m.group(2)
            if unit.startswith('s') or unit in ('sec', 'secs', 'second', 'seconds'):
                return num
            if unit in ('m', 'min', 'mins', 'minute', 'minutes'):
                return num * 60
            if unit.startswith('h') or unit in ('hr', 'hrs', 'hour', 'hours'):
                return num * 3600
            if unit.startswith('d') or unit in ('day', 'days'):
                return num * 86400
            if unit.startswith('w') or unit in ('week', 'weeks'):
                return num * 86400 * 7
            if unit in ('mo', 'month', 'months'):
                return num * 86400 * 30
            if unit.startswith('y') or unit in ('yr', 'year', 'years'):
                return num * 86400 * 365
            return None
        except Exception:
            return None

    def logout(self):
        """Logout from LinkedIn"""
        try:
            # Click on the menu button (Me dropdown)
            menu_button = WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.XPATH, "//button[@data-control-name='nav.settings']"))
            )
            self.browser.execute_script("arguments[0].click();", menu_button)
            time.sleep(1)
            
            # Click on Sign Out
            sign_out = WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='/m/logout/']"))
            )
            self.browser.execute_script("arguments[0].click();", sign_out)
            time.sleep(2)
            
            return True
        except Exception as e:
            print(f"Error during logout: {str(e)}")
            return False

    def logout(self):
        """Logout from LinkedIn"""
        try:
            # Click on Me menu
            menu_button = WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-control-name='nav.settings']"))
            )
            self.browser.execute_script("arguments[0].click();", menu_button)
            time.sleep(1)
            
            # Click Sign Out
            sign_out = WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/m/logout/']"))
            )
            sign_out.click()
            time.sleep(2)
            
            return True
        except Exception as e:
            print(f"Error during logout: {str(e)}")
            return False

    def close(self):
        """Close the browser"""
        if self.browser:
            try:
                self.browser.close()
                self.browser.quit()
            except:
                pass
            finally:
                self.browser = None

def main():
    """
    Example usage of the LinkedIn scraper with different search patterns
    """
    scraper = LinkedInScraper()
    
    try:
        # Example 1: Search for company-specific posts
        print("\nSearching for Apple-related posts...")
        results = scraper.search_content(['apple'], search_type='keywords')
        for post in results[:2]:
            print("\nPost:")
            print(f"Author: {post['author'] or 'No author'}")
            print(f"Headline: {post['author_headline'] or 'No headline'}")
            print(f"Content: {post['content'] if post['content'] else 'No content'}")
            if post['engagement']:
                print(f"Engagement: {post['engagement']}")
            if post['link']:
                print(f"Links: {post['link']}")
            
    finally:
        scraper.close()

if __name__ == "__main__":
    main()