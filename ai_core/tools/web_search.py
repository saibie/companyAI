import os
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from ai_core.llm_gateway import OllamaClient  # 요약을 수행할 클라이언트 임포트

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
        result = search.invoke(query)
        return f"Search Result: {result}"
    except Exception as e:
        return f"Search failed: {str(e)}"

@tool
def fetch_web_content_tool(url: str) -> str:
    """
    Read and SUMMARIZE the content of a specific web page.
    Use this when you need detailed information from a specific URL found via search.
    It returns a concise summary to save your context window.
    
    Args:
        url: The URL of the web page to read.
    """
    print(f"📄 [Tool] Fetching & Summarizing URL: {url}")
    try:
        # 1. 웹페이지 내용 가져오기 (타임아웃 10초)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 2. 불필요한 요소 제거 (스크립트, 스타일, 네비게이션 등)
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            element.extract()
            
        # 3. 텍스트 추출 및 공백 정리
        text = soup.get_text()
        clean_text = " ".join(text.split())
        
        # 4. LLM 입력 한계를 고려하여 원문 자르기
        # (요약 모델에게 던질 때도 너무 길면 에러가 나므로 약 8000자 정도로 제한)
        input_text = clean_text[:8000]
        
        if len(input_text) < 500:
            # 내용이 너무 짧으면 요약 없이 그냥 반환
            return f"📄 [Content of {url}]:\n{input_text}"

        # 5. 요약 프롬프트 작성
        # (별도의 독립적인 요청이므로 시스템 프롬프트 영향 없음)
        summary_prompt = f"""
        Analyze the following web page content and provide a comprehensive summary.
        Focus on facts, key findings, and data relevant to a business or technical context.
        
        [Web Content]:
        {input_text}
        
        [Instruction]:
        Summarize the above content in around 300-500 words.
        """
        
        # 6. OllamaClient를 통해 '단독' 실행 (One-off execution)
        # LangGraph의 State와 무관하게 실행되므로 Context가 누적되지 않음
        client = OllamaClient()
        target_model = os.getenv("LLM_MODEL", "qwen3:8b") # .env에 설정된 모델 사용
        
        response_data = client.generate(model=target_model, prompt=summary_prompt, stream=False)
        summary = response_data.get('response', 'Error: No response from LLM.')
        
        return f"📄 [Summary of {url}]:\n{summary}"
        
    except Exception as e:
        return f"Error fetching/summarizing URL: {str(e)}"