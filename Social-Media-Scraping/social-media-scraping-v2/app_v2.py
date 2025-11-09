#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
import time

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.linkedin_scraper import LinkedInScraper
from storage.db import DataStore

st.set_page_config(
    page_title="Social Media Content Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #0077B5;  /* LinkedIn blue for LinkedIn-focused version */
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #0077B5;
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

def initialize_session_state():
    """Initialize session state variables"""
    if 'scraper' not in st.session_state:
        st.session_state.scraper = None
    if 'scraped_data' not in st.session_state:
        st.session_state.scraped_data = None

def display_results(posts):
    """Display LinkedIn posts in a nice format"""
    if not posts:
        st.warning("No results found!")
        return
        
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Posts", len(posts))
    with col2:
        authors = len(set(post['author'] for post in posts if post['author']))
        st.metric("Unique Authors", authors)
    with col3:
        has_engagement = len([post for post in posts if post.get('engagement')])
        st.metric("Posts with Engagement", has_engagement)
    
    # Add export options
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export to CSV"):
            df = pd.DataFrame(posts)
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                f"linkedin_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with col2:
        if st.button("Export to JSON"):
            json_str = pd.DataFrame(posts).to_json(orient="records", indent=2)
            st.download_button(
                "Download JSON",
                json_str,
                f"linkedin_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json"
            )
    
    # Display posts
    for idx, post in enumerate(posts):
        with st.expander(f"Post {idx + 1}", expanded=idx == 0):
            # Author info
            col1, col2 = st.columns([2, 1])
            with col1:
                if post['author']:
                    st.markdown(f"**Author:** {post['author']}")
                if post['author_headline']:
                    st.markdown(f"**Headline:** {post['author_headline']}")
            with col2:
                if post.get('timestamp'):
                    st.markdown(f"**Posted:** {post['timestamp'][:19]}")
                if post.get('engagement'):
                    st.markdown(f"**Engagement:** {post['engagement']}")
            
            # Content
            if post.get('content'):
                st.markdown("**Content:**")
                st.markdown(post['content'])
            
            # Links
            if post.get('link'):
                st.markdown("**Links:**")
                if isinstance(post['link'], list):
                    for link in post['link']:
                        st.markdown(f"- {link}")
                else:
                    st.markdown(f"- {post['link']}")
            
            st.markdown("---")

def main():
    # Header
    st.markdown('<h1 class="main-header">🔍 LinkedIn Content Scraper</h1>', unsafe_allow_html=True)
    st.markdown("**Search and analyze LinkedIn content with advanced filters**")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Search Settings")
        
        # Search configuration
        search_type = st.selectbox(
            "Search Type",
            ["keywords", "hashtag"],
            help="Choose whether to search by keywords or hashtag"
        )
        
        search_query = st.text_input(
            "Search Query",
            help="Enter keywords or hashtag (without #) to search for"
        )
        
        # Number of posts
        num_posts = st.slider(
            "Number of Posts",
            min_value=1,
            max_value=100,
            value=10,
            help="Maximum number of posts to retrieve"
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            headless_mode = st.checkbox(
                "Headless Mode",
                value=False,
                help="Run browser in background (faster but may be less reliable)"
            )
            
            scroll_pause = st.slider(
                "Scroll Pause (seconds)",
                min_value=1,
                max_value=10,
                value=3,
                help="Time to wait between scrolls for content to load"
            )
        
        # Search button
        search_button = st.button(
            "🔍 Start Search",
            type="primary",
            disabled=not search_query,
            help="Click to start searching"
        )
        
        # Clear results button
        if st.button("🗑️ Clear Results"):
            if st.session_state.scraper:
                st.session_state.scraper.close()
            st.session_state.scraper = None
            st.session_state.scraped_data = None
            st.experimental_rerun()
    
    # Main content area
    if search_button and search_query:
        try:
            with st.spinner(f"Searching LinkedIn for '{search_query}'..."):
                # Initialize scraper if needed
                if not st.session_state.scraper:
                    st.session_state.scraper = LinkedInScraper()
                
                # Create progress bar
                progress = st.progress(0)
                
                # Update progress
                progress.progress(20, "Initializing search...")
                
                # Prepare search query
                if search_type == "keywords":
                    query = search_query.split()
                else:
                    query = search_query
                
                # Update progress
                progress.progress(40, "Searching LinkedIn...")
                
                # Get results
                results = st.session_state.scraper.search_content(
                    keywords=query,
                    search_type=search_type,
                    max_posts=num_posts
                )
                
                # Update progress
                progress.progress(100, "Search complete!")
                time.sleep(0.5)
                progress.empty()
                
                # Store results
                st.session_state.scraped_data = results
                
                # Display results
                display_results(results)
        
        except Exception as e:
            st.error(f"Error occurred: {str(e)}")
            if st.session_state.scraper:
                st.session_state.scraper.close()
                st.session_state.scraper = None
    
    # Display existing results if available
    elif st.session_state.scraped_data:
        display_results(st.session_state.scraped_data)
    
    # Cleanup on session end
    if st.session_state.scraper:
        import atexit
        atexit.register(st.session_state.scraper.close)

if __name__ == "__main__":
    main()