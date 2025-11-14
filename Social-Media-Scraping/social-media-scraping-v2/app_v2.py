import streamlit as st
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import hashlib
from pathlib import Path

# Robust import handling
try:
    from src.scrapers.linkedin_scraper import LinkedInScraper
    from src.storage.db import DataStore
except ImportError:
    import sys
    src_dir = Path(__file__).resolve().parent / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from scrapers.linkedin_scraper import LinkedInScraper
    from storage.db import DataStore

# Page configuration
st.set_page_config(
    page_title="LinkedIn Content Scraper",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'scraper' not in st.session_state:
    st.session_state.scraper = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'db_store' not in st.session_state:
    try:
        st.session_state.db_store = DataStore()
    except Exception:
        st.session_state.db_store = None

def check_credentials():
    """Check if LinkedIn credentials are set"""
    load_dotenv()
    username = os.getenv('LINKEDIN_USERNAME')
    password = os.getenv('LINKEDIN_PASSWORD')
    return username and password

def format_engagement(post):
    """Format engagement metrics for display"""
    parts = []
    if post.get('likes', 0) > 0:
        parts.append(f"👍 {post['likes']:,}")
    if post.get('comments', 0) > 0:
        parts.append(f"💬 {post['comments']:,}")
    if post.get('reposts', 0) > 0:
        parts.append(f"🔄 {post['reposts']:,}")
    return " | ".join(parts) if parts else "No engagement data"

def export_to_csv(results):
    """Convert results to CSV"""
    df = pd.DataFrame(results)
    return df.to_csv(index=False)

def save_to_database(posts, search_query):
    """Save LinkedIn posts to database"""
    if not st.session_state.db_store:
        st.error("❌ Database not available. Check MongoDB connection.")
        return
    
    save_progress = st.progress(0)
    save_status = st.empty()
    
    try:
        save_status.text("💾 Saving LinkedIn posts to database...")
        
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
                "scraped_via": "streamlit_app_v2",
                "scraped_at": datetime.now()
            }
            
            if st.session_state.db_store.insert_linkedin_post(post_data):
                stored_count += 1
            else:
                duplicate_count += 1
            
            progress = (i + 1) / len(posts)
            save_progress.progress(progress)
        
        save_progress.empty()
        save_status.empty()
        
        linkedin_stats = st.session_state.db_store.get_linkedin_stats()
        
        st.success(f"""
        🎉 **Save Complete!**
        
        - ✅ **{stored_count}** new posts saved
        - ⚠️ **{duplicate_count}** duplicates skipped
        - 📊 Total LinkedIn posts in DB: **{linkedin_stats['total_posts']}**
        """)
        
        # Clear results to prevent re-saving
        if 'results' in st.session_state:
            del st.session_state.results
        
    except Exception as e:
        save_progress.empty()
        save_status.empty()
        st.error(f"❌ **Save Error**: {str(e)}")

def main():
    # Header
    st.title("🔍 LinkedIn Content Scraper")
    st.markdown("Search and analyze LinkedIn posts with advanced filtering")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Check credentials
        if not check_credentials():
            st.error("❌ LinkedIn credentials not found!")
            st.info("Please set LINKEDIN_USERNAME and LINKEDIN_PASSWORD in your .env file")
            
            with st.expander("Setup Instructions"):
                st.markdown("""
                1. Create a `.env` file in your project directory
                2. Add the following lines:
                   ```
                   LINKEDIN_USERNAME=your_email@example.com
                   LINKEDIN_PASSWORD=your_password
                   ```
                3. Restart the application
                """)
            return
        else:
            st.success("✅ Credentials configured")
        
        st.divider()
        
        # Search parameters
        st.header("🔎 Search Parameters")
        
        search_type = st.radio(
            "Search Type",
            options=["keywords", "hashtag"],
            help="Choose between keyword search or hashtag search"
        )
        
        if search_type == "hashtag":
            keyword_input = st.text_input(
                "Enter Hashtag",
                placeholder="e.g., artificialintelligence",
                help="Enter hashtag without the # symbol"
            )
        else:
            keyword_input = st.text_area(
                "Enter Keywords",
                placeholder="e.g., machine learning\ndata science\nAI",
                help="Enter one keyword per line for multiple keywords"
            )
        
        num_posts = st.slider(
            "Number of Posts",
            min_value=1,
            max_value=50,
            value=10,
            help="Number of posts to retrieve"
        )
        
        debug_mode = st.checkbox("Debug Mode", help="Show detailed logging")
        
        # Search history
        if st.session_state.search_history:
            st.divider()
            st.header("📜 Search History")
            for i, search in enumerate(st.session_state.search_history[-5:]):
                st.text(f"{search['time']}: {search['query']} ({search['count']} posts)")
    
    # Main content area
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        search_button = st.button(
            "🚀 Start Scraping",
            use_container_width=True,
            type="primary",
            disabled=not keyword_input
        )
    
    if search_button and keyword_input:
        # Prepare keywords
        if search_type == "keywords" and "\n" in keyword_input:
            keywords = [k.strip() for k in keyword_input.split("\n") if k.strip()]
        else:
            keywords = keyword_input.strip()
        
        # Create progress placeholder
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        try:
            # Initialize scraper
            with status_placeholder.container():
                st.info("🔄 Initializing scraper...")
            
            scraper = LinkedInScraper()
            
            # Perform search
            with status_placeholder.container():
                st.info(f"🔍 Searching for: {keywords}")
            
            with st.spinner(f"Scraping {num_posts} posts..."):
                results = scraper.search_content(
                    keywords=keywords,
                    search_type=search_type,
                    max_posts=num_posts,
                    debug=debug_mode
                )
            
            # Store results
            st.session_state.results = results
            
            # Store search query for database saving
            st.session_state.last_search_query = keywords if isinstance(keywords, str) else ", ".join(keywords)
            
            # Add to search history
            st.session_state.search_history.append({
                'time': datetime.now().strftime("%H:%M:%S"),
                'query': keywords if isinstance(keywords, str) else ", ".join(keywords),
                'count': len(results)
            })
            
            # Clear status
            status_placeholder.empty()
            progress_placeholder.empty()
            
            # Success message
            st.success(f"✅ Successfully scraped {len(results)} unique posts!")
            
        except Exception as e:
            st.error(f"❌ Error occurred: {str(e)}")
            status_placeholder.empty()
            progress_placeholder.empty()
    
    # Display results
    if st.session_state.results:
        st.divider()
        
        # Results header with export button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.header(f"📊 Results ({len(st.session_state.results)} posts)")
        with col2:
            csv_data = export_to_csv(st.session_state.results)
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name=f"linkedin_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Display options
        display_mode = st.radio(
            "Display Mode",
            options=["Cards", "Table", "Raw Data"],
            horizontal=True
        )
        
        if display_mode == "Cards":
            # Card view
            for i, post in enumerate(st.session_state.results, 1):
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Display author name properly
                        author_name = post.get('author', 'Unknown Author')
                        if author_name and author_name != 'None':
                            st.subheader(f"{i}. {author_name}")
                        else:
                            st.subheader(f"{i}. Unknown Author")
                        
                        if post.get('author_headline'):
                            # Clean up the headline display
                            headline = post['author_headline']
                            # Remove duplicate text that sometimes appears
                            if headline:
                                # Remove author name from headline if it appears there
                                headline = headline.replace(author_name, '').strip()
                                # Remove duplicate parts
                                parts = headline.split('•')
                                unique_parts = []
                                for part in parts:
                                    part = part.strip()
                                    if part and part not in unique_parts:
                                        # Check if this part is not a duplicate of existing parts
                                        is_duplicate = False
                                        for existing in unique_parts:
                                            if part in existing or existing in part:
                                                is_duplicate = True
                                                break
                                        if not is_duplicate:
                                            unique_parts.append(part)
                                
                                cleaned_headline = ' • '.join(unique_parts[:2])  # Max 2 parts
                                if cleaned_headline and len(cleaned_headline) > 3:
                                    st.caption(cleaned_headline[:150])
                        
                        if post.get('posted_time'):
                            # Clean up time display
                            time_str = post['posted_time']
                            # Extract just the time part if it has extra info
                            if '•' in time_str:
                                time_str = time_str.split('•')[0].strip()
                            st.caption(f"⏰ {time_str}")
                    
                    with col2:
                        st.metric("Engagement", "", format_engagement(post))
                    
                    if post.get('content'):
                        # Clean up content display
                        content = post['content']
                        if content:
                            # Remove excessive whitespace
                            content = ' '.join(content.split())
                            # Fix hashtag formatting
                            content = content.replace('hashtag#', '#')
                            # Limit very long content
                            if len(content) > 1000:
                                content = content[:1000] + "..."
                            
                            with st.expander("View Content", expanded=False):
                                st.text_area("Post Content", content, height=200, disabled=True, label_visibility="collapsed", key=f"linkedin_post_{i}")
                    
                    if post.get('link'):
                        st.markdown(f"[🔗 View on LinkedIn]({post['link']})")
                    
                    st.divider()
        
        elif display_mode == "Table":
            # Table view
            df = pd.DataFrame(st.session_state.results)
            
            # Select columns to display
            columns_to_show = ['author', 'posted_time', 'content', 'likes', 'comments', 'reposts']
            available_columns = [col for col in columns_to_show if col in df.columns]
            
            if available_columns:
                # Truncate content for table view
                if 'content' in df.columns:
                    df['content'] = df['content'].apply(lambda x: x[:100] + '...' if x and len(x) > 100 else x)
                
                st.dataframe(
                    df[available_columns],
                    use_container_width=True,
                    height=600
                )
        
        else:
            # Raw data view
            st.json(st.session_state.results)
        
        # Analytics section
        st.divider()
        st.header("📈 Analytics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_likes = sum(post.get('likes', 0) for post in st.session_state.results)
            st.metric("Total Likes", f"{total_likes:,}")
        
        with col2:
            total_comments = sum(post.get('comments', 0) for post in st.session_state.results)
            st.metric("Total Comments", f"{total_comments:,}")
        
        with col3:
            total_reposts = sum(post.get('reposts', 0) for post in st.session_state.results)
            st.metric("Total Reposts", f"{total_reposts:,}")
        
        with col4:
            avg_engagement = (total_likes + total_comments + total_reposts) / len(st.session_state.results) if st.session_state.results else 0
            st.metric("Avg Engagement", f"{avg_engagement:.1f}")
        
        # Top posts by engagement
        if any(post.get('likes', 0) > 0 for post in st.session_state.results):
            st.subheader("🏆 Top Posts by Engagement")
            sorted_posts = sorted(
                st.session_state.results,
                key=lambda x: x.get('likes', 0) + x.get('comments', 0) + x.get('reposts', 0),
                reverse=True
            )[:5]
            
            for i, post in enumerate(sorted_posts, 1):
                total_engagement = post.get('likes', 0) + post.get('comments', 0) + post.get('reposts', 0)
                st.write(f"{i}. **{post.get('author', 'Unknown')}** - {total_engagement:,} total engagements")
        
        # Save to Database section
        if st.session_state.db_store:
            st.divider()
            st.subheader("💾 Save to Database")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                **Ready to save {len(st.session_state.results)} LinkedIn posts to MongoDB?**
                
                - ✅ Store in dedicated `linkedin_posts` collection
                - ✅ Automatically skip duplicates based on content
                - ✅ Include all engagement metrics
                """)
            
            with col2:
                # Get the search query from session state
                search_query = ""
                if 'last_search_query' in st.session_state:
                    search_query = st.session_state.last_search_query
                
                if st.button("💾 Save to DB", type="primary"):
                    save_to_database(st.session_state.results, search_query)
        else:
            st.info("💡 **Tip:** Configure MongoDB to enable database storage for your scraped posts.")

if __name__ == "__main__":
    main()