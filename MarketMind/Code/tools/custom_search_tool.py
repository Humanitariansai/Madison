import os
# The user's provided example correctly shows BaseTool should be imported from crewai.tools
from crewai.tools import BaseTool
from firecrawl import FirecrawlApp

class WebSearchTool(BaseTool):
    name: str = "Web Search Tool"
    description: str = (
        "Searches the web for a given query using Firecrawl "
        "and returns the search results. Useful for finding information, "
        "product reviews, and understanding general sentiment."
    )

    def _run(self, query: str) -> str:
        """
        The method that executes the tool's logic.
        It searches the web with the given query using the Firecrawl API.
        """
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable not set.")

        app = FirecrawlApp(api_key=api_key)

        print(f"--- Searching the web with Firecrawl for: {query} ---")

        try:
            # Perform a general web search
            search_result = app.search(query=query, limit=10)

            if not search_result or 'data' not in search_result:
                 return f"No web search results found for '{query}'."

            # Process the results into a structured and readable format.
            formatted_results = []
            for result in search_result['data']:
                formatted_results.append({
                    "title": result.get('title', 'No Title'),
                    "url": result.get('url'),
                    "description": result.get('description', 'No Description')
                })

            # Also return a list of URLs for documentation
            urls_found = [result.get('url') for result in search_result['data'] if result.get('url')]
            
            # Create a detailed URL list for the appendix
            url_documentation = []
            for i, url in enumerate(urls_found, 1):
                url_documentation.append(f"{i}. {url}")
            
            result_text = f"Search Results:\n{str(formatted_results)}\n\nURLs Found for Appendix:\n{chr(10).join(url_documentation)}"
            return result_text

        except Exception as e:
            return f"An error occurred during the web search with Firecrawl: {e}"

# We no longer instantiate the tool here.
# It will be instantiated directly in the agent definition.
