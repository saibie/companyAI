import os
import json
from collections import defaultdict
from corp.models import Agent, Task

MAX_AGENT_DEPTH = int(os.getenv("MAX_AGENT_DEPTH", "4"))
MAX_TOTAL_AGENTS = int(os.getenv("MAX_TOTAL_AGENTS", "20"))
MAX_SPAN_OF_CONTROL = int(os.getenv("MAX_SPAN_OF_CONTROL", "5"))
MAX_TASK_ATTEMPTS = int(os.getenv("MAX_TASK_ATTEMPTS", "5"))
MAX_REPEATED_TOOL_CALLS = 3

# 메모리 상에 태스크별 최근 도구 호출 이력 추적
_RECENT_TOOL_CALLS = defaultdict(list)

def check_hiring_allowed(manager, owner):
    """
    무한 고용(Infinite Hiring) 방지를 위해 에이전트 고용 제약조건을 검사합니다.
    """
    if manager:
        target_depth = manager.depth + 1
        if target_depth > MAX_AGENT_DEPTH:
            return False, f"조직 최대 깊이 초과 (현재 {target_depth}단계 / 허용 {MAX_AGENT_DEPTH}단계)"

        direct_reports = Agent.objects.filter(manager=manager, is_active=True).count()
        if direct_reports >= MAX_SPAN_OF_CONTROL:
            return False, f"매니저 1인당 최대 직속 부하 수 초과 (현재 {direct_reports}명 / 허용 {MAX_SPAN_OF_CONTROL}명)"

    total_agents = Agent.objects.filter(owner=owner, is_active=True).count()
    if total_agents >= MAX_TOTAL_AGENTS:
        return False, f"회사 전체 에이전트 정원 초과 (현재 {total_agents}명 / 허용 {MAX_TOTAL_AGENTS}명)"

    return True, "Hiring allowed"


def check_tool_loop(task_id, tool_name, tool_args):
    """
    동일 도구를 동일 인자로 연속 반복 호출하는 무한 루프(Circuit Breaker)를 검사합니다.
    """
    key = str(task_id)
    history = _RECENT_TOOL_CALLS[key]
    
    current_call = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
    history.append(current_call)

    # 최근 N개 유지
    if len(history) > 10:
        history.pop(0)

    # 최근 MAX_REPEATED_TOOL_CALLS 개 항목이 모두 동일한지 검사
    if len(history) >= MAX_REPEATED_TOOL_CALLS:
        recent_slice = history[-MAX_REPEATED_TOOL_CALLS:]
        if len(set(recent_slice)) == 1:
            return True, f"무한 루프 감지: 동일 도구 '{tool_name}' 연속 {MAX_REPEATED_TOOL_CALLS}회 호출 차단"

    return False, "No loop"


def clear_tool_history(task_id):
    key = str(task_id)
    if key in _RECENT_TOOL_CALLS:
        del _RECENT_TOOL_CALLS[key]


def check_task_attempt_limit(task):
    """
    태스크 재시도 횟수가 제한을 초과했는지 검사합니다.
    """
    task.attempt_count += 1
    task.save(update_fields=['attempt_count'])
    
    if task.attempt_count > MAX_TASK_ATTEMPTS:
        return True, f"태스크 최대 시도 횟수 초과 ({task.attempt_count}/{MAX_TASK_ATTEMPTS})"
    return False, f"Attempt {task.attempt_count}/{MAX_TASK_ATTEMPTS}"
