#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.reddit_scraper import RedditScraper
from scrapers.linkedin_scraper import LinkedInScraper
from storage.db import DataStore

st.set_page_config(
    page_title="Social Media Brand Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        border: none;
        padding: 0.5rem;
        border-radius: 0.5rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_components():
    try:
        reddit_scraper = RedditScraper()
        linkedin_scraper = LinkedInScraper()
        db_store = DataStore()
        return reddit_scraper, linkedin_scraper, db_store, None
    except Exception as e:
        return None, None, None, str(e)

def format_post_preview(posts):
    if not posts:
        return pd.DataFrame()
    
    preview_data = []
    for post in posts:
        # Add emoji indicators for special content
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

def main():
    # Header
    st.markdown('<h1 class="main-header">🔍 Social Media Brand Scraper</h1>', unsafe_allow_html=True)
    st.markdown("**Search for brand mentions across social media platforms and save to your database**")
    
    # Initialize components
    reddit_scraper, linkedin_scraper, db_store, error = initialize_components()
    
    # Platform selection
    platform = st.sidebar.selectbox(
        "Select Platform",
        ["Reddit", "LinkedIn"],
        index=0,
        help="Choose which social media platform to scrape"
    )
    
    if error:
        st.error(f"❌ **Setup Error**: {error}")
        st.markdown("""
        **Please check:**
        - Your `.env` file has Reddit API credentials
        - MongoDB connection is working
        - Run `python test_apis.py` to verify setup
        """)
        return
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Search Settings")
        
        # Brand/keyword search input
        search_query = st.text_input(
            "Brand/Keyword to Search",
            placeholder="e.g., Apple, Tesla, Nike",
            help=f"Enter the brand or keywords you want to search for on {platform}"
        )
        
        # LinkedIn-specific options
        if platform == "LinkedIn":
            search_type = st.selectbox(
                "Search Type",
                ["keywords", "hashtag"],
                index=0,
                help="Choose whether to search by keywords or hashtag"
            )
        
        # Number of posts
        num_posts = st.slider(
            "Number of Posts",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
            help="How many posts to scrape (more posts = longer search time)"
        )
        
        # Time filter
        time_filter_type = st.radio(
            "Time Filter Type",
            ["Preset", "Custom Range"],
            index=0,
            help="Choose between preset time periods or custom date range"
        )
        
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
                start_date = st.date_input(
                    "Start Date",
                    help="Start date for custom range"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    help="End date for custom range"
                )
            time_filter = "custom"

        # Engagement filters
        st.subheader("📊 Engagement Filters")
        min_upvotes = st.number_input(
            "Minimum Upvotes",
            min_value=0,
            value=0,
            help="Filter posts with at least this many upvotes"
        )

        # Region filter
        st.subheader("🌍 Region Filter")
        selected_regions = st.multiselect(
            "Filter by Region",
            ["Global", "North America", "Europe", "Asia", "Oceania", "South America", "Africa"],
            default=["Global"],
            help="Select specific regions (based on subreddit categories and flairs)"
        )
        
        st.markdown("---")
        
        # Database stats
        if db_store:
            try:
                stats = db_store.get_stats()
                st.header("📊 Database Stats")
                st.metric("Total Posts", stats['total_posts'])
                
                if stats['by_platform']:
                    for platform_stat in stats['by_platform']:
                        if platform_stat['platform'] == 'reddit':
                            st.metric("Reddit Posts", platform_stat['count'])
            except Exception as e:
                st.warning(f"Could not load stats: {e}")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Search section
        st.header("🔍 Search Reddit")
        
        if not brand_name:
            st.info("👆 Enter a brand name in the sidebar to start searching")
            return
        
        # Search button
        if st.button(f"🔍 Search for '{brand_name}'", type="primary"):
            
            # Progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Update progress
                status_text.text("🔍 Searching Reddit...")
                progress_bar.progress(25)
                
                # Search Reddit with filters
                posts = reddit_scraper.search_subreddits(
                    query=brand_name,
                    limit=num_posts,
                    time_filter=time_filter,
                    start_date=start_date if time_filter == "custom" else None,
                    end_date=end_date if time_filter == "custom" else None,
                    min_upvotes=min_upvotes,
                    regions=None if "Global" in selected_regions else selected_regions
                )
                
                progress_bar.progress(75)
                status_text.text(f"✅ Found {len(posts)} posts!")
                
                # Store results in session state
                st.session_state.search_results = posts
                st.session_state.search_brand = brand_name
                st.session_state.search_time = datetime.now()
                
                progress_bar.progress(100)
                time.sleep(0.5)  # Brief pause to show completion
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Success message
                if posts:
                    st.success(f"🎉 Found **{len(posts)}** posts about **{brand_name}**!")
                else:
                    st.warning(f"⚠️ No posts found for **{brand_name}**. Try a different keyword or time period.")
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ **Search Error**: {str(e)}")
    
    with col2:
        # Quick actions
        st.header("⚡ Quick Actions")
        
        if st.button("📈 View Database Stats"):
            if db_store:
                try:
                    stats = db_store.get_stats()
                    st.json(stats)
                except Exception as e:
                    st.error(f"Error loading stats: {e}")
        
        if st.button("🔍 Search History"):
            # Simple search history (could be expanded)
            if 'search_brand' in st.session_state:
                st.info(f"Last search: **{st.session_state.search_brand}** at {st.session_state.search_time.strftime('%H:%M')}")
            else:
                st.info("No search history yet")
    
    # Results section
    if 'search_results' in st.session_state and st.session_state.search_results:
        st.header("📊 Search Results Preview")
        
        posts = st.session_state.search_results
        brand = st.session_state.search_brand
        
        # Results summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Posts Found", len(posts))
        
        with col2:
            avg_score = sum(post['score'] for post in posts) / len(posts) if posts else 0
            st.metric("Avg Score", f"{avg_score:.1f}")
        
        with col3:
            avg_upvote_ratio = sum(post.get('upvote_ratio', 0) for post in posts) / len(posts) if posts else 0
            st.metric("Avg Upvote %", f"{avg_upvote_ratio*100:.0f}%")
        
        with col4:
            total_awards = sum(post.get('total_awards', 0) for post in posts)
            st.metric("Total Awards", total_awards)
        
        # Preview table
        st.subheader("📋 Post Preview")
        
        preview_df = format_post_preview(posts)
        if not preview_df.empty:
            # Display table with selection
            st.dataframe(
                preview_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Save to database section
            st.subheader("💾 Save to Database")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                **Ready to save {len(posts)} posts about '{brand}' to your MongoDB database?**
                
                This will:
                - ✅ Store all posts with full metadata
                - ✅ Automatically skip duplicates
                - ✅ Index for fast searching later
                """)
            
            with col2:
                if st.button("💾 Save to Database", type="primary"):
                    
                    # Progress for saving
                    save_progress = st.progress(0)
                    save_status = st.empty()
                    
                    try:
                        save_status.text("💾 Saving posts to database...")
                        
                        stored_count = 0
                        duplicate_count = 0
                        
                        for i, post in enumerate(posts):
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
                                
                                # Enhanced metrics
                                "metrics": {
                                    "score": post["score"], 
                                    "comments": post["comments"],
                                    "upvote_ratio": post.get("upvote_ratio"),
                                    "gilded": post.get("gilded", 0),
                                    "total_awards": post.get("total_awards", 0)
                                },
                                
                                # Content flags
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
                                
                                # Flair and categorization
                                "flair": {
                                    "link_flair_text": post.get("link_flair_text"),
                                    "link_flair_css_class": post.get("link_flair_css_class"),
                                    "author_flair_text": post.get("author_flair_text")
                                },
                                
                                # Timestamps
                                "created_at": post["created_at"],
                                "edited_at": post.get("edited"),
                                
                                # Scraping metadata
                                "search_brand": brand,
                                "scraped_via": "streamlit_frontend",
                                "scraped_at": datetime.now()
                            }
                            
                            # Save to database
                            if db_store.insert_post(post_data):
                                stored_count += 1
                            else:
                                duplicate_count += 1
                            
                            # Update progress
                            progress = (i + 1) / len(posts)
                            save_progress.progress(progress)
                        
                        # Clear progress indicators
                        save_progress.empty()
                        save_status.empty()
                        
                        # Success message
                        st.success(f"""
                        🎉 **Save Complete!**
                        
                        - ✅ **{stored_count}** new posts saved
                        - ⚠️ **{duplicate_count}** duplicates skipped
                        - 📊 Total posts in database: **{db_store.get_stats()['total_posts']}**
                        """)
                        
                        # Clear search results to prevent re-saving
                        if 'search_results' in st.session_state:
                            del st.session_state.search_results
                        
                    except Exception as e:
                        save_progress.empty()
                        save_status.empty()
                        st.error(f"❌ **Save Error**: {str(e)}")
        
        else:
            st.warning("No posts to preview")

if __name__ == "__main__":
    main()