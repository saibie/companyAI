from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

@tool
def search_web(query: str) -> str:
    """
    Use this tool to search the internet for current events or specific information.
    Args:
        query: The search keywords.
    """
    print(f"🔍 [Tool] Searching web for: {query}")
    try:
        search = DuckDuckGoSearchRun()
        # DuckDuckGo 실행 (인터넷 연결 필요)
        result = search.invoke(query)
        return f"Search Result: {result}"
    except Exception as e:
        return f"Search failed: {str(e)}"
