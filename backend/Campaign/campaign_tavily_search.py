# campaign_tavily_search.py

from typing import List, Dict, Any
from pydantic import BaseModel
from tavily import TavilyClient

# --- Pydantic Models (Copied from original for self-containment/clean imports) ---
class ResearchQueries(BaseModel):
    product: str
    audience: str
    colors: str
    competitors: str
    strategy: str
# --- End Pydantic Models ---


def perform_tavily_search(research_queries: ResearchQueries, tavily_client: TavilyClient) -> List[Dict[str, Any]]:
    """Performs the Tavily Advanced Search for all queries."""
    if not tavily_client:
        return [{"error": "Tavily client is not initialized. API key is missing."}]

    # .model_dump() is available because it's a Pydantic model
    queries = research_queries.model_dump().values()
    tavily_results = []
    
    print(f"Running Tavily Advanced Search for {len(queries)} queries...")
    
    for q in queries:
        try:
            result = tavily_client.search(
                query=q,
                search_depth="advanced",
                max_results=2,
                include_raw_content=True
            )
            tavily_results.append({
                "query": q,
                "results": [
                    {
                        "url": r.get("url"),
                        "content_snippet": r.get("content")
                    }
                    for r in result.get("results", [])
                ]
            })
        except Exception as e:
            tavily_results.append({
                "query": q,
                "error": f"Tavily error: {str(e)}"
            })

    return tavily_results