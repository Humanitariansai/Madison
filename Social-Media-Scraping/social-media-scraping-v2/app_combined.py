#!/usr/bin/env python3
"""
Combined Social Media Scraper
Supports: Reddit, LinkedIn with MongoDB storage and CSV export
"""
import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
import time
from dotenv import load_dotenv
from pathlib import Path

# Robust import handling
try:
    from src.scrapers.reddit_scraper import RedditScraper
    from src.scrapers.linkedin_scraper import LinkedInScraper
    from src.storage.db import DataStore
except ImportError:
    # Fallback: add src directory to path
    src_dir = Path(__file__).resolve().parent / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from scrapers.reddit_scraper import RedditScraper
    from scrapers.linkedin_scraper import LinkedInScraper
    from storage.db import DataStore

# Page configuration
st.set_page_config(
    page_title="MarketMind",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Hide Streamlit chrome */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 0rem;}

    /* Brand */
    :root {
        --brand: #7aa2f7; /* primary accent */
        --brand-dark: #5c84d1;
        --text: #e5e7eb; /* light text */
        --muted: #9ca3af; /* muted gray */
        --border: #1f2937; /* dark border */
        --bg: #0f1419; /* deep dark */
        --panel: #111827; /* panel background */
    }

    /* Navbar */
    .mm-navbar {position: sticky; top: 0; z-index: 100; background: var(--panel); border-bottom: 1px solid var(--border);}    
    .mm-nav-inner {display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem;}    
    .mm-brand {font-weight: 700; color: var(--text); letter-spacing: 0.2px;}
    /* Nav pills */
    .mm-nav-pills {display: flex; gap: 0.5rem;}
    .mm-pill {padding: 0.4rem 0.8rem; border-radius: 999px; background: transparent; color: var(--muted); border: 1px solid var(--border); cursor: pointer;}
    .mm-pill-active {background: var(--brand); color: #0f1419; border-color: var(--brand);}

    /* Buttons */
    .stButton > button {width: 100%; background-color: var(--brand); color: #0f1419; border: none; padding: 0.6rem 0.8rem; border-radius: 0.5rem;}
    .stButton > button:hover {background-color: var(--brand-dark);}    

    /* Headings */
    .main-header {font-size: 2rem; color: var(--text); margin: 0 0 0.75rem 0;}
    .section-title {font-weight: 600; margin-top: 0.5rem;}
    .small-muted {color: var(--muted); font-size: 0.9rem;}

    /* Cards */
    .mm-card {border: 1px solid var(--border); border-radius: 10px; padding: 1rem; background: var(--panel);}    

    /* Tables */
    div[data-testid="stDataFrame"] {border: 1px solid var(--border); border-radius: 10px; background: var(--panel);}    
    
    /* Hide default Streamlit tabs */
    button[data-baseweb="tab"] {display: none;}
    div[data-baseweb="tab-list"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scraper' not in st.session_state:
    st.session_state.scraper = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0  # 0 = Search, 1 = Results

@st.cache_resource
def initialize_components():
    """Initialize scrapers and database with error handling.
    Note: Do NOT cache LinkedInScraper to avoid keeping a Chrome session in memory.
    """
    try:
        reddit_scraper = RedditScraper()
        db_store = DataStore()
        # Do not create LinkedInScraper here; instantiate per search
        return reddit_scraper, None, db_store, None
    except Exception as e:
        return None, None, None, str(e)

def check_linkedin_credentials():
    """Check if LinkedIn credentials are set"""
    load_dotenv()
    username = os.getenv('LINKEDIN_USERNAME')
    password = os.getenv('LINKEDIN_PASSWORD')
    return username and password

def format_engagement_linkedin(post):
    """Format LinkedIn engagement metrics for display"""
    parts = []
    if post.get('likes', 0) > 0:
        parts.append(f"Likes {post['likes']:,}")
    if post.get('comments', 0) > 0:
        parts.append(f"Comments {post['comments']:,}")
    if post.get('reposts', 0) > 0:
        parts.append(f"Reposts {post['reposts']:,}")
    return " | ".join(parts) if parts else "No engagement data"

def format_post_preview_reddit(posts):
    """Format Reddit posts for table preview"""
    if not posts:
        return pd.DataFrame()
    
    preview_data = []
    for post in posts:
        title = post['title'][:80] + '...' if len(post['title']) > 80 else post['title']
        
        # Add indicators
        indicators = []
        if post.get('nsfw'): indicators.append('🔞')
        if post.get('stickied'): indicators.append('📌')
        if post.get('is_video'): indicators.append('🎥')
        if post.get('spoiler'): indicators.append('⚠️')
        if post.get('gilded', 0) > 0: indicators.append('🥇')
        if post.get('total_awards', 0) > 0: indicators.append('🏆')
        
        title_with_indicators = f"{''.join(indicators)} {title}" if indicators else title
        
        preview_data.append({
            'Subreddit': f"r/{post['subreddit']}",
            'Title': title_with_indicators,
            'Score': post['score'],
            'Upvote %': f"{post.get('upvote_ratio', 0)*100:.0f}%" if post.get('upvote_ratio') else 'N/A',
            'Comments': post['comments'],
            'Author': post['author'],
            'Flair': post.get('link_flair_text', ''),
            'Type': 'Video' if post.get('is_video') else 'Text' if post.get('is_self') else 'Link',
            'Date': post['created_at'].strftime('%Y-%m-%d %H:%M') if post['created_at'] else 'Unknown'
        })
    
    return pd.DataFrame(preview_data)

def export_to_csv(results, platform):
    """Convert results to CSV"""
    df = pd.DataFrame(results)
    return df.to_csv(index=False)

def render_linkedin_results(posts, db_store=None, search_query=""):
    """Render LinkedIn results with cards and analytics"""
    # Persist results defensively
    if posts:
        st.session_state.linkedin_results = posts
    else:
        # Fallback to session
        posts = st.session_state.get('linkedin_results', [])
    if not posts:
        return
    
    st.divider()
    
    # Results header
    st.header(f"Results ({len(posts)} posts)")
    
    # Display options
    display_mode = st.radio(
        "Display Mode",
        options=["Cards", "Table", "Raw Data"],
        horizontal=True,
        key="linkedin_display_mode"
    )
    
    if display_mode == "Cards":
        # Card view
        for i, post in enumerate(posts, 1):
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    author_name = post.get('author', 'Unknown Author')
                    if author_name and author_name != 'None':
                        st.subheader(f"{i}. {author_name}")
                    else:
                        st.subheader(f"{i}. Unknown Author")
                    
                    if post.get('author_headline'):
                        headline = post['author_headline']
                        if headline:
                            headline = headline.replace(author_name, '').strip()
                            parts = headline.split('•')
                            unique_parts = []
                            for part in parts:
                                part = part.strip()
                                if part and part not in unique_parts:
                                    is_duplicate = False
                                    for existing in unique_parts:
                                        if part in existing or existing in part:
                                            is_duplicate = True
                                            break
                                    if not is_duplicate:
                                        unique_parts.append(part)
                            
                            cleaned_headline = ' • '.join(unique_parts[:2])
                            if cleaned_headline and len(cleaned_headline) > 3:
                                st.caption(cleaned_headline[:150])
                    
                    if post.get('posted_time'):
                        time_str = post['posted_time']
                        if '•' in time_str:
                            time_str = time_str.split('•')[0].strip()
                        st.caption(f"{time_str}")
                
                with col2:
                    st.metric("Engagement", "", format_engagement_linkedin(post))
                
                if post.get('content'):
                    content = post['content']
                    if content:
                        content = ' '.join(content.split())
                        content = content.replace('hashtag#', '#')
                        if len(content) > 1000:
                            content = content[:1000] + "..."
                        
                        with st.expander("View Content", expanded=False):
                            st.text_area("Post Content", content, height=200, disabled=True, label_visibility="collapsed", key=f"linkedin_content_{i}")
                
                if post.get('link'):
                    st.markdown(f"[View on LinkedIn]({post['link']})")
                
                st.divider()
    
    elif display_mode == "Table":
        df = pd.DataFrame(posts)
        columns_to_show = ['author', 'posted_time', 'content', 'likes', 'comments', 'reposts']
        available_columns = [col for col in columns_to_show if col in df.columns]
        
        if available_columns:
            if 'content' in df.columns:
                df['content'] = df['content'].apply(lambda x: x[:100] + '...' if x and len(x) > 100 else x)
            
            st.dataframe(df[available_columns], use_container_width=True, height=600)
    
    else:
        st.json(posts)
    
    # Analytics section
    st.divider()
    st.header("Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_likes = sum(post.get('likes', 0) for post in posts)
        st.metric("Total Likes", f"{total_likes:,}")
    
    with col2:
        total_comments = sum(post.get('comments', 0) for post in posts)
        st.metric("Total Comments", f"{total_comments:,}")
    
    with col3:
        total_reposts = sum(post.get('reposts', 0) for post in posts)
        st.metric("Total Reposts", f"{total_reposts:,}")
    
    with col4:
        avg_engagement = (total_likes + total_comments + total_reposts) / len(posts) if posts else 0
        st.metric("Avg Engagement", f"{avg_engagement:.1f}")
    
    # Top posts by engagement
    if any(post.get('likes', 0) > 0 for post in posts):
        st.subheader("Top Posts by Engagement")
        sorted_posts = sorted(
            posts,
            key=lambda x: x.get('likes', 0) + x.get('comments', 0) + x.get('reposts', 0),
            reverse=True
        )[:5]
        
        for i, post in enumerate(sorted_posts, 1):
            total_engagement = post.get('likes', 0) + post.get('comments', 0) + post.get('reposts', 0)
            st.write(f"{i}. **{post.get('author', 'Unknown')}** - {total_engagement:,} total engagements")
    
    # Save to database section (LinkedIn)
    if db_store:
        st.divider()
        st.subheader("Save to Database")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"""
            **Ready to save {len(posts)} LinkedIn posts to MongoDB?**
            
            - Store in dedicated `linkedin_posts` collection
            - Automatically skip duplicates
            - Indexed for fast searching later
            """)
        
        with col2:
            if st.button("Save to DB", type="primary", key="linkedin_save_db"):
                try:
                    stored_count, duplicate_count = save_linkedin_to_db(posts, db_store, search_query)
                    
                    linkedin_stats = db_store.get_linkedin_stats()
                    
                    st.success(f"""
                    Save complete.
                    
                    - {stored_count} new posts saved
                    - {duplicate_count} duplicates skipped
                    - Total LinkedIn posts: {linkedin_stats['total_posts']}
                    """)
                    
                    # Clear results to prevent re-saving
                    if 'results' in st.session_state:
                        del st.session_state.results
                    
                except Exception as e:
                    st.error(f"Save error: {str(e)}")

def save_linkedin_to_db(posts, db_store, search_query):
    """Save LinkedIn posts to database"""
    import hashlib
    
    save_progress = st.progress(0)
    save_status = st.empty()
    
    try:
        save_status.text("Saving LinkedIn posts to database...")
        
        stored_count = 0
        duplicate_count = 0
        
        for i, post in enumerate(posts):
            # Create a content hash for duplicate detection
            content_for_hash = f"{post.get('author', '')}_{post.get('content', '')}_{post.get('posted_time', '')}"
            content_hash = hashlib.md5(content_for_hash.encode()).hexdigest()
            
            # Format post for LinkedIn database
            post_data = {
                "content_hash": content_hash,
                "author": post.get('author', 'Unknown'),
                "author_headline": post.get('author_headline', ''),
                "content": post.get('content', ''),
                "posted_time": post.get('posted_time', ''),
                "link": post.get('link', ''),
                
                # Engagement metrics
                "metrics": {
                    "likes": post.get('likes', 0),
                    "comments": post.get('comments', 0),
                    "reposts": post.get('reposts', 0),
                    "total_engagement": post.get('likes', 0) + post.get('comments', 0) + post.get('reposts', 0)
                },
                
                # Search metadata
                "search_query": search_query,
                "scraped_via": "streamlit_combined",
                "scraped_at": datetime.now()
            }
            
            if db_store.insert_linkedin_post(post_data):
                stored_count += 1
            else:
                duplicate_count += 1
            
            progress = (i + 1) / len(posts)
            save_progress.progress(progress)
        
        save_progress.empty()
        save_status.empty()
        
        return stored_count, duplicate_count
        
    except Exception as e:
        save_progress.empty()
        save_status.empty()
        raise e

def main():
    # Header
    # Navbar with brand + right-aligned nav pills
    col_nav_left, col_nav_right = st.columns([3, 2])
    with col_nav_left:
        st.markdown('<div class="mm-brand" style="padding: 0.4rem 0;">MarketMind</div>', unsafe_allow_html=True)
    with col_nav_right:
        # Use a radio as nav selector, styled as pills
        current_index = st.session_state.active_tab if 'active_tab' in st.session_state else 0
        nav_choice = st.radio(
            label="Navigation",
            options=["Search", "Results"],
            index=current_index,
            horizontal=True,
            key="mm_nav_choice",
            label_visibility="collapsed"
        )
        # Sync session state
        st.session_state.active_tab = 0 if nav_choice == "Search" else 1
        # (Removed duplicate visual pills to avoid extra buttons)
    st.markdown("<div style='border-bottom:1px solid var(--border); margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    
    # Initialize components
    reddit_scraper, linkedin_scraper, db_store, error = initialize_components()
    
    # Render content based on active_tab instead of using st.tabs
    if st.session_state.active_tab == 0:
        # Search tab content
        with st.sidebar:
            st.subheader("Search Settings")
            
            # Platform selection
            available_platforms = ["Reddit", "LinkedIn"]
            if os.getenv("DISABLE_LINKEDIN", "false").lower() == "true":
                available_platforms = ["Reddit"]
            platform = st.selectbox(
                "Select Platform",
                available_platforms,
                index=0,
                help="Choose which social media platform to scrape"
            )
            
            st.markdown("---")

            # Search input
            if platform == "LinkedIn":
                search_type = st.radio("Search Type", options=["keywords", "hashtag"], horizontal=True)

                if search_type == "hashtag":
                    search_query = st.text_input(
                        "Enter Hashtag",
                        placeholder="e.g., artificialintelligence",
                        help="Enter hashtag without the # symbol",
                        key="linkedin_hashtag_input"
                    )
                else:
                    search_query = st.text_area(
                        "Enter Keywords",
                        placeholder="One keyword per line",
                        height=100,
                        key="linkedin_keywords_input"
                    )

                verification_code = st.text_input("Verification Code (if prompted)", type="password")
            else:
                # Reddit search
                search_query = st.text_input(
                    "Brand/Keyword to Search",
                    placeholder="e.g., Apple, Tesla, Nike",
                    help="Enter the brand or keywords you want to search for on Reddit",
                    key="reddit_search_input"
                )

            # Number of posts
            num_posts = st.slider(
                "Number of Posts",
                min_value=5,
                max_value=100,
                value=20,
                step=5,
                help="How many posts to scrape"
            )

            # Reddit-specific filters
            if platform == "Reddit":
                time_filter_type = st.radio("Time Filter", ["Preset", "Custom Range"], index=0, horizontal=True)

                if time_filter_type == "Preset":
                    time_filter = st.selectbox(
                        "Time Period",
                        ["week", "month", "year", "all"],
                        index=0,
                        help="Filter posts by time period"
                    )
                    start_date = None
                    end_date = None
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        start_date = st.date_input("Start Date")
                    with col2:
                        end_date = st.date_input("End Date")
                    time_filter = "custom"

                # Engagement filters
                st.subheader("Filters")
                min_upvotes = st.number_input("Minimum Upvotes", min_value=0, value=0)

                # Region filter
                selected_regions = st.multiselect("Region", ["Global", "North America", "Europe", "Asia", "Oceania", "South America", "Africa"], default=["Global"])

            st.markdown("---")

            # Search history
            if st.session_state.search_history:
                st.subheader("Search History")
                for i, search in enumerate(st.session_state.search_history[-5:]):
                    st.text(f"{search['time']}: {search['query']} ({search['count']} posts)")

            # Database stats (if available)
            if db_store:
                try:
                    stats = db_store.get_stats()
                    st.header("📊 Database Stats")

                    if platform == "Reddit":
                        st.metric("Reddit Posts", stats['total_posts'])
                    elif platform == "LinkedIn":
                        st.metric("LinkedIn Posts", stats.get('linkedin_posts', 0))

                    # Show combined total
                    total_all = stats['total_posts'] + stats.get('linkedin_posts', 0)
                    st.metric("Total Posts", total_all)
                except Exception as e:
                    pass
        
        # Validate credentials
        can_search = True
        if 'platform' in locals():
            if platform == "LinkedIn" and not check_linkedin_credentials():
                st.error("LinkedIn credentials missing. Set LINKEDIN_USERNAME and LINKEDIN_PASSWORD in your environment.")
                can_search = False
            elif platform == "Reddit" and error:
                st.error(f"Setup Error: {error}")
                st.markdown("""
                **Please check:**
                - Your `.env` file has Reddit API credentials
                - Run `python test_apis.py` to verify setup
                """)
                can_search = False
        
        # Always-enabled search button - validate on click
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            search_button = st.button(
                f"Search {platform if 'platform' in locals() else 'Platform'}",
                use_container_width=True,
                type="primary"
            )
        
        # Execute search with validation
        if search_button:
            # Validate query exists
            if not ('search_query' in locals() and search_query):
                st.warning("Please enter a search query.")
            elif not can_search:
                st.error("Cannot search - check credentials above.")
            elif 'platform' in locals():
                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                
                try:
                    with status_placeholder.container():
                        st.caption(f"Searching {platform}...")
                    
                    if platform == "LinkedIn":
                        # LinkedIn search
                        keywords = search_query.strip() if search_type == "hashtag" else \
                                  [k.strip() for k in search_query.split("\n") if k.strip()]
                        
                        with st.spinner(f"Scraping {num_posts} posts..."):
                            runner_url = os.getenv("LINKEDIN_RUNNER_URL")
                            runner_token = os.getenv("LINKEDIN_RUNNER_TOKEN")
                            if runner_url:
                                import requests
                                # Health check before scrape to avoid fallback surprises
                                try:
                                    headers_health = {"X-Auth-Token": runner_token} if runner_token else {}
                                    hc = requests.get(f"{runner_url}/health", headers=headers_health, timeout=8)
                                    if hc.status_code != 200:
                                        raise Exception(f"Runner health failed (HTTP {hc.status_code})")
                                except Exception as e:
                                    raise Exception(f"Local Runner not reachable: {str(e)}. Update LINKEDIN_RUNNER_URL and redeploy.")
                                
                                payload = {
                                    "keywords": keywords if search_type != "hashtag" else [keywords],
                                    "search_type": search_type,
                                    "max_posts": num_posts,
                                    "verification_code": verification_code if verification_code else None,
                                    "debug": False
                                }
                                headers = {"X-Auth-Token": runner_token} if runner_token else {}
                                try:
                                    resp = requests.post(f"{runner_url}/scrape", json=payload, headers=headers, timeout=120)
                                    resp.raise_for_status()
                                    data = resp.json()
                                    results = data.get("results", [])
                                except Exception as e:
                                    raise Exception(f"LinkedIn local runner error: {str(e)}")
                            else:
                                # Fallback: run within this process (local dev)
                                if linkedin_scraper is None:
                                    linkedin_scraper = LinkedInScraper()
                                results = linkedin_scraper.search_content(
                                    keywords=keywords,
                                    search_type=search_type,
                                    max_posts=num_posts,
                                    debug=False,
                                    verification_code=verification_code if verification_code else None
                                )
                    
                    else:
                        # Reddit search
                        with st.spinner(f"Scraping {num_posts} posts..."):
                            results = reddit_scraper.search_subreddits(
                                query=search_query,
                                limit=num_posts,
                                time_filter=time_filter,
                                start_date=start_date if time_filter == "custom" else None,
                                end_date=end_date if time_filter == "custom" else None,
                                min_upvotes=min_upvotes,
                                regions=None if "Global" in selected_regions else selected_regions
                            )
                    
                    # Store results
                    st.session_state.results = results
                    st.session_state.search_query = search_query
                    st.session_state.search_platform = platform
                    st.session_state.search_time = datetime.now()
                    
                    # Add to search history
                    st.session_state.search_history.append({
                        'time': datetime.now().strftime("%H:%M:%S"),
                        'query': search_query if isinstance(search_query, str) else ", ".join(search_query) if isinstance(search_query, list) else str(search_query),
                        'count': len(results)
                    })
                    
                    # Clear status
                    status_placeholder.empty()
                    progress_placeholder.empty()
                except Exception as e:
                    error_message = str(e)
                    st.error(f"Error: {error_message}")
                    if "verification code" in error_message.lower() or "failed to login" in error_message.lower():
                        st.warning("LinkedIn verification required. Enter the code and retry.")
                    else:
                        try:
                            if platform == "LinkedIn" and linkedin_scraper and getattr(linkedin_scraper, 'close', None):
                                linkedin_scraper.close()
                        except Exception:
                            pass
                    status_placeholder.empty()
                    progress_placeholder.empty()
    
    else:
        # Results tab content
        # Hide sidebar on Results tab
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] { display: none; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.subheader("Saved Results")
        if not db_store:
            st.info("Database not configured.")
        else:
            view_platform = st.radio("Platform", ["Reddit", "LinkedIn"], horizontal=True)
            keyword_filter = st.text_input("Keyword filter", placeholder="e.g., apple, tesla, ai")
            limit = st.slider("Max rows", 10, 500, 100, 10)
            st.markdown("---")

            if view_platform == "Reddit":
                if keyword_filter:
                    posts = db_store.search_posts(keyword_filter, limit=limit)
                else:
                    posts = db_store.filter_by_platform("reddit", limit=limit)

                if posts:
                    # Normalize preview
                    preview = []
                    for p in posts:
                        preview.append({
                            "Subreddit": p.get("subreddit", ""),
                            "Title": p.get("title", ""),
                            "Author": p.get("author", ""),
                            "Score": p.get("metrics", {}).get("score"),
                            "Comments": p.get("metrics", {}).get("comments"),
                            "Upvote %": p.get("metrics", {}).get("upvote_ratio"),
                            "Created": p.get("created_at")
                        })
                    df = pd.DataFrame(preview)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No posts found.")

            else:
                posts = db_store.get_linkedin_posts(keyword=keyword_filter or None, limit=limit)
                if posts:
                    preview = []
                    for p in posts:
                        preview.append({
                            "Author": p.get("author", ""),
                            "Headline": p.get("author_headline", ""),
                            "Posted": p.get("posted_time", ""),
                            "Likes": p.get("metrics", {}).get("likes"),
                            "Comments": p.get("metrics", {}).get("comments"),
                            "Reposts": p.get("metrics", {}).get("reposts"),
                            "Content": (p.get("content") or "")[:120]
                        })
                    df = pd.DataFrame(preview)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No posts found.")
    
    # Display results (from last scrape) - show in Search tab after scraping
    if st.session_state.results:
        results = st.session_state.results
        platform_name = st.session_state.get('search_platform', 'Unknown')
        search_query_val = st.session_state.get('search_query', '')
        
        if platform_name == "LinkedIn":
            render_linkedin_results(results, db_store, search_query_val)
            # Keep results in session so table view and Save to DB work
            # You can clear results manually after saving or via a button.
        
        else:
            # Reddit results
            st.divider()
            st.subheader("Results")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Posts Found", len(results))
            
            with col2:
                avg_score = sum(post['score'] for post in results) / len(results) if results else 0
                st.metric("Avg Score", f"{avg_score:.1f}")
            
            with col3:
                avg_upvote_ratio = sum(post.get('upvote_ratio', 0) for post in results) / len(results) if results else 0
                st.metric("Avg Upvote %", f"{avg_upvote_ratio*100:.0f}%")
            
            with col4:
                total_awards = sum(post.get('total_awards', 0) for post in results)
                st.metric("Total Awards", total_awards)
            
            # Preview table
            st.caption("Preview")
            preview_df = format_post_preview_reddit(results)
            
            if not preview_df.empty:
                st.dataframe(preview_df, use_container_width=True, hide_index=True)
                
                # Export removed per request
                
                # Save to database section
                if db_store:
                    st.subheader("Save to Database")
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"""
                        **Ready to save {len(results)} posts to MongoDB?**
                        
                        - Store all posts with full metadata
                        - Automatically skip duplicates
                        - Indexed for fast searching later
                        """)
                    
                    with col2:
                        if st.button("💾 Save to DB", type="primary"):
                            save_progress = st.progress(0)
                            save_status = st.empty()
                            
                            try:
                                save_status.text("💾 Saving posts to database...")
                                
                                stored_count = 0
                                duplicate_count = 0
                                
                                for i, post in enumerate(results):
                                    # Format post for database
                                    post_data = {
                                        "id": post["id"],
                                        "platform": "reddit",
                                        "title": post["title"],
                                        "content": post["text"],
                                        "author": post["author"],
                                        "url": post["url"],
                                        "permalink": post.get("permalink"),
                                        "domain": post.get("domain"),
                                        "subreddit": post["subreddit"],
                                        "metrics": {
                                            "score": post["score"], 
                                            "comments": post["comments"],
                                            "upvote_ratio": post.get("upvote_ratio"),
                                            "gilded": post.get("gilded", 0),
                                            "total_awards": post.get("total_awards", 0)
                                        },
                                        "content_flags": {
                                            "nsfw": post.get("nsfw", False),
                                            "spoiler": post.get("spoiler", False),
                                            "stickied": post.get("stickied", False),
                                            "locked": post.get("locked", False),
                                            "archived": post.get("archived", False),
                                            "distinguished": post.get("distinguished"),
                                            "is_video": post.get("is_video", False),
                                            "is_original_content": post.get("is_original_content", False),
                                            "is_self": post.get("is_self", False)
                                        },
                                        "flair": {
                                            "link_flair_text": post.get("link_flair_text"),
                                            "link_flair_css_class": post.get("link_flair_css_class"),
                                            "author_flair_text": post.get("author_flair_text")
                                        },
                                        "created_at": post["created_at"],
                                        "edited_at": post.get("edited"),
                                        "search_brand": st.session_state.get('search_query', ''),
                                        "scraped_via": "streamlit_combined",
                                        "scraped_at": datetime.now()
                                    }
                                    
                                    if db_store.insert_post(post_data):
                                        stored_count += 1
                                    else:
                                        duplicate_count += 1
                                    
                                    progress = (i + 1) / len(results)
                                    save_progress.progress(progress)
                                
                                save_progress.empty()
                                save_status.empty()
                                
                                st.success(f"""
                                Save complete.
                                
                                - {stored_count} new posts saved
                                - {duplicate_count} duplicates skipped
                                - Total: {db_store.get_stats()['total_posts']} posts
                                """)
                                
                                # Clear results
                                if 'results' in st.session_state:
                                    del st.session_state.results
                                
                            except Exception as e:
                                save_progress.empty()
                                save_status.empty()
                                st.error(f"❌ **Save Error**: {str(e)}")

if __name__ == "__main__":
    main()
    # Footer
    st.markdown(
        """
        <div style="border-top: 1px solid var(--border); margin-top: 1.5rem; padding-top: 0.75rem; color: var(--muted); font-size: 0.9rem;">
            MarketMind • Built for brand intelligence and social insights
        </div>
        """,
        unsafe_allow_html=True,
    )
