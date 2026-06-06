import logfire
from ddgs import DDGS  # <-- This is the only line that changes!

def web_search(query: str) -> str:
    """
    Searches the public internet for general world facts, author biographies, or topics outside the story.
    """
    with logfire.span('tool.web_search', search_query=query) as span:
        try:
            logfire.info("Initiating DuckDuckGo public internet search...")
            
            # Fetch results using the new, unblocked package
            results = list(DDGS().text(query, max_results=3))
            
            span.set_attribute("results_count", len(results))

            if not results:
                logfire.warn("Search completed, but zero results were returned.")
                return "No public information found for this query."
                
            logfire.info("Search successful. Formatting results for the LLM.")

            formatted_results = "\n\n".join(
                [f"Source: {r.get('title', 'Unknown')}\nInfo: {r.get('body', '')}" for r in results]
            )
            
            return formatted_results
            
        except Exception as e:
            logfire.error("DuckDuckGo search encountered a critical failure.", error=str(e))
            return f"Web search encountered an error: {str(e)}"