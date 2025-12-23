from ai_core.tools.web_search import search_web, fetch_web_content_tool
from ai_core.tools.math_tools import calculator_tool
from ai_core.tools.org_tools import create_plan
from ai_core.tools.kms_tools import search_wiki_tool
from ai_core.tools.comm_tools import post_to_channel_tool, read_channel_tool, ask_manager_tool, reply_to_subordinate_tool

# [Tier 0] 기본 소양 (모든 에이전트에게 자동 지급)
# - 계산, 계획, 사내 위키 검색, 의사소통(상사에게 질문, 채널 대화)
TIER_0_TOOLS = [
    calculator_tool,
    create_plan,
    search_wiki_tool,
    ask_manager_tool,
    post_to_channel_tool,
    read_channel_tool,
    reply_to_subordinate_tool
]

# [Tier 1] 인가 필요 도구 (CEO 승인 필요)
# - 문자열 Key와 실제 도구 객체 매핑
TIER_1_REGISTRY = {
    "search_web": search_web,
    "fetch_web_content": fetch_web_content_tool,
    # 추후 "python_repl", "execute_shell" 등 위험 도구 추가
}

def get_authorized_tools(allowed_tool_names: list):
    """
    에이전트의 권한 목록(문자열 리스트)을 받아 실제 도구 객체 리스트를 반환합니다.
    """
    tools = []
    for name in allowed_tool_names:
        if name in TIER_1_REGISTRY:
            tools.append(TIER_1_REGISTRY[name])
    return tools