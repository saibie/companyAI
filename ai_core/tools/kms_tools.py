from langchain_core.tools import tool
from corp.services import kms_service

@tool
def search_wiki_tool(query: str) -> str:
    """
    Use this tool to search the Company Wiki/Knowledge Base.
    Useful for finding SOPs, past successful plans, or common rules BEFORE making a plan.
    Args:
        query: Search keywords or a question.
    """
    results = kms_service.search_wiki(query)
    
    if not results:
        return "No relevant information found in the Company Wiki."
        
    formatted_results = "📚 [Company Wiki Search Results]:\n"
    for idx, doc in enumerate(results):
        formatted_results += f"{idx+1}. [Subject: {doc.subject}]\n   {doc.content}\n"
        
    return formatted_results