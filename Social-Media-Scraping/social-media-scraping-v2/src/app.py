import streamlit as st
import pandas as pd
from scrapers.linkedin_scraper import LinkedInScraper
from typing import Dict, List
import json

def initialize_session_state():
    """Initialize session state variables"""
    if 'scraper' not in st.session_state:
        st.session_state.scraper = None
    if 'scraped_data' not in st.session_state:
        st.session_state.scraped_data = None

def display_results(results: List[Dict], platform: str):
    """Display scraped results in a nice format"""
    if not results:
        st.warning("No results found!")
        return
    
    # Convert results to DataFrame for better display
    df = pd.DataFrame(results)
    
    # Display each post in a card-like format
    for idx, row in df.iterrows():
        with st.expander(f"Post {idx + 1}", expanded=True):
            if row['author']:
                st.markdown(f"**Author:** {row['author']}")
            if row['author_headline']:
                st.markdown(f"**Headline:** {row['author_headline']}")
            if row['content']:
                st.markdown("**Content:**")
                st.markdown(row['content'])
            if row['engagement']:
                st.markdown(f"**Engagement:** {row['engagement']}")
            if row['link']:
                if isinstance(row['link'], list):
                    st.markdown("**Links:**")
                    for link in row['link']:
                        st.markdown(f"- {link}")
                else:
                    st.markdown(f"**Link:** {row['link']}")
            st.markdown("---")

    # Add button to save to database
    if st.button("Save to Database"):
        # TODO: Implement database save functionality
        results_json = json.dumps(results)
        st.success("Data saved successfully!")
        st.code(results_json, language='json')

def main():
    st.title("Social Media Content Scraper")
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Platform selection
        platform = st.selectbox(
            "Select Platform",
            ["LinkedIn", "Twitter", "Instagram"],  # Add more platforms as they're implemented
            key="platform"
        )
        
        # Search type selection for LinkedIn
        if platform == "LinkedIn":
            search_type = st.selectbox(
                "Search Type",
                ["keywords", "hashtag"],
                key="search_type"
            )
        
        # Search query input
        search_query = st.text_input("Enter Search Query", key="search_query")
        
        # Number of posts to scrape
        num_posts = st.number_input(
            "Number of Posts to Scrape",
            min_value=1,
            max_value=100,
            value=10,
            key="num_posts"
        )
        
        # Add scrape button
        scrape_button = st.button("Scrape Content")
    
    # Main content area
    if scrape_button and search_query:
        try:
            with st.spinner(f"Scraping {platform} for '{search_query}'..."):
                if platform == "LinkedIn":
                    if not st.session_state.scraper:
                        st.session_state.scraper = LinkedInScraper()
                    
                    # Convert search query to list if using keywords
                    if search_type == "keywords":
                        query = search_query.split()
                    else:
                        query = search_query
                    
                    # Get results
                    results = st.session_state.scraper.search_content(
                        keywords=query,
                        search_type=search_type,
                        max_posts=num_posts
                    )
                    
                    # Store in session state
                    st.session_state.scraped_data = results
                    
                    # Display results
                    display_results(results, platform)
                    
                else:
                    st.error(f"{platform} scraping not implemented yet!")
        
        except Exception as e:
            st.error(f"Error occurred while scraping: {str(e)}")
            if st.session_state.scraper:
                st.session_state.scraper.close()
                st.session_state.scraper = None

    # Add cleanup on session end
    if st.session_state.scraper:
        import atexit
        atexit.register(st.session_state.scraper.close)

if __name__ == "__main__":
    main()