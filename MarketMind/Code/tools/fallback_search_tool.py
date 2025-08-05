import os
import requests
from crewai.tools import BaseTool

class FallbackSearchTool(BaseTool):
    name: str = "Fallback Search Tool"
    description: str = (
        "A fallback search tool that uses DuckDuckGo or similar search engines "
        "to find information when other search tools fail. Useful for finding "
        "competitor information, company details, and market data."
    )

    def _run(self, query: str) -> str:
        """
        Fallback search method using DuckDuckGo API or similar.
        """
        try:
            # Use DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant information
                results = []
                
                # Add abstract if available
                if data.get('Abstract'):
                    results.append(f"Abstract: {data['Abstract']}")
                
                # Add related topics
                if data.get('RelatedTopics'):
                    for topic in data['RelatedTopics'][:5]:
                        if isinstance(topic, dict) and topic.get('Text'):
                            results.append(f"Related: {topic['Text']}")
                
                # Add answer if available
                if data.get('Answer'):
                    results.append(f"Answer: {data['Answer']}")
                
                if results:
                    return f"Search Results:\n{chr(10).join(results)}\n\nNote: This search used DuckDuckGo API. For more detailed results, use the primary search tool."
                else:
                    return f"Search completed for '{query}' but no specific results found. Try using the primary search tool for more detailed results."
            else:
                return f"Search failed with status code: {response.status_code}"
                
        except Exception as e:
            return f"Fallback search failed: {str(e)}. Please try a different search approach." 