import requests
from bs4 import BeautifulSoup
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

@tool
def fetch_web_content_tool(url: str) -> str:
    """
    Read the full text content of a specific web page.
    Use this when 'search_web' snippets are too short or incomplete.
    Args:
        url: The URL of the web page to read.
    """
    try:
        # 타임아웃을 10초로 설정하여 무한 대기 방지
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 불필요한 스크립트와 스타일 제거
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        # 텍스트만 추출하고 공백 정리
        text = soup.get_text()
        clean_text = " ".join(text.split())
        
        # LLM 컨텍스트 크기를 고려하여 앞부분 4000자만 반환
        return clean_text[:4000] + ("..." if len(clean_text) > 4000 else "")
        
    except Exception as e:
        return f"Error fetching URL: {str(e)}"